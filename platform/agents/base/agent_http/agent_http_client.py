#!/usr/bin/python3
import traceback, asyncio
import time, json
import requests, aiohttp, websocket
from aiohttp import web
from aiohttp.client_ws import ClientWebSocketResponse
from base.agent_public.agent_log import logger
from base.agent_public.agent_tool import cut_object

# ws_pool:dict[str, list] = {}

# def get_ws_connect(ws_server):
#     if ws_server not in ws_pool:
#         ws_pool[ws_server] = [websocket.create_connection(ws_server, timeout=5) for i in range(10)]
#     return ws_pool[ws_server].pop()

# def back_ws_connect(ws_server, ws):
#     if ws_server not in ws_pool:
#         ws_pool[ws_server] = []
#     ws_pool[ws_server].append(ws)


def sendRequest(url, data, uid="0", timeout=120):
    ret = ""
    try:
        btime = int(time.time()*1000)
        header = {"Content-Type": "application/json"}
        dt = json.dumps(data, ensure_ascii=False).encode('utf-8')
        respon = requests.post(url, data=dt, headers=header, timeout=(2, timeout))
        ret = json.loads(respon.text)
        logger.info(f"uid:{uid} req:{data} resp:{cut_object(ret)} {len(str(ret))} url:{url} time:{int(time.time()*1000) - btime}ms")
    except Exception as e:
        errmsg = f"其他错误, {type(e)}"
        if isinstance(e, requests.exceptions.ReadTimeout) or isinstance(e, TimeoutError):
            errmsg = "回复超时"
        elif isinstance(e, requests.exceptions.ConnectTimeout):
            errmsg = "连接超时"
        logger.error(f"uid:{uid} req:{data} url:{url}  resp:{ret} {errmsg} {traceback.format_exc()}")
        return ""
    return ret


def gptWebsocket(ws_server, data, uid="0", timeout=600):
    ret_section = ""
    try:
        seq = int(time.time()*1000)
        if "reserveOrigin" in data:
            data["reserveOrigin"] = "yes" if data["reserveOrigin"] else "no"
        query_data = {'method': 'gptChatReq', 'data': data, "seq":str(seq)}
        logger.info(f"{uid} 新建任务:{query_data} {ws_server}")
        ws = websocket.create_connection(ws_server, timeout=5)
        message = json.dumps(query_data)
        ws.send(message)
        recv_begin_time = int(time.time()*1000)
        while True:
            data = ws.recv()
            logger.debug(f"{uid} {seq} 接收服务器消息:{data}")
            if not data:
                data = '{"code": 0, "data":{"eventTime": "3.58", "finishReason": "stop", "contents": ""}}'
            if data:
                respData = json.loads(data)
                dc = {}
                if "data" in respData:
                    dc = respData["data"]
                code = respData["code"]
                if "finishReason" in dc and "contents" in dc:
                    resp = dc["contents"]
                    finish_reason = dc["finishReason"]
                    if str(code) != "0":
                        resp = ""
                    if resp:
                        ret_section += resp
                    if finish_reason in ["stop","length"]:
                        break
            now_time = int(time.time()*1000)
            if now_time - recv_begin_time > timeout*1000:
                logger.info(f"{uid} {seq} {timeout}秒没有接收完全，结束任务")
                break
    except Exception as e:
        logger.error(traceback.format_exc())
    ws.close()
    return ret_section


async def sendRequestSync(url, data, uid="0", timeout=120):
    ret = ""
    try:
        btime = int(time.time()*1000)
        header = {"Content-Type": "application/json"}
        dt = json.dumps(data, ensure_ascii=False)
        async with aiohttp.ClientSession(timeout=2) as session:
            async with session.post(url, data=dt.encode('utf-8'), headers=header, timeout=timeout) as respon:
                ret = await respon.json()
                logger.info(f"uid:{uid} req:{dt} resp:{ret} {len(str(ret))} url:{url} time:{int(time.time()*1000) - btime}ms")
    except Exception as e:
        errmsg = f"其他错误, {type(e)}"
        if isinstance(e, requests.exceptions.ReadTimeout) or isinstance(e, TimeoutError):
            errmsg = "回复超时"
        elif isinstance(e, requests.exceptions.ConnectTimeout):
            errmsg = "连接超时"
        logger.error(f"uid:{uid} req:{data} url:{url}  resp:{ret} {errmsg} {traceback.format_exc()}")
        return ""
    return ret


