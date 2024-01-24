export const isValidJSON = (value) => {
  if (typeof value == 'string') {
    try {
      const obj = JSON.parse(value);
      if (typeof obj == 'object' && obj) {
        return true;
      } else {
        return false;
      }
    } catch (e) {
      return false;
    }
  }
  return false;
};

export const isFunction = (f) => {
  return Object.prototype.toString.call(f) === '[object Function]';
};

export const isArray = (f) => {
  return Object.prototype.toString.call(f) === '[object Array]';
};

export const isString = (f) => {
  return Object.prototype.toString.call(f) === '[object String]';
};

export const isArrayBuffer = (buffer) => {
  return Object.prototype.toString.call(buffer) === '[object ArrayBuffer]';
};
