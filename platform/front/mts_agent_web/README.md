# MTS-Agent

## 1 项目说明

该项目为 MTS-Agent 的 Web 前端调试工具

### 1.1 概述

### 1.2 系统设计

### 1.3 工程设计

#### 1.4 工程文件结构

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

### 1.5 安装部署

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

工程文件名 dist

### 1.6 运行

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
