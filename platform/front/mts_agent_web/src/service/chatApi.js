import request from '../utils/request';

// 对话http接口
export async function fetchChatCommand(params) {
  return request('/mts_agent/dialogue/v1/dialogue_http', {
    method: 'POST',
    body: { ...params }
  });
}

// GM命令接口
export async function fetchGMCommand(params) {
  return request('/mts_agent/gm/v1/command', {
    method: 'POST',
    body: { ...params }
  });
}

// 印象查询
export async function fetchImpressions(params) {
  return request('/rag_service/cluster/impressions_search', {
    method: 'POST',
    body: { ...params }
  });
}

// 策略查询
export async function fetchStrategyPage(params) {
  return request('/rag_service/strategy/dialogue/page', {
    method: 'POST',
    body: { ...params }
  });
}

// 插入策略
export async function fetchAddTrigger(params) {
  return request('/mts_agent/strategy/v1/dialogue/tigger/add', {
    method: 'POST',
    body: { ...params }
  });
}

// TTS语音合成
export async function fetchTTS(params) {
  return window.fetch('/openai-tts/v1/text', {
    method: 'POST',
    body: JSON.stringify(params)
  });
}

// 记忆查询
export async function fetchMemoryPage(params) {
  return request('/rag_service/storage/user/all_memory/page', {
    method: 'POST',
    body: { ...params }
  });
}

// 文档上传
export async function fetchUploadDoc(params) {
  return request('/rag_service/database/document/upload', {
    method: 'POST',
    body: params
  });
}

// 分页获取文档
export async function fetchGetDoc(params) {
  return request('/rag_service/database/document/page', {
    method: 'POST',
    body: params
  });
}

// 文档删除
export async function fetchDeleteDoc(params) {
  return request('/rag_service/database/document/delete', {
    method: 'POST',
    body: params
  });
}
