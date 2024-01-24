# -*- coding: utf-8 -*-

__author__ = r'wsb310@gmail.com'

from hagworm.frame.fastapi.base import APIRouter


from controller import common, storage, tool, database, cluster, strategy


router = APIRouter(prefix=r'/rag_service')


router.include_router(common.router)
router.include_router(storage.router)
router.include_router(tool.router)
router.include_router(database.router)
router.include_router(cluster.router)
router.include_router(strategy.router)
