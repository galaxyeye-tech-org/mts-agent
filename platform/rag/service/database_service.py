# -*- coding: utf-8 -*-
from collections import defaultdict

import pymilvus
from hagworm.extend.asyncio.buffer import QueueBuffer
from hagworm.extend.base import Utils
from hagworm.extend.error import catch_error
from pymilvus import utility, Collection
from pymongo import errors

from service import ServiceBase, DataSource

from setting import Config


class DataQueueBuffer(QueueBuffer):

    def __init__(self, maxsize: int, timeout: int, task_limit: int, *, refresh=False):

        super().__init__(self._handle_data, maxsize, timeout, task_limit)

        self._data_source = DataSource()

        self._refresh = refresh

    def get_mongo_collection(self, collection_name: str):

        return self._data_source.get_mongo_collection(Config.MongoDBName, collection_name)

    @staticmethod
    def _process_milvus_data(data_list):

        result = []

        for item in zip(*data_list):
            result.append(list(item))

        return result

    @staticmethod
    def _process_es_del_data(query_list):

        should_dsl = []
        query_dsl = {
            r'bool': {
                r'filter': {
                    r'bool': {
                        r'should': should_dsl
                    }
                }
            }
        }

        for query in query_list:
            should_dsl.append(query)

        return query_dsl

    async def _handle_data(self, data_list):
        """
        :param: data_list
        """

        mongo_data_items = defaultdict(list)
        milvus_add_data_items = defaultdict(list)
        milvus_del_expr_items = defaultdict(list)

        for item in data_list:
            data = item[r'data']
            action = item[r'action']
            mongo_collection_name = data[r'mongo'][r'collection']
            mongo_data = data[r'mongo'][r'data']
            milvus_collection_name = data[r'milvus'][r'collection']
            milvus_data = data[r'milvus'][r'data']

            if action == r'delete_many':
                mongo_data_items[mongo_collection_name].append(mongo_data)
                # 删除表达式
                milvus_del_expr_items[milvus_collection_name].append(milvus_data)

            elif action == r'delete_one':
                mongo_data_items[mongo_collection_name].append(mongo_data)
                milvus_del_expr_items[milvus_collection_name].append(milvus_data)

            elif action == r'add':
                mongo_data_items[mongo_collection_name].append(mongo_data)
                # 删除表达式
                milvus_add_data_items[milvus_collection_name].append(milvus_data)

            else:
                Utils.log.error(f'undefined queue buffer action {action}')
                continue

        for collection_name, items in mongo_data_items.items():

            collection = self.get_mongo_collection(collection_name)

            Utils.log.info(f'{collection_name} mongodb bulk write: {len(items)}')

            try:

                await collection.bulk_write(items, ordered=False)

            except errors.BulkWriteError as err:

                Utils.log.error(
                    Utils.json_encode(
                        err.details,
                        indent=4,
                        ensure_ascii=False
                    )
                )
            except pymilvus.exceptions.ParamError as err:

                Utils.log.error(f'insert memory failed! ParamError: {err}')

            except Exception as err:

                Utils.log.error(f'{collection_name} mongodb bulk write error: {str(err)}')

        for collection_name, items in milvus_add_data_items.items():

            # format_items = self._process_milvus_data(items)

            Utils.log.info(f'{collection_name} milvus bulk write: {len(items)}')

            try:

                await self._data_source.milvus_client.insert(collection_name, items)

            except Exception as err:

                Utils.log.error(f'{collection_name} milvus bulk write error: {str(err)}')

        for collection_name, items in milvus_del_expr_items.items():

            for expr in items:

                Utils.log.info(f'{collection_name} milvus del {expr=}')

                await self._data_source.milvus_client.delete(collection_name, filter_=expr)


class DatabaseService(ServiceBase):

    def __init__(self):

        super().__init__()

        self._data_queue_buffer = DataQueueBuffer(
            Config.DialogMongoQueueBufferMemoryMaxSize,
            Config.DialogMongoQueueBufferMemoryTimeout,
            Config.DialogMongoQueueBufferMemoryTaskLimit
        )

    @property
    def data_queue_buffer(self):
        return self._data_queue_buffer

    async def release(self):

        pass

    async def initialize(self):

        pass

    @staticmethod
    async def list_milvus_collections():

        result = []

        with catch_error():

            _collections = utility.list_collections()

            for item in _collections:

                result.append(Collection(item).describe())

        return result

    async def rebuild_milvus_dialogue_strategy(self):

        result = False

        with catch_error():

            if utility.has_collection(Config.MilvusCollectionDialogueStrategyName):

                utility.drop_collection(Config.MilvusCollectionDialogueStrategyName)

            await self._data_source.load_dialogue_strategy_collection()

            await self._rebuild_milvus_dialogue_strategy_from_mongodb()

            result = True

        return result

    async def _rebuild_milvus_dialogue_strategy_from_mongodb(self):

        result = -1

        with catch_error():

            page_size = Config.EmbeddingServiceThreadWorker // 2

            mongo_collection = self.get_dialogue_strategy_mongo_collection()
            milvus_collection = Collection(Config.MilvusCollectionDialogueStrategyName)

            _total = await mongo_collection.count_documents({})
            cursor = mongo_collection.find({})
            _doc: dict

            for _ in range(self.math.ceil(_total / page_size)):

                ids, robot_ids, attentions, vectors = [], [], [], []
                insert_memories = [ids,  robot_ids, attentions,  vectors]

                for _doc in await cursor.to_list(length=page_size):
                    content = _doc[r'data'][r'意图']
                    vector = await self._data_source.get_vector(content)
                    ids.append(_doc[r'_id'])
                    robot_ids.append(_doc[r'robot_id'])
                    attentions.append(_doc[r'attention'])
                    vectors.append(vector)

                if any(insert_memories):
                    await self._data_source.milvus_add(milvus_collection, insert_memories)

            result = _total

        return result
