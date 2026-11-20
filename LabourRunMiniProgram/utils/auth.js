const config = require('../config/index');
const request = require('./request');

const TOKEN_KEY = request.TOKEN_KEY;
const USER_KEY = 'labourrun_user';
const EXPIRES_KEY = 'labourrun_token_expires_at';
let loginPromise = null;

function getToken() {
  return wx.getStorageSync(TOKEN_KEY) || '';
}

function getUser() {
  return wx.getStorageSync(USER_KEY) || null;
}

function getExpiresAt() {
  return Number(wx.getStorageSync(EXPIRES_KEY) || 0);
}

function setSession(data) {
  wx.setStorageSync(TOKEN_KEY, data.token);
  wx.setStorageSync(USER_KEY, data.user || null);
  wx.setStorageSync(
    EXPIRES_KEY,
    Date.now() + Number(data.expiresIn || 0) * 1000
  );
}

function clearSession() {
  wx.removeStorageSync(TOKEN_KEY);
  wx.removeStorageSync(USER_KEY);
  wx.removeStorageSync(EXPIRES_KEY);
}

function isLoggedIn() {
  const token = getToken();
  if (!token) return false;
  const expiresAt = getExpiresAt();
  if (!expiresAt) return true;
  return expiresAt > Date.now() + 30000;
}

function getLoginCode() {
  if (config.useMockLogin) {
    return Promise.resolve(config.mockLoginCode);
  }
  return new Promise((resolve, reject) => {
    wx.login({
      success(res) {
        if (res && res.code) {
          resolve(res.code);
        } else {
          reject(new Error('微信登录失败：未获取到 code'));
        }
      },
      fail(err) {
        reject(
          new Error((err && err.errMsg) || '微信登录失败')
        );
      },
    });
  });
}

function login(options) {
  const force = options && options.force;
  if (!force && isLoggedIn()) {
    return Promise.resolve(getUser());
  }
  if (loginPromise) {
    return loginPromise;
  }

  loginPromise = getLoginCode()
    .then((code) =>
      request({
        url: '/auth/login',
        method: 'POST',
        data: { code },
        auth: false,
        retry: false,
      })
    )
    .then(
      (data) => {
        setSession(data);
        loginPromise = null;
        return data.user;
      },
      (error) => {
        loginPromise = null;
        throw error;
      }
    );

  return loginPromise;
}

function ensureLogin() {
  if (isLoggedIn()) {
    return Promise.resolve(getUser());
  }
  return login();
}

function updateUser(user) {
  wx.setStorageSync(USER_KEY, user);
  return user;
}

module.exports = {
  login,
  ensureLogin,
  getToken,
  getUser,
  updateUser,
  clearSession,
  isLoggedIn,
};
