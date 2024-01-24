// 消息队列
export class Queue {
  items = [];

  enqueue = function (element) {
    this.items.push(element);
  };

  dequeue = function () {
    return this.items.shift();
  };

  // 拼接数组
  splice = function (list) {
    items = [...this.items, ...list];
  };

  // 排序（key对应值需要为number类型）
  sort = function (key) {
    this.items.sort((a, b) => {
      return a[key] - b[key];
    });
  };

  // 检查队列内容（用于字幕）
  checkFront = function (start, end) {
    return this.items.slice(start, end);
  };

  front = function () {
    return this.items[0];
  };

  isEmpty = function () {
    return this.items.length === 0;
  };

  clear = function () {
    this.items = [];
  };

  size = function () {
    return this.items.length;
  };

  print = function () {
    console.log(this.items.toString());
  };
}
