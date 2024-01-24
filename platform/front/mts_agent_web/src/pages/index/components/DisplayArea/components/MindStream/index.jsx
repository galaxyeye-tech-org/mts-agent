import dayjs from 'dayjs';
import { useEffect } from 'react';
import { connect } from 'umi';
import styles from './styles.less';

const simplifyKey = ['content', 'source', 'target', 'response', 'attention', 'msg']; // 简化展示key
const colorKey = ['response', 'msg', 'content']; // 蓝色高亮key

const MindStream = (props) => {
  const { chatModel, isSimplify = false } = props;
  const { mindStream } = chatModel;

  useEffect(() => {
    // todo
  }, [mindStream]);

  const empty = <div className={styles.empty}>暂无思绪流</div>;

  const mindItem = (item, index) => {
    // 提取时间参数并解析
    const processItem = (data) => {
      let time = null;
      if (data.time) {
        time = data.time;
        delete data.time;
      } else {
        time = dayjs().format('HH:mm:ss');
      }
      let resList = Object.entries(data);
      if (isSimplify) {
        resList = resList.filter(([key, value]) => {
          return simplifyKey.includes(key);
        });
      }
      return { time, resList };
    };

    const { time, resList } = processItem(JSON.parse(JSON.stringify(item)));
    return (
      <div className={styles.mind} key={index}>
        <div className={`${styles.item} ${styles.time}`}>
          <div className={styles.item_key}>{'时间'}</div>
          <div className={styles.item_value}>{time ?? '--'}</div>
        </div>
        {resList.map((entries, index) => {
          return (
            <div className={styles.item} key={index}>
              <div className={styles.item_key}>{`${entries[0]}:`}</div>
              <div className={`${styles.item_value} ${colorKey.includes(entries[0]) ? styles.enhance : ''}`}>
                {JSON.stringify(entries[1])}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className={styles.wrapper}>
      {mindStream.length > 0
        ? mindStream.map((item, index) => {
            return mindItem(item, index);
          })
        : empty}
    </div>
  );
};

export default connect(({ chatModel }) => ({ chatModel }))(MindStream);
