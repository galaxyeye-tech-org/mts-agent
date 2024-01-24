#-*- encoding: utf-8 -*-
__author__ = 'Jianggb'
"""GM命令解析，思绪流写入，表达状态设置"""
import traceback
from sanic import Blueprint
from sanic.response import json as sjson
from base.agent_public.agent_log import logger
from base.thoughts_flow_client.thoughtsFlow import ThoughtFlow
from base.agent_public.agent_exception import *
from dialogue_service.gm_command import GmCommand


gm_bp = Blueprint('mts_agent_gm_v1', url_prefix='/mts_agent/gm/v1')

thtFlow = ThoughtFlow()

@gm_bp.route('/command', methods=['POST'])
async def dialogue_input(request):
    resp = {"code":-1, "msg":""}
    try:
        query = request.json
        logger.info(f"gm command: {query}")
        resp = await GmCommand.parse_request(thtFlow, query)
    except MissingParamException as e:
        resp = {"code": 9446, "msg": f"参数错误,缺少{e}"}
    except Exception as e:
        resp = {"code": 9444, "msg":f"{traceback.format_exc()}"}
    try:
        logger.info(f"resp: {resp}")
        return sjson(resp)
    except Exception as e:
        logger.error(f"gm command: {traceback.format_exc()}")


# from sanic import Sanic
# from sanic.server.protocols.websocket_protocol import WebSocketProtocol
# from base.agent_public.agent_config import agent_port
# app = Sanic("dialogue_service")
# app.blueprint(dialogue_bp)


# @app.listener('before_server_start')
# async def start_background_task(app:Sanic, loop):
#     for i in range(2):
#         app.add_task(expression())


# if __name__ == '__main__':
    
#     app.run(host="0.0.0.0", port=agent_port, protocol=WebSocketProtocol, single_process=True) 

