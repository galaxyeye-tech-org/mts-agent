#-*- encoding: utf-8 -*-
__author__ = 'Jianggb'

"""对话接入和表达发出"""
import json
import optparse
import sys, os
import traceback, time, asyncio
from sanic.request import Request
from sanic import Blueprint, Websocket
from sanic.response import json as sjson
from sanic.response import file, text
from sanic.exceptions import WebsocketClosed
from base.agent_public.agent_log import logger
from base.agent_storage_client.agent_content import ContentResult
from base.agent_storage_client.user_status import UserStatus
from base.large_model_client.agent_llm import request_llm
from base.thoughts_flow_client.thoughtsFlow import ThoughtFlow
from base.agent_public.agent_tool import check_param
from base.agent_public.agent_exception import *
from dialogue_service.dialogue_service import DialogueService

from setting import BaseConfig


dialogue_bp = Blueprint('mts_agent_v1', url_prefix='/mts_agent/dialogue/v1')

uid_ws_map:dict[str, (Request, Websocket)] = {}

thtFlow = ThoughtFlow()


# 定义一个工作协程 发送表达
async def expression():

    dialog_queue_buffer = DialogueService().dialog_queue_buffer

    msg = {}
    while True:
        try:
            msgs = thtFlow.subStream(["Main"], "expression", "expression", count=1)
            if not msgs:
                await asyncio.sleep(0.2)
                continue
        
            msg = msgs[0]

            _uid = msg["uid"] if "uid" in msg else None
            task = msg["task_id"] if "task_id" in msg else _uid
            usable_second_exp = False if "msg" in msg else True
            if "source" in msg and msg["source"] == "主动表达" and usable_second_exp:
                # 预写入主动表达时间, 后续可能没有实际表达
                await UserStatus.set_AI_second_exp(_uid)
            if not _uid:
                logger.warning(f"{msg} 没有uid,丢弃")
                continue
            if _uid not in uid_ws_map:
                await thtFlow.save_context(task, {"思绪流消息":f"{_uid} 没有可用连接 {msg} 丢弃"})
                logger.warning(f"{_uid} 没有可用连接 {msg} 丢弃")
                continue
            
            logger.info(f"expression: {msg}")

            ws:Websocket = uid_ws_map[_uid][1]
            thtflow_json = {"type":"思绪流消息", "data":msg}
            thtflow_json["uid"] = _uid
            await ws.send(json.dumps(thtflow_json))

            if "target" not in msg or msg["target"] != "表达管理":
                continue
            #msg = {"method": "expression", "data": {"uid":uid, "content": f"你好，我是{uid}"}, "seq": time.time()}

            if "表达类型" in msg and msg["表达类型"] == "发送协议":
                response_json = msg["response"]
                response_json["uid"] = _uid
                response_json["task_id"] = task
                await thtFlow.save_context(task, {"发送协议":response_json})
                await ws.send(json.dumps(response_json))
                continue
            exp_status = thtFlow.thtredis.get_expression_status(_uid)
            if exp_status == "红灯":
                await ContentResult.add_main_result(task, {"表达状态为红灯":msg})
                continue
            out_put = msg["content"]
            response_map = msg["response_map"] if "response_map" in msg else out_put
            resp_id = msg["resp_id"] if "resp_id" in msg else None
            idx = msg["idx"] if "idx" in msg else None
            role = msg["role"] if "role" in msg else "assistant"
            ret_json = {"code":0, "msg":"ok", "data":msg}
            await thtFlow.save_context(task, {"表达":ret_json})

            uid, content, resp_id, idx, tp, role, response = await thtFlow.save_dialogue_history(
                _uid, out_put, resp_id, idx, "A", role, response_map
            )

            await dialog_queue_buffer.append({
                r'_op_type': r'create',
                r'_index': BaseConfig.DialogElasticsearchIndex,
                r'uid': uid,
                r'content': content,
                r'resp_id': resp_id,
                r'idx': idx,
                r'tp': tp,
                r'role': role,
                r'response_map': response,
                r'@timestamp': int(time.time() * 1000),
            })

            await ws.send(json.dumps(ret_json))
            if "source" in msg and msg["source"] == "主动表达":
                # 更新主动表达时间，实际表达出去的时间
                if usable_second_exp:
                    await UserStatus.set_AI_second_exp(_uid)
            else:
                await UserStatus.set_AI_lasted_exp(_uid)
        except Exception as e:
            logger.error(f"expression: {traceback.format_exc()} {msg}")


@dialogue_bp.websocket(f'/dialogue')
async def dialogue_websocket(request:Request, ws:Websocket):
    uid = "0"
    try:
        uid = request.get_args().get("uid", "0")
    except Exception as e:
        pass
    logger.info(f"dialogue_websocket: {request} {uid}")
    if uid != "0":
        uid_ws_map[uid] = (request, ws)
        await UserStatus.set_user_online(uid)
    while True:
        try:
            msg = await ws.recv()
            logger.info(f"dialogue_websocket: {msg}")
            msg_json = json.loads(msg)
            check_param(msg_json, ["uid", "method", "data", "seq"])
            uid = msg_json["uid"]
            if uid not in uid_ws_map:
                uid_ws_map[uid] = (request, ws)
                await UserStatus.set_user_online(uid)
            elif uid_ws_map[uid][1] != ws:
                if uid_ws_map[uid][1] and uid_ws_map[uid][1].ws_proto.state != 1:
                    uid_ws_map[uid] = (request, ws)
                    await UserStatus.set_user_online(uid)
                else:
                    raise UidConnectedException(f"uid:{uid}已存在连接, {uid_ws_map[uid][0].ip}")

            resp = await DialogueService().parse_request(thtFlow, msg_json)
        except MissingParamException as e:
            resp = {"code": 9446, "msg": f"参数错误,缺少{e}"}
        except UidConnectedException as e:
            resp = {"code": 9445, "msg": f"{e}"}
            await ws.send(json.dumps(resp))
            await ws.close()
            continue
        except WebsocketClosed as e:
            logger.info(f"Client disconnected {uid}")
            if uid and uid in uid_ws_map:
                del uid_ws_map[uid]
                await UserStatus.set_user_offline(uid)

        except Exception as e:
            resp = {"code": 9444, "msg":f"{traceback.format_exc()}"}
        logger.info(f"resp: {resp}")
        await ws.send(json.dumps(resp))


@dialogue_bp.route('/dialogue_http', methods=['POST'])
async def dialogue_input(request):
    resp = {"code":-1, "msg":""}
    try:
        query = request.json
        logger.info(f"http dialogue_input: {query}")
        resp = await DialogueService().parse_request(thtFlow, query)
    except MissingParamException as e:
        resp = {"code": 9446, "msg": f"参数错误,缺少{e}"}
    except Exception as e:
        resp = {"code": 9444, "msg":f"{traceback.format_exc()}"}
    try:
        logger.info(f"resp: {resp}")
        return sjson(resp)
    except Exception as e:
        logger.error(f"dialogue_input: {traceback.format_exc()}")


# from sanic import Sanic
# from sanic.server.protocols.websocket_protocol import WebSocketProtocol
# app = Sanic("dialogue_service")
# app.blueprint(dialogue_bp)


# @app.listener('before_server_start')
# async def start_background_task(app:Sanic, loop):
#     for i in range(2):
#         app.add_task(expression())


# if __name__ == '__main__':
    
#     app.run(host="0.0.0.0", port=12401, protocol=WebSocketProtocol, single_process=True) 

