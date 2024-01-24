import logging
import os
from logging.handlers import TimedRotatingFileHandler


class LoggerConfig(object):
    def __init__(self, log_path, file_name, level_):
        if not os.path.exists(log_path):
            os.mkdir(log_path)

        self.file_name = file_name
        self.log_path = log_path

        self.level = level_

    def init_logger(self, file_name=None, level=None):
        """
        初始化日志配置
        :param file_name:
        :param level:
        :return:
        """
        log_file_name = self.log_path + '/' + self.file_name

        # 初始化filename和level参数
        if file_name is None:
            file_name = log_file_name
        if level is None:
            level = self.level

        # log_fmt = '%(levelname)s%(asctime)s %(pathname)s[line:%(lineno)d] %(message)s'
        log_fmt = '%(levelname)s%(asctime)s %(message)s'

        formatter = logging.Formatter(log_fmt, datefmt="%Y%m%d.%H%M%S")
        log_file_handler = TimedRotatingFileHandler(filename=file_name, when="MIDNIGHT", interval=1, backupCount=100)
        log_file_handler.suffix = "%Y-%m-%d"
        log_file_handler.setFormatter(formatter)
        logging.basicConfig(level=self._get_log_level(level))
        log = logging.getLogger()
        log.addHandler(log_file_handler)

        return log

    @classmethod
    def _get_log_level(cls, level):
        """
        日志级别获取
        :param level:
        :return:
        """
        log_level = logging.INFO
        if level == 'DEBUG':
            log_level = logging.DEBUG
        elif level == 'WARNING':
            log_level = logging.WARNING
        elif level == 'ERROR':
            log_level = logging.ERROR
        return log_level


def get_logger_conf(log_path, module_name, level):
    return LoggerConfig(log_path, module_name + ".log", level).init_logger()
