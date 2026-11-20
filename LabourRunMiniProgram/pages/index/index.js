const auth = require('../../utils/auth');
const api = require('../../utils/api');
const ui = require('../../utils/ui');

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
  },

  onLoad() {
    this.requesting = false;
    this.pending = null;
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 0 });
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
        return api.getHome();
      })
      .then((data) => {
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
              loading: false,
              error: '',
              bannerError: false,
            },
            state
          )
        );
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
        })
        .catch((error) => {
          this.setData({ submitting: false });
          ui.showError(error);
        });
    });
  },

  onBannerError() {
    this.setData({ bannerError: true });
  },

  onRetry() {
    this.loadData();
  },
});
