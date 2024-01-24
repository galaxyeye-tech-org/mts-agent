import dayjs from 'dayjs';
import { fetchChatCommand, fetchGMCommand } from '../service/chatApi';

export default {
  namespace: 'chatModel',
  state: {
    chatList: [], // 对话列表
    historyChatList: [], // 历史对话列表
    mindStream: [], // 思绪流
    missionId: '', // 当前任务id
    missionDetail: {}, // 当前任务上下文
    workMemory: {}, // 工作记忆
    intention: '当前暂无意图', // 当前意图
    globalRole: '', // 当前角色
    isConnect: false, // websocket连接状态
    isMute: localStorage.getItem('MTS_TOOL_AUDIO_STATE') === 'true' // 是否关闭tts语音合成（用字符串标识）
  },
  effects: {
    // 获取任务信息
    *fetchGetMissionDetail({ payload, callback }, { call, put }) {
      const response = yield call(fetchChatCommand, payload);
      const { success = false } = response;
      if (success) {
        const { task_context } = response;
        yield put({
          type: 'setChatModel',
          payload: { missionDetail: task_context, missionId: payload?.data?.task_id ?? '' }
        });
      }
      if (callback) callback(response);
    },
    // 获取工作记忆
    *fetchGetWorkMemory({ payload, callback }, { call, put }) {
      const response = yield call(fetchGMCommand, payload);
      const { success = false } = response;
      if (success) {
        const { data } = response;
        yield put({
          type: 'setChatModel',
          payload: { workMemory: data?.work_memory ?? {} }
        });
      }
      if (callback) callback(response);
    },
    // 获取历史聊天记录
    *fetchGetHistoryChat({ payload, callback }, { call, put }) {
      const response = yield call(fetchGMCommand, payload);
      const { success = false } = response;
      if (success) {
        const { data } = response;
        yield put({
          type: 'setChatModel',
          payload: { historyChatList: data?.dialogue_list ?? [] }
        });
      }
      if (callback) callback(response);
    },
    // 查询当前角色
    *fetchGetRole({ payload, callback }, { call, put }) {
      const response = yield call(fetchGMCommand, payload);
      const { success = false } = response;
      if (success) {
        const { data } = response;
        yield put({
          type: 'setChatModel',
          payload: { globalRole: data?.role ? data?.role : '' }
        });
      }
      if (callback) callback(response);
    },
    // 查询当前意图
    *fetchGetIntention({ payload, callback }, { call, put }) {
      const response = yield call(fetchGMCommand, payload);
      const { success = false } = response;
      if (success) {
        const { data } = response;
        yield put({
          type: 'setChatModel',
          payload: { intention: data?.result?.main_task ? data?.result?.main_task : '当前暂无意图' }
        });
      }
      if (callback) callback(response);
    }
  },
  reducers: {
    setChatModel(state, { payload }) {
      return {
        ...state,
        ...payload
      };
    },
    // 在聊天列表末尾插入
    setChatList(state, { payload }) {
      const { message } = payload;
      const copyList = JSON.parse(JSON.stringify(state.chatList));
      if (message && Object.keys(message).length > 0) {
        message.time = dayjs().format('HH:mm:ss');
        if (state.globalRole && message.type === 'ai') {
          message.currentRole = state.globalRole; // 添加当前对话角色
        }
        copyList.push(message);
      }
      return {
        ...state,
        chatList: copyList
      };
    },
    // 在思绪流列表末尾插入
    setMindStreamList(state, { payload }) {
      const { message } = payload;
      const copyList = JSON.parse(JSON.stringify(state.mindStream));
      if (message && Object.keys(message).length > 0) {
        message.time = dayjs().format('HH:mm:ss');
        copyList.push(message);
      }
      return {
        ...state,
        mindStream: copyList
      };
    }
  }
};
