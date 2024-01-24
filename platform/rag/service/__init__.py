# -*- coding: utf-8 -*-

__author__ = r'wsb310@gmail.com'

import typing
import traceback
import torch
import re
import spacy

from FlagEmbedding import FlagModel

from contextlib import contextmanager
from typing import Union, Optional, Dict, List

from elasticsearch import AsyncElasticsearch, helpers
from pymilvus.orm.mutation import MutationResult
from pymongo import errors
from neo4j import AsyncGraphDatabase, AsyncDriver
from pymilvus import MilvusClient as _MilvusClient, utility, Collection

from hagworm.extend.asyncio.buffer import QueueBuffer
from hagworm.extend.asyncio.future import ThreadWorker
from hagworm.extend.trace import get_trace_id
from hagworm.extend.error import Ignore
from hagworm.extend.metaclass import Singleton
from hagworm.extend.asyncio.base import Utils
from hagworm.extend.asyncio.redis import RedisDelegate
from hagworm.extend.asyncio.mongo import MongoDelegate

from setting import Config


MILVUS_THREAD_WORKER = ThreadWorker(Config.MilvusServiceThreadWorker)
EMBEDDING_THREAD_WORKER = ThreadWorker(Config.EmbeddingServiceThreadWorker)

SENTENCE_SPLIT_SIZE = 20


@contextmanager
def es_bulk_error():

    try:
        yield
    except helpers.BulkIndexError as err:
        Utils.log.error(err.errors[:5])
    except:
        Utils.log.error(traceback.format_exc())


