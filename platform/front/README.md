# MTS-Agent

## 1 项目说明

该项目为 MTS-Agent 的 Web 前端调试工具

### 1.1 概述

### 1.2 系统设计

#### 连接模块

![image](/doc/pic/front/连接模块.png)

- 输入 uid 与 websocket 连接地址，建立 websocket 连接

#### 对话模块

![image](/doc/pic/front/对话模块.png)

1. 连接后展示以下内容

- 连接后，根据 uid 查询历史对话，并放入对话记录中，历史对话下方加上分割线，提示“以上为历史对话”
  - POST /mts_agent/gm/v1/command `查询历史对话`
  - 示例：

```json
{
  "uid": "cmrtest009",
  "method": "get_history_dialog",
  "seq": "123456"
}
```

- 连接后，根据 uid 查询当前表达状态，选择红灯或绿灯
  - POST /mts_agent/gm/v1/command `查询表达状态`
  - 示例

```json
{
  "uid": "cmrtest009",
  "method": "get_exp_status",
  "seq": "123456"
}
```

2. 对话

- 点击发送时，将输入框中的内容通过 websocket 发送
- 区分输入与输出的角色，并展示接收时间
- AI 输出需要依据\n 换行，并支持 markdown 显示
- websocket 返回对话格式如下

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "uid": "cmrtest009",
    "task_id": "cmrtest009_1703043397658",
    "target": "表达管理",
    "content": "您提到头晕时会有点站不稳，这可能是头晕的一个常见症状。您在休息或平躺时会感到好转吗？",
    "attention": "80",
    "role": "医生",
    "写入函数": "diffusion_service.py:40:diffusion_service",
    "source": "问题分解",
    "divide": [
      0,
      "ok",
      "cmrtest009",
      1703050743680,
      {
        "句式判断": 12,
        "关联对象": 22,
        "标签": 30
      }
    ],
    "parent_id": ["1703050675711-0"],
    "msg_id": "1703050746100-0",
    "seq": "99099"
  }
}
```

1. 红绿灯切换，单选，选中后调用接口设置表达红绿灯，成功后切换单选项，界面上在当前对话下方加上分割线，提示“已切换为{当前状态}”

- POST /mts_agent/gm/v1/command `设置表达红绿灯`
- 示例

```json
{
    "uid": "jgbtest123",
    "method": "set_exp_status",
    "seq": "123456",
    "data": {"status":"红灯"/"绿灯"}
}
```

4. 清除历史对话，点击后调用接口，界面上在当前对话下方加上分割线，提示“以上对话已清除”

- POST /mts_agent/dialogue/v1/dialogue_http `清除历史对话`
- 示例

```json
{
  "uid": "jgbtest1001",
  "method": "clear_dialogue_history",
  "seq": "123456"
}
```

#### 信息展示模块

信息展示模块，展示聊天过程中产生的对话信息

![image](/doc/pic/front/信息展示模块.png)

1. 思绪流

- websocket 返回的`type`为`思绪流消息`时，展示在思绪流中
- 实时更新
- 需要展示接收时间
- 示例

```json
{
  "type": "思绪流消息",
  "data": {
    "uid": "cmrtest001",
    "seq": "2333",
    "content": "外面下雨了。",
    "target": "对话管理",
    "task_id": "cmrtest001_1703051178120",
    "source": "None",
    "写入函数": "dialogue_service.py:41:input_request",
    "attention": "30",
    "divide": [
      0,
      "ok",
      "cmrtest001",
      "2333",
      {
        "句式判断": 11,
        "关联对象": 20,
        "标签": 31
      }
    ],
    "parent_id": ["0-0"],
    "msg_id": "1703051181575-0"
  },
  "uid": "cmrtest001"
}
```

2. 当前任务信息

- 上方显示当前任务 id
- 切换到该 tab 时更新
- 返回的 json 格式化显示
- POST /mts_agent/dialogue/v1/dialogue_http `查询任务上下文`
- 示例

```json
{
  "uid": "cmrtest009",
  "method": "get_task_context",
  "seq": "123456",
  "data": { "task_id": "cmrtest009_1703050441903" }
}
```

3. 工作记忆

- 切换到该 tab 时更新
- 返回的 json 格式化显示
- POST /mts_agent/gm/v1/command `查询工作记忆`
- 示例

```json
{
  "uid": "cmrtest009",
  "method": "get_work_memory",
  "seq": "123456"
}
```

#### 插入信息模块

用于主动插入信息到 agent 中

![image](/doc/pic/front/插入信息模块.png)

1. 插入思绪流

- POST /mts_agent/gm/v1/command `插入思绪流`
- 示例

```json
{
  "uid": "jgbtest123",
  "method": "insert_stream",
  "seq": "123456",
  "data": { "content": "我是一个好人", "attention": 75, "divide": ["11", "22"] }
}
```

- data 部分为输入框中的预期输入，默认`{"content":"我是一个好人", "attention":75, "divide":["11", "22"]}`

2. 插入策略

- 用户输入为`content`
- `robot_id`默认为"agent001"
- `attention`默认为"60"
- POST /mts_agent/strategy/v1/dialogue/tigger/add
- 示例

```json
{
  "content": "要是用户态度较强硬，还一直不听其他人的建议，你不要和他硬碰硬，应该柔和的和他说，再给他一些相似的案例。",
  "robot_id": "agent001",
  "uid": "test001",
  "attention": 60
}
```

3. 改变角色

- POST /mts_agent/gm/v1/command `角色转换`
- 示例：
```json
{
    "uid": "test001",
    "method": "set_role_transform",
    "seq": "1703835963000",
    "data": {
        "content": "扮演一个消防员"
    }
}
```

#### 信息查询模块

![image](/doc/pic/front/信息查询模块.png)

1. QA 检索

- 输入为`content`
- POST /mts_agent/gm/v1/command `匹配qa`
- 示例

```json
{
  "uid": "jgbtest123",
  "method": "get_qa_by_content",
  "seq": "123456",
  "data": { "content": "问题分解" }
}
```

2. 长期记忆 embedding

- 输入为`content`
- POST /mts_agent/gm/v1/command `匹配长期记忆`
- 示例

```json
{
  "uid": "cmrtest010",
  "method": "get_memory_by_content",
  "seq": "123456",
  "data": { "content": "最近睡眠不太好" }
}
```

3. 任务上下文

- 输入为**用户自行填入**的`task_id`
- 接口同[当前任务信息](#当前任务信息)
  POST /mts_agent/dialogue/v1/dialogue_http `查询任务上下文`

```json
{
  "uid": "cmrtest009",
  "method": "get_task_context",
  "seq": "123456",
  "data": { "task_id": "cmrtest009_1703054131544" }
}
```

4. 任务大模型回复

- 输入为**用户自行填入**的`task_id`
- POST /mts_agent/gm/v1/command `查询任务大模型回复`
- 示例

```json
{
  "uid": "cmrtest009",
  "method": "get_llm_result",
  "seq": "123456",
  "data": { "task_id": "cmrtest009_1703043397658" }
}
```

5. 印象查询

- http://172.16.10.191:9090
- POST /rag_service/cluster/impressions_search `impressions search`
- 示例

```json
{
  "uid": "xtest001"
}
```

6. 策略查询

- `robot_id`默认为"agent001"
- `limit`默认为"100"
- http://172.16.10.191:9090
- POST /rag_service/strategy/dialogue/page `分页获取该robot_id下所有策略`
- 示例

```json
{
  "robot_id": "agent001",
  "limit": 100
}
```

7. 记忆查询
   
- POST /rag_service/storage/user/all_memory/page `游标方式范围查询用户记忆`
- 示例：
```json
{
    "uid": "Young1226",
    "limit": 50,
    "cursor": 0,
    "type": "猜想"
}
```

8. 文档操作与查询

POST /rag_service/database/document/page `分页获取文档`  
POST /rag_service/database/document/upload `文档上传`  
POST /rag_service/database/document/delete `删除文档`  

1. 点击文档操作与查询，展示文件总数、和各文件状态（包括已上传的文件名、上传进度、导入时间、删除按钮）
2. 点击删除按钮后，重新查询当前文件状态
3. 支持手动刷新


### 1.3 工程文件结构

```
agent_tool_web
├─ .gitignore
├─ .npmrc
├─ .prettierignore
├─ .prettierrc.js                # 相关文档
├─ config                        # 项目配置文件
│  ├─ config.js                  # 开发环境配置
│  └─ config.prd.js              # 生产环境配置
├─ doc                           # 相关文档
├─ package.json                  # 开发配置文件
├─ README.md
└─ src
   ├─ assets                     # 静态资源文件
   ├─ layouts                    # 布局文件
   ├─ models                     # dva数据管理
   ├─ pages                      # 页面组件
   │  ├─ global.less             # 全局样式
   │  └─ index                   # 主页面组件
   │     ├─ components
   │     │  ├─ ChatArea          # 聊天组件（左侧）
   │     │  ├─ DisplayArea       # 显示组件（中部）
   │     │  └─ SearchArea        # 查询组件（右侧）
   │     ├─ index.jsx
   │     └─ styles.less
   ├─ service
   │  └─ chatApi.js              # 接口封装
   └─ utils
      ├─ asrWebsocket.js         # asr websocket工具
      ├─ audioPlayer.js          # 语音播放工具
      ├─ constants.js            # 常量存储
      ├─ isType.js               # 类型判断工具
      ├─ recorder.js             # 录音工具
      ├─ request.js              # 请求封装
      ├─ structure.js            # 常用数据结构
      └─ websocket.js            # 聊天websocket工具
```

### 1.4 安装部署

#### 1.安装 node

本项目需要本地安装 node 环境，node 版本要求 16.14.0 及以上。

node 安装过程省略，终端输入下面命令查看 node 版本，验证是否安装成功：

```
node -v
```

#### 2.安装 yarn

本项目采用`yarn`进行依赖管理，安装 yarn 命令如下：

```
npm install -g yarn
```

#### 3.安装依赖

输入以下命令安装项目所需依赖：

```
yarn
```

#### 4.项目打包

执行以下命令，即可在根目录下生成打包后的工程文件，进行部署：

```
yarn build  # 开发环境
yarn build:prd  # 生产环境
```

在路径`/platform/front/dist`下存在已经打包好的前端工程代码，可以直接用于部署。

### 1.5 运行

#### 1.安装依赖

输入以下命令安装项目所需依赖：

```
yarn
```

#### 2.运行项目

输入以下命令启动项目：

```
yarn start             # 开发环境
yarn start:prd         # 生产环境
```
