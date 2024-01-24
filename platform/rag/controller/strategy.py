# -*- coding: utf-8 -*-

from pydantic.fields import Field
from fastapi import Body

from hagworm.frame.fastapi.base import APIRouter
from hagworm.frame.fastapi.model import BaseModel

from model.responses import ErrorResponse, ErrorCode, PageResponse
from model.utils import DataUtils
from service.strategy_service import StrategyService


router = APIRouter(prefix=r'/strategy', tags=[r'strategy'])


class FormDialogueStrategyAdd(BaseModel):

    uid: str = Field(DataUtils.StrategyPublicUid, title=r'uid 公有为0')
    robot_id: str = Field(..., title=r'机器人ID')
    data: dict = Field(..., title=r'策略实体', description=r'由于字段暂未完全确定, 目前仅用dict表示, 后期调整')
    attention: int = Field(..., ge=0, le=100, title=r'关注度')


class FormStrategyPageAll(BaseModel):

    robot_id: str = Field(..., title=r'机器人ID')
    uids: list[str] = Field(None, title=r'uid数组, 如果为空则时查询该robot_id下所有')
    include_public: bool = Field(
        True, title=r'是否包含公有策略',
        description=r'当传入了uids并且include_public为true时追加公有策略，当未传入uids时默认查询robot_id下所有'
    )
    limit: int = Field(1000, title=r'分页查询数量')


class FormDialogueStrategyDel(BaseModel):

    id: str = Field(..., title=r'主键')


class FormGetStrategiesContent(BaseModel):

    robot_id: str = Field(..., title=r'机器人ID')
    uid: str = Field(None, title=r'uid')
    include_public: bool = Field(True, title=r'是否包含公有策略')
    content: str = Field(..., title=r'意图文本', min_length=1)
    radius: float = Field(0.8, title=r'查询半径', example=0.8)
    limit: int = Field(1000, title=r'分页查询数量', ge=1)


@router.post(r'/dialogue/add', summary=r'增加一条对话策略数据')
async def add_dialogue_strategy(form: FormDialogueStrategyAdd = Body(...)):

    record_id = await StrategyService().add_dialogue_strategy(form.robot_id, form.uid, form.data, form.attention)

    if record_id is None:

        raise ErrorResponse(ErrorCode.InternalServerError)

    return record_id


@router.post(r'/dialogue/page', summary=r'分页获取该robot_id uids下所有策略')
async def page_all_dialogue_strategy(form: FormStrategyPageAll = Body(...)):

    total, infos = await StrategyService().page_all_dialogue_strategy(
        form.robot_id, form.uids, form.include_public, form.limit
    )

    return PageResponse(total, infos)



@router.post(r'/dialogue/del', summary=r'删除一条对话策略数据')
async def add_dialogue_strategy(form: FormDialogueStrategyDel = Body(...)):

    result = await StrategyService().del_dialogue_strategy(form.id)

    if not result:

        raise ErrorResponse(ErrorCode.InternalServerError)

    return result


@router.post(r'/dialogue/get', summary=r'根据意图文本查询策略数据')
async def get_dialogue_strategies_by_content(form: FormGetStrategiesContent = Body(...)):

    ids_scores = await StrategyService().get_similar_dialogue_strategies(
        form.robot_id, form.uid, form.include_public, form.content, form.radius, form.limit,
    )

    response = []

    if len(ids_scores):

        infos = await StrategyService().get_dialogue_strategies(list(ids_scores.keys()))

        if infos is None:
            raise ErrorResponse(ErrorCode.InternalServerError)

        infos = {row[r'id']: row for row in infos}

        for _id, score in ids_scores.items():
            if _id in infos:
                record = infos[_id]
                record[r'score'] = score
                response.append({
                    r'id': record[r'id'],
                    r'score': record[r'score'],
                    r'robot_id': record[r'robot_id'],
                    r'uid': record[r'uid'],
                    r'data': record[r'data'],
                    r'attention': record[r'attention'],
                })

    return response


@router.post(r'/milvus/dialogue_strategy/rebuild', summary=r'重建milvus的dialogue_strategy向量collection')
async def rebuild_milvus_dialogue_strategy_collection():

    return await StrategyService().rebuild_milvus_dialogue_strategy()


@router.post(r'/milvus/dialogue_strategy/regenerate', summary=r'dialogue_strategy mongo collection添加embeddings')
async def regenerate_milvus_dialogue_strategy_collection():

    return await StrategyService().regenerate_dialogue_strategies()


@router.post(r'/mongo/dialogue/regenerate', summary=r'dialogue_strategy mongo collection 添加公有uid')
async def regenerate_mongo_dialogue_strategy_collection():

    return await StrategyService().regenerate_mongo_dialogue_strategy_collection()

