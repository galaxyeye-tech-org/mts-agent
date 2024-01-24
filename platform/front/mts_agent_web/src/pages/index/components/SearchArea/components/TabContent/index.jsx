import { Button, Input, Select } from 'antd';
import dayjs from 'dayjs';
import { useEffect, useMemo, useState } from 'react';
import ReactJson from 'react-json-view';
import styles from './styles.less';

const memoryOptions = [
  { value: '猜想', label: '猜想' },
  { value: '用户陈述', label: '用户陈述' },
  { value: '结论', label: '结论' }
];

const TabContent = (props) => {
  const { visible, action, name, search = false, isMemory = false, tips } = props;
  const [content, setContent] = useState(null);
  const [searchInput, setSearchInput] = useState(isMemory ? memoryOptions[0].value : ''); //检索输入框内容

  useEffect(() => {
    // 非搜索类自动更新数据
    if (visible && action && !search) {
      action().then((res) => {
        if (res && Object.keys(res).length > 0) {
          setContent(res);
        } else {
          setContent(null);
        }
      });
    }
  }, [visible]);

  const empty = <div className={styles.empty}>{`暂无${name}`}</div>;

  // 搜索模块
  const searchContent = () => {
    const handleSearchChange = (e) => {
      const inputText = e.target.value;
      setSearchInput(inputText);
    };

    const handleSelectChange = (data) => {
      setSearchInput(data);
    };

    // 处理查询
    const handleSearch = () => {
      action(searchInput).then((res) => {
        if (res && Object.keys(res).length > 0) {
          setContent(res);
        } else {
          setContent(null);
        }
      });
    };

    return (
      <div className={styles.input}>
        {isMemory ? (
          <Select
            className={styles.input_text}
            options={memoryOptions}
            value={searchInput}
            onChange={handleSelectChange}
            placeholder={tips ?? '请选择检索条件'}
          ></Select>
        ) : (
          <Input
            className={styles.input_text}
            value={searchInput}
            onChange={handleSearchChange}
            placeholder={tips ?? '请输入检索条件'}
          ></Input>
        )}

        <Button className={styles.input_btn} type="primary" onClick={handleSearch}>
          查询
        </Button>
      </div>
    );
  };

  // json视图
  const JSONView = useMemo(() => {
    return (
      <div className={styles.detail__json}>
        <ReactJson src={content} name={name} collapsed={1} displayDataTypes={false}></ReactJson>
      </div>
    );
  }, [content, name]);

  // 记忆视图
  const memoryView = useMemo(() => {
    if (!content) {
      return null;
    }
    const { total = 0, infos = [] } = content;
    return (
      <div className={styles.memory}>
        <div className={styles.memory_total}>总数：{total}</div>
        <div>
          {infos.map((info) => {
            return (
              <div className={styles.memory__item}>
                <div>{dayjs(info.timestamp).format('YYYY-MM-DD HH:mm:ss')}</div>
                <div className={styles.memory__item_content}>{info.content}</div>
                <div>
                  <span className={styles.memory__item_red}>attention: </span>
                  <span className={styles.memory__item_blue}>{info.attention}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }, [content]);

  return (
    <div className={styles.wrapper}>
      {search && searchContent()}
      {content ? (isMemory ? memoryView : JSONView) : empty}
    </div>
  );
};

export default TabContent;
