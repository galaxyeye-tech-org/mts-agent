# -*- coding: utf-8 -*-

__author__ = r'wsb310@gmail.com'

import itertools

from fastapi import Body
from hagworm.frame.fastapi.base import APIRouter
from hagworm.frame.fastapi.model import BaseModel
from pydantic.fields import Field

from model.fields import QAPair
from model.responses import ErrorResponse, ErrorCode, PageResponse
from service.memory_service import MemoryService
from service.qa_service import QAService
from service.storage_service import StorageService

router = APIRouter(prefix=r'/storage', tags=[r'storage'])


class FormUserMemoryAdd(BaseModel):

    uid: str = Field(..., description=r'uid')
    timestamp: int = Field(..., description='毫秒时间戳')
    attention: int = Field(100, ge=0, le=100, description='关注度')
    content: str = Field(..., description='文本内容', min_length=1)
    type: str = Field(..., description=r'记忆类型')
    confidence: int = Field(..., ge=0, le=100, description='置信度')
    other_data: dict = Field(None, description=r'其他数据')


class FormUserMemoryGetByContent(BaseModel):

    uid: str = Field(..., description=r'uid')
    content: str = Field(..., description=r'查询文本内容', min_length=1)
    limit: int = Field(1, ge=1, le=100, description=r'查询相似记忆数量')
    attention: int = Field(None, ge=0, lt=100, description='关注度')
    decayed_attention: int = Field(0, gt=0, lt=100, description='关注度')
    radius: float = Field(0.7, title=r'查询半径', example=0.7)


class FormUserMemoryDelete(BaseModel):

    id: str = Field(..., description=r'用户记忆主键id')


class FormUserMemoryDeleteAll(BaseModel):

    uid: str = Field(..., description=r'uid')


class FormUserMemoryPageAll(BaseModel):

    uid: str = Field(..., description=r'uid')

    limit: int = Field(10, ge=1, le=100, description=r'分页查询数量')

    type: str = Field(None, description=r'记忆类型')


class FormUserAnswerFromQA(BaseModel):

    uid: str = Field(..., description=r'uid')

    content: str = Field(..., min_length=1, description=r'Question问题文本')


class FormBatchUserAnswerFromQA(BaseModel):

    uid: str = Field(..., description=r'uid')

    content_list: list[str] = Field(..., min_length=1, description=r'Question问题文本列表')


class FormUserAnswerFromMemoryAndQA(BaseModel):

    uid: str = Field(..., description=r'uid')

    content: str = Field(..., min_length=1, description=r'Question问题文本')

    radius: float = Field(0.7, title=r'查询半径', example=0.7)

    attention: int = Field(..., ge=0, le=100, description=r'关注度')


class FormBatchUserAnswerFromMemoryAndQA(BaseModel):

    uid: str = Field(..., description=r'uid')

    content_list: list[str] = Field(..., min_length=1, description=r'Question问题文本列表')

    radius: float = Field(0.7, title=r'查询半径', example=0.7)

    attention: int = Field(..., ge=0, le=100, description=r'关注度')


@router.post(r'/user/memory/add', summary=r'添加用户记忆')
async def add_user_memory(form: FormUserMemoryAdd = Body(...)):

    record_id = await StorageService().add_memory(
        form.uid, form.timestamp, form.attention, form.content, form.type, form.confidence, form.other_data
    )

    if not record_id:

        raise ErrorResponse(ErrorCode.InternalServerError)

    return record_id


@router.post(r'/user/memory/get', summary=r'根据文本搜索用户的相似记忆')
async def get_user_memories_by_content(form: FormUserMemoryGetByContent = Body(...)):

    records = await MemoryService().get_similar_memory(
        form.uid, form.content, form.attention, form.radius, form.limit, form.decayed_attention
    )

    response = []

    if len(records) > 0:

        infos = await StorageService().get_memory_list(list(records))
        for info in infos:
            info[r'score'] = records[info[r'_id']]

        response = sorted(infos, key=lambda item: item['score'], reverse=True)

    return response


