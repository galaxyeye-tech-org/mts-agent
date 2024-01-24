import { fetchTTS } from '@/service/chatApi.js';
import { isArrayBuffer } from './isType';
import { Queue } from './structure';

let player = null; // 播放context
let isPlay = false; // 播放状态
let fetchIndex = 0; // 请求顺序索引
let playIndex = -1; // 当前播放索引
const audioQueue = new Queue(); // 待播放队列

// 初始化方法
function initPlayer() {
  player = new AudioContext({ latencyHint: 'balanced' });
}

// TTS语音合成方法
function openTTS(text) {
  const currentIndex = fetchIndex;
  fetchIndex++;
  fetchTTS({ text })
    .then(async (res) => {
      if (res && res.status === 200) {
        try {
          const arraybuffer = await res.arrayBuffer();
          playAudio({ arraybuffer, index: currentIndex });
        } catch (err) {
          console.warn('tts解析错误', err);
        }
      } else {
        playAudio({ arraybuffer: null, index: currentIndex });
      }
    })
    .catch((_) => {
      playAudio({ arraybuffer: null, index: currentIndex });
    });
}

// 播放方法
async function playAudio({ arraybuffer, index }) {
  // 播放完成，查找下一项
  const seekNext = () => {
    if (!audioQueue.isEmpty()) {
      const newItem = audioQueue.dequeue();
      playAudio(newItem);
    }
  };

  if (!player || !isArrayBuffer(arraybuffer)) {
    playIndex = index;
    seekNext();
    return;
  }

  if (isPlay) {
    audioQueue.enqueue({ arraybuffer, index }); // 当前正在播放，入队
  } else if (index !== playIndex + 1) {
    audioQueue.enqueue({ arraybuffer, index }); // 不是连续的，入队
    audioQueue.sort('index');
    const newItem = audioQueue.dequeue();
    if (newItem.index === playIndex + 1) {
      playAudio(newItem);
    } else {
      audioQueue.enqueue(newItem);
    }
  } else {
    const audioBuffer = await player.decodeAudioData(arraybuffer);
    const sourceNode = player.createBufferSource();
    sourceNode.buffer = audioBuffer;
    sourceNode.connect(player.destination);
    sourceNode.onended = () => {
      isPlay = false;
      seekNext();
    };
    sourceNode.start(0);
    isPlay = true;
    playIndex = index;
  }
}

// 结束方法
function stopAudio() {}

// 测试
function testAudio() {
  openTTS('这是第一句');
  openTTS('你好，这是第二句,别走开哦');
  openTTS('再见');
}

export { initPlayer, openTTS, playAudio, stopAudio, testAudio };
