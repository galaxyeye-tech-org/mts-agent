# -*- coding: utf-8 -*-

__author__ = r'wsb310@gmail.com'

from hagworm.extend.config import Field, HostType, StrListType, Configure
from hagworm.third.nacos.config import Configure as NacosConfig


class _Config(NacosConfig):

    MongoHost: StrListType = Field(r'Mongo')
    MongoAuth: str = Field(r'Mongo')
    MongoUser: str = Field(r'Mongo')
    MongoPasswd: str = Field(r'Mongo')
    MongoDBName: str = Field(r'Mongo')
    MongoMinConn: int = Field(r'Mongo')
    MongoMaxConn: int = Field(r'Mongo')

    RedisHost: HostType = Field(r'Redis')
    RedisPasswd: str = Field(r'Redis')
    RedisMinConn: int = Field(r'Redis')
    RedisMaxConn: int = Field(r'Redis')
    RedisExpire: int = Field(r'Redis')
    RedisKeyPrefix: str = Field(r'Redis')
    RedisClusterMode: bool = Field(r'Redis')

    Debug: bool = Field(r'Base')
    GZip: bool = Field(r'Base')
    Secret: str = Field(r'Base')

    DocServiceThreadWorker: int = Field(r'Thread')
    QAServiceThreadWorker: int = Field(r'Thread')
    MilvusServiceThreadWorker: int = Field(r'Thread')
    EmbeddingServiceThreadWorker: int = Field(r'Thread')

    AllowOrigins: StrListType = Field(r'Cros')
    AllowMethods: StrListType = Field(r'Cros')
    AllowHeaders: StrListType = Field(r'Cros')
    AllowCredentials: bool = Field(r'Cros')

    LogLevel: str = Field(r'Log')
    LogFilePath: str = Field(r'Log')
    LogFileSplitSize: int = Field(r'Log')
    LogFileSplitTime: str = Field(r'Log')
    LogFileBackups: int = Field(r'Log')

    LogElasticsearchHost: StrListType = Field(r'Log')
    LogElasticsearchIndex: str = Field(r'Log')
    LogElasticsearchHostUsername: str = Field(r'Log')
    LogElasticsearchHostPassword: str = Field(r'Log')

    RabbitMQServerURL: str = Field(r'RabbitMQ')
    RabbitMQDocumentImportExchange: str = Field(r'RabbitMQ')
    RabbitMQDocumentImportQueueName: str = Field(r'RabbitMQ')

    QANeo4jUri: str = Field(r'Neo4j')
    QANeo4jUsername: str = Field(r'Neo4j')
    QANeo4jPassword: str = Field(r'Neo4j')
    QANeo4jDBName: str = Field(r'Neo4j')
    DocNeo4jUri: str = Field(r'Neo4j')
    DocNeo4jUsername: str = Field(r'Neo4j')
    DocNeo4jPassword: str = Field(r'Neo4j')
    DocNeo4jDBName: str = Field(r'Neo4j')

    MilvusAlias: str = Field(r'Milvus')
    MilvusHost: str = Field(r'Milvus')
    MilvusPort: int = Field(r'Milvus')
    MilvusUri: str = Field(r'Milvus')
    MilvusToken: str = Field(r'Milvus')
    MilvusDBName: str = Field(r'Milvus')
    MilvusCollectionDocumentName: str = Field(r'Milvus')
    MilvusCollectionQuestionName: str = Field(r'Milvus')
    MilvusCollectionMemoryName: str = Field(r'Milvus')
    MilvusCollectionDialogueStrategyName: str = Field(r'Milvus')

    MilvusCollectionClusterName: str = Field(r'Milvus')

    Word2VecBgeName: str = Field(r'Word2Vec')
    Word2VecBgeDim: int = Field(r'Word2Vec')
    Word2VecSimcseName: str = Field(r'Word2Vec')
    Word2VecSimcseDim: int = Field(r'Word2Vec')

    DialogMongoQueueBufferMemoryMaxSize: int = Field('QueueBuffer')
    DialogMongoQueueBufferMemoryTimeout: int = Field('QueueBuffer')
    DialogMongoQueueBufferMemoryTaskLimit: int = Field('QueueBuffer')

    DataStorageMongoMemory: str = Field(r'DataStorage')
    DataStorageMongoDocument: str = Field(r'DataStorage')
    DataStorageMongoDocumentParagraph: str = Field(r'DataStorage')
    DataStorageMongoQuestion: str = Field(r'DataStorage')
    DataStorageMongoCluster: str = Field(r'DataStorage')
    DataStorageMongoVec: str = Field(r'DataStorage')
    DataStorageMongoDialogueStrategy: str = Field(r'DataStorage')

    DataStorageElasticsearchHost: str = Field(r'DataStorage')
    DataStorageElasticsearchUsername: str = Field(r'DataStorage')
    DataStorageElasticsearchPassword: str = Field(r'DataStorage')
    DataStorageElasticsearchShards: int = Field(r'DataStorage')
    DataStorageElasticsearchPoolSize: int = Field(r'DataStorage')
    DataStorageElasticsearchTimeout: int = Field(r'DataStorage')

    FlagModelPath: str = Field(r'Embedding')

    ClusterMtsAgent: str = Field(r'Cluster')
    ClusterFreeCluster: int = Field(r'Cluster')
    ClusterOriginFreeImpression: int = Field(r'Cluster')
    ClusterFreeImpression: int = Field(r'Cluster')
    ClusterThreshold: float = Field(r'Cluster')
    ClusterConfidence: float = Field(r'Cluster')
    ClusterConfidenceWeight: float = Field(r'Cluster')
    ClusterGuess: float = Field(r'Cluster')
    ClusterImpressionThreshold: float = Field(r'Cluster')
    ClusterAttentionDecay: int = Field(r'Cluster')
    ClusterImpressionValues: StrListType = Field(r'Cluster')

    MtsAgentLlmMatchQuestionUrl: str = Field(r'MtsAgent')
    MtsAgentLlmBatchMatchQuestionUrl: str = Field(r'MtsAgent')

    DefaultQAConfi: int = Field(r'Default')
    DefaultQAQuestionConfi: int = Field(r'Default')
    DefaultQAAnswerConfi: int = Field(r'Default')
    DefaultMemoryConfi: int = Field(r'Default')
    DefaultMemoryDescriptionConfi: int = Field(r'Default')
    DefaultQAUserAnswerConfi: int = Field(r'Default')

    CronMemoryAttentionDecayHour: int = Field(r'Cron')


class _EnvConfig(Configure):

    ADDRESSES: str = Field(r'NACOS', r'')
    NAMESPACE: str = Field(r'NACOS', r'')
    DATA_ID: str = Field(r'NACOS', r'./config/rag-server-local.yaml')
    NAME: str = Field(r'SERVICE', r'rag-server')
    IP: str = Field(r'SERVICE', r'')
    PORT: int = Field(r'SERVICE', 9090)
    PROCESS_NUM: int = Field(r'SERVICE', 2)


EnvConfig = _EnvConfig()
EnvConfig.read_env()

Config = _Config(EnvConfig.ADDRESSES, EnvConfig.DATA_ID, namespace=EnvConfig.NAMESPACE)
