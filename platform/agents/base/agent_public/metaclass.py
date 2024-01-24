# -*- coding: utf-8 -*-

__author__ = r'wsb310@gmail.com'

import os
import threading
import warnings
import traceback


class SingletonMetaclass(type):
    """单例的元类实现
    """

    def __init__(cls, __name, __bases, __dict):

        super().__init__(__name, __bases, __dict)

        cls._instance = None
        cls._process_id = None

    def __call__(cls, *args, **kwargs):

        # noinspection PyBroadException
        try:

            if cls._instance is not None:

                cls.check_process_id()

                return cls._instance

            else:

                cls._instance = super().__call__(*args, **kwargs)
                cls._process_id = os.getpid()

                return cls._instance

        except Exception as _:

            traceback.print_exc()

    def check_process_id(cls) -> bool:

        if cls._process_id == os.getpid():
            return True
        else:
            warnings.warn(f'Memory replication may cause system resource conflicts: {cls.__qualname__}')
            return False


class Singleton(metaclass=SingletonMetaclass):
    """单例基类
    """
    pass


class SafeSingletonMetaclass(SingletonMetaclass):
    """线程安全的单例的元类实现
    """

    def __init__(cls, __name, __bases, __dict):

        super().__init__(__name, __bases, __dict)

        cls._lock = threading.Lock()

    def __call__(cls, *args, **kwargs):

        with cls._lock:
            return super().__call__(*args, **kwargs)


class SafeSingleton(metaclass=SafeSingletonMetaclass):
    """线程安全的单例基类
    """
    pass