@router.post(r'/user/memory/delete', summary=r'清除该用户下某个记忆')
async def delete_user_memory(form: FormUserMemoryDelete = Body(...)):

    res = await StorageService().delete_memory(form.id)

    if not res:

        raise ErrorResponse(ErrorCode.InternalServerError)

    return res


@router.post(r'/user/all_memory/delete', summary=r'清除该用户下所有记忆')
async def delete_user_all_memory(form: FormUserMemoryDeleteAll = Body(...)):

    res = await StorageService().delete_user_memory(form.uid)

    if not res:

        raise ErrorResponse(ErrorCode.InternalServerError)

    return res


@router.post(r'/user/all_memory/page', summary=r'分页获取该用户下的所有记忆')
async def page_user_all_memory(form: FormUserMemoryPageAll = Body(...)):

    total, cursor, infos = await StorageService().page_user_all_memory(
        form.uid, memory_type=form.type, limit=form.limit
    )

    return PageResponse(total, infos, cursor=cursor)


@router.post(r'/user/qa/answer', summary=r'从QA中获取答案')
async def get_answer_from_qa(form: FormUserAnswerFromQA = Body(...)):

    return await QAService().get_answer_node_from_qa(form.uid, form.content)


@router.post(r'/user/qa/batch_answer', summary=r'批量从QA中获取答案')
async def batch_get_answer_from_qa(form: FormBatchUserAnswerFromQA = Body(...)):

    return await QAService().batch_get_answer_node_from_qa(form.uid, form.content_list)


@router.post(r'/user/qa_and_memory/answer', summary=r'从QA以及长期记忆中获取答案')
async def get_answer_from_qa_and_memory(form: FormUserAnswerFromMemoryAndQA = Body(...)):

    res = {}

    qa_answers: QAPair = {}
    memory_answers: list[dict] = []

    qa_answers = await QAService().get_answer_node_from_qa(form.uid, form.content, radius=form.radius)

    memories = await MemoryService().get_similar_memory(form.uid, form.content, radius=form.radius)

    if len(memories) > 0:

        memory_answers = await StorageService().get_memory_list(list(memories))

    if len(qa_answers) == 0 and len(memory_answers) == 0:

        return res

    answer_content = await StorageService().match_question(form.uid, form.content, qa_answers, memory_answers)

    if not answer_content:

        return res

    if not (res := await QAService().insert_qa_node_pair(form.uid, form.content, answer_content, form.attention)):

        raise ErrorResponse(ErrorCode.QAServerInsertQAError)

    return res


@router.post(r'/user/qa_and_memory/batch_answer', summary=r'批量从QA以及长期记忆中获取答案')
async def batch_get_answer_from_qa_and_memory(form: FormBatchUserAnswerFromMemoryAndQA = Body(...)):

    qa_answers: QAPair = {}
    memory_answers: list[dict] = []

    vectors = await QAService().batch_get_vectors(form.content_list)

    if vectors is None:

        return {question: [] for question in form.content_list}

    _batch_qa_answers = await QAService().batch_get_answer_node_from_qa(
        form.uid, form.content_list, radius=form.radius, vectors=vectors
    )
    qa_answers = dict(itertools.chain.from_iterable(_.items() for _ in _batch_qa_answers.values()))

    _batch_memories = await MemoryService().batch_get_similar_memory(
        form.uid, form.content_list, radius=form.radius, vectors=vectors
    )
    _memory_ids = list(set(itertools.chain.from_iterable(_batch_memories.values())))

    if len(_memory_ids) > 0:

        memory_answers = await StorageService().get_memory_list(_memory_ids)

    if len(qa_answers) == 0 and len(memory_answers) == 0:

        return {question: [] for question in form.content_list}

    _match_res = await StorageService().batch_match_question(form.uid, form.content_list, qa_answers, memory_answers)

    return await QAService().batch_insert_qa_node_pair(form.uid, _match_res, form.attention, vectors=vectors)



