# -*- coding: utf-8 -*-
# @FileName  : app.py
# @Description TODO
# @Author： yangmingxing
# @Email: yangmingxing@galaxyeye-tech.com
# @Date 11/9/22 2:10 PM 
# @Version 1.0

import tornado
import tornado.ioloop
import tornado.web
import tornado.gen
import logging
import yaml

logging.basicConfig(level="INFO")
logger = logging.getLogger()

from settings import *
from server.server import OpenaiService

logging.getLogger('apscheduler.executors.default').propagate = False


def make_app():
    logger.info("Project is ready ...")
    return tornado.web.Application([
        (r"/gptService/v1/sentenceZH", OpenaiService)
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(9999)
    tornado.ioloop.IOLoop.current().start()
    exit(0)