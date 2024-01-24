# agent-tool-web 接口描述文档

## 聊天模块（左侧）

### 1. 建立聊天连接：

- 接口：`ws://xxxx:xx/mts_agent/dialogue/v1/dialogue?uid=xxxx`
- 说明：
  ```
  # 客户端发送消息协议格式
  {
    uid: 'xxx',
    method: 'input',
    data: {
      content: '聊天输入内容'
    },
    seq: 'any'
  }
  ```

### 2. 清除对话记录

- 接口：`/mts_agent/dialogue/v1/dialogue_http`
- 参数：`{ uid: 'xxx', method: 'clear_dialogue_history', seq: 'any' }`

### 3. 清除当前角色

- 接口：`/mts_agent/gm/v1/command`
- 参数：`{ uid: 'xxx', method: 'clear_robot_role', seq: 'any' }`

### 4. 聊天红绿灯

- 接口：`/mts_agent/gm/v1/command`
- 参数：
  - 查询红绿灯初始状态：`{ uid: 'xxx', method: 'get_exp_status', seq: 'any' }`
  - 切换红绿灯：`{ uid: 'xxx', method: 'set_exp_status', seq: 'any', data: { status: '红灯/绿灯' } }`

## 信息展示模块

### 5.思绪流

来源于聊天 websocket 协议，协议消息内容：

```
{
    "type": "思绪流消息",
    "data": {
        "uid": "jgbtest1011",
        "seq": "99099",
        "content": "最近心情很不好。",
        "target": "对话管理",
        "task_id": "jgbtest1011_1702692174907",
        "source": "None",
        "写入函数": "dialogue_service.py:41:input_request",
        "parent_id": [ "0-0" ],
        "msg_id": "1702692174920-0"
    },
    "uid": "xxx"
}
```

### 6.当前任务信息

- 接口：`/mts_agent/dialogue/v1/dialogue_http`
- 参数：`{uid:'xxx', method:'get_task_context', seq:'any', data:{ task_id:'xxx' }}`

说明：查询参数中的 task_id 来自于来聊天 websocket 协议，协议消息内容：

```
# 初始创建连接，返回初始task_id
{
    "code": 0,
    "msg": "ok",
    "uid": "xxx",
    "seq": "any",
    "task_id": "jgbtest1011_1702692174907"
}

# 后续聊天过程中，任务切换，推送新的task_id
{
    "type": "任务切换",
    "data": {
        "task": {
            "task_change": 1,
            "main_task": "提供心理支持和倾听",
            "prompt": {...}
        }
    },
    "uid": "xxx",
    "task_id": "jgbtest1011_1702692174907"
}
```

### 7.工作记忆

- 接口：`/mts_agent/gm/v1/command`
- 参数：`{ uid: 'xxx', method: 'get_work_memory', seq: 'any' }`

## 输入模块

### 8.插入思绪流

- 接口：`/mts_agent/gm/v1/command`
- 参数：`{ uid: 'xxx', method: 'insert_stream', seq: 'any', data: mindObj}`
- 说明：参数中 mindObj 为思绪流 JSON 对象，由用户输入的 string 内容序列化而来，默认内容为：`"{"content":"我是一个好人", "attention":75, "divide":["11", "22"]}"`

### 9.插入策略

- 接口：`/mts_agent/strategy/v1/dialogue/tigger/add`
- 参数：`{ uid: 'xxx', content: 'xxxx', robot_id: 'agent001', attention: 60}`
- 说明：参数`robot_id`值固定为`agent001`，策略内容`content`为自然语言输入，例如："用户向你倾述负面情绪的时候，你一定要对用户进行安慰，还要鼓励他，让他感受到你的温暖"

### 10.改变角色

- 接口：`/mts_agent/gm/v1/command`
- 参数：`{ uid: 'xxx', method: 'set_role_transform', seq: 'any', data: {content: 'xxxx'}`
- 说明：角色内容`content`为自然语言输入，例如："你是一个医生"、"你是一个程序员"

## 查询模块

### 11. QA 检索

- 接口：`/mts_agent/gm/v1/command`
- 参数：`{ uid: 'xxx', method: 'get_qa_by_content', seq: 'any', data: {content: 'QA检索条件'}`

### 12. 长期记忆 embedding

- 接口：`/mts_agent/gm/v1/command`
- 参数：`{ uid: 'xxx', method: 'get_memory_by_content', seq: 'any', data: {content: '长期记忆检索条件'}`

### 13. 印象查询

- 接口：`/rag_service/cluster/impressions_search`
- 参数：`{ uid: 'xxx' }`

### 14. 策略查询

- 接口：`/rag_service/strategy/dialogue/page`
- 参数：`{ robot_id: 'agent001', limit: 100, uids: ['xxx'] }`
- 说明：参数`robot_id`值固定为`agent001`，`limit`为查询数量，默认 100 条，uids 为 uid 列表

### 15. 记忆查询

- 接口：`/rag_service/storage/user/all_memory/page`
- 参数：`{ uid: 'xxx', limit: 50, cursor: 0, type: data }`
- 说明：
  - `limit`：查询条数，默认 50
  - `cursor`：查询起始位置，默认 0
  - `type`：查询类型，可选字典值：`猜想`、`用户陈述`、`结论`

### 16. 任务上下文

- 接口：`/mts_agent/dialogue/v1/dialogue_http`
- 参数：`{ uid: 'xxx', method: 'get_task_context', seq: 'any', data: { task_id: 'xxx' }`
- 说明：参数`task_id`来源于用户输入

### 17. 任务大模型回复

- 接口：`/mts_agent/gm/v1/command`
- 参数：`{ uid: 'xxx', method: 'get_llm_result', seq: 'any', data: { task_id: 'xxx' }`
- 说明：参数`task_id`来源于用户输入

### 18. 文档操作与查询

#### 上传文档

- 接口：`/rag_service/database/document/upload`
- 参数：

  ```
  {
    upload_files: File1,
    upload_files: File2,
    upload_files: File3,
    confidence: 50
  }
  ```

- 说明：上传参数为 formData 格式，`upload_files`为文件内容，可多文件上传，`confidence`为置信度，默认 50

#### 删除文档

- 接口：`/rag_service/database/document/delete`
- 参数：`{ ids: ['xxx','xxx'] }`
- 说明：ids 为待删除文件 id 列表

#### 文档查询

- 接口：`/rag_service/database/document/page`
- 参数：`{ limit: 50, cursor: 0 }`
- - 说明：
  - `limit`：查询条数，默认 50
  - `cursor`：查询起始位置，默认 0

## 语音接口

### TTS 语音合成

- 接口：`/openai-tts/v1/text`
- 参数：`{ text: '待合成内容'}`

### ASR 语音识别

- 接口：`ws://xxxx:xx/speech-service-atw/v1/wsasr`
