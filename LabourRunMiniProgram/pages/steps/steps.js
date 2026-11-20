const config = require('../../config/index');
const auth = require('../../utils/auth');
const api = require('../../utils/api');
const ui = require('../../utils/ui');

Page({
  data: {
    ticks: Array.from({ length: 44 }, (_, i) => i * (360 / 44)),
    adds: [1, 2, 3, 4],
    couponBalance: '0.00',
    todaySteps: 0,
    convertibleSteps: 0,
    convertibleCoupons: '0.00',
    dailyCapReached: false,
    canExchange: false,
    challenge: null,
    activityRules: [],
    loading: true,
    syncing: false,
    exchanging: false,
    reminderOn: false,
    error: '',
  },

  onLoad() {
    this.requesting = false;
    this.pending = null;
    this.exchangeRequestId = '';
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 1 });
    }
    this.loadData();
  },

  onPullDownRefresh() {
    this.loadData({ silent: true }).then(
      () => wx.stopPullDownRefresh(),
      () => wx.stopPullDownRefresh()
    );
  },

  loadData(options) {
    const silent = options && options.silent;
    if (this.requesting) {
      return this.pending || Promise.resolve();
    }
    this.requesting = true;
    this.setData(silent ? { error: '' } : { loading: true, error: '' });

    this.pending = auth
      .ensureLogin()
      .then(function () {
        return Promise.all([api.getSteps(), api.getHome()]);
      })
      .then((result) => {
        const steps = result[0] || {};
        const home = result[1] || {};
        const activity = home.activity || {};
        this.requesting = false;
        this.pending = null;
        this.setData({
          activityRules: activity.rules || [],
          loading: false,
          error: '',
        });
        this.applyStepsData(steps);
      })
      .catch((error) => {
        this.requesting = false;
        this.pending = null;
        this.setData({
          loading: false,
          error: (error && error.message) || '加载失败',
        });
        ui.showError(error);
      });
    return this.pending;
  },

  applyStepsData(data) {
    const account = (data && data.couponAccount) || {};
    const summary = (data && data.stepSummary) || {};
    const exchangedSteps = Number(summary.exchangedSteps || 0);
    const dailyCapSteps = Number(summary.dailyCapSteps || 10000);
    const convertibleCoupons = summary.convertibleCoupons || '0.00';
    const patch = {
      couponBalance: account.balance || '0.00',
      todaySteps: Number(summary.todaySteps || 0),
      convertibleSteps: Number(summary.convertibleSteps || 0),
      convertibleCoupons,
      dailyCapReached: exchangedSteps >= dailyCapSteps,
      canExchange: Number(convertibleCoupons) > 0,
    };
    if (data && data.challenge !== undefined) {
      patch.challenge = data.challenge;
    }
    this.setData(patch);
  },

  getStepPayload() {
    if (config.useMockSteps) {
      return Promise.resolve({ mockSteps: config.mockSteps });
    }
    return new Promise((resolve, reject) => {
      wx.getWeRunData({
        success(res) {
          if (!res.encryptedData || !res.iv) {
            reject(new Error('未获取到微信运动步数'));
            return;
          }
          resolve({
            encryptedData: res.encryptedData,
            iv: res.iv,
          });
        },
        fail(err) {
          const error = new Error(
            (err && err.errMsg) || '获取微信运动步数失败'
          );
          error.authDenied = true;
          reject(error);
        },
      });
    });
  },

  showWeRunPermissionModal() {
    wx.showModal({
      title: '需要微信运动权限',
      content: '请允许小程序读取微信运动步数，或在设置中开启微信运动。',
      confirmText: '去设置',
      success(res) {
        if (res.confirm) {
          wx.openSetting({});
        }
      },
    });
  },

  onSyncTap() {
    if (this.data.syncing) return;
    this.setData({ syncing: true });
    wx.showLoading({ title: '同步中', mask: true });

    auth
      .ensureLogin()
      .then(() => this.getStepPayload())
      .then((payload) => api.syncSteps(payload))
      .then((data) => {
        this.applyStepsData(data);
        wx.hideLoading();
        ui.toast('步数同步成功');
      })
      .catch((error) => {
        wx.hideLoading();
        if (error && error.authDenied) {
          this.showWeRunPermissionModal();
        } else {
          ui.showError(error);
        }
      })
      .then(() => {
        this.setData({ syncing: false });
      });
  },

  doExchange() {
    if (this.data.exchanging) return;
    if (!this.exchangeRequestId) {
      this.exchangeRequestId =
        'mini-' +
        Date.now() +
        '-' +
        Math.random().toString(36).slice(2, 8);
    }

    const requestId = this.exchangeRequestId;
    this.setData({ exchanging: true });
    wx.showLoading({ title: '兑换中', mask: true });

    auth
      .ensureLogin()
      .then(function () {
        return api.exchangeSteps({ requestId: requestId });
      })
      .then((data) => {
        this.applyStepsData(data);
        this.exchangeRequestId = '';
        wx.hideLoading();
        ui.toast('兑换成功');
      })
      .catch((error) => {
        wx.hideLoading();
        if (error && error.code) {
          this.exchangeRequestId = '';
        }
        ui.showError(error);
      })
      .then(() => {
        this.setData({ exchanging: false });
      });
  },

  onExchangeTap() {
    if (this.data.exchanging) return;
    if (this.data.dailyCapReached) {
      ui.toast('今日已达标');
      return;
    }
    if (!this.data.convertibleSteps) {
      ui.toast('暂无可兑换步数');
      return;
    }
    if (!this.data.canExchange) {
      ui.toast('不足 100 步，暂不可兑换');
      return;
    }
    ui.confirm(
      '确认兑换',
      '确认兑换 ' +
        this.data.convertibleCoupons +
        ' 兑换券？未兑换步数会保留在今日可兑步数中。'
    ).then((confirmed) => {
      if (confirmed) this.doExchange();
    });
  },

  onCouponTap() {
    wx.navigateTo({ url: '/pages/coupon/coupon' });
  },

  onRulesTap() {
    const rules = this.data.activityRules || [];
    if (!rules.length) {
      ui.toast('暂无活动规则');
      return;
    }
    const content = rules
      .map((rule) => (rule.no || '') + '. ' + (rule.text || ''))
      .join('\n');
    wx.showModal({
      title: '活动规则',
      content,
      showCancel: false,
      confirmText: '知道了',
    });
  },

  onRankingTap() {
    ui.toast('排行榜功能建设中');
  },

  onHomeTap() {
    wx.switchTab({ url: '/pages/index/index' });
  },

  onChallengeMore() {
    wx.navigateTo({ url: '/pages/challenge/challenge' });
  },

  onFriendMore() {
    ui.toast('好友助力功能建设中');
  },

  onInviteHint() {
    ui.toast('请点击上方“邀请好友”按钮分享');
  },

  onReminderToggle() {
    this.setData({ reminderOn: !this.data.reminderOn });
    ui.toast('提醒功能建设中');
  },

  onRetry() {
    this.loadData();
  },

  onShareAppMessage() {
    return {
      title: '邀请你参加 LabourRun 步数挑战',
      path: '/pages/index/index',
    };
  },
});
