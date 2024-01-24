import Recorder from 'recorder-core';
import 'recorder-core/src/engine/pcm';
import 'recorder-core/src/extensions/waveview';
import { isFunction } from './isType';

let rec = null; // Recorder实例
let wave = null; // WaveView波形图实例

// 初始化
function initRecorder(params) {
  const { type = 'pcm', bitRate = 16, sampleRate = 16000, process = () => {} } = params ?? {};

  const onProcess = (buffers, powerLevel, bufferDuration, bufferSampleRate) => {
    if (wave) {
      wave.input(buffers[buffers.length - 1], powerLevel, bufferSampleRate);
    }
    if (isFunction(process)) process(Recorder.SampleData(buffers.slice(-1), bufferSampleRate, sampleRate).data);
  };
  rec = new Recorder({ type, bitRate, sampleRate, onProcess });
}

// 初始化波形图插件
function initWaveView(option) {
  wave = Recorder.WaveView(option);
}

// 获取录音权限(调用open)
function getPermission(params) {
  if (!rec) {
    console.log('获取录音权限失败，未初始化');
    return;
  }
  const { success = () => {}, fail = () => {} } = params ?? {};

  const successCallback = (e) => {
    console.log('[Recorder H5] open success');
    if (isFunction(success)) success(e);
  };

  const failCallback = (e) => {
    console.log('[Recorder H5] open fail');
    if (isFunction(fail)) fail(e);
  };

  rec.open(successCallback, failCallback);
}

// 关闭录音器
function closeRecorder(params) {
  if (!rec) return;
  const { success = () => {} } = params ?? {};
  const successCallback = (e) => {
    console.log('[Recorder H5] close success');
    if (isFunction(success)) success(e);
  };
  rec.close(successCallback);
}

// 开始录音
function startRecorder() {
  rec.start();
}

// 结束录音
function stopRecorder(params) {
  if (!rec) {
    return;
  }
  const { success = () => {}, fail = () => {} } = params ?? {};
  const successCallback = (e) => {
    if (isFunction(success)) success(e);
  };
  const failCallback = (e) => {
    if (isFunction(fail)) fail(e);
  };
  rec.stop(successCallback, failCallback, false); //第三个参数表示禁止自动close
}

export { closeRecorder, initWaveView, getPermission, initRecorder, startRecorder, stopRecorder };
