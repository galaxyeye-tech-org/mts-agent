import { fetchChatCommand, fetchGMCommand } from '@/service/chatApi';
import { closeASRWebSocket, createASRWebSocket, sendASR } from '@/utils/asrWebsocket.js';
import * as Player from '@/utils/audioPlayer.js';
import { isString } from '@/utils/isType';
import * as Recorder from '@/utils/recorder.js';
import { connectWebsocket, getWebSocketState, initWebsocket, sendMessage } from '@/utils/websocket';
import { AudioOutlined, RollbackOutlined } from '@ant-design/icons';
import { Button, Input, Modal, Radio, message } from 'antd';
import { debounce } from 'lodash';
import MarkdownIt from 'markdown-it';
import { Fragment, useEffect, useRef, useState } from 'react';
import { connect } from 'umi';
import styles from './styles.less';

// 波形图参数设置
const waveOption = {
  elem: '.recorderWave', // css类选择器
  width: 500,
  height: 30,
  keep: false,
  lineWidth: 2, // 线条宽度
  scale: 1, // 缩放
  phase: 21.8 // 相位
};

const ChatArea = (props) => {
  const { chatModel, dispatch } = props;
  const { chatList, historyChatList, isConnect, intention, isMute } = chatModel;
  const [messageApi, contextHolder] = message.useMessage();
  const [lightState, setLightState] = useState(true);
  const [uidInput, setUidInput] = useState('');
  const [urlInput, setUrlInput] = useState('ws://localhost/mts_agent/dialogue/v1/dialogue');
  const [textInput, setTextInput] = useState('');
  const [isMicrophone, setIsMicrophone] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false); // 是否说话

  const chatContentRef = useRef();
  const md = new MarkdownIt({
    html: false,
    linkify: true,
    typographer: false
  }); // markdown渲染实例

  useEffect(() => {
    // 初始化录音功能
    Recorder.initRecorder({
      // 当前触发速率1/12s,约80ms
      process: (data) => {
        sendASR(data.buffer); // 发送录音数据到asrWS
      }
    });
    // 初始化播放器
    Player.initPlayer();
  }, []);

  useEffect(() => {
    localStorage.setItem('MTS_TOOL_AUDIO_STATE', isMute ? 'true' : 'false');
  }, [isMute]);

  useEffect(() => {
    // 聊天列表更新时滚动到底部
    if (chatContentRef.current) {
      chatContentRef.current.scrollTop = chatContentRef.current.scrollHeight;
    }
  }, [chatList, historyChatList]);

  useEffect(() => {
    if (isSpeaking) {
      createASRWebSocket({
        onClose: () => {
          setIsSpeaking(false);
        },
        onError: (err) => {
          console.warn('[asr] 连接意外断开', err);
          messageApi.error('ASR连接已断开');
        }
      });
      Recorder.initWaveView(waveOption);
      Recorder.getPermission({
        success: () => {
          console.log('麦克风权限获取成功，open');
          Recorder.startRecorder();
        },
        fail: (err) => {
          messageApi.error(err ?? '获取麦克风权限失败');
          closeASRWebSocket();
          setIsSpeaking(false);
        }
      });
    } else {
      closeASRWebSocket();
      Recorder.stopRecorder();
    }
  }, [isSpeaking]);

  // 创建连接
  const handleLink = () => {
    if (!uidInput) {
      messageApi.warning('请输入uid');
      return;
    }
    if (!urlInput) {
      messageApi.warning('请输入url');
      return;
    }
    const linkSuccess = () => {
      messageApi.success('连接成功');
      initLightState();
      initChatHistory();
      initRole();
      initIntention();
    };
    const linkErr = () => {
      messageApi.error('连接断开');
    };
    initWebsocket(uidInput);
    connectWebsocket(urlInput, linkSuccess, linkErr);
  };

  // 处理发送
  const handleSend = () => {
    if (!isConnect) {
      messageApi.warning('当前websocket离线，请先创建连接');
      return;
    }
    if (!textInput || !textInput.trim()) {
      setTextInput('');
      return;
    }
    sendMessage(textInput);
    setTextInput('');
  };

  // 处理红绿灯切换
  const handleLightChange = debounce((e) => {
    const value = e.target.value ? '绿灯' : '红灯';
    const { chatUid } = getWebSocketState();
    fetchGMCommand({ uid: chatUid, method: 'set_exp_status', seq: '2333', data: { status: value } }).then((res) => {
      if (res && res.success) {
        messageApi.success('切换成功');
        setLightState(e.target.value);
        dispatch({
          type: 'chatModel/setChatList',
          payload: {
            message: { type: 'line', content: `已切换为${value}` }
          }
        });
      } else {
        messageApi.error(res?.msg ?? '切换失败');
      }
    });
  }, 1000);

  // 查询红绿灯初始状态
  const initLightState = () => {
    const { chatUid } = getWebSocketState();
    fetchGMCommand({ uid: chatUid, method: 'get_exp_status', seq: '2333' }).then((res) => {
      if (res && res.success) {
        const { status } = res.data;
        if (status === '绿灯') {
          setLightState(true);
        } else {
          setLightState(false);
        }
      }
    });
  };

  // 查询聊天历史记录
  const initChatHistory = () => {
    const { chatUid } = getWebSocketState();
    dispatch({
      type: 'chatModel/fetchGetHistoryChat',
      payload: { uid: chatUid, method: 'get_history_dialog', seq: '2333' }
    });
  };

  // 初始化查询角色
  const initRole = () => {
    const { chatUid } = getWebSocketState();
    dispatch({
      type: 'chatModel/fetchGetRole',
      payload: { uid: chatUid, method: 'get_robot_role', seq: '2333' }
    });
  };

  // 初始化意图
  const initIntention = () => {
    const { chatUid } = getWebSocketState();
    dispatch({
      type: 'chatModel/fetchGetIntention',
      payload: { uid: chatUid, method: 'get_intention', seq: '2333', data: {} }
    });
  };

  // 清除历史对话记录
  const handleClearContext = () => {
    const { chatUid } = getWebSocketState();
    if (!isConnect) {
      messageApi.warning('当前websocket离线，请先创建连接');
      return;
    }
    Modal.confirm({
      title: '提示',
      content: '是否清除对话记录',
      cancelText: '取消',
      okText: '清除',
      onOk: debounce(() => {
        fetchChatCommand({ uid: chatUid, method: 'clear_dialogue_history', seq: '2333' }).then((res) => {
          const { success } = res;
          if (success) {
            messageApi.success('清除对话成功');
            dispatch({
              type: 'chatModel/setChatList',
              payload: {
                message: { type: 'line', content: '以上对话已清除' }
              }
            });
          } else {
            messageApi.error(res?.msg ?? '清除失败');
          }
        });
      }, 500)
    });
  };

  // 清除当前角色
  const clearRole = debounce(() => {
    if (!isConnect) {
      messageApi.warning('当前websocket离线，请先创建连接');
      return;
    }
    const { chatUid } = getWebSocketState();
    fetchGMCommand({ uid: chatUid, method: 'clear_robot_role', seq: '2333' }).then((res) => {
      const { success } = res;
      if (success) {
        messageApi.success('清除角色成功');
        dispatch({
          type: 'chatModel/setChatList',
          payload: {
            message: { type: 'line', content: '当前角色已重置' }
          }
        });
        dispatch({
          type: 'chatModel/setChatModel',
          payload: { globalRole: '' }
        });
      } else {
        messageApi.error(res?.msg ?? '清除失败');
      }
    });
  }, 500);

  // 切换输入模式
  const handleSwitch = () => {
    // if (isSpeaking) {
    //   setIsSpeaking(false);
    // } else {
    //   setIsMicrophone((pre) => !pre);
    // }
  };

  // 打开关闭麦克风
  const handleSpeaking = () => {
    if (!isConnect) {
      messageApi.warning('当前websocket离线，请先创建连接');
      return;
    }
    if (isSpeaking) {
      return;
    } else {
      setIsSpeaking(true);
    }
  };

  // 打开关闭声音
  const handleSwitchVoice = () => {
    dispatch({
      type: 'chatModel/setChatModel',
      payload: { isMute: !isMute }
    });
  };

  // 历史项
  const historyItem = (item, index) => {
    const { role } = item;

    if (role === 'user') {
      return (
        <div className={`${styles.item} ${styles.user}`} key={index}>
          <div className={styles.item__text}>
            <div className={`${styles.item__text_time} ${styles.right}`}>{'--'}</div>
            <div className={styles.item__text_content}>{item?.content}</div>
          </div>
          <div className={styles.item__icon_user}></div>
        </div>
      );
    } else {
      return (
        <div className={`${styles.item} ${styles.ai}`} key={index}>
          <div className={styles.item__icon_ai}></div>
          <div className={styles.item__text}>
            <div className={styles.item__text_time}>{'--'}</div>
            <div
              className={styles.item__text_content}
              dangerouslySetInnerHTML={{ __html: md.renderInline(isString(item?.content) ? item?.content : ' ') }}
            ></div>
          </div>
        </div>
      );
    }
  };

  // 聊天项
  const chatItem = (item, index) => {
    const { type, currentRole } = item;
    if (type === 'user') {
      return (
        <div className={`${styles.item} ${styles.user}`} key={index}>
          <div className={styles.item__text}>
            <div className={`${styles.item__text_time} ${styles.right}`}>{item?.time ?? ''}</div>
            <div className={styles.item__text_content}>{item?.data?.content}</div>
          </div>
          <div className={styles.item__icon_user}></div>
        </div>
      );
    }
    if (type === 'ai') {
      return (
        <div className={`${styles.item} ${styles.ai}`} key={index}>
          <div className={styles.item__icon_ai}></div>
          <div className={styles.item__text}>
            <div className={styles.item__text_time}>
              <span>{currentRole ? `<${currentRole}>` : ''}</span>
              {item?.time ?? ''}
            </div>
            <div
              className={styles.item__text_content}
              dangerouslySetInnerHTML={{
                __html: md.renderInline(isString(item?.data?.content) ? item?.data?.content : ' ')
              }}
            ></div>
          </div>
        </div>
      );
    }
    if (type === 'line' && item.content) {
      return <div className={styles.chat__content_line}>{item.content}</div>;
    }
  };

  // 历史分割线
  const divideLine = () => {
    return <div className={styles.chat__content_line}>----------------以上为历史对话----------------</div>;
  };

  // 连接状态标识点
  const statusPoint = (
    <div className={`${styles.point} ${isConnect ? styles.link : styles.disLink}`}>
      <div className={`${styles.point_inside} ${isConnect ? styles.link_inside : styles.disLink_inside}`}></div>
    </div>
  );

  // 文本输入
  const traditionalContent = () => {
    return (
      <Fragment>
        <div className={styles.chat__input_switch} onClick={handleSwitch}>
          <AudioOutlined />
        </div>
        <Input
          className={styles.chat__input_area}
          placeholder="请输入对话内容"
          value={textInput}
          onChange={(e) => {
            setTextInput(e.target.value);
          }}
          onPressEnter={handleSend}
        ></Input>
        <Button className={styles.chat__input_btn} type="primary" onClick={handleSend}>
          发送
        </Button>
      </Fragment>
    );
  };

  // 麦克风输入
  const microPhoneContent = () => {
    return (
      <Fragment>
        <div className={`${styles.chat__input_switch} ${isSpeaking ? styles.talk : ''}`} onClick={handleSwitch}>
          {isSpeaking ? <div className={styles.cube}></div> : <RollbackOutlined />}
        </div>
        <div className={styles.chat__input_micro} onClick={handleSpeaking}>
          {isSpeaking ? <div class="recorderWave" style={{ width: '540px', height: '30px' }}></div> : '开始说话'}
        </div>
      </Fragment>
    );
  };

  return (
    <Fragment>
      <div className={styles.link}>
        <Input
          placeholder="请输入uid"
          className={`${styles.link__input} ${styles.mobile}`}
          value={uidInput}
          onChange={(e) => {
            setUidInput(e.target.value);
          }}
        ></Input>
        <Input
          placeholder="请输入url"
          className={`${styles.link__input} ${styles.mobile2}`}
          value={urlInput}
          onChange={(e) => {
            setUrlInput(e.target.value);
          }}
        ></Input>
        <Button
          type="primary"
          icon={statusPoint}
          ghost
          className={`${styles.link__btn} ${styles.mobile3}`}
          onClick={handleLink}
        >
          {isConnect ? '已连接' : '连接'}
        </Button>
      </div>
      <div className={styles.chat}>
        <div className={styles.chat__top}>
          <div className={styles.chat__top__btn}>
            <Button type="primary" ghost onClick={handleClearContext}>
              清除对话记录
            </Button>
            <Button type="primary" className={styles.chat__top__btn_margin} ghost onClick={clearRole}>
              清除当前角色
            </Button>
            {/* <div
              className={`${styles.chat__top__btn_voice} ${isMute ? styles.voiceOff : styles.voiceOn}`}
              title={isMute ? '开启语音合成' : '静音'}
              onClick={handleSwitchVoice}
            ></div> */}
          </div>
          <Radio.Group value={lightState} onChange={handleLightChange} disabled={!isConnect}>
            <Radio value={false}>红灯</Radio>
            <Radio value={true}>绿灯</Radio>
          </Radio.Group>
        </div>
        {isConnect && (
          <div className={styles.chat__intention}>
            <div className={styles.chat__intention_title}>意图：</div>
            <div className={styles.chat__intention_text}>{intention}</div>
          </div>
        )}
        <div className={styles.chat__content} ref={chatContentRef}>
          {historyChatList.map((item, index) => {
            return historyItem(item, index);
          })}
          {historyChatList.length > 0 && divideLine()}
          {chatList.map((item, index) => {
            return chatItem(item, index);
          })}
        </div>
        {/* 文本/语音输入框 */}
        <div className={styles.chat__input}>{isMicrophone ? microPhoneContent() : traditionalContent()}</div>
      </div>
      {contextHolder}
    </Fragment>
  );
};

export default connect(({ chatModel }) => ({ chatModel }))(ChatArea);
