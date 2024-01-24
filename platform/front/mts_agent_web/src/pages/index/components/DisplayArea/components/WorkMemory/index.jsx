import { getWebSocketState } from '@/utils/websocket';
import { useEffect, useState } from 'react';
import ReactJson from 'react-json-view';
import { connect } from 'umi';
import styles from './styles.less';

const WorkMemory = (props) => {
  const { chatModel, visible, dispatch } = props;
  const { workMemory } = chatModel;
  const [isMemory, setIsMemory] = useState(false);

  useEffect(() => {
    if (visible) {
      initWorkMemory();
    }
  }, [visible]);

  useEffect(() => {
    if (workMemory && Object.keys(workMemory).length > 0) {
      setIsMemory(true);
    } else {
      setIsMemory(false);
    }
  }, [workMemory]);

  // 刷新工作记忆
  const initWorkMemory = () => {
    const { isConnected, chatUid } = getWebSocketState();
    if (isConnected && chatUid) {
      dispatch({
        type: 'chatModel/fetchGetWorkMemory',
        payload: { uid: chatUid, method: 'get_work_memory', seq: '2333' }
      });
    }
  };

  const empty = <div className={styles.empty}>暂无工作记忆</div>;

  const detailContent = () => {
    return (
      <div className={styles.detail}>
        <ReactJson src={workMemory} name={'工作记忆'} collapsed={1} displayDataTypes={false}></ReactJson>
      </div>
    );
  };

  return <div className={styles.wrapper}>{isMemory ? detailContent() : empty}</div>;
};

export default connect(({ chatModel }) => ({ chatModel }))(WorkMemory);