async def gptWebsocketSync(ws_server, data, uid="0", timeout=600):
    ret_section = ""
    try:
        seq = int(time.time()*1000)
        if "reserveOrigin" in data:
            data["reserveOrigin"] = "yes" if data["reserveOrigin"] else "no"
        query_data = {'method': 'gptChatReq', 'data': data, "seq":str(seq)}
        logger.info(f"{uid} 新建任务:{query_data} {ws_server}")
        async with aiohttp.ClientSession() as session:
            session_id = id(session)
            logger.info(f"ClientSession, {session_id} {uid}")
            async with session.ws_connect(ws_server, timeout=5, autoping=True) as ws:
                logger.info(f"ws_connect, {session_id} {uid}")
                recv_task = asyncio.create_task(recvHand(ws, uid, timeout, seq))
                logger.info(f"连接成功开始发送任务, {session_id} {uid}")
                await ws.send_json(query_data)
                logger.info(f"发送成功开始接收回复, {session_id} {uid}")
                ret_section = await recv_task
    except Exception as e:
        logger.error(traceback.format_exc())
    return ret_section


async def recvHand(ws:ClientWebSocketResponse, uid=None, timeout=600, seq=None):
    ret_section = ""
    recv_begin_time = int(time.time()*1000)
    while True:
        data = ""
        msg = await ws.receive(timeout=timeout)
        logger.info(f"{uid} {seq} 接收服务器消息:{msg}")
        if msg.type == web.WSMsgType.TEXT:
            data = msg.data
        elif msg.type == web.WSMsgType.BINARY:
            data = str(msg.data)
        elif msg.type == web.WSMsgType.PING:
            await ws.pong(msg.data)
        elif msg.type in [web.WSMsgType.CLOSED, web.WSMsgType.CLOSE, web.WSMsgType.ERROR]:
            data = '{"code": 0, "data":{"eventTime": "3.58", "finishReason": "stop", "contents": ""}}'
        else:
            logger.info(f"recv: {msg}")
        if data:
            respData = json.loads(data)
            dc = {}
            if "data" in respData:
                dc = respData["data"]
            code = respData["code"]
            if "finishReason" in dc and "contents" in dc:
                resp = dc["contents"]
                finish_reason = dc["finishReason"]
                if str(code) != "0":
                    resp = ""
                if resp:
                    ret_section += resp
                if finish_reason in ["stop","length"]:
                    break
        now_time = int(time.time()*1000)
        if now_time - recv_begin_time > timeout*1000:
            logger.info(f"{uid} {seq} {timeout}秒没有接收完全，结束任务")
            break
    return ret_section


if __name__ == '__main__':

    async def main():
        ws_url = "ws://127.0.0.1:25005"
        data = {
            "mode": "chat",
            "message": "你好",
            "dialogs": [
                {'role': 'user', 'content': '你好'},
                {'role': 'assistant', 'content': '哈喽'}
            ]
        }
        async def tmp_gptWebsocketSync(ws_server, data, uid="0", timeout=600):
            ret_section = ""
            try:
                seq = int(time.time()*1000)
                if "reserveOrigin" in data:
                    data["reserveOrigin"] = "yes" if data["reserveOrigin"] else "no"
                logger.info(f"{uid} 新建任务:{data} {ws_server}")
                async with aiohttp.ClientSession() as session:
                    session_id = id(session)
                    logger.info(f"ClientSession, {session_id} {uid}")
                    async with session.ws_connect(ws_server, timeout=5, autoping=True) as ws:
                        logger.info(f"ws_connect, {session_id} {uid}")
                        recv_task = asyncio.create_task(recvHand(ws, uid, timeout, seq))
                        logger.info(f"连接成功开始发送任务, {session_id} {uid}")
                        await ws.send_json(data)
                        logger.info(f"发送成功开始接收回复, {session_id} {uid}")
                        ret_section = await recv_task
            except Exception as e:
                logger.error(traceback.format_exc())
            return ret_section
        ret = await tmp_gptWebsocketSync(ws_url, data)
        logger.info(f"{ret}")
    asyncio.run(main())
