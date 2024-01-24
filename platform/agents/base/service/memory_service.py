import json
import time
import uuid
from typing import Optional, Union

from rediscluster import RedisCluster

from base.agent_public.agent_redis import AgentRedis
from base.agent_public.agent_tool import redis_prefix
from base.agent_public.metaclass import Singleton


class WorkMemoryService(Singleton):
    KEY = r'mem_work'
    EX = 3600   # 工作记忆过期时间
    KEY_EX = 3600 * 24 * 7  # key过期清理时间

    def __init__(self):
        self._redis_client: RedisCluster = AgentRedis().conn

    async def save_memory_of_user(
            self, uid: str, timestamp: Optional[Union[int, float]], attention: int, content: Optional[Union[str, dict]],
            expire_time: int = EX,
            **kwargs
    ):
        key = redis_prefix(f'{self.KEY}_{uid}')
        field_time = int(int(time.time()) + expire_time)
        field = f'{field_time}:{uuid.uuid1()}'

        data = {
            r'uid': uid,
            r'timestamp': timestamp,
            r'attention': attention,
            r'content': content
        }
        data.update(kwargs)
        self._redis_client.expire(key, self.KEY_EX)
        self._redis_client.hset(key, field, json.dumps(data, ensure_ascii=False))

    async def get_memories_of_user(self, uid: str) -> list:
        key = redis_prefix(f'{self.KEY}_{uid}')
        work_memory_map = self._redis_client.hgetall(key)
        ret_memory_list = []
        expire_field = []
        now_time = int(time.time())
        work_memory_map = {key: work_memory_map[key] for key in sorted(work_memory_map)}
        for field in work_memory_map:
            # 这个判断是为了做兼容, 未来需要删除
            if not r':' in field:
                continue

            field_time, _ = field.split(':', 1)

            if now_time > int(float(field_time)):
                expire_field.append(field)
                continue
            ret_memory_list.append(json.loads(work_memory_map[field]))
        
        if expire_field:
            self._redis_client.hdel(key, *expire_field)

        return ret_memory_list

    async def save_intention_for_user_robot_id(self, uid: str, robot_id: str, data: dict):

        key = redis_prefix(f'{self.KEY}_{uid}_{robot_id}:intention')

        val = json.dumps(data)

        self._redis_client.set(key, val)

    async def get_intention_for_user_robot_id(self, uid: str, robot_id: str) -> dict:

        key = redis_prefix(f'{self.KEY}_{uid}_{robot_id}:intention')
        resp = self._redis_client.get(key)

        intention_record = {}

        if resp:
            intention_record = json.loads(resp)

        return intention_record
