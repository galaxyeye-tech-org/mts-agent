# -*- coding: utf-8 -*-

__author__ = r'wsb310@gmail.com'

import typing

from fastapi import Body, File, UploadFile
from pydantic.fields import Field

from hagworm.extend.base import Utils

from hagworm.frame.fastapi.base import APIRouter
from hagworm.frame.fastapi.model import BaseModel

from model.enum import EnumTaskStatus

from service.doc_service import DocService
from service.qa_service import QAService

from model.responses import ErrorResponse, ErrorCode


router = APIRouter(prefix=r'/common', tags=[r'common'])


# class FormDocService(BaseModel):
#
#     method: str = Field(..., description=r'方法')
#     body: typing.Dict[str, typing.Any] = Field(..., description=r'数据')


# class FormQAService(BaseModel):
#
#     method: str = Field(..., description=r'方法')
#     body: typing.Dict[str, typing.Any] = Field(..., description=r'数据')


# @router.post(r'/multi_doc_search')
# async def multi_doc_search(data: FormDocService = Body(...)):
#
#     try:
#         if data.method == r'query_context':
#             return await DocService().query(data.body[r'query'], data.body[r'diffusion'], data.body[r'max_token'])
#     except Exception as err:
#         Utils.log.error(str(err))
#         raise ErrorResponse(ErrorCode.InternalServerError)


# @router.post(r'/qa_service')
# async def qa_service(data: FormQAService = Body(...)):
#
#     try:
#         # return await QAService().execute(data.method, data.body)
#         return await QAService().execute_action(data.method, data.body)
#     except Exception as err:
#         Utils.log.error(str(err))
#         raise ErrorResponse(ErrorCode.InternalServerError)

##############################################################################################################

class FormDocQuery(BaseModel):

    uid: str = Field(..., description=r'UID')
    query: str = Field(..., description=r'原问题')
    diffusion: typing.List[str] = Field(..., description=r'扩散')
    limit: int = Field(15, gt=1, lt=100, description=r'搜索条数')
    radius: float = Field(0.75, gt=-1, lt=1, description=r'相似度')
    max_token: int = Field(5000, description=r'最大字符数')
    es_min_score: float = Field(5, title=r'es最小分数')


# @router.post(r'/doc/search')
# async def search_docs(data: FormDocQuery = Body(...)):
#     return await DocService().search(data.query, data.diffusion, data.max_token)

##############################################################################################################


class _QAInsertTask(BaseModel):

    task_id: str = Field(..., description=r'任务ID')
    content: str = Field(..., description=r'内容')
    type: str = Field(..., description=r'类型')
    confidence: int = Field(None, ge=-1, le=100, description='置信度')
    parent_id: str = Field(..., description=r'父节点ID')
    attention: int = Field(..., description=r'关注度')
    status: EnumTaskStatus = Field(..., description=r'状态')


class FormQAInsert(BaseModel):

    uid: str = Field(..., description=r'用户ID')
    task_list: typing.List[_QAInsertTask] = Field(..., description=r'任务列表')


@router.post(r'/qa/insert')
async def insert_qa(data: FormQAInsert = Body(...)):

    node_ids = await QAService().insert_node(
        data.uid,
        [_task.model_dump() for _task in data.task_list]
    )

    return {r'node_ids': node_ids}


class FormQAUpdate(BaseModel):

    uid: str = Field(..., description=r'用户ID')
    node_id: str = Field(..., description=r'节点ID')
    status: EnumTaskStatus = Field(..., description=r'状态')


@router.post(r'/qa/update')
async def update_qa(data: FormQAUpdate = Body(...)):
    return await QAService().update_node(data.uid, data.node_id, data.status.value)


class FormQADelete(BaseModel):

    uid: str = Field(..., description=r'用户ID')
    node_id: str = Field(..., description=r'节点ID')


@router.post(r'/qa/delete')
async def delete_qa(data: FormQADelete = Body(...)):
    return await QAService().delete_node(data.uid, data.node_id)


class FormQASearchByID(BaseModel):

    uid: str = Field(..., description=r'用户ID')
    node_id: str = Field(..., description=r'节点ID列表')


class FormQASearchByIDS(BaseModel):

    uid: str = Field(..., description=r'用户ID')
    node_ids: list[str] = Field(..., description=r'节点ID')


@router.post(r'/qa/search_by_node_id')
async def search_qa_by_id(data: FormQASearchByID = Body(...)):
    return await QAService().query_by_node_id(data.uid, data.node_id)


@router.post(r'/qa/search_by_node_ids')
async def search_qa_by_id(data: FormQASearchByIDS = Body(...)):
    return await QAService().query_by_node_ids(data.uid, data.node_ids)


class FormQASearchByContent(BaseModel):

    uid: str = Field(..., description=r'用户ID')
    top: int = Field(15, gt=1, lt=100, description=r'搜索条数')
    content: typing.List[str] = Field(..., description=r'节点ID')


@router.post(r'/qa/search_by_content')
async def search_qa_by_content(data: FormQASearchByContent = Body(...)):
    return await QAService().query_by_question(data.uid, data.top, data.content)


@router.post(r'/document/search')
async def search_document(data: FormDocQuery = Body(...)):

    vector_result = await DocService().search_doc(data.uid, data.query, data.diffusion, data.limit, data.radius, data.max_token)

    # es_result = await DocService().search_elasticsearch_doc(data.uid, data.query, data.diffusion, data.es_min_score, data.limit)

    return {r'vector_result': vector_result}
    # return {r'vector_result': vector_result, r'es_result': es_result}
