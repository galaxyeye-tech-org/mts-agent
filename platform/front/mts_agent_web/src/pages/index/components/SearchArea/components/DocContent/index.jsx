import { fetchDeleteDoc, fetchGetDoc, fetchUploadDoc } from '@/service/chatApi';
import { getWebSocketState } from '@/utils/websocket';
import { CloseOutlined, SyncOutlined, UploadOutlined } from '@ant-design/icons';
import { Button, Modal, Tooltip, Upload, message } from 'antd';
import dayjs from 'dayjs';
import { useEffect, useMemo, useRef, useState } from 'react';
import { connect } from 'umi';
import styles from './styles.less';

let freshTimer = null; // 轮询文件列表定时器

const DocContent = (props) => {
  const { visible, chatModel } = props;
  const { isConnect } = chatModel;
  const fileState = useRef();
  const [messageApi, contextHolder] = message.useMessage();
  const [fileList, setFileList] = useState([]); // 已上传文件列表
  const [uploadFiles, setUploadFiles] = useState([]); // 待上传文件列表
  const [count, setCount] = useState(0); // 文件数量
  const [isSpin, setIsSpin] = useState(false); // 按钮旋转效果
  const [errInfo, setErrInfo] = useState([]); // 错误内容
  const [modalVisible, setModalVisible] = useState(false); // 错误弹窗

  const updateFiles = (function () {
    let fileList;
    return function (list, setState) {
      if (!fileList) {
        fileList = list;
        setState && setState(list);
      }
      return {
        fileList,
        reset() {
          fileList = false;
        }
      };
    };
  })();

  useEffect(() => {
    if (visible) {
      getDocList();
      freshTimer = setInterval(() => {
        getDocList();
      }, 10 * 1000);
    }
    return () => {
      // 清空轮询定时器
      if (freshTimer) {
        clearInterval(freshTimer);
        freshTimer = null;
      }
    };
  }, [visible]);

  useEffect(() => {
    if (uploadFiles.length > 0) {
      const { chatUid } = getWebSocketState();
      const formData = new FormData();
      uploadFiles.forEach((file) => {
        formData.append('upload_files', file);
      });
      formData.append('confidence', 50);
      formData.append('uid', chatUid);
      fetchUploadDoc(formData).then((res) => {
        if (res && res.success) {
          const { data } = res;
          const dataValues = Object.values(data);
          const errData = dataValues.filter((item) => {
            return item.err !== '';
          });
          console.log('错误信息', errData);
          if (errData.length > 0) {
            setErrInfo(errData);
            setModalVisible(true);
          } else {
            messageApi.success('上传成功');
          }
          getDocList();
        } else {
          messageApi.error('上传失败');
        }
      });
      fileState.current.reset();
      setUploadFiles([]);
    }
  }, [uploadFiles]);

  // 刷新文件列表
  const getDocList = (callback) => {
    const { chatUid, isConnected } = getWebSocketState();
    if (chatUid && isConnected)
      fetchGetDoc({ cursor: 0, limit: 100, uid: chatUid }).then((res) => {
        if (res && res.success) {
          const { data } = res;
          const { total, infos } = data;
          setFileList(infos);
          setCount(total);
          if (callback) {
            callback(res);
          }
        }
      });
  };

  // 刷新提示
  const freshTip = (res) => {
    if (res && res.success) {
      messageApi.success('刷新成功');
    } else {
      messageApi.error('刷新失败');
    }
  };

  // 删除文件
  const handleDelete = (id) => {
    fetchDeleteDoc({ ids: [id] }).then((res) => {
      if (res && res.success) {
        messageApi.success('删除成功');
        getDocList();
      } else {
        messageApi.error('删除失败');
      }
    });
  };

  // 文件列表项
  const fileItem = (item, index) => {
    const statusMap = {
      0: '待处理',
      1: '处理中',
      2: '成功',
      3: '失败'
    };

    const colorMap = {
      0: '#000000',
      1: '#2c6fff',
      2: '#1d8b1d',
      3: '#ff2b2b'
    };

    return (
      <div className={styles.file} key={item.id ?? index}>
        <div className={styles.file_name}>
          <Tooltip title={item.name}>{item.name}</Tooltip>
        </div>
        <div className={styles.file_status} style={{ color: colorMap[item.status] }}>
          {statusMap[item.status]}
        </div>
        <div className={styles.file_time}>{dayjs.unix(item.gmt_create).format('YYYY/M/D')}</div>
        <div className={styles.file_btn} onClick={handleDelete.bind(this, item.id)}>
          <CloseOutlined />
        </div>
      </div>
    );
  };

  // 错误信息内容
  const errContent = useMemo(() => {
    return (
      <ul>
        {errInfo.map((item, index) => {
          return <li key={index}>{item.err}</li>;
        })}
      </ul>
    );
  }, [errInfo]);

  // 上传参数
  const uploadOptions = {
    accept: '.doc,.docx',
    showUploadList: false,
    multiple: true,
    beforeUpload: (_, fileList) => {
      // 加入待上传列表
      fileState.current = updateFiles(fileList, setUploadFiles);
      return false;
    }
  };

  // 错误信息提示弹窗
  const modalOption = {
    title: '上传异常',
    open: modalVisible,
    closeIcon: false,
    okText: '确定',
    cancelButtonProps: { style: { display: 'none' } },
    onOk: () => {
      setErrInfo([]);
      setModalVisible(false);
    }
  };

  return (
    <div className={styles.wrapper}>
      <div className={styles.upload}>
        <Upload {...uploadOptions}>
          <Tooltip title={'目前仅支持中文文档，可按住ctrl多选'}>
            <Button disabled={!isConnect} icon={<UploadOutlined />}>
              点击上传文件
            </Button>
          </Tooltip>
        </Upload>
        <div className={styles.count}>
          <div className={styles.count_text}>{`总数:${count}`}</div>
          <div
            className={styles.count_icon}
            onMouseEnter={() => {
              setIsSpin(true);
            }}
            onMouseLeave={() => {
              setIsSpin(false);
            }}
            onClick={getDocList.bind(this, freshTip)}
            title={'刷新'}
          >
            <SyncOutlined spin={isSpin} />
          </div>
        </div>
      </div>
      <div className={styles.content}>
        <div className={styles.list}>
          {fileList.map((item) => {
            return fileItem(item);
          })}
        </div>
      </div>
      <Modal {...modalOption}>{errContent}</Modal>
      {contextHolder}
    </div>
  );
};

export default connect(({ chatModel }) => ({ chatModel }))(DocContent);
