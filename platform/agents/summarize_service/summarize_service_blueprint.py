#-*- encoding: utf-8 -*-
__author__ = 'Jianggb'

import traceback

from sanic import Blueprint
from sanic.response import json as sjson
from base.agent_public.agent_exception import MissingParamException
from base.agent_public.agent_log import logger
from base.agent_public.agent_tool import check_param
from base.thoughts_flow_client.thoughtsFlow import ThoughtFlow


summarize_bp = Blueprint('mts_agent_summarize_v1', url_prefix='/mts_agent/summarize/v1')

thtFlow = ThoughtFlow()

@summarize_bp.route('/summarize', methods=['POST'])
async def summarize(request):
    resp = {"code":-1, "msg":""}
    try:
        query = request.json
        logger.info(f"summarize: {query}")
        check_param(query, ["uid", "content_list", "seq"])
        uid = query["uid"]
        seq = query["seq"]
        content_list = query["content_list"]
        cluster_id = query["cluster_id"]

        msg = {"uid": uid, "seq": seq, "cluster_id":cluster_id,"content_list": content_list, "target": "印象冲击总结", "source":"印象冲击"}
        await thtFlow.writeMsgToMain(msg)

        resp = {"code":0, "msg":"ok", "uid":uid, "seq":seq}
    except MissingParamException as e:
        resp = {"code": 9446, "msg": f"参数错误,缺少{e}"}
    except Exception as e:
        resp = {"code":9444, "msg":f"{traceback.format_exc()}"}
    return sjson(resp)


@summarize_bp.route('/del_summarize', methods=['POST'])
async def del_summarize(request):
    resp = {"code":-1, "msg":""}
    try:
        query = request.json
        logger.info(f"summarize: {query}")
        check_param(query, ["uid", "cluster_ids", "seq"])
        uid = query["uid"]
        seq = query["seq"]
        cluster_ids = query["cluster_ids"]

        msg = {"uid": uid, "seq": seq, "cluster_ids":cluster_ids, "target": "印象冲击总结", "source":"印象冲击"}
        await thtFlow.writeMsgToMain(msg)

        resp = {"code":0, "msg":"ok", "uid":uid, "seq":seq}
    except MissingParamException as e:
        resp = {"code": 9446, "msg": f"参数错误,缺少{e}"}
    except Exception as e:
        resp = {"code":9444, "msg":f"{traceback.format_exc()}"}
    return sjson(resp)



if __name__ == '__main__':
    ""
    