class MilvusClient(_MilvusClient):

    def load_collection(self, collection_name: str):
        return self._load(collection_name)

    def has_collection(self, collection_name: str) -> bool:
        return utility.has_collection(collection_name, using=self._using)

    def get_collection(self, collection_name: str) -> Collection:
        return Collection(collection_name, using=self._using)

    @MILVUS_THREAD_WORKER
    def insert(
            self,
            collection_name: str,
            data: Union[Dict, List[Dict]],
            batch_size: int = 0,
            progress_bar: bool = False,
            timeout: Optional[float] = None,
            **kwargs,
    ) -> List[Union[str, int]]:

        return super().insert(collection_name, data, batch_size, progress_bar, timeout, **kwargs)

    @MILVUS_THREAD_WORKER
    def delete(
        self,
        collection_name: str,
        pks: Optional[Union[list, str, int]] = None,
        timeout: Optional[float] = None,
        filter_: Optional[str] = "",
        **kwargs,
    ):

        return super().delete(collection_name, pks, timeout, filter_, **kwargs)

    @MILVUS_THREAD_WORKER
    def get(
        self,
        collection_name: str,
        ids: Union[list, str, int],
        output_fields: Optional[List[str]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> List[dict]:

        return super().get(collection_name, ids, output_fields, timeout, **kwargs)

    @MILVUS_THREAD_WORKER
    def search(
        self,
        collection_name: str,
        data: Union[List[list], list],
        filter_: str = "",
        limit: int = 10,
        output_fields: Optional[List[str]] = None,
        search_params: Optional[dict] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> List[dict]:

        return super().search(collection_name, data, filter_, limit, output_fields, search_params, timeout, **kwargs)

    @MILVUS_THREAD_WORKER
    def query(
        self,
        collection_name: str,
        filter_: str,
        output_fields: Optional[List[str]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> List[dict]:

        return super().query(collection_name, filter_, output_fields, timeout, **kwargs)

    @MILVUS_THREAD_WORKER
    def upsert(
        self,
        collection_name: str,
        data: Union[List, Dict],
        partition_name: Optional[str] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> MutationResult:

        _conn = self.get_collection(collection_name)
        return _conn.upsert(data, partition_name, timeout, **kwargs)


class StorageQueueBuffer(QueueBuffer):

    def __init__(self, maxsize, timeout, task_limit):

        super().__init__(self._handle_data, maxsize, timeout, task_limit)

        self._data_source = DataSource()

    async def _handle_data(self, data_list: typing.List[dict]):

        try:

            Utils.log.info(f'storage bulk write: {len(data_list)}')

            await self._handle_mongo(data_list)
            await self._handle_milvus(data_list)

        except errors.BulkWriteError as err:

            Utils.log.error(
                Utils.json_encode(
                    err.details,
                    indent=4,
                    ensure_ascii=False
                )
            )

        except Exception as err:

            Utils.log.error(str(err))

    async def _handle_mongo(self, data_list: typing.List[dict]):
        pass

    async def _handle_milvus(self, data_list: typing.List[dict]):
        pass


class DataSource(Singleton, RedisDelegate, MongoDelegate):

    def __init__(self):

        RedisDelegate.__init__(self)
        MongoDelegate.__init__(self)

        self._qa_neo4j_client: Optional[AsyncDriver] = None
        self._doc_neo4j_client: Optional[AsyncDriver] = None

        self._milvus_client: Optional[MilvusClient] = None

        self._flag_model: Optional[FlagModel] = None

        self._spacy_split_model: spacy.Language = spacy.load(r'zh_core_web_trf')
        self._spacy_vector_model: spacy.Language = spacy.load(r'zh_core_web_lg')

        # if Config.DataStorageElasticsearchUsername and Config.DataStorageElasticsearchPassword:
        #     basic_auth = (Config.DataStorageElasticsearchUsername, Config.DataStorageElasticsearchPassword)
        # else:
        #     basic_auth = None

        # self._elasticsearch = AsyncElasticsearch(
        #     Config.DataStorageElasticsearchHost,
        #     basic_auth=basic_auth,
        #     connections_per_node=Config.DataStorageElasticsearchPoolSize,
        #     request_timeout=Config.DataStorageElasticsearchTimeout
        # )

    @classmethod
    async def initialize(cls):

        inst = cls()

        if Config.RedisClusterMode:
            await inst.init_redis_cluster(
                Config.RedisHost[0], Config.RedisHost[1], password=Config.RedisPasswd,
                min_connections=Config.RedisMinConn, max_connections=Config.RedisMaxConn
            )
        else:
            await inst.init_redis_single(
                Config.RedisHost[0], Config.RedisHost[1], password=Config.RedisPasswd,
                min_connections=Config.RedisMinConn, max_connections=Config.RedisMaxConn
            )

        inst._redis_pool.set_key_prefix(Config.RedisKeyPrefix)

        inst.init_mongo(
            Config.MongoHost, Config.MongoUser, Config.MongoPasswd,
            auth_source=Config.MongoAuth,
            min_pool_size=Config.MongoMinConn, max_pool_size=Config.MongoMaxConn, max_idle_time=3600
        )

        await inst._init_neo4j()
        await inst._init_milvus()

        await inst._init_embedding()

    async def _init_embedding(self):

        Utils.log.info(r'initialize Embedding')

        self._flag_model = FlagModel(
            Config.FlagModelPath,
            query_instruction_for_retrieval=r'为这个句子生成表示以用于检索相关文章：'
        )

    async def _init_neo4j(self):

        self._qa_neo4j_client = AsyncGraphDatabase.driver(
            Config.QANeo4jUri,
            auth=(Config.QANeo4jUsername, Config.QANeo4jPassword),
            database=Config.QANeo4jDBName
        )

        await self._qa_neo4j_client.verify_connectivity()

        _server_info = await self._qa_neo4j_client.get_server_info()

        Utils.log.info(f'initialize neo4j for qa: {_server_info.agent} => {_server_info.connection_id}')

        self._doc_neo4j_client = AsyncGraphDatabase.driver(
            Config.DocNeo4jUri,
            auth=(Config.DocNeo4jUsername, Config.DocNeo4jPassword),
            database=Config.DocNeo4jDBName
        )

        await self._doc_neo4j_client.verify_connectivity()

        _server_info = await self._doc_neo4j_client.get_server_info()

        Utils.log.info(f'initialize neo4j for doc: {_server_info.agent} => {_server_info.connection_id}')

    async def _release_neo4j(self):

        await self._qa_neo4j_client.close()
        await self._doc_neo4j_client.close()

    async def _init_milvus(self):

        self._milvus_client = MilvusClient(Config.MilvusUri, token=Config.MilvusToken, db_name=Config.MilvusDBName)

        Utils.log.info(r'initialize milvus')

    async def _release_milvus(self):

        self._milvus_client.close()

    @classmethod
    async def release(cls):

        inst = cls()

        inst.close_mongo_pool()

        await inst.close_redis_pool()

        await inst._release_neo4j()
        await inst._release_milvus()

    # @property
    # def elasticsearch(self):
    #
    #     return self._elasticsearch

    @property
    def spacy_vector_model(self) -> spacy.Language:

        return self._spacy_vector_model

    @EMBEDDING_THREAD_WORKER
    def spacy_sentence_split(self, text: str) -> List[str]:

        document = self._spacy_split_model(text)
        sentences = []

        for sent in document.sents:
            if len(re.findall(r'[！？。]', sent.text)) > 1:
                _doc = self._spacy_vector_model(sent.text)
                sentences.extend(_st.text for _st in _doc.sents)
            else:
                sentences.append(sent.text)

        if len(sentences) < 2:
            return sentences

        sentences = [self._spacy_vector_model(text) for text in sentences]

        while len(sentences) > 1:

            for idx, sent in enumerate(sentences):

                if len(sent.text) > SENTENCE_SPLIT_SIZE:
                    continue

                if idx == 0:

                    _sent = self._spacy_vector_model(sent.text + sentences[idx + 1].text)
                    sentences = [_sent] + sentences[2:]

                elif idx == (len(sentences) - 1):

                    _sent = self._spacy_vector_model(sentences[idx - 1].text + sent.text)
                    sentences = sentences[:-2] + [_sent]

                else:

                    simi_l = simi_r = 0

                    if sent.has_vector:

                        if sentences[idx - 1].has_vector:
                            simi_l = sent.similarity(sentences[idx - 1])

                        if sentences[idx + 1].has_vector:
                            simi_r = sent.similarity(sentences[idx + 1])

                    if simi_l >= simi_r:
                        _sent = self._spacy_vector_model(sentences[idx - 1].text + sent.text)
                        sentences = sentences[:idx - 1] + [_sent] + sentences[idx + 1:]
                    else:
                        _sent = self._spacy_vector_model(sent.text + sentences[idx + 1].text)
                        sentences = sentences[:idx] + [_sent] + sentences[idx + 2:]

                break

            else:

                break

        return [sent.text for sent in sentences]


    @EMBEDDING_THREAD_WORKER
    def get_vector(self, query: str) -> List:

        ndarray = self._flag_model.encode(query)

        return ndarray.tolist()

    @property
    def neo4j_client_for_qa(self) -> AsyncDriver:
        return self._qa_neo4j_client

    @property
    def neo4j_client_for_doc(self) -> AsyncDriver:
        return self._doc_neo4j_client

    @property
    def milvus_client(self) -> MilvusClient:
        return self._milvus_client


class ServiceBase(Singleton, Utils):

    def __init__(self):

        self._data_source = DataSource()

    @property
    def trace_id(self):

        return get_trace_id()

    def Break(self, *args, layers=1):

        raise Ignore(*args, layers=layers)

    def get_question_mongo_collection(self):
        return self._data_source.get_mongo_collection(
            Config.MongoDBName,
            Config.DataStorageMongoQuestion
        )

    def get_memory_mongo_collection(self):
        return self._data_source.get_mongo_collection(
            Config.MongoDBName,
            Config.DataStorageMongoMemory
        )

    def get_cluster_mongo_collection(self):
        return self._data_source.get_mongo_collection(
            Config.MongoDBName,
            Config.DataStorageMongoCluster
        )

    def get_vec_mongo_collection(self):
        return self._data_source.get_mongo_collection(
            Config.MongoDBName,
            Config.DataStorageMongoVec
        )

    def get_dialogue_strategy_mongo_collection(self):

        return self._data_source.get_mongo_collection(
            Config.MongoDBName,
            Config.DataStorageMongoDialogueStrategy,
        )

    def get_document_mongo_collection(self):
        return self._data_source.get_mongo_collection(
            Config.MongoDBName, Config.DataStorageMongoDocument
        )

    def get_document_paragraph_mongo_collection(self):

        return  self._data_source.get_mongo_collection(
            Config.MongoDBName, Config.DataStorageMongoDocumentParagraph
        )
