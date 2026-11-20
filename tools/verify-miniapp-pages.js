/* eslint-disable no-console */
const http = require('http');
const https = require('https');
const assert = require('assert');
const path = require('path');

const storage = Object.create(null);
let pullDownStops = 0;

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
    if (options.fail) options.fail({ errMsg: error.message });
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
  stopPullDownRefresh() {
    pullDownStops += 1;
  },
  showModal(options) {
    if (options.success) options.success({ confirm: true, cancel: false });
  },
  openSetting() {},
  switchTab() {},
  navigateTo() {},
};

const miniRoot = path.resolve(__dirname, '..', 'LabourRunMiniProgram');
const auth = require(path.join(miniRoot, 'utils', 'auth'));

function setByPath(target, key, value) {
  const parts = key.split('.');
  let node = target;
  for (let i = 0; i < parts.length - 1; i += 1) {
    if (!node[parts[i]]) node[parts[i]] = {};
    node = node[parts[i]];
  }
  node[parts[parts.length - 1]] = value;
}

function createPage(relativePath) {
  let captured = null;
  global.Page = function (config) {
    captured = config;
  };
  const modulePath = path.join(miniRoot, relativePath);
  delete require.cache[require.resolve(modulePath)];
  require(modulePath);
  assert(captured, 'Page() not called for ' + relativePath);

  const page = Object.assign({}, captured);
  page.data = JSON.parse(JSON.stringify(captured.data || {}));
  page.setData = function (patch) {
    Object.keys(patch || {}).forEach((key) => {
      setByPath(this.data, key, patch[key]);
    });
  };
  page.getTabBar = function () {
    return null;
  };
  return page;
}

function waitFor(check, label, timeout) {
  const limit = timeout || 15000;
  const started = Date.now();
  return new Promise((resolve, reject) => {
    const timer = setInterval(() => {
      let ok = false;
      try {
        ok = check();
      } catch (error) {
        clearInterval(timer);
        reject(error);
        return;
      }
      if (ok) {
        clearInterval(timer);
        resolve();
        return;
      }
      if (Date.now() - started > limit) {
        clearInterval(timer);
        reject(new Error('timeout: ' + label));
      }
    }, 50);
  });
}

async function main() {
  auth.clearSession();

  // 首页：加载、报名、取消、再次报名
  const indexPage = createPage('pages/index/index.js');
  indexPage.onLoad();
  indexPage.onShow();
  await waitFor(() => indexPage.data.loading === false, 'index load');
  assert(indexPage.data.activity && indexPage.data.activity.noticeText);
  assert(indexPage.data.rules.length > 0);

  const indexPullDownBefore = pullDownStops;
  indexPage.onPullDownRefresh();
  await waitFor(
    () => pullDownStops > indexPullDownBefore && indexPage.data.loading === false,
    'index pull down refresh'
  );
  assert(indexPage.data.error === '');
  console.log('[ok] index pull down refresh');

  const phone = '138' + String(Date.now()).slice(-8);
  indexPage.onNameInput({ detail: { value: '页面验收' } });
  indexPage.onPhoneInput({ detail: { value: phone } });
  indexPage.onCompanyInput({ detail: { value: '页面验收单位' } });
  indexPage.onSubmit();
  await waitFor(() => indexPage.data.submitting === false, 'index submit');
  assert(indexPage.data.registration.status === 'registered');
  const registrationId = indexPage.data.registration.id;
  console.log('[ok] index submit', registrationId);

  indexPage.onCancel();
  await waitFor(
    () =>
      indexPage.data.submitting === false &&
      indexPage.data.registration.status === 'cancelled',
    'index cancel'
  );
  console.log('[ok] index cancel', indexPage.data.statusText);

  indexPage.onSubmit();
  await waitFor(
    () =>
      indexPage.data.submitting === false &&
      indexPage.data.registration.status === 'registered',
    'index re-register'
  );
  assert(indexPage.data.registration.id === registrationId);
  console.log('[ok] index re-register', indexPage.data.registration.id);

  // 步数宝：加载、同步、兑换
  const stepsPage = createPage('pages/steps/steps.js');
  stepsPage.onLoad();
  stepsPage.onShow();
  await waitFor(() => stepsPage.data.loading === false, 'steps load');
  assert(stepsPage.data.challenge);
  assert(stepsPage.data.activityRules.length > 0);

  const stepsPullDownBefore = pullDownStops;
  stepsPage.onPullDownRefresh();
  await waitFor(
    () => pullDownStops > stepsPullDownBefore && stepsPage.data.loading === false,
    'steps pull down refresh'
  );
  assert(stepsPage.data.error === '');
  console.log('[ok] steps pull down refresh');

  stepsPage.onSyncTap();
  await waitFor(
    () => stepsPage.data.syncing === false && stepsPage.data.convertibleSteps === 6638,
    'steps sync'
  );
  assert(stepsPage.data.convertibleCoupons === '0.66');
  console.log('[ok] steps sync', stepsPage.data.convertibleCoupons);

  stepsPage.onExchangeTap();
  await waitFor(
    () => stepsPage.data.exchanging === false && stepsPage.data.couponBalance === '0.66',
    'steps exchange'
  );
  assert(stepsPage.data.convertibleSteps === 0);
  console.log('[ok] steps exchange', stepsPage.data.couponBalance);

  // 兑换券明细
  const couponPage = createPage('pages/coupon/coupon.js');
  couponPage.onLoad();
  couponPage.onShow();
  await waitFor(
    () => couponPage.data.loading === false && couponPage.data.list.length > 0,
    'coupon load'
  );
  assert(couponPage.data.balance === '0.66');
  assert(couponPage.data.list[0].amount === '0.66');
  console.log('[ok] coupon ledger', couponPage.data.list.length);

  // 我：昵称修改
  const userPage = createPage('pages/user/user.js');
  userPage.onLoad();
  userPage.onShow();
  await waitFor(() => userPage.data.loading === false, 'user load');

  const userPullDownBefore = pullDownStops;
  userPage.onPullDownRefresh();
  await waitFor(
    () => pullDownStops > userPullDownBefore && userPage.data.loading === false,
    'user pull down refresh'
  );
  assert(userPage.data.error === '');
  console.log('[ok] user pull down refresh');

  userPage.openNicknameEdit();
  userPage.onNicknameInput({ detail: { value: '页面昵称' } });
  userPage.saveNickname();
  await waitFor(
    () => userPage.data.savingNickname === false && userPage.data.nickname === '页面昵称',
    'user nickname'
  );
  console.log('[ok] user nickname', userPage.data.nickname);

  // 挑战详情
  const challengePage = createPage('pages/challenge/challenge.js');
  challengePage.onLoad();
  await waitFor(() => challengePage.data.loading === false, 'challenge load');
  assert(challengePage.data.challenge.targetSteps === 12000);
  assert(challengePage.data.rules.length > 0);
  console.log('[ok] challenge detail', challengePage.data.challenge.title);

  console.log('\nMini-program page-level verification passed.');
}

main().catch((error) => {
  console.error('\nPage verification failed:', error.message);
  if (error.stack) console.error(error.stack);
  process.exit(1);
});
