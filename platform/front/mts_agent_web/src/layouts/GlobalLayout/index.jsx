import { Outlet } from 'umi';
import styles from './styles.less';

export default function GlobalLayout() {
  window.onerror = (err) => {
    console.log('捕获到全局异常:', err);
  };

  return (
    <div className={styles.wrapper}>
      <Outlet></Outlet>
    </div>
  );
}
