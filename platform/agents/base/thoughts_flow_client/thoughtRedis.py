#-*- encoding: utf-8 -*-
__author__ = 'Jianggb'

import traceback
import time

from rediscluster import RedisClusterException,RedisClusterError

from base.agent_public.agent_tool import *
from base.agent_public.agent_redis import AgentRedis

from setting import BaseConfig


class ThoughtRedis:
    def __init__(self):
        self.__rc = AgentRedis().conn

    def getRc(self):
        return self.__rc

    def reConnect(self):
        "重连3次，每次间隔4秒，都失败则抛出异常"
        reCount = 3
        while reCount > 0:
            reCount -= 1
            try:
                self.__rc = AgentRedis().conn
                return
            except Exception as e:
                time.sleep(4)
                logger.info("尝试连接.....")
                pass
        if reCount == 0:
            raise RedisClusterError("多次连接失败")

    def __str__(self):
        return "CSFRedis"

    def writeMsg(self, msgDic, stream):
        "stream写入消息"
        if len(stream) == 0:
            raise ValueError('stream 必须不为空')
        if len(msgDic) == 0:
            raise ValueError('msgDic 必须不为空')
        mid = self.__rc.xadd(stream, msgDic, maxlen=100000)
        logger.debug("id:%s, stream:%s, msgDic:%s"%(mid, stream, msgDic))
        return mid

    def readMsg(self, streams, block=None, count=None):
        """
        从多个stream获取消息\n
        streams:stream名与已获取的最大id字典，如{"反应模式":"0-0","好奇心":"$","情绪":"1618489889536-0"}\n
        block:阻塞毫秒时间　count:获取消息数量\n
        0-0最小id表示从第一个消息开始读,$从最后一个消息开始读
        """
        msg = self.__rc.xread(streams,block=block,count=count)
        logger.debug(msg)
        return msg

    def readMsgFromStream(self, stream, id="$", block=None, count=None):
        """
        从指定stream获取消息\n
        stream:stream名\n
        id:已获取的最大id，如"0-0","$","1618489889536-0" \n
        block:阻塞毫秒时间　count:获取消息数量\n
        0-0最小id表示从第一个消息开始读,$从最后一个消息开始读
        """
        if len(stream) == 0:
            raise ValueError('stream 必须不为空')
        streams = {}
        streams[stream] = id
        msg = self.__rc.xread(streams,block=block,count=count)
        logger.debug(msg)
        return msg

    def readMsgFromStreamByGroup(self, group, consumer,streams, block=None, count=None, noack=False):
        """
        从指定streams获取count个消息\n
        group:订阅画布消息组名 consumer:组内消费者名 streams:画布名列表\n
        block:阻塞毫秒时间 count:获取消息数量 noack:是否不用ack
        """
        if len(streams) == 0:
            raise ValueError('streams 必须不为空')
        streamDic = {}
        for stream in streams:
            streamDic[stream] = ">"
        msg = None
        try:
            msg = self.__rc.xreadgroup(group, consumer, streamDic,block=block,count=count,noack=noack)
        except RedisClusterException as e:
            #捕获RedisClusterException，重连
            self.reConnect()
            #重连后重新执行命令
            try:
                msg = self.__rc.xreadgroup(group, consumer, streamDic,block=block,count=count,noack=noack)
            except Exception as e:
                logger.error("读取消息失败:%s"%e)
                time.sleep(4)
                raise e
        if msg:
            logger.debug(msg)
        return msg

    def getNotAckMsg(self, stream, group, timeout=10000):
        """
        获取组group在stream中还未答复的消息,默认10s未答复\n
        stream:stream名\n
        group:组名\n
        timeout:超时时间默认10s
        """
        msgs = self.__rc.xpending_range(stream, group, "-", "+", 10)
        retMsgid = []
        logger.debug(msgs)
        for msg in msgs:
            if msg["time_since_delivered"] > timeout:
                ret = self.__rc.xrange(stream, min=msg['message_id'], max=msg['message_id'], count=1)
                retMsgid.append(ret[0][0])
        logger.debug(retMsgid)
        return retMsgid

    def ackMsg(self, stream, group, *ids):
        """
        处理完或接收到消息后确认消息\n
        stream:stream名\n
        group:组名\n
        ids:确认消息
        """
        return self.__rc.xack(stream, group, *ids)

    def groupInfo(self, stream):
        "获取stream组信息"
        msg = self.__rc.xinfo_groups(stream)
        return msg

    def addGroup(self, stream, group, id='$'):
        "创建组，默认获取最新消息，id='0-0'从头开始获取消息"
        self.__rc.xgroup_create(stream, group, id, True)

    def readMsgById(self, stream, id):
        "读取指定id消息"
        return self.__rc.xrange(stream, id, id)

    def streamExist(self, stream):
        "判断stream是否存在"
        ret = self.__rc.exists(stream)
        return ret

    def revRangeById(self, stream, id='+', count=10):
        """
        从id开始倒序读取id之前的count个消息
        默认从最后一条消息读取10条消息
        """
        rlcount = count
        if id != '+':
            rlcount += 1
        ret = self.__rc.xrevrange(stream, id, '-', rlcount)
        if id != '+':
            ret = ret[1:]
        return ret

    def rangeById(self, stream, id1, count=100):
        """
        查询id之后还有多少消息
        """
        ret = self.__rc.xrange(stream, id1, '+', count)
        return ret

    def addRegisterMode(self, msgId, mode):
        "添加模块订阅消息"
        self.__rc.hset(buildSubMsgListKey(), msgId, mode)

    def getAllRegiste(self):
        "获取所有模块订阅消息"
        return self.__rc.hgetall(buildSubMsgListKey())

    def setTrans(self, msgid, transdic):
        "保存透传字段"
        key = buildTransKey(msgid)
        self.__rc.hset(key, mapping=transdic)
        self.__rc.expire(key, 4*60*60)

    def getTrans(self, msgid):
        "查询透传字段"
        key = buildTransKey(msgid)
        return self.__rc.hgetall(key)

    def setTransChatModel(self, robotid, chatModel):
        "保存透传字段"
        key = buildTransChatModel(robotid)
        self.__rc.set(key, str(chatModel))
        self.__rc.expire(key, 4*60*60)

    def getTransChatModel(self, robotid):
        "查询透传字段"
        key = buildTransChatModel(robotid)
        return self.__rc.get(key)

    def get_attention_ratio(self, model="public"):
        "获取model模块的专注度系数"
        ret = self.__rc.get(buildAttentionRatioKey(model))
        if not ret:
            ret = 1
        try:
            ret = float(ret)
        except Exception as e:
            logger.error(traceback.format_exc())
            ret = 1
        return ret

    def set_attention_ratio(self, ratio, model="public"):
        "设置model模块的专注度系数"
        return self.__rc.set(buildAttentionRatioKey(model), ratio)

    def get_min_attention(self, model):
        "获取model模块的最低专注度"
        ret = self.__rc.get(buildMinAttentionKey(model))
        if not ret:
            ret = BaseConfig.DefaultMinAttention
        try:
            ret = float(ret)
        except Exception as e:
            logger.error(traceback.format_exc())
            ret = BaseConfig.DefaultMinAttention
        return ret

    def set_min_attention(self, model, attention):
        "设置model模块的最低专注度"
        return self.__rc.set(buildMinAttentionKey(model), attention)

    def set_expression_status(self, uid, status):
        "设置表达状态"
        return self.__rc.set(buildExpStatusKey(uid), status)

    def get_expression_status(self, uid):
        "查询表达状态"
        exp_status = self.__rc.get(buildExpStatusKey(uid))
        logger.info(f"查询表达状态: {uid} {exp_status}")
        if exp_status:
            return exp_status
        else:
            return "绿灯"

    def set_last_task(self, uid, task, nodeid):
        "设置最近任务"
        task_value = f"{task}@{nodeid}"
        logger.info(f"设置最近任务 {uid} {task_value}")
        return self.__rc.set(buildLastTaskKey(uid), task_value)

    def delete_last_task(self, uid):
        "删除最近任务"
        logger.info(f"删除最近任务 {uid}")
        return self.__rc.delete(buildLastTaskKey(uid))

    def get_last_task(self, uid):
        "查询最近任务"
        task_value:str = self.__rc.get(buildLastTaskKey(uid))
        logger.info(f"查询最近任务 {uid} {task_value}")
        if not task_value:
            return []
        idx = task_value.rfind("@")
        if idx:
            nodeid = task_value[idx+1:]
            task = task_value[:idx]
            return [task, nodeid]
        else:
            return [task_value, "None"]


if __name__ == '__main__':
    scf1=ThoughtRedis()
    task = "task@001"
    nodeid = "nodeid001"
    task_value = f"{task}@{nodeid}"
    idx = task_value.rfind("@")
    if idx:
        nodeid = task_value[idx+1:]
        task = task_value[:idx]
        print(task, nodeid)
    

