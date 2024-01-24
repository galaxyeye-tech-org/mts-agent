# -*- coding: utf-8 -*-
import os

import yaml
from hagworm.extend.config import Field, StrListType, Configure
from hagworm.third.nacos.config import Configure as NacosConfig


SECTION = r'Base'

class _Config(NacosConfig):

    Debug: str = Field(r'Base')
    ListenNacosPrompts: StrListType = Field('Base')
    DialoguePrompt: StrListType = Field(r'Base')

    GptServer: str = Field(r'Base')
    RagService: str = Field(r'Base')
    AttentionUrl: str = Field(r'Base')

    DefaultMinAttention: int = Field(r'Base')
    ConvergenceMinAttention: int = Field(r'Base')
    PermanentMemAttention: int = Field(r'Base')
    SecondExpressionTime: int = Field(r'Base')
    MaxQps: int = Field(r'Base')

    serviceFiles: StrListType = Field(r'Base')

    LogLevel: str = Field(r'Log')
    LogFilePath: str = Field(r'Log')
    LogFileSplitSize: int = Field(r'Log')
    LogFileSplitTime: str = Field(r'Log')
    LogFileBackups: int = Field(r'Log')

    RedisCluster: bool = Field(r'Redis')
    RedisKeyPrefix: str = Field(r'Redis')
    RedisIp: str = Field(r'Redis')
    RedisPort: str = Field(r'Redis')
    RedisPwd: str = Field(r'Redis')
    RedisLockIp: str = Field(r'Redis')
    RedisLockPort: int = Field(r'Redis')
    RedisLockPwd: str = Field(r'Redis')
    RedisLockIsCluster: bool = Field(r'Redis')

    DialogElasticsearchHost: str = Field(r'Dialog')
    DialogElasticsearchIndex: str = Field(r'Dialog')
    DialogElasticsearchHostUsername: str = Field(r'Dialog')
    DialogElasticsearchHostPassword: str = Field(r'Dialog')
    DialogElasticsearchNumberOfReplicas: int = Field(r'Dialog')
    DialogActionQueueBufferMaxSize: int = Field(r'Dialog')
    DialogActionQueueBufferTimeout: int = Field(r'Dialog')
    DialogActionQueueBufferTaskLimit: int = Field(r'Dialog')


class _PromptConfig(NacosConfig):

    def _reload_config(self, content: str):

        self._clear_options()
        if self._format == r'yaml':
            self._parser.read_dict({SECTION: yaml.load(content, yaml.Loader)})

        self._load_options()

    def __contains__(self, item) -> bool:

        return item in self.to_dict(SECTION)

    def __getitem__(self, key) -> str:

        try:
            return self.to_dict(SECTION)[key]
        except KeyError:
            raise KeyError(f'Nacos Read Prompt Config Error: {key=}')

APP_DIR = os.getenv('APP_DIR', '.')

class _EnvConfig(Configure):

    ADDRESSES: str = Field(r'NACOS', r'')
    NAMESPACE: str = Field(r'NACOS', r'')
    Config_DATA_ID: str = Field(r'NACOS', f'{APP_DIR}/config/mts-agent-base-local.yaml')
    Prompt_DATA_ID: str = Field(r'NACOS', f'{APP_DIR}/config/mts-agent-prompt-local.yaml')
    GROUP: str = Field(r'NACOS', r'dev')
    PORT: int = Field(r'SERVICE', 12400)


EnvConfig = _EnvConfig()
EnvConfig.read_env()

BaseConfig = _Config(EnvConfig.ADDRESSES, EnvConfig.Config_DATA_ID, namespace=EnvConfig.NAMESPACE, group=EnvConfig.GROUP)
PromptConfig = _PromptConfig(EnvConfig.ADDRESSES, EnvConfig.Prompt_DATA_ID, namespace=EnvConfig.NAMESPACE, group=EnvConfig.GROUP)
