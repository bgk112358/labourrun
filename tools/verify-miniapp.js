/* eslint-disable no-console */
const http = require('http');
const https = require('https');
const assert = require('assert');
const path = require('path');

const storage = Object.create(null);

function requestByNode(options) {
  const url = new URL(options.url);
  const method = options.method || 'GET';
  const headers = Object.assign({}, options.header || {});
  let body = null;

  if (method === 'GET' && options.data) {
    Object.keys(options.data).forEach((key) => {
      const value = options.data[key];
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, value);
      }
    });
  } else if (options.data !== undefined) {
    body = JSON.stringify(options.data);
    headers['Content-Length'] = Buffer.byteLength(body);
  }

  const lib = url.protocol === 'https:' ? https : http;
  const req = lib.request(
    {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname + url.search,
      method,
      headers,
    },
    (res) => {
      let raw = '';
      res.on('data', (chunk) => {
        raw += chunk;
      });
      res.on('end', () => {
        let data = raw;
        try {
          data = raw ? JSON.parse(raw) : null;
        } catch (error) {
          // keep raw text
        }
        if (options.success) {
          options.success({
            statusCode: res.statusCode,
            data,
            header: res.headers,
          });
        }
      });
    }
  );

  req.on('error', (error) => {
    if (options.fail) {
      options.fail({ errMsg: error.message });
    }
  });

  if (body) req.write(body);
  req.end();
}

global.wx = {
  getStorageSync(key) {
    return storage[key] === undefined ? '' : storage[key];
  },
  setStorageSync(key, value) {
    storage[key] = value;
  },
  removeStorageSync(key) {
    delete storage[key];
  },
  clearStorageSync() {
    Object.keys(storage).forEach((key) => delete storage[key]);
  },
  request: requestByNode,
  login(options) {
    if (options.success) options.success({ code: 'node-mock-code' });
  },
  getWeRunData(options) {
    if (options.success) {
      options.success({ encryptedData: 'mock', iv: 'mock' });
    }
  },
  showToast(options) {
    console.log('[toast]', options.title);
  },
  showLoading() {},
  hideLoading() {},
  showModal(options) {
    if (options.success) options.success({ confirm: true, cancel: false });
  },
  openSetting() {},
  switchTab(options) {
    console.log('[switchTab]', options.url);
  },
  navigateTo(options) {
    console.log('[navigateTo]', options.url);
  },
};

const miniRoot = path.resolve(__dirname, '..', 'LabourRunMiniProgram');
const auth = require(path.join(miniRoot, 'utils', 'auth'));
const api = require(path.join(miniRoot, 'utils', 'api'));

function log(step, value) {
  console.log('[ok]', step, value === undefined ? '' : value);
}

async function main() {
  auth.clearSession();

  const user = await auth.ensureLogin();
  assert(user && user.id, 'login should return user');
  log('login', user.id);

  const home = await api.getHome();
  assert(home.activity && home.activity.noticeText, 'home activity missing');
  assert(Array.isArray(home.activity.rules) && home.activity.rules.length > 0);
  log('home', home.activity.noticeText);

  const phone = '139' + String(Date.now()).slice(-8);
  const payload = {
    realName: '验收用户',
    phone,
    company: '验收单位',
  };
  const registration = await api.createRegistration(payload);
  assert(registration.status === 'registered', 'registration failed');
  log('registration', registration.id);

  const updated = await api.updateRegistration(registration.id, {
    company: '验收单位二部',
  });
  assert(updated.company === '验收单位二部', 'registration update failed');
  log('registration update', updated.company);

  const cancelled = await api.cancelRegistration(registration.id);
  assert(cancelled.status === 'cancelled', 'cancel failed');
  log('registration cancel', cancelled.status);

  const restored = await api.createRegistration(payload);
  assert(restored.status === 'registered', 're-register failed');
  assert(restored.id === registration.id, 're-register should reuse record');
  log('registration re-register', restored.id);

  const steps = await api.getSteps();
  assert(steps.couponAccount && steps.couponAccount.balance === '0.00');
  assert(steps.challenge && steps.challenge.targetSteps === 12000);
  log('steps overview', steps.challenge.targetSteps);

  const sync = await api.syncSteps({ mockSteps: 6638 });
  assert(sync.stepSummary.todaySteps === 6638);
  assert(sync.stepSummary.convertibleSteps === 6638);
  assert(sync.stepSummary.convertibleCoupons === '0.66');
  log('step sync', sync.stepSummary.convertibleCoupons);

  const requestId = 'verify-' + Date.now();
  const exchange = await api.exchangeSteps({ requestId });
  assert(exchange.exchange.steps === 6638);
  assert(exchange.exchange.couponAmount === '0.66');
  assert(exchange.couponAccount.balance === '0.66');
  log('exchange', exchange.exchange.couponAmount);

  const repeated = await api.exchangeSteps({ requestId });
  assert(repeated.exchange.id === exchange.exchange.id);
  assert(repeated.couponAccount.balance === '0.66');
  log('exchange idempotency', repeated.exchange.id);

  const ledger = await api.getLedger({ page: 1, pageSize: 20 });
  assert(ledger.total === 1);
  assert(ledger.list[0].amount === '0.66');
  log('ledger', ledger.list[0].balanceAfter);

  const me = await api.getMe();
  assert(me.id === user.id);
  const updatedMe = await api.updateMe({ nickname: '验收昵称' });
  assert(updatedMe.nickname === '验收昵称');
  log('nickname', updatedMe.nickname);

  const challenge = await api.getChallenge();
  assert(challenge.targetSteps === 12000);
  assert(Array.isArray(challenge.rules) && challenge.rules.length > 0);
  log('challenge', challenge.title);

  // 401 自动重新登录 + 重试
  wx.setStorageSync('labourrun_token', 'invalid-token');
  const refreshedMe = await api.getMe();
  assert(refreshedMe.id === user.id);
  log('401 re-login retry', refreshedMe.id);

  console.log('\nMini-program API integration verification passed.');
}

main().catch((error) => {
  console.error('\nVerification failed:', error.message);
  if (error.stack) console.error(error.stack);
  process.exit(1);
});
