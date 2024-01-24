import { isValidJSON } from './isType';

// 请求controller队列
const requestList = new Map();

// 拦截器
const interceptor = (response) => {
  const { status } = response;
  if (status >= 200 && status < 300) {
    if (response.headers.get('Content-Type').startsWith('application/json')) {
      return response.json().then((data) => {
        return { data, response };
      });
    } else {
      return response.blob().then((data) => {
        return { data, response };
      });
    }
  } else {
    return Promise.reject({ response, msg: response.statusText });
  }
};

/**
 * 发起http请求
 * @param {String} url            请求地址
 * @param {Object} options        基础配置项
 * @param {Object} otherOptions   特殊配置项(比如是否需要鉴权等)
 * @return {Promise}
 */
export default async function request(url, options = {}, otherOptions = {}) {
  /**
   * isResponse 返回结果是否放在请求头的response中
   */
  const { isResponse = false } = otherOptions;
  let defaultOptions = {
    method: options.method || 'GET',
    headers: {}
  };
  if (options.method === 'POST' && options.body) {
    if (options.body && options.body instanceof FormData) {
      defaultOptions.body = options.body;
    } else {
      defaultOptions.headers['Content-Type'] = 'application/json';
      defaultOptions.body = JSON.stringify(options.body);
    }
  }

  defaultOptions.headers = {
    ...defaultOptions.headers,
    ...(options.headers || {})
  };

  // 取消重复请求
  const mapKey = url + ' ' + JSON.stringify(defaultOptions);
  const controller = new AbortController();
  if (requestList.get(mapKey)) {
    requestList.get(mapKey).abort();
  }
  requestList.set(mapKey, controller);

  defaultOptions.signal = controller.signal;
  return window
    .fetch(url, defaultOptions)
    .then((response) => interceptor(response))
    .then(({ data, response }) => {
      requestList.delete(mapKey); // 请求成功，从请求队列中删除该请求controller
      if (data && Object.prototype.toString.call(data) === '[object Object]') {
        if (data.code === 0) {
          return { success: true, ...data };
        } else {
          return { success: false, ...data };
        }
      } else if (isResponse) {
        // 返回结果在response中的情况
        let res = response.headers.get('Response');
        if (res && isValidJSON(res)) {
          res = JSON.parse(res);
          if (res.code === 0) {
            return { success: true, ...res, data };
          } else {
            return { success: false, ...res };
          }
        } else {
          return { success: false, data };
        }
      } else {
        // 部分接口报错返回json，否则返回流，也当做正常处理
        return { success: true, data };
      }
    })
    .catch((err) => {
      requestList.delete(mapKey);
      return { success: false, ...err };
    });
}

// 清空所有未完成请求
export function clearAllRequest() {
  requestList.forEach((request) => {
    request.abort();
  });
  requestList.clear();
}
