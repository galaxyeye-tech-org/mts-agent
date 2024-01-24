# -*- coding: utf-8 -*-

__author__ = r'wsb310@gmail.com'

import asyncio

import io
import typing
import aio_pika

from mswordtree import GetWordDocTree
from mswordtree.Item import Item
from pandas import DataFrame

from pymongo import HASHED, ASCENDING, DESCENDING, InsertOne
from pymilvus import DataType
from elasticsearch import helpers

from hagworm.extend.error import catch_error

from hagworm.third.rabbitmq import create_connection
from hagworm.third.rabbitmq.publish import RabbitMQProducerForExchange
from hagworm.third.rabbitmq.consume import RabbitMQConsumerForExchange

from model.const import DOCUMENT_ELASTICSEARCH_INDEX
from model.utils import DataUtils

from model.enum import EnumDocumentStatus, EnumDocumentNodeType

from service import ServiceBase, es_bulk_error

from setting import Config


class DocService(ServiceBase):

    def __init__(self):

        super().__init__()

        self._mq_connection: aio_pika.RobustConnection = create_connection(Config.RabbitMQServerURL)

        self._mq_producer: RabbitMQProducerForExchange = RabbitMQProducerForExchange(
            self._mq_connection,
            Config.RabbitMQDocumentImportExchange,
        )

        self._mq_consumer: RabbitMQConsumerForExchange = RabbitMQConsumerForExchange(
            self._mq_connection,
            Config.RabbitMQDocumentImportQueueName,
            Config.RabbitMQDocumentImportExchange
        )

        self._document_import_task: typing.Optional[asyncio.Task] = None

    async def initialize(self):

        self.log.info(r'initialize DocService')

        await self._check_document_mongo_collection()

        # await self._check_neo4j_document_graph()

        self._check_milvus_document_collection()

        # await self._check_elasticsearch_document_index()

        await self._mq_producer.open()
        await self._mq_consumer.open()

        self._document_import_task = self.create_task(
            self._mq_consumer.block_pull(
                self._consume_document_import_message, True
            )
        )

    async def release(self):

        self._document_import_task.cancel()

        await self._mq_producer.close()
        await self._mq_consumer.close()
        await self._mq_connection.close()

    async def _check_document_mongo_collection(self):

        with catch_error():

            mongo_db = self._data_source.get_mongo_database(Config.MongoDBName)

            if not (names := await mongo_db.list_collection_names()) or Config.DataStorageMongoDocument not in set(names):

                _collection = mongo_db.get_collection(Config.DataStorageMongoDocument)

                await _collection.create_index([(r'name', HASHED)])
                await _collection.create_index([(r'uid', HASHED)])
                await _collection.create_index([(r'status', HASHED)])
                await _collection.create_index([(r'confidence', DESCENDING)])
                await _collection.create_index([(r'gmt_create', DESCENDING)])

                self.log.info(r'create document collection and index')

            if not (names := await mongo_db.list_collection_names()) or Config.DataStorageMongoDocumentParagraph not in set(names):

                _collection = mongo_db.get_collection(Config.DataStorageMongoDocumentParagraph)

                await _collection.create_index([(r'uid', HASHED)])
                await _collection.create_index([(r'type', HASHED)])
                await _collection.create_index([(r'index', ASCENDING)])
                await _collection.create_index([(r'document_id', HASHED)])
                await _collection.create_index([(r'paragraph_id', HASHED)])
                await _collection.create_index([(r'parent_id', HASHED)])
                await _collection.create_index([(r'confidence', DESCENDING)])

                self.log.info(r'create document paragraph mongo collection and index')

    # async def _check_neo4j_document_graph(self):
    #
    #     with catch_error():
    #
    #         await self._data_source.neo4j_client_for_doc.execute_query(
    #             r'CREATE CONSTRAINT uni_doc_container_name IF NOT EXISTS FOR (n:doc_container) REQUIRE (n.name) IS UNIQUE'
    #         )
    #
    #         await self._data_source.neo4j_client_for_doc.execute_query(
    #             r'CREATE CONSTRAINT uni_doc_content_name IF NOT EXISTS FOR (n:doc_content) REQUIRE (n.name) IS UNIQUE'
    #         )
    #
    #         await self._data_source.neo4j_client_for_doc.execute_query(
    #             r'CREATE INDEX idx_doc_content_type IF NOT EXISTS FOR (n:doc_content) ON (n.type)'
    #         )
    #
    #         await self._data_source.neo4j_client_for_doc.execute_query(
    #             r'CREATE INDEX idx_doc_content_document_id IF NOT EXISTS FOR (n:doc_content) ON (n.document_id)'
    #         )
    #
    #         await self._data_source.neo4j_client_for_doc.execute_query(
    #             r'MERGE (r:doc_container {name: "doc_root"})'
    #         )
    #
    #         self.log.info(f'initialize neo4j document root node')

    def _check_milvus_document_collection(self):

        with catch_error():

            milvus_client = self._data_source.milvus_client

            _collection_name = Config.MilvusCollectionDocumentName

            if not milvus_client.has_collection(_collection_name):

                _schema = milvus_client.create_schema()
                _schema.add_field(r'id', DataType.VARCHAR, is_primary=True, auto_id=False, max_length=50)
                _schema.add_field(r'uid', DataType.VARCHAR, max_length=50)
                _schema.add_field(r'document_id', DataType.VARCHAR, max_length=50)
                _schema.add_field(r'paragraph_id', DataType.VARCHAR, max_length=50)
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
                _collection.create_index(r'uid', {r'index_type': r'Trie'}, index_name=r'idx_uid')
                _collection.create_index(r'document_id', {r'index_type': r'Trie'}, index_name=r'idx_document_id')
                _collection.create_index(r'paragraph_id', {r'index_type': r'Trie'}, index_name=r'idx_paragraph_id')
                _collection.create_index(r'confidence', {r'index_type': r'STL_SORT'}, index_name=r'idx_confidence')

            self.log.info(f'initialize document milvus collection: {_collection_name}')

    # async def _check_elasticsearch_document_index(self):
    #
    #     result = False
    #
    #     with catch_error():
    #
    #         indices = self._data_source.elasticsearch.indices
    #
    #         if not await indices.exists(index=DOCUMENT_ELASTICSEARCH_INDEX):
    #
    #             _resp = await indices.create(
    #                 index=DOCUMENT_ELASTICSEARCH_INDEX,
    #                 settings={
    #                     r'index': {
    #                         r'refresh_interval': r'2s',
    #                         r'number_of_shards': Config.DataStorageElasticsearchShards,
    #                     },
    #                     r'analysis': {
    #                         'analyzer': {
    #                             'custom_ik_smart_analyzer': {
    #                                 'type': 'custom',
    #                                 'tokenizer': 'ik_smart',
    #                                 'filter': ['stopwords_filter']
    #                             },
    #                             'custom_ik_max_word_analyzer': {
    #                                 'type': 'custom',
    #                                 'tokenizer': 'ik_max_word',
    #                                 'filter': ['stopwords_filter']
    #                             },
    #                         },
    #                         'filter': {
    #                             'stopwords_filter': {
    #                                 'type': 'stop',
    #                                 'stopwords_path': '../plugins/ik/config/extra_stopword.dic'
    #                             }
    #                         }
    #                     },
    #                 },
    #                 mappings={
    #                     r'dynamic': r'strict',
    #                     r'properties': {
    #                         r'document_id': {
    #                             r'type': r'keyword',
    #                         },
    #                         r'paragraph_id': {
    #                             r'type': r'keyword',
    #                         },
    #                         r'confidence': {
    #                             r'type': r'byte'
    #                         },
    #                         r'content': {
    #                             r'type': r'text',
    #                             r'analyzer': r'custom_ik_max_word_analyzer',
    #                             r'search_analyzer': r'custom_ik_smart_analyzer',
    #                         },
    #                     }
    #                 }
    #             )
    #
    #             self.log.info(f"create elasticsearch document index: {_resp.body}")
    #
    #         result = True
    #
    #     return result

    # async def _delete_elasticsearch_document_index(self):
    #
    #     result = False
    #
    #     with catch_error():
    #
    #         indices = self._data_source.elasticsearch.indices
    #
    #         _resp = await indices.delete(
    #             index=DOCUMENT_ELASTICSEARCH_INDEX
    #         )
    #
    #         self.log.info(f"delete elasticsearch document index: {_resp.body}")
    #
    #         result = True
    #
    #     return result

    async def _consume_document_import_message(self, message: aio_pika.IncomingMessage):

        with catch_error():

            doc_data = self.msgpack_decode(message.body)

            self.log.info(f"import document paragraph begin: {doc_data[r'_id']} / {doc_data[r'name']}")

            _collection = self.get_document_mongo_collection()

            await _collection.update_one(
                {r'_id': doc_data[r'_id']},
                {'$set': {r'status': EnumDocumentStatus.Progress.value}}
            )

            if await self._save_paragraph(doc_data):

                await _collection.update_one(
                    {r'_id': doc_data[r'_id']},
                    {'$set': {r'status': EnumDocumentStatus.Complete.value}}
                )

            else:

                await _collection.update_one(
                    {r'_id': doc_data[r'_id']},
                    {'$set': {r'status': EnumDocumentStatus.Failed.value}}
                )

            self.log.info(f"import document paragraph finished: {doc_data[r'_id']} / {doc_data[r'name']}")

    async def get_paragraph_dict(self, ids: typing.List) -> typing.Dict:

        result = {}

        with catch_error():

            _collection = self.get_document_paragraph_mongo_collection()

            cursor = _collection.find(
                {r'_id': {'$in': ids}},
                {r'_id': 1, r'type': 1, r'index': 1, r'document_id': 1, r'paragraph_id': 1, r'parent_id': 1, r'content': 1, r'confidence': 1}
            )

            for _doc in await cursor.to_list(length=len(ids)):
                result[_doc['_id']] = _doc

        return result

    async def _save_paragraph(self, doc_data: typing.Dict):

        result = False

        with catch_error():

            _collection = self.get_document_paragraph_mongo_collection()

            doc_root = {
                r'_id': doc_data['_id'],
                r'uid': doc_data['uid'],
                r'type': EnumDocumentNodeType.Title.value,
                r'index': 0,
                r'document_id': doc_data[r'_id'],
                r'paragraph_id': r'',
                r'parent_id': r'',
                r'content': doc_data[r'name'],
                r'confidence': doc_data[r'confidence'],
                r'embeddings': await self._data_source.get_vector(doc_data[r'name']),
            }

            mongo_data = [InsertOne(doc_root)]
            # neo4j_data = [doc_root]
            milvus_data = []
            # es_page_data = []

            node_list = doc_data[r'content']

            while node_list:

                _next_node_list = []

                for _node in node_list:

                    _node_data = {
                        r'_id': _node['id'],
                        r'uid': doc_data['uid'],
                        r'type': EnumDocumentNodeType.Title.value,
                        r'index': len(mongo_data),
                        r'document_id': doc_data[r'_id'],
                        r'paragraph_id': r'',
                        r'parent_id': _node['parent_id'],
                        r'content': _node['content'],
                        r'confidence': doc_data[r'confidence'],
                        r'embeddings': await self._data_source.get_vector(_node['content']),
                    }

                    mongo_data.append(InsertOne(_node_data))
                    # neo4j_data.append(_node_data)

                    if len(_node[r'items']) > 0:

                        _next_node_list.extend(_node[r'items'])

                    elif _node_data['content'].find(r'[DataFrame]') == 0:

                        _node_data[r'type'] = EnumDocumentNodeType.Sentence.value
                        _node_data['content'] = _node_data['content'][11:]
                        _node_data['paragraph_id'] = _node_data['_id']
                        _node_data['embeddings'] = await self._data_source.get_vector(_node_data['content'])

                        milvus_data.append(
                            {
                                r'id': _node_data[r'_id'],
                                r'uid': _node_data[r'uid'],
                                r'document_id': _node_data[r'document_id'],
                                r'paragraph_id': _node_data[r'paragraph_id'],
                                r'confidence': _node_data[r'confidence'],
                                r'embeddings': _node_data[r'embeddings'],
                            }
                        )

                    else:

                        _sentence = await self._data_source.spacy_sentence_split(_node_data['content'])

                        if len(_sentence) < 2:

                            _node_data[r'type'] = EnumDocumentNodeType.Sentence.value
                            _node_data['paragraph_id'] = _node_data['_id']

                            milvus_data.append(
                                {
                                    r'id': _node_data[r'_id'],
                                    r'uid': _node_data[r'uid'],
                                    r'document_id': _node_data[r'document_id'],
                                    r'paragraph_id': _node_data[r'paragraph_id'],
                                    r'confidence': _node_data[r'confidence'],
                                    r'embeddings': _node_data[r'embeddings'],
                                }
                            )

                        else:

                            _node_data[r'type'] = EnumDocumentNodeType.Paragraph.value
                            _node_data['paragraph_id'] = _node_data['_id']

                            milvus_data.append(
                                {
                                    r'id': _node_data[r'_id'],
                                    r'uid': _node_data[r'uid'],
                                    r'document_id': _node_data[r'document_id'],
                                    r'paragraph_id': _node_data[r'paragraph_id'],
                                    r'confidence': _node_data[r'confidence'],
                                    r'embeddings': _node_data[r'embeddings'],
                                }
                            )

                            # es_page_data.append(
                            #     dict(
                            #         _op_type=r'create',
                            #         _index=DOCUMENT_ELASTICSEARCH_INDEX,
                            #         _id=_node_data[r'_id'],
                            #         document_id=_node_data['document_id'],
                            #         paragraph_id=_node_data['paragraph_id'],
                            #         confidence=_node_data['confidence'],
                            #         content=_node_data['content'],
                            #     )
                            # )

                            for _content in _sentence:

                                _sequence_data = {
                                    r'_id': self.uuid1_urn(),
                                    r'uid': doc_data['uid'],
                                    r'type': EnumDocumentNodeType.Sentence.value,
                                    r'index': len(mongo_data),
                                    r'document_id': doc_data[r'_id'],
                                    r'paragraph_id': _node_data['_id'],
                                    r'parent_id': _node_data['_id'],
                                    r'content': _content,
                                    r'confidence': doc_data[r'confidence'],
                                    r'embeddings': await self._data_source.get_vector(_content),
                                }

                                mongo_data.append(InsertOne(_sequence_data))
                                # neo4j_data.append(_sequence_data)

                                milvus_data.append(
                                    {
                                        r'id': _sequence_data[r'_id'],
                                        r'uid': _node_data[r'uid'],
                                        r'document_id': _sequence_data[r'document_id'],
                                        r'paragraph_id': _sequence_data[r'paragraph_id'],
                                        r'confidence': _sequence_data[r'confidence'],
                                        r'embeddings': _sequence_data[r'embeddings'],
                                    }
                                )

                    self.log.info(f"save paragraph: {_node_data[r'_id']}")

                node_list, _next_node_list = _next_node_list, []

            if mongo_data:
                for _idx in range(0, len(mongo_data), 500):
                    await _collection.bulk_write(mongo_data[_idx: _idx + 500], ordered=False)

            # if neo4j_data:
            #     for _data in neo4j_data:
            #         await self._add_neo4j_node(**_data)

            if milvus_data:
                for _idx in range(0, len(milvus_data), 500):
                    await self._data_source.milvus_client.insert(
                        Config.MilvusCollectionDocumentName,
                        milvus_data[_idx: _idx + 500]
                    )

            # if es_page_data:
            #     with es_bulk_error():
            #         await helpers.async_bulk(
            #             self._data_source.elasticsearch,
            #             actions=es_page_data,
            #         )

            result = True

        return result

    # async def _add_neo4j_node(
    #         self,
    #         _id: str, type: int, index: int, document_id: str, paragraph_id: str, parent_id: str,
    #         content: str, confidence: int, **_
    # ):
    #
    #     with catch_error():
    #
    #         data = {
    #             r'name': _id,
    #             r'type': type,
    #             r'index': index,
    #             r'document_id': document_id,
    #             r'paragraph_id': paragraph_id,
    #             r'parent_id': parent_id,
    #             r'content': content,
    #             r'confidence': confidence,
    #         }
    #
    #         if parent_id:
    #
    #             await self._data_source.neo4j_client_for_doc.execute_query(
    #                 r'''
    #                 MATCH (c1:doc_content) WHERE c1.name = $parent_id
    #                 MERGE (c2:doc_content {name: $name, type: $type, index: $index, document_id: $document_id, paragraph_id: $paragraph_id, parent_id: $parent_id, content: $content, confidence: $confidence})
    #                 MERGE (c1) -[:doc_link]-> (c2)
    #                 ''',
    #                 parameters_=data,
    #             )
    #
    #         else:
    #
    #             await self._data_source.neo4j_client_for_doc.execute_query(
    #                 r'''
    #                 MATCH (r:doc_container {name: "doc_root"})
    #                 MERGE (c:doc_content {name: $name, type: $type, index: $index, document_id: $document_id, paragraph_id: $paragraph_id, parent_id: $parent_id, content: $content, confidence: $confidence})
    #                 MERGE (r) -[:doc_link]-> (c)
    #                 ''',
    #                 parameters_=data
    #             )

    def _doc_to_json(self, parent_id: str, items: typing.List[Item]) -> typing.List[typing.Dict]:

        result = []

        for item in items:

            _id = self.uuid1_urn()
            _content = item.Content

            if isinstance(_content, DataFrame):
                _content = f'[DataFrame]{_content.to_markdown()}'
            elif not isinstance(_content, str):
                _content = str(_content)

            _content = _content.strip()

            if len(_content) < 2:
                continue

            result.append(
                {
                    r'id': _id,
                    r'items': self._doc_to_json(_id, item.Items[1:]),
                    r'content': _content,
                    r'parent_id': parent_id,
                }
            )

        return result

    async def page_all_document(self, uid: str, status: typing.Optional[int] = None, cursor_gmt_create: int = 0, limit: int = 10):

        total = 0
        infos = []

        with catch_error():

            _collection = self.get_document_mongo_collection()

            _where = {r'uid': uid}

            if status is not None:
                _where[r'status'] = status

            if cursor_gmt_create:

                _where[r'gmt_create'] = {r'$gt': cursor_gmt_create}

            total = await _collection.count_documents(_where)

            if not total:
                self.Break()

            infos = await _collection.find(
                _where, {r'_id': 1, r'name': 1, r'confidence': 1, r'status': 1, r'gmt_create': 1}
            ).sort([(r'gmt_create', 1)]).limit(limit).to_list(limit)

            if len(infos) < limit:

                cursor_gmt_create = None

            else:

                cursor_gmt_create = infos[-1][r'gmt_create']

            infos = DataUtils.format_mongo_records(infos)

        return total, cursor_gmt_create, infos

    # async def _get_neo4j_parent_nodes(self, node_ids: list[str]):
    #
    #     with catch_error():
    #
    #         # records, summary, keys = await self._data_source.neo4j_client_for_doc.execute_query(
    #         #     r'''
    #         #     MATCH (node:doc_content WHERE node.type = 1 AND node.name in $node_names)<-[:doc_link]-(root:doc_content)
    #         #     RETURN
    #         #     root.name as node_id,
    #         #     root.content as content,
    #         #     collect (
    #         #         {
    #         #             id: node.name,
    #         #             content: node.content,
    #         #             index: node.index
    #         #         }
    #         #     ) as children
    #         #     ''',
    #         #     parameters_={
    #         #         r'node_names': node_ids,
    #         #     },
    #         # )
    #
    #         records, summary, keys = await self._data_source.neo4j_client_for_doc.execute_query(
    #             r'''
    #             MATCH (node:doc_content WHERE node.type = 1 AND node.name in $node_names)<-[:doc_link]-(root:doc_content)
    #             RETURN
    #             DISTINCT root.name as node_id,
    #             root.content as content
    #             ''',
    #             parameters_={
    #                 r'node_names': node_ids,
    #             },
    #         )
    #
    #         if records:
    #             records = [record.data() for record in records]
    #
    #         return records, summary, keys

    async def document_split(self, ids: typing.List[str]):

        result = []

        with catch_error():

            _collection = self.get_document_mongo_collection()

            if ids:
                cursor = _collection.find({r'_id': {'$in': ids}})
            else:
                cursor = _collection.find({})

            for doc_data in await cursor.to_list(length=0xff):

                self.log.info(f"splitting document: {doc_data[r'name']}")

                node_list = doc_data[r'content']

                while node_list:

                    _next_node_list = []

                    for _node in node_list:

                        if len(_node[r'items']) > 0:
                            _next_node_list.extend(_node[r'items'])
                        else:
                            _sentence = await self._data_source.spacy_sentence_split(_node['content'])
                            result.extend(_sentence)

                    node_list, _next_node_list = _next_node_list, []

        return result

    # async def search_elasticsearch_doc(self, uid: str, query: str, diffusion: list[str], min_score: int, limit: int):
    #
    #     result = []
    #
    #     with catch_error():
    #
    #         # 如果确定要用 query必须加权
    #         contents = [query] + diffusion
    #
    #         query = {
    #             r'bool': {
    #                 r'should': [
    #                     {r'match': {r'content': content}} for content in contents
    #                 ]
    #             }
    #         }
    #
    #         _resp = await self._data_source.elasticsearch.search(
    #             index=DOCUMENT_ELASTICSEARCH_INDEX,
    #             query=query,
    #             size=limit,
    #             min_score=min_score
    #         )
    #
    #         _datalist = _resp.body[r'hits'][r'hits']
    #
    #         for _item in _datalist:
    #             result.append(
    #                 {
    #                     r'id': _item[r'_id'],
    #                     r'distance': _item[r'_score'],
    #                     r'sentence': _item[r'_source'][r'content'],
    #                     r'paragraph': _item[r'_source'][r'content'],
    #                 }
    #             )
    #
    #     return result

    async def search_doc(self, uid: str, query: str, diffusion: list[str], limit: int, radius: float, max_token: int):

        result = []

        with catch_error():

            contents = [query] + diffusion

            vectors = [await self._data_source.get_vector(val) for val in contents]

            milvus_resp = await self._data_source.milvus_client.search(
                Config.MilvusCollectionDocumentName, vectors,
                filter_=f'uid == "{uid}"',
                search_params={
                    r'params': {
                        r'nprobe': 10,
                        r'radius': radius,
                    },
                },
                limit=limit,
                output_fields=[r'id', r'document_id', r'paragraph_id', r'confidence'],
            )

            _node_ids = [_item[r'id'] for _item in self.itertools.chain(*milvus_resp)]
            _paragraph_data = {}

            for _item in self.itertools.chain(*milvus_resp):
                _paragraph_id = _item[r'entity'][r'paragraph_id']
                if _paragraph_id not in _paragraph_data:
                    _paragraph_data[_paragraph_id] = _item

            total_content = 0

            paragraph_nodes = await self.get_paragraph_dict(list(_paragraph_data.keys()) + _node_ids)

            for _node_id, _node_data in _paragraph_data.items():

                if _node_id not in paragraph_nodes or _node_data[r'id'] not in paragraph_nodes:
                    continue

                _sentence_content = paragraph_nodes[_node_data[r'id']][r'content']
                _paragraph_content = paragraph_nodes[_node_id][r'content']

                _total = len(_paragraph_content) + total_content

                if len(result) > 0 and _total > max_token:
                    self.Break()

                total_content = _total

                result.append(
                    {
                        r'id': _node_data[r'id'],
                        r'distance': _node_data[r'distance'],
                        r'sentence': _sentence_content,
                        r'paragraph': _paragraph_content,
                    }
                )

        return result

    async def import_doc_files(self, uid: str, confidence: int, files: typing.Dict[str, bytes]):

        result = {}

        with catch_error():

            insert_data = []
            message_data = []

            gmt_create = self.timestamp()

            _collection = self.get_document_mongo_collection()

            for file_name, file_data in files.items():

                try:

                    _doc_data = await _collection.find_one({r'uid': uid, r'name': file_name})

                    if _doc_data is not None:
                        raise Exception(f'document has existed: {file_name}')

                    _doc_id = self.md5(f'{file_name}@{uid}')

                    _doc_tree = GetWordDocTree(io.BytesIO(file_data))
                    _doc_json = self._doc_to_json(_doc_id, _doc_tree.Items)

                    _doc_data = {
                        r'_id': _doc_id,
                        r'uid': uid,
                        r'name': file_name,
                        r'content': _doc_json,
                        r'confidence': confidence,
                        r'status': EnumDocumentStatus.Normal.value,
                        r'gmt_create': gmt_create,
                    }

                    insert_data.append(InsertOne(_doc_data))
                    message_data.append(self.msgpack_encode(_doc_data))

                    result[file_name] = {r'id': _doc_id, r'err': r''}

                except Exception as err:

                    self.log.error(str(err))

                    result[file_name] = {r'id': r'', r'err': f'文档解析异常：{err}'}

            if insert_data:
                await _collection.bulk_write(insert_data, ordered=False)

            if message_data:
                for _msg in message_data:
                    await self._mq_producer.publish(_msg)

        return result

    async def get_document(self, ids: typing.List[str]):

        result = []

        with catch_error():

            _collection = self.get_document_mongo_collection()

            cursor = _collection.find({r'_id': {r'$in': ids}})

            result.extend(
                await cursor.to_list(length=len(ids))
            )

        return result

    async def rebuild_document(self, ids: typing.List[str]):

        result = False

        with catch_error():

            # await self.rebuild_elasticsearch_document_index(ids)

            if ids:

                # await self._data_source.neo4j_client_for_doc.execute_query(
                #     r'''
                #     MATCH (n:doc_content WHERE n.name in $names)
                #     DETACH DELETE n
                #     ''',
                #     parameters_={
                #         r'names': ids,
                #     }
                # )

                _collection = self.get_document_paragraph_mongo_collection()

                await _collection.delete_many({r'document_id': {r'$in': ids}})

                _ids_str = r','.join(f"'{_id}'" for _id in ids)

                await self._data_source.milvus_client.delete(
                    Config.MilvusCollectionDocumentName,
                    filter_=f"document_id in [{_ids_str}]"
                )

                _collection = self.get_document_mongo_collection()

                cursor = _collection.find({r'_id': {r'$in': ids}})

                for _doc in await cursor.to_list(length=len(ids)):
                    await self._mq_producer.publish(
                        self.msgpack_encode(_doc)
                    )

                self.log.info(r'rebuild document from mongodb finished')

                result = True

            else:

                # await self._data_source.neo4j_client_for_doc.execute_query(r'MATCH (n:doc_container) DETACH DELETE n')
                # await self._data_source.neo4j_client_for_doc.execute_query(r'MATCH (n:doc_content) DETACH DELETE n')
                # await self._data_source.neo4j_client_for_doc.execute_query(r'MERGE (r:doc_container {name: "doc_root"})')

                milvus_client = self._data_source.milvus_client

                _collection = Config.MilvusCollectionDocumentName

                if milvus_client.has_collection(_collection):
                    milvus_client.drop_collection(_collection)

                self._check_milvus_document_collection()

                _collection = self.get_document_paragraph_mongo_collection()

                await _collection.delete_many({})

                _collection = self.get_document_mongo_collection()

                total = await _collection.count_documents({})
                page_size = 500

                cursor = _collection.find({})

                for _index in range(self.math.ceil(total / page_size)):

                    self.log.info(f'rebuild document from mongodb {_index}')

                    for _doc in await cursor.to_list(length=page_size):
                        await self._mq_producer.publish(
                            self.msgpack_encode(_doc)
                        )

                self.log.info(r'rebuild document from mongodb finished')

                result = True

        return result

    async def delete_document(self, ids: typing.List[str]):

        result = False

        with catch_error():

            # await self._data_source.neo4j_client_for_doc.execute_query(
            #     r'''
            #     MATCH (n:doc_content WHERE n.name in $names)
            #     DETACH DELETE n
            #     ''',
            #     parameters_={
            #         r'names': ids,
            #     }
            # )

            _collection = self.get_document_mongo_collection()

            await _collection.delete_many({r'_id': {r'$in': ids}})

            _collection = self.get_document_paragraph_mongo_collection()

            await _collection.delete_many({r'document_id': {r'$in': ids}})

            _ids_str = r','.join(f"'{_id}'" for _id in ids)

            await self._data_source.milvus_client.delete(
                Config.MilvusCollectionDocumentName,
                filter_=f"document_id in [{_ids_str}]"
            )

            # query = {
            #     r'terms': {
            #         r'document_id': ids
            #     }
            # }
            #
            # _resp = await self._data_source.elasticsearch.delete_by_query(
            #     index=DOCUMENT_ELASTICSEARCH_INDEX,
            #     query=query,
            #     scroll_size=2000,
            #     slices=r'auto',
            #     wait_for_completion=False,
            # )
            #
            # self.log.info(f'delete document elasticsearch {query=} resp: {_resp.body}')

            result = True

        return result

    # async def rebuild_elasticsearch_document_index(self, ids: typing.Optional[list[str]] = None):
    #
    #     result = False
    #
    #     with catch_error():
    #
    #         await self._delete_elasticsearch_document_index()
    #         await self._check_elasticsearch_document_index()
    #
    #         await self._rebuild_elasticsearch_document_index(ids)
    #
    #         result = True
    #
    #     return result

    # async def _rebuild_elasticsearch_document_index(self, document_ids: typing.Optional[list[str]] = None):
    #
    #     result = False
    #
    #     with catch_error():
    #
    #         page_size = 3000
    #         collection = self.get_document_paragraph_mongo_collection()
    #
    #         query = {r'type': EnumDocumentNodeType.Paragraph.value}
    #
    #         if document_ids:
    #             query[r'document_id'] = {r'$in': document_ids}
    #
    #         _total = await collection.count_documents(query)
    #
    #         cursor = collection.find(query)
    #
    #         for _ in range(self.math.ceil(_total / page_size)):
    #
    #             es_page_data = []
    #
    #             for _doc in await cursor.to_list(length=page_size):
    #
    #                 es_page_data.append(
    #                     dict(
    #                         _op_type=r'create',
    #                         _index=DOCUMENT_ELASTICSEARCH_INDEX,
    #                         _id=_doc['_id'],
    #                         document_id=_doc['document_id'],
    #                         paragraph_id=_doc['paragraph_id'],
    #                         confidence=_doc['confidence'],
    #                         content=_doc['content'],
    #                     )
    #                 )
    #
    #             if es_page_data:
    #                 with es_bulk_error():
    #                     await helpers.async_bulk(
    #                         self._data_source.elasticsearch,
    #                         actions=es_page_data,
    #                     )
    #
    #         result = True
    #
    #     return result
