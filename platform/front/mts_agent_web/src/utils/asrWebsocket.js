/**
 * 语音识别websocket实例
 */

import { isFunction } from './isType';
import { sendMessage } from './websocket';

let ws = undefined; // 实例
let isConnect = false; // 是否处于连接状态

// 处理返回消息
const handleMessage = (msg) => {
  const data = JSON.parse(msg.data);
  console.log('[asr] msg', data);
  if (data && data.code === 0) {
    const { result } = data;
    const { slice_type, voice_text_str } = result;
    if (slice_type === 2) {
      sendMessage(voice_text_str); // 将识别结果发送给聊天websocket
    }
  } else {
    console.warn('[asr] 错误消息', data?.message ?? '无');
  }
};

// 创建websocket连接
function createASRWebSocket({ onClose, onError }) {
  if (isConnect) {
    console.log('[asr] 请勿重复连接');
    return;
  }
  ws = new WebSocket(ASR_URL);
  // 设置推流格式
  ws.binaryType = 'arraybuffer';
  ws.onopen = () => {
    console.log('[asr] 连接成功');
    isConnect = true;
  };
  ws.onmessage = handleMessage;
  ws.onerror = (err) => {
    console.warn('[asr] 连接错误');
    isConnect = false;
    if (isFunction(onError)) {
      onError(err);
    }
  };
  ws.onclose = () => {
    console.warn('[asr] 连接关闭');
    isConnect = false;
    if (isFunction(onClose)) {
      onClose();
    }
  };
}

function closeASRWebSocket() {
  if (ws && isConnect) {
    ws.close();
    ws = undefined;
  }
}

// 发送消息
function sendASR(data) {
  if (ws) {
    ws.send(data);
  }
}

export { closeASRWebSocket, createASRWebSocket, sendASR };
