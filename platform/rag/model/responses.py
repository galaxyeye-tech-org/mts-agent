# -*- coding: utf-8 -*-

from fastapi.responses import UJSONResponse

from hagworm.extend.struct import Enum, Result
from hagworm.extend.text import StrUtils
from hagworm.extend.trace import get_trace_id
from hagworm.frame.fastapi.response import ErrorResponse as _ErrorResponse


class Response(UJSONResponse):

    def __init__(self, content=None, status_code=200, *args, **kwargs):

        self._trace_id = get_trace_id()

        super().__init__(content, status_code, *args, **kwargs)

    def render(self, content):

        return super().render(
            StrUtils.to_camel_dict(Result(data=content, msg=r'ok', trace_id=self._trace_id))
        )


class ErrorResponse(_ErrorResponse):

    def __init__(self, code: Enum, **kwargs):

        content = code.value[1]

        if r'content' in kwargs:
            content += f"\n{kwargs[r'content']}"

        if r'status_code' in kwargs:
            status_code = kwargs[r'status_code']
        else:
            status_code = 406

        super().__init__(code.value[0], content=content, status_code=status_code)

    def render(self, content):

        return super().render(
            StrUtils.to_camel_dict(Result(code=self._code, msg=content, trace_id=self._trace_id))
        )


class ErrorCode(Enum):

    InternalServerError = (-1, r'未定义错误')
    ResourceNotFoundError = (-2, r'指定资源不存在')
    ServerNetworkError = (-3, r'服务器网络异常')
    UnsupportedOperation = (-4, r'不支持的操作')
    ResourceAlreadyExists = (-5, r'资源已存在')

    MilvusInsertError = (-101, r'向量数据插入失败')
    ClusterParamError = (-102, r'聚类接口参数错误')

    MtsAgentHttpServerError = (-201, r'MTsAgent服务请求失败')
    MtsAgentHttpStatusError = (-202, r'MTsAgent服务响应状态异常')
    MtsAgentHttpResError = (-203, r'MTsAgent服务响应数据异常')

    QAServerInsertQAError = (-301, r'QA问题求解插入失败')


class PageResponse(dict):

    def __init__(self, total, infos, **kwargs):
        
        super().__init__()

        self[r'total'] = total
        self[r'infos'] = infos

        self.update(kwargs)
