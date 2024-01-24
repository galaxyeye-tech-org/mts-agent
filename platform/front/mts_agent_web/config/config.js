import { resolve } from 'path';
import { defineConfig } from 'umi';

export default defineConfig({
  title: 'MTS调试工具',
  routes: [{ path: '/', wrappers: ['@/layouts/GlobalLayout/index.jsx'], component: './index/index.jsx' }],
  npmClient: 'yarn',
  hash: true,
  history: {
    type: 'hash'
  },
  publicPath: '', // 部署时需要更改为''
  alias: {
    '@components': resolve(__dirname, './src/components'),
    '@utils': resolve(__dirname, './src/utils'),
    '@assets': resolve(__dirname, './src/assets'),
    '@service': resolve(__dirname, './src/service'),
    '@layouts': resolve(__dirname, './src/layouts')
  },
  styles: [`body { margin: 0px; }`],
  plugins: ['@umijs/plugins/dist/dva'],
  dva: {},
  proxy: {
    '/mts_agent': {
      target: 'http://172.16.2.217:12400', // 冠斌本地
      changeOrigin: true
    },
    '/rag_service': {
      target: 'http://172.16.10.191:9090', // 印象查询
      changeOrigin: true
    },
    '/openai-tts': {
      target: 'http://172.16.3.175:9094', // 语音合成
      changeOrigin: true
    }
  },
  define: {
    WS_URL: 'ws://172.16.2.217:12400/mts_agent/dialogue/v1/dialogue', // 聊天ws地址
    ASR_URL: 'ws://172.16.3.172:9092/speech-service-atw/v1/wsasr' // 语音识别ws地址
  }
});
