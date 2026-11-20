const config = require('../config/index');

const TOKEN_KEY = 'labourrun_token';

function buildUrl(path) {
  if (/^https?:\/\//.test(path)) {
    return path;
  }
  const base = config.apiBaseUrl.replace(/\/$/, '');
  return base + (path.charAt(0) === '/' ? path : '/' + path);
}

function makeError(res) {
  const body = (res && res.data) || {};
  const error = new Error(body.message || '请求失败');
  error.code = body.code;
  error.statusCode = res && res.statusCode;
  error.data = body.data;
  return error;
}

function request(options) {
  const opts = options || {};
  const useAuth = opts.auth !== false;
  const canRetry = opts.retry !== false;
  const token = wx.getStorageSync(TOKEN_KEY);

  return new Promise((resolve, reject) => {
    const header = Object.assign(
      { 'Content-Type': 'application/json' },
      useAuth && token ? { Authorization: 'Bearer ' + token } : {},
      opts.header || {}
    );

    wx.request({
      url: buildUrl(opts.url),
      method: opts.method || 'GET',
      data: opts.data || {},
      header,
      timeout: opts.timeout || 15000,
      success(res) {
        const body = (res && res.data) || {};
        if (
          res &&
          res.statusCode >= 200 &&
          res.statusCode < 300 &&
          body.code === 0
        ) {
          resolve(body.data);
          return;
        }

        const error = makeError(res);
        const needLogin =
          (res && res.statusCode === 401) ||
          body.code === 1001 ||
          body.code === 1002 ||
          body.code === 1003;

        if (needLogin && useAuth && canRetry) {
          const auth = require('./auth');
          auth
            .login({ force: true })
            .then(() =>
              request(Object.assign({}, opts, { retry: false }))
            )
            .then(resolve, reject);
          return;
        }
        reject(error);
      },
      fail(err) {
        const error = new Error(
          (err && err.errMsg) || '网络异常，请稍后重试'
        );
        error.errMsg = err && err.errMsg;
        reject(error);
      },
    });
  });
}

module.exports = request;
module.exports.TOKEN_KEY = TOKEN_KEY;
