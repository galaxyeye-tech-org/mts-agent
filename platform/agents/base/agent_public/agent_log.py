# -*- coding: utf-8 -*-
import sys

from hagworm.extend.asyncio.base import Utils
from hagworm.extend.logging import init_logger, LogFileRotator

from setting import BaseConfig


class Logger:

    @staticmethod
    def initialize():

        file_rotation = LogFileRotator.make(BaseConfig.LogFileSplitSize, BaseConfig.LogFileSplitTime)

        sfile = sys.argv[0]
        bpos = sfile.rfind('/') + 1
        epos = sfile.rfind('.') if sfile.rfind('.') > 0 else len(sfile)
        logfile = sfile[bpos:epos]

        file_name = logfile + r'_runtime_{time}.log'

        init_logger(
            level=BaseConfig.LogLevel.upper(),
            file_name=file_name,
            file_path=BaseConfig.LogFilePath,
            file_rotation=file_rotation,
            file_retention=BaseConfig.LogFileBackups,
            debug=BaseConfig.Debug,
        )


Logger.initialize()

logger = Utils.log


if __name__ == '__main__':
    LogFilePath = './logs'
    Logger().initialize()

    logger = Utils.log
    logger.info('hello')
