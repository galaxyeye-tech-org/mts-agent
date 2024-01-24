# -*- coding: utf-8 -*-

import typing

from fastapi import Form, Body, File, UploadFile
from pydantic.fields import Field

from hagworm.frame.fastapi.base import APIRouter
from hagworm.frame.fastapi.model import BaseModel, Depends

from model.enum import EnumDocumentStatus
from model.responses import PageResponse
from service.database_service import DatabaseService
from service.doc_service import DocService
from service.qa_service import QAService
from service.memory_service import MemoryService


router = APIRouter(prefix='/database', tags=[r'database'])


class FormDocumentIDs(BaseModel):

    ids: typing.List[str] = Field(..., description=r'ID列表')


# @router.post(r'/rebuild_doc', summary=r'重建文档向量')
# async def rebuild_doc():
#
#     return await DocService().rebuild()


@router.post(r'/milvus/collections/list', summary=r'milvus向量库列表')
async def list_milvus_collection():

    return await DatabaseService().list_milvus_collections()


@router.post(r'/milvus/question/rebuild', summary=r'重建milvus的question向量collection')
async def rebuild_milvus_question_collection():

    return await QAService().rebuild_milvus_question()


@router.post(r'/milvus/memory/rebuild', summary=r'重建milvus的memory向量collection')
async def rebuild_milvus_memory_collection():

    return await MemoryService().rebuild_milvus_memory()


@router.post(r'/neo4j/question/rebuild', summary=r'重建neo4j的question向量collection')
async def rebuild_neo4j_question_collection():

    return await QAService().rebuild_neo4j_question()


@router.post(r'/mongodb/memory_embeddings/regenerate', summary=r'重建mongodb的memory向量字段')
async def regenerate_memory_embeddings():

    return await MemoryService().regenerate_memory_embeddings()


@router.post(r'/mongodb/memory_fields/regenerate', summary=r'重建mongodb的memory表type,confidence,decayed字段')
async def regenerate_memory_fields():

    return await MemoryService().regenerate_memory_fields()


@router.post(r'/mongodb/question_fields/regenerate', summary=r'重建mongodb的question表confidence字段')
async def regenerate_question_fields():

    return await QAService().regenerate_question_fields()

##############################################################################################################

class FormDocumentPageAll(BaseModel):

    uid: str = Field(..., title=r'UID')

    status: typing.Optional[EnumDocumentStatus] = Field(None, title=r'状态')

    cursor: int = Field(0, ge=0, title=r'上次分页查询响应的数据游标')

    limit: int = Field(10, ge=1, le=100, title=r'分页查询数量')


@router.post(r'/document/page', summary=r'分页获取文档')
async def page_all_document(form: FormDocumentPageAll = Body(...)):

    total, cursor, infos = await DocService().page_all_document(form.uid, form.status, form.cursor, form.limit)

    return PageResponse(total, infos, cursor=cursor)


@router.post(r'/document/split', summary=r'句子拆分')
async def document_split(data: FormDocumentIDs = Body(...)):

    return await DocService().document_split(data.ids)


class FormDocumentUpload(BaseModel):

    uid: str = Form(..., description=r'UID')
    confidence: int = Form(0, description=r'置信度')
    upload_files: typing.List[UploadFile] = File(..., description=r'文件上传')


@router.post(r'/document/upload', summary=r'上传文档')
async def upload_docs(data: typing.Dict = Depends(FormDocumentUpload)):

    _files = {_file.filename: await _file.read() for _file in data[r'upload_files']}

    return await DocService().import_doc_files(data[r'uid'], data[r'confidence'], _files)


@router.post(r'/document/data', summary=r'获取文档')
async def get_document(data: FormDocumentIDs = Body(...)):

    return await DocService().get_document(data.ids)


@router.post(r'/document/rebuild', summary=r'重建文档分句')
async def rebuild_document(data: FormDocumentIDs = Body(...)):

    return await DocService().rebuild_document(data.ids)


@router.post(r'/document/delete', summary=r'删除文档')
async def delete_docs(data: FormDocumentIDs = Body(...)):

    return await DocService().delete_document(data.ids)


# @router.post(r'/document/rebuild_es', summary=r'重建文档ES')
# async def rebuild_document(form: FormDocumentIDs = Body(...)):
#
#     return await DocService().rebuild_elasticsearch_document_index(form.ids)
