#-*- encoding: utf-8 -*-
__author__ = 'Jianggb'
import asyncio
import json
import re
import sys,time
from redis import ResponseError
import traceback
from base.large_model_client.agent_llm import request_llm
from base.thoughts_flow_client.thoughtRedis import ThoughtRedis
from base.agent_storage_client.agent_storage import StorageClient
from base.attention_client.agent_attention import AttentionClient

from base.agent_public.agent_tool import *

from setting import BaseConfig


class ThoughtFlow(StorageClient, AttentionClient):
    '思绪流写入消息读取消息'
    def __init__(self):
        super().__init__()
        self.thtredis = ThoughtRedis()
        self.streamGroup:dict[str, list] = {}
        self.transkey = ["robotId", "分流器类别", "事件Id", "分流器", "seq"]
        self.model = None
        self.min_attention = BaseConfig.DefaultMinAttention
        self.ratio = 1

    def init(self):
        self.min_attention = BaseConfig.DefaultMinAttention
        self.ratio = 1

    def get_attention_threshold(self):
        self.min_attention = BaseConfig.DefaultMinAttention
        self.ratio = 1
        try:
            min_att = self.thtredis.get_min_attention(self.model)
            if min_att:
                self.min_attention = round(float(min_att), 2)
            att_ratio = self.thtredis.get_attention_ratio()
            if att_ratio:
                self.ratio = round(float(att_ratio), 2)
        except Exception as e:
            logger.error(traceback.format_exc())
        ret = round(float(self.min_attention * self.ratio), 2)
        logger.info(f"当前attention阈值: {ret}")
        return ret

    def set_attention_threshold(self, msg_id, group, stream):
        count_map = self.rangeById(stream, {group:msg_id})
        count = count_map[group] if group in count_map else 0
        logger.info(f"积压量: {count} {stream}")
        ori_att = self.thtredis.get_min_attention(self.model)
        if not ori_att:
            ori_att = BaseConfig.DefaultMinAttention
        min_att = ori_att
        if 100 < count < 200:
            min_att = min_att*1.2
        elif 200 < count < 500:
            min_att = min_att*1.5
        elif 500 < count:
            min_att = min_att*2
        elif count < 5:
            min_att = min_att*0.5

        if min_att > 90:
            min_att = 90
        elif min_att < 70:
            min_att = 70
        logger.info(f"{ori_att} 调整之后: {min_att}")

        min_att = round(float(min_att), 2)
        self.thtredis.set_min_attention(self.model, min_att)


    def __str__(self):
        return "ThoughtFlow"

    def isStorType(self, value):
        """
        判断类型是否为bytes bool float int str
        """
        if isinstance(value, (bytes, memoryview)) or \
            isinstance(value, float) or isinstance(value, int) or isinstance(value, str):
            return True
        else:
            return False

    async def writeMsgToMain(self, msgDic:dict, sourceidList:list=['0-0'], msg_divide=None):
        """
        主stream写入消息\n
        sourceidList 源消息id列表;sourceId为空时，默认由0-0产生
        """
        if sourceidList == None or len(sourceidList) == 0:
            sourceidList = ['0-0']
        if not isinstance(sourceidList, list):
            sourceidList = [sourceidList]
        frame = sys._getframe(1)
        code = frame.f_code
        file = code.co_filename.split('/')[-1]
        info = f"{file}:{code.co_firstlineno}:{code.co_name}"
        msgDic["写入函数"] = info
        if "source" not in msgDic:
            msgDic["source"] = self.model
        if ("target" in msgDic and msgDic["target"] in ["表达管理", "响应服务"]) \
            or "uid" not in msgDic or "content" not in msgDic:
            self.writeMsgToStream(msgDic, "Main", sourceidList)
            return
        try:
            msgDic["quest_role"] = "assistant"
            if "source" in msgDic and msgDic["source"] == "用户输入":
                msgDic["quest_role"] = "user"
            if "attention" not in msgDic:
                msgDic["attention"] = await self.attention_remark(msgDic)
            if "divide" not in msgDic:
                msgDic["divide"] = await self.divide_remark(msgDic)
            if "quest_role" in msgDic:
                del msgDic["quest_role"]
            attention = int(msgDic["attention"]) if "attention" in msgDic else 70
            divide = msgDic["divide"] if "divide" in msgDic else []
            if isinstance(divide, str):
                try:
                    divide = eval(divide)
                except Exception as e:
                    pass
            if msg_divide:
                if not isinstance(msg_divide, list):
                    msg_divide = [msg_divide]
                for div in msg_divide:
                    if div not in divide:
                        divide.append(div)
            divide = [str(i) for i in divide]
            msgDic["divide"] = divide
            if attention and divide and attention > BaseConfig.PermanentMemAttention and ("11" in divide or "结论" in divide or "印象" in divide):
                logger.info(f"写入工作记忆: {msgDic}")
                tp = "用户陈述"
                if "印象" in divide:
                    tp = "印象"
                elif "结论" in divide:
                    tp = "结论"
                await self.save_work_memory(msgDic["uid"], msgDic["content"], int(time.time()*1000), 
                                int(msgDic["attention"]), 0.1, **{"source": f"思绪流_{self.model}", "type": tp})
            if attention and divide and attention > BaseConfig.PermanentMemAttention and ("11" in divide and "22" in divide):
                logger.info(f"写入长期记忆: {msgDic}")
                tp = "猜想"
                if msgDic["source"] == "用户输入":
                    tp = "用户陈述"
                elif "结论" in divide:
                    tp = "结论"
                kargs = {"source": f"思绪流_{self.model}", "type": tp}
                if "cluster_id" in msgDic:
                    kargs["cluster_id"] = msgDic["cluster_id"]
                await self.memory_add(msgDic["uid"], msgDic["content"], int(msgDic["attention"]), 
                                        **kargs)
        except Exception as e:
            logger.info(traceback.format_exc())
        self.writeMsgToStream(msgDic, "Main", sourceidList)

    def writeMsgToStream(self, msgDic:dict, stream, sourceidList:list=['0-0']):
        """
        stream写入消息\n
        sourceidList 源消息id列表;sourceId为空时，默认由0-0产生
        """
        if len(msgDic) == 0:
            raise ValueError('msgDic 必须不为空')
        if sourceidList == None or len(sourceidList) == 0:
            sourceidList = ['0-0']
        if "msg_id" in msgDic and stream == "Main":
            del msgDic["msg_id"]
        for key in msgDic.keys():
            if not self.isStorType(msgDic[key]):
                msgDic[key] = str(msgDic[key])
                
        if "parent_id" not in msgDic or (len(sourceidList) > 0 and sourceidList[0] != '0-0'):
            msgDic["parent_id"] = str(sourceidList)
        logger.info("msgDic:%s stream:%s"%(msgDic, stream))
        return self.thtredis.writeMsg(msgDic, GenStreamKey(stream))

    def mStr2Obj(self, mstr):
        """
        判断是否是结构类型,如果是转成结构类型，返回结果
        """
        if len(mstr) == 0:
            return mstr
        retStr = mstr
        if isinstance(mstr, str):
            #以[]{}()判断字符串是否可以转换成python list dict tuple类型
            if (mstr[0] == '{' and mstr[len(mstr)-1] == '}') or (mstr[0] == '[' and mstr[len(mstr)-1] == ']') or \
                (mstr[0] == '(' and mstr[len(mstr)-1] == ')'):
                try:
                    retStr = eval(mstr)
                except Exception as e:
                    #转换失败返回原字符串
                    logger.info(f"{mstr} 尝试eval失败,保持字符串处理")
        return retStr

    def transMsg(self, msg):
        """
        字符串value转成复杂类型
        """
        if not isinstance(msg, dict):
            return msg
        for key in msg:
            msg[key] = self.mStr2Obj(msg[key])
        return msg

    def subStream(self, streams:list, group, consumer, block=None, count=None):
        """
        从指定streams获取count个消息\n
        streams:画布名列表 group:订阅组名称 consumer:组内消费者名称\n
        block:阻塞毫秒时间,默认不阻塞 count:获取消息数量,默认所有新消息
        """
        #logger.info("subStream: %s"%(streams))
        #判断是否是新组，如果是则新建组
        lStream = []
        if not isinstance(streams, list):
            raise ValueError("streams 必须是list")
        for stream in streams:
            lStream.append(GenStreamKey(stream))
        self.createGroup(group, lStream)
        allmsgs = None
        try:
            allmsgs = self.thtredis.readMsgFromStreamByGroup(group, consumer, lStream, block=block,count=count,noack=True)
        except ResponseError as e:
            #stream类型key被删除后的异常 ResponseError: NOGROUP
            estr = str(e)
            if estr.find("NOGROUP") != -1:
                #清除self.streamGroup本地缓存，重新订阅
                self.streamGroup.clear()
                self.createGroup(group, lStream)
                allmsgs = self.thtredis.readMsgFromStreamByGroup(group, consumer, lStream, block=block,count=count,noack=True)
            else:
                raise e
        except Exception as e:
            raise e
        retMsg = []
        maxmsgid = None
        #logger.info("获取到消息")
        for smsg in allmsgs:
            for ikv in smsg[1]:
                msgid = ikv[0]
                if not maxmsgid or msgid > maxmsgid:
                    maxmsgid = msgid
                tsmsg = self.transMsg(ikv[1])
                if smsg[0] == GenStreamKey("Main"):
                    tsmsg["msg_id"] = msgid
                try:
                    if "msg_id" not in tsmsg:
                        tsmsg["msg_id"] = msgid
                    self.transmit(tsmsg)
                    self.transChatModel(tsmsg)
                except Exception as e:
                    logger.error(traceback.format_exc())
                retMsg.append(tsmsg)
        # if retMsg:
        #     logger.info("readMsgFromStreamByGroup:%s"%(retMsg))
        if maxmsgid:
            self.dataService(stream, group, maxmsgid)
        return retMsg

    def transmit(self, msg):
        "处理透传字段"
        if "parent_id" not in msg or "msg_id" not in msg:
            return
        sourceids:list = msg["parent_id"]
        msgid = msg["msg_id"]
        #继承sourceid的透传字段
        sourceids.sort(reverse=True)
        stransdic = self.thtredis.getTrans(sourceids[0])
        #logger.info(f"stransdic: {stransdic} {sourceids}")
        if stransdic:
            for key in stransdic:
                if key not in msg or not msg[key]:
                    msg[key] = stransdic[key]
        #保存msgid的透传字段
        transdic = {}
        for key in self.transkey:
            if key in msg:
                transdic[key] = str(msg[key])
                if key == "chatModel":
                    robotid = msg["robotId"]
                    if str(msg[key]) == "0":
                        chatdic = {'flow':str(False)}
                    else:
                        chatdic = {'flow':str(True)}
                    self.thtredis.setTransChatModel(robotid, chatdic)
        if transdic:
            self.thtredis.setTrans(msgid, transdic)
            tmptransdic = self.thtredis.getTrans(msgid)
            logger.debug(f"tmptransdic: {tmptransdic} {msgid}")

    def transChatModel(self, msg):
        if 'trans_status' not in msg or msg['trans_status'] != '开始转录' or \
            "robotId" not in msg or "chatModel" not in msg or not isinstance(msg["chatModel"], dict):
            return

        robotid = msg["robotId"]
        chatModel = msg["chatModel"] if "chatModel" in msg and isinstance(msg["chatModel"], dict) else {}
        transdic = {}
        for key in chatModel:
            transdic[key] = str(chatModel[key])
        self.thtredis.setTransChatModel(robotid, transdic)
        tmptransdic = self.thtredis.getTransChatModel(robotid)
        logger.info(f"transChatModel: {tmptransdic} {robotid}")

    def revReadMsg(self, stream, id='+', count=10):
        """
        从id开始倒序读取id之前的count个消息\n
        默认从最后一条消息读取10条消息
        """
        if len(stream) == 0 or stream == None:
            raise ValueError('stream 必须不为空')
        ret = self.thtredis.revRangeById(GenStreamKey(stream), id, count)
        retMsg = []
        logger.info("revReadMsg:%s"%(ret))
        for smsg in ret:
            msgid = smsg[0]
            tsmsg = self.transMsg(smsg[1])
            tsmsg["msg_id"] = msgid
            retMsg.append(tsmsg)
        return retMsg

    def ackMsg(self, stream, group, *ids):
        """
        处理完或接收到消息后确认消息\n
        stream:stream名\n
        group:组名\n
        ids:确认消息
        """
        self.thtredis.ackMsg(GenStreamKey(stream), group, *ids)

    def createGroup(self, groupName, streams):
        """
        #判断是否是新组，如果是则新建组
        """
        #logger.info("self.streamGroup:%s"%(self.streamGroup))
        for stream in streams:
            #在本地缓存，说明时已创建组,直接返回
            if stream in self.streamGroup and groupName in self.streamGroup[stream]:
                return
            elif self.thtredis.streamExist(stream):
                #stream　key 必须在redis存在，否则会异常
                groups = self.thtredis.groupInfo(stream)
                if stream not in self.streamGroup:
                    #增加stream key到本地缓存，并添加组
                    self.streamGroup[stream] = []
                    for group in groups:
                        self.streamGroup[stream].append(group["name"])
                else:
                    for group in groups:
                        if group["name"] not in self.streamGroup[stream]:
                            #缓存未在本地缓存的组
                            self.streamGroup[stream].append(group["name"])
            if stream not in self.streamGroup or groupName not in self.streamGroup[stream]:
                #新增组
                self.thtredis.addGroup(stream, groupName, id='0-0')
                if stream not in self.streamGroup:
                    self.streamGroup[stream] = []
                self.streamGroup[stream].append(groupName)
        #logger.info("self.streamGroup:%s"%(self.streamGroup))

    def registerMsg(self, msgid, mode):
        """
        注册模块订阅消息
        msgid:消息类型 mode:接收画布名
        """
        self.thtredis.addRegisterMode(msgid, mode)

    def dataService(self, stream, group, msgid):
        "上报统计服务,上报stream当前处理的msgid"
        if stream == '统计':
            return
        data = {"stream":stream, "group":group, "reportid":str(msgid)}
        btime = int(time.time()*1000)
        dataStream = GenStreamKey("统计")
        #self.thtredis.writeMsg(data, dataStream)
        #logger.info(f"上报统计: {data} {int(time.time()*1000) - btime}")

    def readLastMsg(self, stream):
        "获取意识流最后一条消息"
        msg = self.revReadMsg(stream, count=1)
        msgid = None
        if msg:
            msgid = msg[0]["msg_id"]
        return msgid

    def rangeById(self, stream, groupdc:dict):
        """
        查询id之后还有多少消息
        """
        if not dict:
            return {}
        msgidlist = list(groupdc.values())
        minmsgid = msgidlist[0]
        retdic = {}
        for msgid in msgidlist:
            retdic[msgid] = 0
            if msgid < minmsgid:
                minmsgid = msgid
        
        ret = self.thtredis.rangeById(GenStreamKey(stream), minmsgid)
        while len(ret) == 100:
            lastmsgid = "0"
            for msg in ret:
                msgid = msg[0]
                if msgid > lastmsgid:
                    lastmsgid = msgid
                for rmsgid in retdic:
                    if msgid > rmsgid:
                        retdic[rmsgid] += 1
            ret = self.thtredis.rangeById(GenStreamKey(stream), lastmsgid)
        for msg in ret:
            msgid = msg[0]
            for rmsgid in retdic:
                if msgid > rmsgid:
                    retdic[rmsgid] += 1
        
        groupdc = {group:retdic[groupdc[group]] for group in groupdc}
        return groupdc

    async def divide_remark(self, request):
        """
        "句式判断":{
            "11":"陈述",
            "12":"疑问",
            "13":"祈使"
        },
        "关联对象":{
            "20":"都无关",
            "21":"与assistant相关",
            "22":"与user相关",
            "23":"都相关"
        },
        "标签":{
            "30":"没有符合要求的标签",
            "31":"描述客观世界的知识",
            "32":"描述个人的感受、观念"
        }
        """
        ret = []
        try:
            query = request
            logger.info(f"divide_remark: {query}")
            uid = query["uid"]
            seq = query["seq"] if "seq" in query else int(time.time()*1000)
            input_txt = query["content"]
            task = query["task_id"] if "task_id" in query else uid
            
            if self.model in ["对话"]:
                llm_data = {'uid':uid, 'input':input_txt}
                divide_response = await request_llm(task, llm_data, "分流_句式判断")
                numbers_in_string = re.findall(r'(\d+)', divide_response)
                if numbers_in_string:
                    tmp_divide = str(numbers_in_string[0])
                    ret.append(tmp_divide)

            
            dialog_list, history_list = await self.get_dialogue_history(uid)
            ori_dialog_list = []
            quest_role = query["quest_role"] if "quest_role" in query else "assistant"
            for dialog in dialog_list:
                role = dialog["role"]
                if dialog["role"] != "user":
                    role = "assistant"
                ori_dialog = {"content": dialog["content"], "role": role}
                ori_dialog_list.append(ori_dialog)
            llm_data = {'uid':uid, 'input':input_txt, "dialog_list":dialog_list, "history_list":history_list, 
                        "ori_dialog_list":ori_dialog_list, "quest_role":quest_role}

            divide_response = await request_llm(task, llm_data, "分流")
            divide_map = json.loads(divide_response)
            ret.extend(divide_map.values())
        except Exception as e:
            logger.info(f"{traceback.format_exc()}")
        return ret


    async def attention_remark(self, request):
        attention = 10
        try:
            query = request
            logger.info(f"attention_remark: {query}")
            uid = query["uid"]
            seq = query["seq"] if "seq" in query else int(time.time()*1000)
            input_txt = query["content"]
            task = query["task_id"] if "task_id" in query else uid
            dialog_list, history_list = await self.get_dialogue_history(uid)
            ori_dialog_list = []
            quest_role = query["quest_role"] if "quest_role" in query else None
            for dialog in dialog_list:
                role = dialog["role"]
                if dialog["role"] != "user":
                    if not quest_role:
                        quest_role = dialog["role"]
                    role = "assistant"
                ori_dialog = {"content": dialog["content"], "role": role}
                ori_dialog_list.append(ori_dialog)
            llm_data = {'uid':uid, 'input':input_txt, "dialog_list":dialog_list, "history_list":history_list, 
                        "ori_dialog_list":ori_dialog_list, "quest_role":quest_role}
            attention_response = await request_llm(task, llm_data, "关注度")
            numbers_in_string = re.findall(r'(\d+)', attention_response)
            
            if numbers_in_string:
                attention = int(numbers_in_string[0])
            if attention > 100:
                attention = 100
            return attention
        except Exception as e:
            logger.info(f"{traceback.format_exc()}")
        return attention


if __name__ == '__main__':
    scf1=ThoughtFlow()
    async def main():
        msg = {'uid': 'jgbtest1014', 'seq': '99099', 'content': '最近心情很不好。', 'target': '对话管理', 'task_id': 'jgbtest1014_1703053254341', 'source': 'None', '写入函数': 'dialogue_service.py:41:input_request', 'attention': 40, 'divide': '[11, 22, 32]', 'parent_id': "['0-0']"}
        ret = scf1.rangeById("Main", {"ConvergenceService":"1703571810791-0"})
        logger.info(ret)

    asyncio.run(main())
