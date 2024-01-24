# -*- coding: utf-8 -*-

__author__ = r'wsb310@gmail.com'

import uvicorn

from fastapi.middleware.cors import CORSMiddleware

from hagworm.frame.fastapi.base import DEFAULT_HEADERS, create_fastapi
from hagworm.extend.base import Utils
from hagworm.extend.logging import LogFileRotator, ElasticsearchSink
from hagworm.third.nacos.client import NacosInstanceRegister

from service import DataSource
from service.database_service import DatabaseService
from service.doc_service import DocService
from service.qa_service import QAService
from service.storage_service import StorageService
from service.memory_service import MemoryService
from service.cluster_service import ClusterService
from service.strategy_service import StrategyService

from setting import Config, EnvConfig
from controller import router


async def system_initialize():

    Config.open()

    await DataSource.initialize()
    await DatabaseService().initialize()
    await DocService().initialize()
    await QAService().initialize()
    await StorageService().initialize()
    await MemoryService().initialize()
    await ClusterService().initialize()
    await StrategyService().initialize()


async def system_release():

    await StrategyService().release()
    await ClusterService().release()
    await MemoryService().release()
    await StorageService().release()
    await QAService().release()
    await DocService().release()
    await DatabaseService().release()
    await DataSource.release()

    Config.close()

if Config.LogElasticsearchHost:

    if Config.LogElasticsearchHostUsername and Config.LogElasticsearchHostPassword:
        basic_auth = (Config.LogElasticsearchHostUsername, Config.LogElasticsearchHostPassword)
    else:
        basic_auth = None

    log_handler = ElasticsearchSink(
        Config.LogElasticsearchHost,
        Config.LogElasticsearchIndex,
        basic_auth=basic_auth
    )

else:

    log_handler = None

app = create_fastapi(
    log_level=Config.LogLevel,
    log_handler=log_handler,
    log_file_path=Config.LogFilePath,
    log_file_rotation=LogFileRotator.make(Config.LogFileSplitSize, Config.LogFileSplitTime),
    log_file_retention=Config.LogFileBackups,
    debug=Config.Debug,
    routes=router.routes,
    on_startup=[system_initialize],
    on_shutdown=[system_release],
    title=r'RagServer',
    version=r'0.1'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.AllowOrigins,
    allow_methods=Config.AllowMethods,
    allow_headers=Config.AllowHeaders,
    allow_credentials=Config.AllowCredentials,
)


if EnvConfig.IP:
    Register = NacosInstanceRegister(
        EnvConfig.ADDRESSES, EnvConfig.NAME, EnvConfig.IP, EnvConfig.PORT, 5,
        namespace=EnvConfig.NAMESPACE, weight=1
    )
    Register.start()


if __name__ == r'__main__':

    Utils.log.warning(r'THE PRODUCTION ENVIRONMENT IS STARTED USING GUNICORN')

    uvicorn.run(app, port=EnvConfig.PORT, log_config=None, headers=DEFAULT_HEADERS)
