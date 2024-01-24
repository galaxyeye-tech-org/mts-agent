import { Switch, Tabs } from 'antd';
import { useMemo, useState } from 'react';
import MindStream from './components/MindStream';
import MissionDetail from './components/MissionDetail';
import WorkMemory from './components/WorkMemory';

import styles from './styles.less';

const TagKeys = ['mind', 'mission', 'memory'];

export default function DisplayArea() {
  const [activeKey, setActiveKey] = useState(TagKeys[0]);
  const [isSimplify, setIsSimplify] = useState(false); // 是否启用简化模式
  const items = [
    {
      key: TagKeys[0],
      label: '思绪流',
      children: (
        <div className={styles.tab}>
          <MindStream isSimplify={isSimplify}></MindStream>
        </div>
      )
    },
    {
      key: TagKeys[1],
      label: '当前任务信息',
      children: (
        <div className={styles.tab}>
          <MissionDetail visible={activeKey === TagKeys[1]}></MissionDetail>
        </div>
      )
    },
    {
      key: TagKeys[2],
      label: '工作记忆',
      children: (
        <div className={styles.tab}>
          <WorkMemory visible={activeKey === TagKeys[2]}></WorkMemory>
        </div>
      )
    }
  ];

  const handleTabChange = (activeKey) => {
    setActiveKey(activeKey);
  };

  // 右侧占位
  const stone = <div className={styles.stone}></div>;

  // 精简切换按钮
  const switchContent = useMemo(() => {
    const handleChange = (data) => {
      setIsSimplify(data);
    };
    if (activeKey === TagKeys[0]) {
      return (
        <Switch
          className={styles.switch}
          value={isSimplify}
          checkedChildren="精简"
          unCheckedChildren="普通"
          onChange={handleChange}
        />
      );
    } else {
      return stone;
    }
  }, [activeKey, isSimplify]);

  return (
    <div className={styles.display}>
      <Tabs
        defaultActiveKey={TagKeys[0]}
        onChange={handleTabChange}
        tabBarExtraContent={{ left: switchContent, right: stone }}
        centered
        items={items}
      />
    </div>
  );
}
