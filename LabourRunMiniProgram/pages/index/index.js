const auth = require('../../utils/auth');
const api = require('../../utils/api');
const ui = require('../../utils/ui');
const format = require('../../utils/format');

Page({
  data: {
    activity: null,
    rules: [],
    registration: null,
    form: {
      realName: '',
      phone: '',
      company: '',
    },
    loading: true,
    submitting: false,
    error: '',
    bannerError: false,
    submitText: '提交报名',
    statusText: '',
    isRegistered: false,
    isCancelled: false,
    rewards: [],
    redeemingRewardId: '',
  },

  onLoad() {
    this.requesting = false;
    this.pending = null;
    this.rewardRequestIds = {};
  },

  onShow() {
    console.log('[home] onShow');
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 0 });
    }
    this.loadData();
  },

  onPullDownRefresh() {
    console.log('[home] pull down refresh');
    this.loadData({ silent: true }).then(
      () => wx.stopPullDownRefresh(),
      () => wx.stopPullDownRefresh()
    );
  },

  loadData(options) {
    const silent = options && options.silent;
    console.log('[home] loadData start', {
      silent: Boolean(silent),
      requesting: this.requesting,
    });
    if (this.requesting) {
      console.log('[home] loadData reuse pending request');
      return this.pending || Promise.resolve();
    }
    this.requesting = true;
    this.setData(silent ? { error: '' } : { loading: true, error: '' });

    this.pending = auth
      .ensureLogin()
      .then(function () {
        console.log('[home] login ready, requesting /home');
        return api.getHome();
      })
      .then((data) => {
        console.log('[home] loadData success');
        const activity = data.activity || {};
        const registration = data.registration || null;
        const form = registration
          ? {
              realName: registration.realName || '',
              phone: registration.phone || '',
              company: registration.company || '',
            }
          : { realName: '', phone: '', company: '' };
        const state = this.getRegistrationState(registration);
        this.requesting = false;
        this.pending = null;
        this.setData(
          Object.assign(
            {
              activity,
              rules: activity.rules || [],
              registration,
              form,
              rewards: data.rewards || [],
              loading: false,
              error: '',
              bannerError: false,
            },
            state
          )
        );
      })
      .catch((error) => {
        console.error('[home] loadData fail', error);
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

  getRegistrationState(registration) {
    if (registration && registration.status === 'registered') {
      return {
        submitText: '保存修改',
        statusText: '已报名',
        isRegistered: true,
        isCancelled: false,
      };
    }
    if (registration && registration.status === 'cancelled') {
      return {
        submitText: '重新报名',
        statusText: '已取消报名，可重新提交',
        isRegistered: false,
        isCancelled: true,
      };
    }
    return {
      submitText: '提交报名',
      statusText: '',
      isRegistered: false,
      isCancelled: false,
    };
  },

  applyRegistration(registration) {
    const state = this.getRegistrationState(registration);
    this.setData(
      Object.assign(
        {
          registration,
          form: {
            realName: (registration && registration.realName) || '',
            phone: (registration && registration.phone) || '',
            company: (registration && registration.company) || '',
          },
        },
        state
      )
    );
  },

  onNameInput(event) {
    this.setData({ 'form.realName': event.detail.value });
  },

  onPhoneInput(event) {
    this.setData({ 'form.phone': event.detail.value });
  },

  onCompanyInput(event) {
    this.setData({ 'form.company': event.detail.value });
  },

  validateForm() {
    const name = (this.data.form.realName || '').trim();
    const phone = (this.data.form.phone || '').trim();
    const company = (this.data.form.company || '').trim();

    if (name.length < 2 || name.length > 20) {
      ui.toast('姓名需为 2-20 个字符');
      return null;
    }
    if (!/^1[3-9]\d{9}$/.test(phone)) {
      ui.toast('请输入正确的 11 位手机号');
      return null;
    }
    if (company.length < 2 || company.length > 50) {
      ui.toast('工作单位需为 2-50 个字符');
      return null;
    }
    return {
      realName: name,
      phone,
      company,
    };
  },

  onSubmit() {
    if (this.data.submitting) return;
    const payload = this.validateForm();
    if (!payload) return;

    const registration = this.data.registration;
    const wasRegistered =
      registration && registration.status === 'registered';
    this.setData({ submitting: true });

    auth
      .ensureLogin()
      .then(() => {
        if (registration && registration.status === 'registered') {
          return api.updateRegistration(registration.id, payload);
        }
        return api.createRegistration(payload);
      })
      .then((data) => {
        this.applyRegistration(data);
        this.setData({ submitting: false });
        ui.toast(wasRegistered ? '保存成功' : '报名成功');
        this.loadData({ silent: true });
      })
      .catch((error) => {
        this.setData({ submitting: false });
        ui.showError(error);
      });
  },

  onCancel() {
    const registration = this.data.registration;
    if (
      !registration ||
      registration.status !== 'registered' ||
      this.data.submitting
    ) {
      return;
    }

    ui.confirm(
      '取消报名',
      '确定取消报名吗？取消后可以再次报名。'
    ).then((confirmed) => {
      if (!confirmed) return;
      this.setData({ submitting: true });
      auth
        .ensureLogin()
        .then(function () {
          return api.cancelRegistration(registration.id);
        })
        .then((data) => {
          this.applyRegistration(data);
          this.setData({ submitting: false });
          ui.toast('已取消报名');
          this.loadData({ silent: true });
        })
        .catch((error) => {
          this.setData({ submitting: false });
          ui.showError(error);
        });
    });
  },

  onRewardTap(event) {
    if (this.data.redeemingRewardId) return;
    const rewardId = event.currentTarget.dataset.id;
    const reward = (this.data.rewards || []).find(
      (item) => item.id === rewardId
    );
    if (!reward) return;

    if (reward.redeemed) {
      this.showRewardDetail(reward);
      return;
    }
    if (!reward.canRedeem) {
      ui.toast(reward.disabledReason || '暂不可兑换');
      return;
    }

    ui.confirm(
      '确认兑换',
      '使用 ' +
        reward.couponCost +
        ' 兑换券兑换「' +
        reward.name +
        '」？'
    ).then((confirmed) => {
      if (confirmed) this.doRedeemReward(reward);
    });
  },

  doRedeemReward(reward) {
    if (this.data.redeemingRewardId) return;
    if (!this.rewardRequestIds) this.rewardRequestIds = {};
    let requestId = this.rewardRequestIds[reward.id];
    if (!requestId) {
      requestId =
        'reward-' +
        Date.now() +
        '-' +
        Math.random().toString(36).slice(2, 8);
      this.rewardRequestIds[reward.id] = requestId;
    }

    this.setData({ redeemingRewardId: reward.id });
    auth
      .ensureLogin()
      .then(() => api.redeemReward(reward.id, { requestId }))
      .then((data) => {
        delete this.rewardRequestIds[reward.id];
        const redemption = (data && data.redemption) || {};
        const rewards = (this.data.rewards || []).map((item) => {
          if (item.id !== reward.id) return item;
          return Object.assign({}, item, {
            redeemed: true,
            redemptionCode: redemption.code || '',
            redeemedAt: redemption.createdAt || '',
            redemptionRewardName:
              redemption.rewardName || item.name,
            redemptionCouponCost:
              redemption.couponAmount || item.couponCost,
            canRedeem: false,
            disabledReason: null,
          });
        });
        this.setData({
          rewards,
          redeemingRewardId: '',
        });
        ui.toast('兑换成功');
      })
      .catch((error) => {
        if (error && error.code) {
          delete this.rewardRequestIds[reward.id];
        }
        this.setData({ redeemingRewardId: '' });
        ui.showError(error);
      });
  },

  showRewardDetail(reward) {
    const code = reward.redemptionCode || '';
    if (!code) {
      ui.toast('兑换码获取中，请下拉刷新');
      return;
    }
    const rewardName =
      reward.redemptionRewardName || reward.name || '';
    wx.showModal({
      title: rewardName || '奖励详情',
      content:
        '兑换码：' +
        code +
        '\n奖励：' +
        rewardName +
        (reward.redeemedAt
          ? '\n兑换时间：' + format.formatTime(reward.redeemedAt)
          : ''),
      showCancel: false,
      confirmText: '知道了',
    });
  },

  onRewardImageError(event) {
    const rewardId = event.currentTarget.dataset.id;
    const rewards = (this.data.rewards || []).map((item) =>
      item.id === rewardId
        ? Object.assign({}, item, { imageError: true })
        : item
    );
    this.setData({ rewards });
  },

  onBannerError() {
    this.setData({ bannerError: true });
  },

  onRetry() {
    this.loadData();
  },
});
