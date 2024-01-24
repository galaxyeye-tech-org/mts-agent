# -*- coding: utf-8 -*-

__author__ = r'wsb310@gmail.com'

from typing import List, Dict, Optional

from pymilvus import DataType, Collection
from pymongo import UpdateOne
from hagworm.extend.asyncio.future import ThreadWorker
from hagworm.extend.error import catch_error

from service import ServiceBase, StorageQueueBuffer
from service.database_service import DatabaseService
from setting import Config


THREAD_WORKER = ThreadWorker(Config.MilvusServiceThreadWorker)


class UpdateQueueBuffer(StorageQueueBuffer):

    async def _handle_mongo(self, data_list: List[dict]):

        data = []

        for _data in data_list:
            data.append(
                UpdateOne(**_data)
            )

        _collection = self._data_source.get_mongo_collection(Config.MongoDBName, Config.DataStorageMongoMemory)

        await _collection.bulk_write(data, ordered=False)


class MemoryService(ServiceBase):

    def __init__(self):

        super().__init__()

        self._database_service = DatabaseService()
        self._data_queue_buffer = self._database_service.data_queue_buffer

        self._update_queue_buffer = UpdateQueueBuffer(
            Config.DialogMongoQueueBufferMemoryMaxSize,
            Config.DialogMongoQueueBufferMemoryTimeout,
            Config.DialogMongoQueueBufferMemoryTaskLimit,
        )

    async def initialize(self):

        self._check_milvus_memory_collection()

    async def release(self):

        pass

    def _check_milvus_memory_collection(self):

        with catch_error():

            milvus_client = self._data_source.milvus_client

            _collection_name = Config.MilvusCollectionMemoryName

            if not milvus_client.has_collection(_collection_name):

                _schema = milvus_client.create_schema()
                _schema.add_field(r'id', DataType.VARCHAR, is_primary=True, auto_id=False, max_length=50)
                _schema.add_field(r'uid', DataType.VARCHAR, max_length=50)
                _schema.add_field(r'attention', DataType.INT8)
                _schema.add_field(r'decayed_attention', DataType.INT8)
                _schema.add_field(r'confidence', DataType.INT8)
                _schema.add_field(r'embeddings', DataType.FLOAT_VECTOR, dim=Config.Word2VecBgeDim)

                _index_params = {
                    r'field_name': r'embeddings',
                    r'index_type': r'IVF_FLAT',
                    r'metric_type': r'IP',
                    r'params': {r'nlist': 2048},
                }

                milvus_client.create_collection_with_schema(
                    _collection_name,
                    _schema,
                    _index_params,
                    consistency_level=r'Strong'
                )

                _collection = milvus_client.get_collection(_collection_name)
                _collection.create_index(r'uid', {r'index_type': r'Trie'})
                _collection.create_index(r'attention', {r'index_type': r'STL_SORT'})
                _collection.create_index(r'decayed_attention', {r'index_type': r'STL_SORT'})
                _collection.create_index(r'confidence', {r'index_type': r'STL_SORT'})

            self.log.info(f'initialize milvus collection: {_collection_name}')

    async def rebuild_milvus_memory(self):

        result = False

        with catch_error():

            _milvus_client = self._data_source.milvus_client
            _milvus_collection_name = Config.MilvusCollectionMemoryName

            if _milvus_client.has_collection(_milvus_collection_name):

                _milvus_client.drop_collection(_milvus_collection_name)

            self._check_milvus_memory_collection()

            await self._rebuild_milvus_memory_from_mongodb()

            result = True

        return result

    async def _rebuild_milvus_memory_from_mongodb(self):

        result = -1

        with catch_error():

            page_size = Config.EmbeddingServiceThreadWorker // 2

            mongo_collection = self.get_memory_mongo_collection()
            milvus_collection_name = Config.MilvusCollectionMemoryName
            milvus_client = self._data_source.milvus_client

            _total = await mongo_collection.count_documents({})
            cursor = mongo_collection.find({})
            _doc: dict

            for _ in range(self.math.ceil(_total / page_size)):

                insert_memories = []

                for _doc in await cursor.to_list(length=page_size):
                    content = _doc[r'content']
                    if not (embeddings := _doc.get(r'embeddings', None)):
                        embeddings = await self._data_source.get_vector(content)
                    insert_memories.append({
                        r'id': _doc[r'_id'],
                        r'uid': _doc[r'uid'],
                        r'attention': _doc[r'attention'],
                        r'decayed_attention': _doc[r'decayed_attention'],
                        r'confidence': _doc[r'confidence'],
                        r'embeddings': embeddings
                    })

                if any(insert_memories):

                    await milvus_client.insert(milvus_collection_name, insert_memories)

            result = _total

        return result

    async def get_similar_memory(
            self, uid: str, content: str,
            ge_attention: int = None, radius: float = 0.7, limit: int = 10, gt_decayed_attention: int = 0
    ) -> dict[str, float]:

        result = {}

        with catch_error():

            _milvus_client = self._data_source.milvus_client
            _milvus_collection_name = Config.MilvusCollectionMemoryName

            _search_vec = await self._data_source.get_vector(content)
            _search_params = {
                r'params': {r'nprobe': 10, r'radius': radius},
                r'anns_field': r'embeddings',
            }

            self.log.info(f'{content=} ==> {len(_search_vec)=}; {uid=}, {ge_attention=}, {limit=}')

            _expr = [f'uid == "{uid}"', f'decayed_attention > {gt_decayed_attention}']

            if ge_attention:
                _expr.append(f'attention >= {ge_attention}')

            _expr = r' and '.join(_expr)
            _res = await _milvus_client.search(
                _milvus_collection_name, [_search_vec],
                search_params=_search_params,
                filter_=_expr,
                limit=limit,
                output_fields=[r'id']
            )

            self.log.info(f'get similar memories: {_res}')
            result = {item[r'id']: item[r'distance'] for item in _res[0]}

        return result

    async def batch_get_similar_memory(
            self, uid: str, content_list: list[str],
            ge_attention: int = None, radius: float = 0.7, limit: int = 10, vectors: dict[str, list[float]] = None,
            gt_decayed_attention: int = 0
    ) -> dict[str, dict[str, float]]:

        result = {content: {} for content in content_list}

        with catch_error():

            _milvus_client = self._data_source.milvus_client
            _milvus_collection_name = Config.MilvusCollectionMemoryName

            if not vectors:
                vector_list = [await self._data_source.get_vector(content) for content in content_list]

            else:
                vector_list = [vectors[content] for content in content_list]

            _search_params = {
                r'params': {r'nprobe': 10, r'radius': radius},
                r'anns_field': r'embeddings',
            }

            _expr = [f'uid == "{uid}"', f'decayed_attention > {gt_decayed_attention}']

            if ge_attention:
                _expr.append(f'attention >= {ge_attention}')

            _expr = r' and '.join(_expr)
            _res = await _milvus_client.search(
                _milvus_collection_name, vector_list,
                search_params=_search_params,
                filter_=_expr,
                limit=limit,
                output_fields=[r'id']
            )

            for content, memory in zip(content_list, _res):
                result[content] = {item[r'id']: item[r'distance'] for item in memory}

            self.log.info(f'{uid=} {content_list=} batch get similar memories: {result}')

        return result

    def get_delete_memory_expr(self, _id: str = None, uid: str = None, le_attention: int = 0, ge_attention: int = 0):

        result = None

        with catch_error():

            expr = []

            if _id:
                expr.append(f'id in ["{_id}"]')

            if uid:
                expr.append(f'uid == "{uid}"')

            if ge_attention:
                expr.append(f'attention >= {ge_attention}')

            if le_attention:
                expr.append(f'attention <= {ge_attention}')

            expr = ' and '.join(expr)
            self.log.info(f'delete memory {expr=}')

            result = expr

        return result

    async def regenerate_memory_embeddings(self):

        result = -1

        with catch_error():

            page_size = Config.EmbeddingServiceThreadWorker // 2

            mongo_collection = self.get_memory_mongo_collection()

            _total = await mongo_collection.count_documents({})
            cursor = mongo_collection.find({})
            _doc: dict

            for _ in range(self.math.ceil(_total / page_size)):

                for _doc in await cursor.to_list(length=page_size):
                    if not _doc.get(r'embeddings', None):
                        content = _doc[r'content']
                        embeddings = await self._data_source.get_vector(content)
                        _doc[r'embeddings'] = embeddings
                        await self._update_queue_buffer.append({
                            r'filter': {
                                r'_id': _doc[r'_id'],
                            },
                            r'update': {
                                r'$set': {
                                    r'embeddings': embeddings
                                }
                            }
                        })

            result = _total

        return result

    async def regenerate_memory_fields(self):

        result = -1

        with (catch_error()):

            page_size = 100

            mongo_collection = self.get_memory_mongo_collection()

            _total = await mongo_collection.count_documents({})
            cursor = mongo_collection.find({})
            _doc: dict

            for _ in range(self.math.ceil(_total / page_size)):

                for _doc in await cursor.to_list(length=page_size):
                    _update_fields, _type = {}, None

                    if r'type' not in _doc:

                        _type = _doc.get(r'other_data', {}).get(r'type')
                        _update_fields[r'type'] = _type

                    else:

                        _type = _doc[r'type']

                    if r'confidence' not in _doc:

                        if _type == r'用户陈述':
                            _update_fields[r'confidence'] = Config.DefaultMemoryDescriptionConfi

                        else:
                            _update_fields[r'confidence'] = Config.DefaultMemoryConfi

                    if r'decayed_attention' not in _doc:

                        _update_fields[r'decayed_attention'] = _doc.get(r'attention')

                    if _update_fields:
                        self._update_queue_buffer.safe_append({
                            r'filter': {
                                r'_id': _doc[r'_id'],
                            },
                            r'update': {
                                r'$set': _update_fields
                            }
                        })

            result = _total

        return result
