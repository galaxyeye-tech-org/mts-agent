# -*- coding: utf-8 -*-

__author__ = r'wsb310@gmail.com'

from hagworm.frame.gunicorn import DEFAULT_WORKER_STR, SIMPLE_LOG_CONFIG

from setting import EnvConfig

# 进程数
workers = EnvConfig.PROCESS_NUM

# 工人类
worker_class = DEFAULT_WORKER_STR

# 日志配置
logconfig_dict = SIMPLE_LOG_CONFIG

# 绑定地址
bind = f':{EnvConfig.PORT}'
