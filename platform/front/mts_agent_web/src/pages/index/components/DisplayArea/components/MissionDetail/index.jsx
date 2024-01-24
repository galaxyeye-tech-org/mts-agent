import { getWebSocketState } from '@/utils/websocket';
import { Tooltip, message } from 'antd';
import { useEffect, useState } from 'react';
import ReactJson from 'react-json-view';
import { connect } from 'umi';
import styles from './styles.less';

const MissionDetail = (props) => {
  const { chatModel, visible, dispatch } = props;
  const { missionDetail, missionId } = chatModel;
  const [isData, setIsData] = useState(false);

  const [messageApi, contextHolder] = message.useMessage();

  useEffect(() => {
    if (visible) {
      const { chatUid, taskId } = getWebSocketState();
      if (chatUid && taskId) {
        dispatch({
          type: 'chatModel/fetchGetMissionDetail',
          payload: {
            uid: chatUid,
            method: 'get_task_context',
            seq: '2333',
            data: { task_id: taskId }
          }
        });
      }
    }
  }, [visible]);

  useEffect(() => {
    if (missionDetail && Object.keys(missionDetail).length > 0) {
      setIsData(true);
    } else {
      setIsData(false);
    }
  }, [missionDetail]);

  const handlePaste = () => {
    try {
      if (navigator.clipboard) {
        // 安全环境下采用clipboard API进行拷贝
        navigator.clipboard.writeText(missionId).then(() => {
          messageApi.success('复制成功');
        });
      } else {
        // 非安全环境下拷贝方案
        const input = document.createElement('textarea');
        document.body.appendChild(input);
        input.value = missionId;
        input.select();
        if (document.execCommand('copy')) {
          document.execCommand('copy');
          messageApi.success('复制成功');
        }
        document.body.removeChild(input);
      }
    } catch (err) {
      messageApi.error('当前浏览器不支持复制，请手动复制');
    }
  };

  const empty = <div className={styles.empty}>暂无任务信息</div>;

  const jsonView = () => {
    return (
      <div className={styles.detail}>
        {missionId ? (
          <div className={styles.detail__id}>
            <div className={styles.detail__id_title}>task_id:</div>
            <Tooltip title={'点击复制'}>
              <div className={styles.detail__id_num} onClick={handlePaste}>
                {missionId}
              </div>
            </Tooltip>
          </div>
        ) : null}
        <div className={styles.detail__json}>
          <ReactJson src={missionDetail} name={'当前任务信息'} collapsed={1} displayDataTypes={false}></ReactJson>
        </div>
        {contextHolder}
      </div>
    );
  };

  return <div className={styles.wrapper}>{isData ? jsonView() : empty}</div>;
};

export default connect(({ chatModel }) => ({ chatModel }))(MissionDetail);
