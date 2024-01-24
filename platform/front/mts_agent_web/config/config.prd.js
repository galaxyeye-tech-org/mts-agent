import { defineConfig } from 'umi';
import baseConfig from './config';

const { ...otherConfig } = baseConfig;

export default defineConfig({
  ...otherConfig,
  proxy: {
    ...otherConfig.proxy
  },
  define: {
    ...otherConfig.define,
    WS_URL: 'wss://dev.nekoplan.com/mts_agent/dialogue/v1/dialogue', // 聊天ws地址
    ASR_URL: 'wss://dev.nekoplan.com/speech-service-atw/v1/wsasr' // 语音识别ws地址
  }
});
