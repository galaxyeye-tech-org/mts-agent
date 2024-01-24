# -*- coding: utf-8 -*-

__author__ = r'wsb310@gmail.com'

from hagworm.extend.asyncio.net import HTTPJsonClientPool
from hagworm.extend.asyncio.task import DCSCronTask
from pymongo import DESCENDING, HASHED, InsertOne, DeleteOne, DeleteMany, UpdateOne

from hagworm.extend.error import catch_error

from model import const
from model.fields import QAPair
from model.responses import ErrorResponse, ErrorCode
from model.utils import AttentionUtils
from service import ServiceBase
from service.database_service import DatabaseService
from service.memory_service import MemoryService

from setting import Config


class StorageService(ServiceBase):

    def __init__(self):

        super().__init__()

        self._database_service = DatabaseService()
        self._milvus_service = MemoryService()

        self._data_queue_buffer = self._database_service.data_queue_buffer

        self._http_json_client = HTTPJsonClientPool(
            retries=const.HTTP_RETRY_COUNT,     # TODO 确认大模型的请求响应平均时间，修改重试次数以及超时
            timeout=const.HTTP_CLIENT_TIMEOUT
        )

        self._decay_memory_attention_cron_task = DCSCronTask(
            self._data_source.get_redis_client(),
            r'decay memory attention',
            f'0 */{Config.CronMemoryAttentionDecayHour} * * *',
            self._decay_attention
        )

    async def initialize(self):

        await self._check_memory_mongo_collection()
        await self._check_dialogue_strategy_mongo_collection()
        self._decay_memory_attention_cron_task.start()

    async def release(self):

        self._decay_memory_attention_cron_task.stop()

    async def _check_memory_mongo_collection(self):

        with catch_error():

            mongo_db = self._data_source.get_mongo_database(Config.MongoDBName)

            if not (names := await mongo_db.list_collection_names()) or Config.DataStorageMongoMemory not in set(names):

                _collection = mongo_db.get_collection(Config.DataStorageMongoMemory)

                await _collection.create_index([(r'uid', HASHED), (r'attention', DESCENDING)])
                await _collection.create_index([(r'decayed_attention', DESCENDING)])
                await _collection.create_index([(r'gmt_create', DESCENDING)])
                await _collection.create_index([(r'gmt_modify', DESCENDING)])

                self.log.info(r'create memory mongo collection and index')

    async def _check_dialogue_strategy_mongo_collection(self):

        with catch_error():

            mongo_db = self._data_source.get_mongo_database(Config.MongoDBName)

            if not (names := await mongo_db.list_collection_names()) or Config.DataStorageMongoDialogueStrategy not in set(names):

                _collection = mongo_db.get_collection(Config.DataStorageMongoDialogueStrategy)

                await _collection.create_index([(r'robot_id', HASHED)])
                await _collection.create_index([(r'uid', HASHED)])
                await _collection.create_index([(r'attention', DESCENDING)])
                await _collection.create_index([(r'gmt_create', DESCENDING)])
                await _collection.create_index([(r'gmt_modify', DESCENDING)])

                self.log.info(r'create dialogue strategy mongo collection and index')

    async def add_memory(
            self, uid: str, timestamp_ms: int, attention: int, content: str,
            type_: str, confidence: int, other_data: dict
    ) -> str:

        result = None

        with catch_error():

            gmt_create = self.timestamp()

            _id = self.uuid1_urn()

            vector = await self._data_source.get_vector(content)

            record = {
                r'_id': _id,
                r'uid': uid,
                r'timestamp': timestamp_ms,
                r'attention': attention,
                r'decayed_attention': attention,
                r'content': content,
                r'type': type_,
                r'confidence': confidence,
                r'other_data': other_data,
                r'gmt_create': gmt_create,
                r'gmt_modify': gmt_create,
            }

            self.log.info(f'add memory {record=}')

            record[r'embeddings'] = vector

            milvus_data = {
                r'id': _id,
                r'uid': uid,
                r'attention': attention,
                r'decayed_attention': attention,
                r'embeddings': vector,
                r'confidence': confidence
            }

            await self._data_queue_buffer.append({
                r'action': r'add',
                r'data': {
                    r'milvus': {
                        r'collection': Config.MilvusCollectionMemoryName,
                        r'data': milvus_data,
                    },
                    r'mongo': {
                        r'collection': Config.MilvusCollectionMemoryName,
                        r'data': InsertOne(record),
                    }
                }
            })

            result = _id

        return result

    async def get_memory(self, _id):

        result = None

        with catch_error():

            _collection = self.get_memory_mongo_collection()

            result = await _collection.find_one({r'_id': _id}, {r'embeddings': 0})

        return result

    async def get_memory_list(self, id_list: list[str]) -> list[dict]:

        result = None

        with catch_error():

            _collection = self.get_memory_mongo_collection()

            _where = {r'_id': {r'$in': id_list}}
            exclude_field = {r'embeddings': 0}

            result = await _collection.find(_where, exclude_field).to_list(len(id_list))

        return result

    async def delete_memory(self, _id: str):

        result = False

        with catch_error():

            _collection = self.get_memory_mongo_collection()

            record = await _collection.find_one({r'_id': _id})

            if not record:
                raise ErrorResponse(ErrorCode.ResourceNotFoundError)

            self.log.info(f'delete memory: {record["_id"]}')

            expr = self._milvus_service.get_delete_memory_expr(_id)

            await self._data_queue_buffer.append({
                r'action': r'delete_one',
                r'data': {
                    r'milvus': {
                        r'collection': Config.MilvusCollectionMemoryName,
                        r'data': expr,
                    },
                    r'mongo': {
                        r'collection': Config.MilvusCollectionMemoryName,
                        r'data': DeleteOne({r'_id': _id}),
                    }
                }
            })

            result = True

        return result

    async def delete_user_memory(self, uid: str):

        result = False

        with catch_error():
            _collection = self.get_memory_mongo_collection()

            self.log.info(f'delete user memory: {uid=}')

            expr = self._milvus_service.get_delete_memory_expr(uid=uid)
            await self._data_queue_buffer.append({
                r'action': r'delete_many',
                r'data': {
                    r'milvus': {
                        r'collection': Config.MilvusCollectionMemoryName,
                        r'data': expr
                    },
                    r'mongo': {
                        r'collection': Config.MilvusCollectionMemoryName,
                        r'data': DeleteMany({r'uid': uid}),
                    }
                }
            })

            result = True

        return result

    async def page_user_all_memory(
            self, uid: str,
            memory_type: str = None, cursor_gmt_create: int = 0, limit: int = 10
    ):

        total = 0
        infos = []

        with catch_error():

            _collection = self.get_memory_mongo_collection()

            _where = {r'uid': uid}
            exclude_field = {r'embeddings': 0}

            if memory_type:

                _where[r'type'] = memory_type

            total = await _collection.count_documents(_where)

            if not total:

                self.Break(f'{uid=} have no any memory!')

            if cursor_gmt_create:

                _where[r'gmt_create'] = {r'$lt': cursor_gmt_create}

            infos = await _collection.find(_where, exclude_field).sort([(r'gmt_create', -1)]).limit(limit).to_list(limit)

            if len(infos) < limit:

                cursor_gmt_create = None

            else:

                cursor_gmt_create = infos[-1][r'gmt_create']

        return total, cursor_gmt_create, infos

    async def match_question(self, uid: str, content: str, qa_answers: QAPair, memories: list[dict]):

        result = None

        with catch_error():

            try:

                data = {
                    r'uid': uid,
                    r'content': content,
                    r'qa_map': dict(qa_answers),
                    r'memory_list': memories
                }
                self.log.info(f'match_question call params: {data=}')
                res = await self._http_json_client.send_request(r'POST', Config.MtsAgentLlmMatchQuestionUrl, json=data)

            except Exception as err:

                self.log.error(f'match_question call failed: {err}')
                raise ErrorResponse(ErrorCode.MtsAgentHttpServerError)

            if res.status != 200:

                self.log.error(f'match_question http status failed: {res.status} => {res.body}')
                raise ErrorResponse(ErrorCode.MtsAgentHttpStatusError)

            else:

                if res.body.get(f'code') == 0:

                    self.log.info(f'match_question get matched answer: {res.body}')
                    result = res.body.get(r'answer')

                elif res.body.get("code") == -1:

                    self.log.info(f'match_question have no answer: {res.body}')

                else:

                    self.log.error(f'match_question response error: {res.body}')
                    raise ErrorResponse(ErrorCode.MtsAgentHttpResError)

        return result

    async def batch_match_question(
            self, uid: str, content_list: list[str], qa_answers: QAPair, memories: list[dict]
    ) -> dict[str, str]:

        result = None

        with catch_error():

            try:

                data = {
                    r'uid': uid,
                    r'content_list': content_list,
                    r'qa_map': dict(qa_answers),
                    r'memory_list': memories
                }
                self.log.info(f'batch match question call params: {data=}')
                res = await self._http_json_client.send_request(r'POST', Config.MtsAgentLlmBatchMatchQuestionUrl, json=data)

            except Exception as err:

                self.log.error(f'batch match question call failed: {err}')
                raise ErrorResponse(ErrorCode.MtsAgentHttpServerError)

            if res.status != 200:

                self.log.error(f'batch match question http status failed: {res.status} => {res.body}')
                raise ErrorResponse(ErrorCode.MtsAgentHttpStatusError)

            else:

                if res.body.get(f'code') == 0:

                    self.log.info(f'batch match question get matched answer: {res.body}')
                    result = res.body.get(r'answer')

                elif res.body.get("code") == -1:

                    self.log.info(f'batch match question have no answer: {res.body}')

                else:

                    self.log.error(f'batch match question response error: {res.body}')
                    raise ErrorResponse(ErrorCode.MtsAgentHttpResError)

        return result

    async def _decay_attention(self):

        result = None

        with catch_error():

            page_size = 100

            _collection = self.get_memory_mongo_collection()
            _milvus_client = self._data_source.milvus_client

            _where = {r'decayed_attention': {r'$gt': 0}}
            _include_fields = {r'attention': 1, r'gmt_create': 1}

            _total = await _collection.count_documents(_where)
            cursor = _collection.find(_where, _include_fields)
            _current_timestamp = self.timestamp()

            for _ in range(self.math.ceil(_total / page_size)):

                _mongo_data = []
                _milvus_data = []
                _milvus_ids = []

                for _doc in await cursor.to_list(length=page_size):

                    decayed_attention = AttentionUtils.get_decayed_of_attention(
                        _doc.get(r'attention', 0),
                        _doc[r'gmt_create'],
                        cost_hour_decay_one_attention=Config.CronMemoryAttentionDecayHour,
                        current_timestamp=_current_timestamp
                    )

                    if decayed_attention != _doc.get(r'attention', 0):

                        _mongo_data.append(UpdateOne({r'_id': _doc[r'_id']},
                                                     {r'$set': {r'decayed_attention': decayed_attention}}))
                        _milvus_ids.append(_doc[r'_id'])

                _milvus_data = await _milvus_client.query(Config.MilvusCollectionMemoryName, f'id in {_milvus_ids}')

                for data in _milvus_data:

                    data['decayed_attention'] = decayed_attention

                await _collection.bulk_write(_mongo_data, ordered=False)

                await _milvus_client.upsert(Config.MilvusCollectionMemoryName, _milvus_data)

            self.log.info(f'total decay {_total} memories')
            result = _total

        return result
