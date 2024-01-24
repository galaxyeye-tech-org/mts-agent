import AiChat from 'bm-aichat-core';
import { getDvaApp } from 'umi';
import { isFunction } from './isType';

let aiChat = null; // 聊天插件实例
let isConnected = false; // 当前连接状态
let chatUid = ''; // 当前连接uid
let taskId = ''; // 当前任务id
const { dispatch } = getDvaApp()._store;

// 初始化websocket
export function initWebsocket(uid) {
  chatUid = uid;
  aiChat = new AiChat({
    getAichatReqParams: (params) => params
  });
}

// 打开连接
export function connectWebsocket(url, successCallback, errorCallback) {
  if (!aiChat || !chatUid) {
    return;
  }
  const wsUrl = url ?? WS_URL;

  aiChat.setReconnect(false); // 禁止自动重连
  aiChat.createConnect(`${wsUrl}?uid=${chatUid}`);

  aiChat.onStatusChange(({ websocketIsOk }) => {
    console.log('[ws] status changed:', websocketIsOk);
    isConnected = websocketIsOk;
    dispatch({
      type: 'chatModel/setChatModel',
      payload: { isConnect: websocketIsOk }
    });
    if (websocketIsOk && isFunction(successCallback)) {
      successCallback();
    }
    if (!websocketIsOk && isFunction(errorCallback)) {
      errorCallback();
    }
  });

  aiChat.onMessage((msg) => {
    console.log('%c [ws] ack message:', 'color: #07c160; font-size: 14px', msg);
  });

  // 处理未知类型消息
  aiChat.onUnknownMethod((msg) => {
    const { type, data = {}, task_id } = msg;
    console.log('%c [ws] unKnow ack message:', 'color: #0ca1f7; font-size: 14px', msg);
    if (type === '思绪流消息') {
      dispatch({
        type: 'chatModel/setMindStreamList',
        payload: { message: data }
      });
    } else if (type === '意图切换') {
      dispatch({
        type: 'chatModel/setChatModel',
        payload: { intention: data.main_task ?? '当前暂无意图' }
      });
    } else if (type === '任务切换') {
      taskId = task_id;
      dispatch({
        type: 'chatModel/fetchGetMissionDetail',
        payload: {
          uid: chatUid,
          method: 'get_task_context',
          seq: '2333',
          data: { task_id }
        }
      });
    } else if (data?.target === '表达管理') {
      const { chatModel = {} } = getDvaApp()._store.getState();
      const { isMute } = chatModel;
      // 仅当开启语音输入模式时进行语音合成
      // if (!isMute && data && data.content && isString(data.content)) {
      //   openTTS(data.content);
      // }
      dispatch({
        type: 'chatModel/setChatList',
        payload: { message: { data, type: 'ai' } }
      });
    } else if (task_id) {
      taskId = task_id;
      dispatch({
        type: 'chatModel/fetchGetMissionDetail',
        payload: {
          uid: chatUid,
          method: 'get_task_context',
          seq: '2333',
          data: { task_id }
        }
      });
    }
  });

  // 已连接过程中错误处理
  aiChat.onError((err) => {
    console.log('%c [ws] error:', 'color: #fd9090; font-size: 14px', JSON.stringify(err));
  });
}

// 关闭websocket
export function closeWebsocket() {
  aiChat.closeConnect();
}

// 发送消息方法
export function sendMessage(text) {
  if (!aiChat || !isConnected) {
    return;
  }
  const message = {
    uid: chatUid,
    method: 'input',
    data: {
      content: text
    },
    seq: '2333'
  };
  aiChat.sendMessage(message);
  message.type = 'user';
  dispatch({
    type: 'chatModel/setChatList',
    payload: { message }
  });
}

// 状态参数查询
export function getWebSocketState() {
  return { isConnected, chatUid, taskId };
}
