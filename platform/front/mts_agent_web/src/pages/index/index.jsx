import ChatArea from './components/ChatArea';
import DisplayArea from './components/DisplayArea';
import SearchArea from './components/SearchArea';
import styles from './styles.less';

export default function HomePage() {
  return (
    <div className={styles.wrapper}>
      <div className={`${styles.content} ${styles.main}`}>
        <ChatArea></ChatArea>
      </div>
      <div className={`${styles.content} ${styles.onlyPc}`}>
        <DisplayArea></DisplayArea>
      </div>
      <div className={`${styles.content} ${styles.onlyPc}`}>
        <SearchArea></SearchArea>
      </div>
    </div>
  );
}
