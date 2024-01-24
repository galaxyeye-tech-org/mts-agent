# -*- coding: utf-8 -*-
import traceback
import sys
import typing
from contextlib import contextmanager

from elasticsearch import helpers, ApiError as ESApiError, NotFoundError as ESNotFoundError, \
    AsyncElasticsearch

from hagworm.extend.asyncio.buffer import QueueBuffer
from hagworm.extend.asyncio.redis import RedisDelegate
from hagworm.extend.metaclass import Singleton
from hagworm.extend.asyncio.base import Utils
from base.agent_public.agent_log import logger

from setting import BaseConfig


@contextmanager
def es_bulk_error():

    try:
        yield
    except helpers.BulkIndexError as err:
        Utils.log.error(err.errors[:5])
    except:
        logger.error(traceback.format_exc())


class DialogElasticsearchDataStreamUtil:

    def __init__(
            self, elasticsearch: AsyncElasticsearch, stream_name: str, *,
            rollover_max_age: str = r'1d', rollover_max_primary_shard_size: str = r'50gb', delete_min_age: str = r'30d',
            refresh_interval: str = r'5s', number_of_replicas=0, timestamp_order: str = r'desc'
    ):

        self._elasticsearch = elasticsearch

        self._stream_name = stream_name
        self._policy_name = f'{stream_name}-ilm-policy'

        self._rollover_max_age = rollover_max_age
        self._rollover_max_primary_shard_size = rollover_max_primary_shard_size

        self._delete_min_age = delete_min_age
        self._refresh_interval = refresh_interval
        self._number_of_replicas = number_of_replicas
        self._timestamp_order = timestamp_order

    async def initialize(self):

        try:
            await self._elasticsearch.indices.get_data_stream(name=self._stream_name)
        except ESNotFoundError as _:
            await self._create_lifecycle()
            await self._create_index_template()
        except ESApiError as err:
            logger.error(f'{str(err.info)}\n')
        except Exception as err:
            logger.error(f'{str(err)}\n')

    async def _create_lifecycle(self):

        try:

            policy = {
                r'phases': {
                    r'hot': {
                        r'actions': {
                            r'rollover': {
                                r'max_age': self._rollover_max_age,
                                r'max_primary_shard_size': self._rollover_max_primary_shard_size,
                            },
                            r'set_priority': {
                                r'priority': 100,
                            }
                        },
                        r'min_age': r'0ms',
                    },
                    r'delete': {
                        r'actions': {
                            r'delete': {}
                        },
                        r'min_age': self._delete_min_age,
                    },
                },
            }

            _resp = await self._elasticsearch.ilm.put_lifecycle(name=self._policy_name, policy=policy)

            logger.info(f'put_lifecycle resp {str(_resp)}\n')

        except ESApiError as err:

            logger.error(f'{str(err.info)}\n')

        except Exception as err:

            logger.error(f'{str(err)}\n')

    async def _create_index_template(self):
        try:

            mappings = {
                r'dynamic': r'strict',
                r'properties': {
                    r'uid': {
                        r'type': r'keyword',
                    },
                    r'content': {
                        r'type': r'text',
                        r'norms': False,
                    },
                    r'resp_id': {
                        r'type': r'keyword',
                    },
                    r'idx': {
                        r'type': r'keyword',
                    },
                    r'tp': {
                        r'type': r'keyword',
                    },
                    r'role': {
                        r'type': r'keyword',
                    },
                    r'response_map': {
                        r'type': r'text',
                        r'norms': False,
                    },
                    r'@timestamp': {
                        r'type': r'date',
                    },
                }
            }

            template = {
                r'settings': {
                    r'index': {
                        r'lifecycle': {
                            r'name': self._policy_name,
                        },
                        r'refresh_interval': self._refresh_interval,
                        r'number_of_replicas': self._number_of_replicas,
                        r'sort': {
                            r'field': r'@timestamp',
                            r'order': self._timestamp_order,
                        }
                    },
                },
                r'mappings': mappings,
            }

            _resp = await self._elasticsearch.indices.put_index_template(
                name=self._stream_name,
                template=template,
                index_patterns=[f'{self._stream_name}*'],
                data_stream={},
            )

            logger.info(f'put_index_template resp {str(_resp)}\n')

        except ESApiError as err:

            logger.error(f'{str(err.info)}\n')

        except Exception as err:

            logger.error(f'{str(err)}\n')


class DataSource(Singleton, RedisDelegate):

    def __init__(self):

        RedisDelegate.__init__(self)

        if BaseConfig.DialogElasticsearchHostUsername and BaseConfig.DialogElasticsearchHostPassword:
            basic_auth = (BaseConfig.DialogElasticsearchHostUsername, BaseConfig.DialogElasticsearchHostPassword)
        else:
            basic_auth = None

        if BaseConfig.DialogElasticsearchHost:
            self._dialogue_elasticsearch: AsyncElasticsearch = AsyncElasticsearch(BaseConfig.DialogElasticsearchHost, basic_auth=basic_auth)
        else:
            self._dialogue_elasticsearch = None

    @property
    def dialogue_elasticsearch(self) -> typing.Optional[AsyncElasticsearch]:
        return self._dialogue_elasticsearch

    @classmethod
    async def initialize(cls):

        inst = cls()

        if BaseConfig.RedisLockIsCluster:

            (await inst.init_redis_cluster(
                BaseConfig.RedisLockIp, BaseConfig.RedisLockPort, password=BaseConfig.RedisLockPwd,
                min_connections=16, max_connections=32
            )).set_key_prefix(BaseConfig.RedisKeyPrefix)

        else:

            (await inst.init_redis_single(
                BaseConfig.RedisLockIp, BaseConfig.RedisLockPort, password=BaseConfig.RedisLockPwd,
                min_connections=16, max_connections=32
            )).set_key_prefix(BaseConfig.RedisKeyPrefix)

        if BaseConfig.DialogElasticsearchHost:
            await DialogElasticsearchDataStreamUtil(
                inst._dialogue_elasticsearch, BaseConfig.DialogElasticsearchIndex,
                rollover_max_age=r'7d', rollover_max_primary_shard_size=r'50gb', delete_min_age=r'30d',
                number_of_replicas=BaseConfig.DialogElasticsearchNumberOfReplicas,
            ).initialize()

    @classmethod
    async def release(cls):

        inst = cls()

        await inst.close_redis_pool()

class ServiceBase(Singleton, Utils):

    def __init__(self):

        self._data_source = DataSource()


class DialogElasticsearchQueueBuffer(QueueBuffer):

    def __init__(self, maxsize: int, timeout: int, task_limit: int):

        super().__init__(self._handle_data, maxsize, timeout, task_limit)

        self._data_source = DataSource()

        self._elasticsearch = self._data_source.dialogue_elasticsearch

    async def _handle_data(self, data_list):

        with es_bulk_error():

            if BaseConfig.DialogElasticsearchHost:

                logger.info(f'dialog elasticsearch bulk write: {len(data_list)}')
                await helpers.async_bulk(
                    self._elasticsearch,
                    actions=data_list,
                )

