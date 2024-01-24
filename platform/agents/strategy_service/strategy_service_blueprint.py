#-*- encoding: utf-8 -*-

import traceback, time

from sanic import Blueprint
from sanic.request import Request
from sanic.response import json as sjson

from base.agent_public.agent_exception import MissingParamException
from base.agent_public.agent_log import logger
from base.agent_public.agent_tool import check_param
from strategy_service.service.strategy_logic_service import StrategyLogicService

strategy_bp = Blueprint(r'mts_agent_strategy_v1', url_prefix=r'/mts_agent/strategy/v1')


@strategy_bp.route(r'/dialogue/tigger/add', methods=[r'POST'])
async def strategy_add_for_user(request: Request):
    """
    添加对话触发策略
    """
    resp = {r'code': -1, r'msg': r''}

    try:

        query = request.json
        logger.info(f"divide_remark: {query}")
        check_param(query, [r'content', r'robot_id', r'uid'])

        uid = query[r'uid']
        seq = query.get(r'seq', int(time.time()*1000))
        input_txt = query[r'content']
        robot_id = query[r'robot_id']
        attention = query.get(r'attention', 60)
        task = query.get(r'task_id', uid)

        storage_resp = await StrategyLogicService().strategy_add_for_user(input_txt, task, robot_id, attention)
        if not storage_resp:
            raise Exception(r'策略写入持久化失败')

        resp = {r'code': 0, r'msg': r'ok', r'seq': seq, r'data': storage_resp}

    except MissingParamException as e:
        resp = {"code": 9446, "msg": f"参数错误,缺少{e}"}

    except Exception as e:
        resp = {"code": 9444, "msg": f"{traceback.format_exc()}"}

    return sjson(resp)


