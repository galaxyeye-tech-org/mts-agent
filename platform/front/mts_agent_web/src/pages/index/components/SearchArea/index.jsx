import {
  fetchAddTrigger,
  fetchChatCommand,
  fetchGMCommand,
  fetchImpressions,
  fetchMemoryPage,
  fetchStrategyPage
} from '@/service/chatApi';
import { getWebSocketState } from '@/utils/websocket';
import { Button, Input, Modal, Tabs, message } from 'antd';
import { useState } from 'react';
import { connect } from 'umi';
import DocContent from './components/DocContent';
import TabContent from './components/TabContent';
import styles from './styles.less';

const { TextArea } = Input;
const defaultText = '{"content":"我是一个好人", "attention":75, "divide":["11", "22"]}';
const tabList = ['qa', 'embedding', 'impress', 'strategy', 'memory', 'mission', 'gpt', 'doc']; // tab key

const SearchArea = (props) => {
  const { chatModel, dispatch } = props;
  const { isConnect } = chatModel;

  const [mindInput, setMindInput] = useState(defaultText); //思绪流输入框内容
  const [loading, setLoading] = useState(false); // 插入策略加载状态
  const [mindLoading, setMindLoading] = useState(false); // 插入思绪流加载状态
  const [roleLoading, setRoleLoading] = useState(false); // 插入思绪流加载状态
  const [currentTab, setCurrentTab] = useState(tabList[0]);

  const [messageApi, contextHolder] = message.useMessage();

  // 查询任务上下文
  const queryMissionContext = (id) => {
    return new Promise((resolve, reject) => {
      if (!isConnect) {
        messageApi.warning('当前websocket离线，请先建立连接');
        resolve(null);
        return;
      }
      if (!id) {
        resolve(null);
        return;
      }
      const { chatUid } = getWebSocketState();
      fetchChatCommand({
        uid: chatUid,
        method: 'get_task_context',
        seq: '2333',
        data: { task_id: id }
      }).then((res) => {
        if (res && res.success) {
          resolve(res?.task_context ?? {});
        } else {
          resolve(null);
        }
      });
    });
  };

  // 查询任务大模型回复
  const queryGPTReplay = (id) => {
    return new Promise((resolve, reject) => {
      if (!isConnect) {
        messageApi.warning('当前websocket离线，请先建立连接');
        resolve(null);
        return;
      }
      if (!id) {
        resolve(null);
        return;
      }
      const { chatUid } = getWebSocketState();
      fetchGMCommand({
        uid: chatUid,
        method: 'get_llm_result',
        seq: '2333',
        data: { task_id: id }
      }).then((res) => {
        if (res && res.success) {
          resolve(res?.data?.result ?? {});
        } else {
          resolve(null);
        }
      });
    });
  };

  // 查询QA信息
  const queryQA = (data) => {
    return new Promise((resolve, reject) => {
      if (!isConnect) {
        messageApi.warning('当前websocket离线，请先建立连接');
        resolve(null);
        return;
      }
      if (!data) {
        resolve(null);
        return;
      }
      const { chatUid } = getWebSocketState();
      fetchGMCommand({
        uid: chatUid,
        method: 'get_qa_by_content',
        seq: '2333',
        data: { content: data }
      }).then((res) => {
        if (res && res.success) {
          resolve(res?.data?.result ?? {});
        } else {
          resolve(null);
        }
      });
    });
  };

  // 查询长期记忆embedding
  const queryEmbedding = (data) => {
    return new Promise((resolve, reject) => {
      if (!isConnect) {
        messageApi.warning('当前websocket离线，请先建立连接');
        resolve(null);
        return;
      }
      if (!data) {
        resolve(null);
        return;
      }
      const { chatUid } = getWebSocketState();
      fetchGMCommand({
        uid: chatUid,
        method: 'get_memory_by_content',
        seq: '2333',
        data: { content: data }
      }).then((res) => {
        if (res && res.success) {
          resolve(res?.data?.result ?? {});
        } else {
          resolve(null);
        }
      });
    });
  };

  // 查询印象信息
  const queryImpressions = () => {
    return new Promise((resolve, reject) => {
      if (!isConnect) {
        resolve(null);
        return;
      }
      const { chatUid } = getWebSocketState();
      fetchImpressions({
        uid: chatUid
      }).then((res) => {
        if (res && res.success) {
          resolve(res?.data ?? {});
        } else {
          resolve(null);
        }
      });
    });
  };

  // 查询策略信息
  const queryStrategy = () => {
    return new Promise((resolve, reject) => {
      if (!isConnect) {
        resolve(null);
        return;
      }
      const { chatUid } = getWebSocketState();
      fetchStrategyPage({ robot_id: 'agent001', limit: 100, uids: [chatUid] }).then((res) => {
        if (res && res.success) {
          resolve(res?.data ?? {});
        } else {
          resolve(null);
        }
      });
    });
  };

  // 查询记忆信息
  const queryMemory = (data) => {
    return new Promise((resolve, reject) => {
      if (!isConnect) {
        messageApi.warning('当前websocket离线，请先建立连接');
        resolve(null);
        return;
      }
      if (!data) {
        resolve(null);
        return;
      }
      const { chatUid } = getWebSocketState();
      fetchMemoryPage({
        uid: chatUid,
        limit: 50,
        cursor: 0,
        type: data
      }).then((res) => {
        if (res && res.success) {
          resolve(res?.data ?? {});
        } else {
          resolve(null);
        }
      });
    });
  };

  // tab列表
  const items = [
    {
      key: tabList[0],
      label: 'QA检索',
      children: (
        <TabContent
          name={'QA检索'}
          visible={currentTab === tabList[0]}
          action={queryQA}
          search={true}
          tips={'请输入QA检索条件'}
        ></TabContent>
      )
    },
    {
      key: tabList[1],
      label: '长期记忆embedding',
      children: (
        <TabContent
          name={'长期记忆embedding'}
          visible={currentTab === tabList[1]}
          action={queryEmbedding}
          search={true}
          tips={'请输入长期记忆检索条件'}
        ></TabContent>
      )
    },
    {
      key: tabList[2],
      label: '印象查询',
      children: (
        <TabContent name={'印象查询'} visible={currentTab === tabList[2]} action={queryImpressions}></TabContent>
      )
    },
    {
      key: tabList[3],
      label: '策略查询',
      children: <TabContent name={'策略查询'} visible={currentTab === tabList[3]} action={queryStrategy}></TabContent>
    },
    {
      key: tabList[4],
      label: '记忆查询',
      children: (
        <TabContent
          name={'记忆查询'}
          visible={currentTab === tabList[4]}
          search={true}
          isMemory={true}
          action={queryMemory}
        ></TabContent>
      )
    },
    {
      key: tabList[5],
      label: '任务上下文',
      children: (
        <TabContent
          name={'任务上下文'}
          visible={currentTab === tabList[5]}
          action={queryMissionContext}
          search={true}
          tips={'请输入task_id'}
        ></TabContent>
      )
    },
    {
      key: tabList[6],
      label: '任务大模型回复',
      children: (
        <TabContent
          name={'任务大模型回复'}
          visible={currentTab === tabList[6]}
          action={queryGPTReplay}
          search={true}
          tips={'请输入task_id'}
        ></TabContent>
      )
    },
    {
      key: tabList[7],
      label: '文档操作与查询',
      children: <DocContent visible={currentTab === tabList[7]}></DocContent>
    }
  ];

  const handleMindChange = (e) => {
    const inputText = e.target.value;
    setMindInput(inputText);
  };

  const handleTabChange = (activeKey) => {
    setCurrentTab(activeKey);
  };

  // 插入思绪流
  const handleInsertMind = () => {
    if (!mindInput || !mindInput.trim()) {
      return;
    }
    let mindObj = {};
    try {
      mindObj = JSON.parse(mindInput);
    } catch (err) {
      messageApi.error('JSON解析失败，请检查输入内容');
      return;
    }
    setMindLoading(true);
    const { chatUid } = getWebSocketState();
    fetchGMCommand({
      uid: chatUid,
      method: 'insert_stream',
      seq: '2333',
      data: mindObj
    })
      .then((res) => {
        if (res && res.success) {
          messageApi.success('思绪插入成功');
        } else {
          Modal.error({
            title: '失败',
            content: res.msg ? res.msg : '思绪插入失败',
            okText: '确定'
          });
        }
        setMindLoading(false);
      })
      .catch((_) => {
        setMindLoading(false);
      });
  };

  // 插入策略
  const handleInsertStrategy = () => {
    if (!mindInput || !mindInput.trim()) {
      messageApi.warning('请输入策略内容');
      return;
    }
    setLoading(true);
    const { chatUid } = getWebSocketState();
    fetchAddTrigger({
      uid: chatUid,
      content: mindInput,
      robot_id: 'agent001',
      attention: 60
    })
      .then((res) => {
        if (res && res.success) {
          messageApi.success('策略插入成功');
        } else {
          Modal.error({
            title: '失败',
            content: res.msg ? res.msg : '策略插入失败',
            okText: '确定'
          });
        }
        setLoading(false);
      })
      .catch((_) => {
        setLoading(false);
      });
  };

  // 改变角色
  const handleChangeRole = () => {
    if (!mindInput || !mindInput.trim()) {
      messageApi.warning('请输入角色内容');
      return;
    }
    setRoleLoading(true);
    const { chatUid } = getWebSocketState();
    fetchGMCommand({
      uid: chatUid,
      method: 'set_role_transform',
      seq: '2333',
      data: {
        content: mindInput
      }
    })
      .then((res) => {
        if (res && res.success) {
          messageApi.success('切换角色成功');
          // 成功后查询角色
          dispatch({
            type: 'chatModel/fetchGetRole',
            payload: { uid: chatUid, method: 'get_robot_role', seq: '2333' }
          });
        } else {
          Modal.error({
            title: '失败',
            content: res.msg ? res.msg : '切换角色失败',
            okText: '确定'
          });
        }
        setRoleLoading(false);
      })
      .catch((_) => {
        setRoleLoading(false);
      });
  };

  return (
    <div className={styles.search}>
      <TextArea
        className={styles.search_area}
        placeholder={'请输入策略/JSON格式思绪流'}
        value={mindInput}
        onChange={handleMindChange}
        autoSize={{ minRows: 4, maxRows: 4 }}
      ></TextArea>
      <div className={styles.search__btn}>
        <Button
          className={styles.search__btn_insert}
          type="primary"
          disabled={!isConnect || loading || roleLoading}
          loading={mindLoading}
          onClick={handleInsertMind}
        >
          插入思绪流
        </Button>
        <Button
          className={styles.search__btn_insert}
          type="primary"
          disabled={!isConnect || mindLoading || roleLoading}
          onClick={handleInsertStrategy}
          loading={loading}
        >
          插入策略
        </Button>
        <Button
          className={styles.search__btn_insert}
          type="primary"
          disabled={!isConnect || mindLoading || loading}
          onClick={handleChangeRole}
          loading={roleLoading}
        >
          改变角色
        </Button>
      </div>
      <div className={styles.search__multiple}>
        <Tabs value={currentTab} onChange={handleTabChange} items={items} />
      </div>
      {contextHolder}
    </div>
  );
};

export default connect(({ chatModel }) => ({ chatModel }))(SearchArea);
