const auth = require('../../utils/auth');
const api = require('../../utils/api');
const ui = require('../../utils/ui');

Page({
  data: {
    user: null,
    nickname: '微信用户',
    nicknameDraft: '',
    editVisible: false,
    savingNickname: false,
    loading: true,
    error: '',
    stats: {
      favoriteCount: 0,
      footprintCount: 0,
    },
    orders: [
      { label: '待付款', icon: 'wallet' },
      { label: '待发货', icon: 'box' },
      { label: '待收货', icon: 'truck' },
      { label: '已完成', icon: 'doc' },
      { label: '售后', icon: 'back' },
    ],
    menus: [
      { label: '我的收藏', icon: '★' },
      { label: '我的优惠券', icon: '◈' },
      { label: '我的卡券', icon: '¥' },
      { label: '领券中心', icon: '⊕' },
      { label: '收货地址', icon: '⌖' },
      { label: '绑定手机号', icon: '▤' },
      { label: '分销中心', icon: '◎' },
      { label: '分类', icon: '▦' },
      { label: '个人资料', icon: '☺' },
      { label: '清除缓存', icon: '♻' },
      { label: '客服', icon: '✆' },
    ],
  },

  onLoad() {
    this.requesting = false;
    this.pending = null;
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 2 });
    }
    this.loadMe();
  },

  onPullDownRefresh() {
    this.loadMe({ silent: true }).then(
      () => wx.stopPullDownRefresh(),
      () => wx.stopPullDownRefresh()
    );
  },

  loadMe(options) {
    const silent = options && options.silent;
    if (this.requesting) {
      return this.pending || Promise.resolve();
    }
    this.requesting = true;
    this.setData(silent ? { error: '' } : { loading: true, error: '' });

    this.pending = auth
      .ensureLogin()
      .then(function () {
        return api.getMe();
      })
      .then((user) => {
        this.requesting = false;
        this.pending = null;
        auth.updateUser(user);
        this.setData({
          user,
          nickname: user.nickname || '微信用户',
          loading: false,
          error: '',
        });
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

  openNicknameEdit() {
    if (this.data.savingNickname) return;
    this.setData({
      nicknameDraft: this.data.nickname,
      editVisible: true,
    });
  },

  closeNicknameEdit() {
    if (this.data.savingNickname) return;
    this.setData({ editVisible: false });
  },

  onNicknameInput(event) {
    this.setData({ nicknameDraft: event.detail.value });
  },

  saveNickname() {
    if (this.data.savingNickname) return;
    const nickname = (this.data.nicknameDraft || '').trim();
    if (!nickname) {
      ui.toast('请输入昵称');
      return;
    }
    if (nickname.length > 32) {
      ui.toast('昵称最多 32 个字符');
      return;
    }

    this.setData({ savingNickname: true });
    auth
      .ensureLogin()
      .then(function () {
        return api.updateMe({ nickname });
      })
      .then((user) => {
        auth.updateUser(user);
        this.setData({
          user,
          nickname: user.nickname || '微信用户',
          editVisible: false,
          savingNickname: false,
        });
        ui.toast('昵称已保存');
      })
      .catch((error) => {
        this.setData({ savingNickname: false });
        ui.showError(error);
      });
  },

  onPlaceholderTap() {
    ui.toast('功能建设中');
  },

  onSettingTap() {
    ui.toast('设置功能建设中');
  },

  onLocationTap() {
    ui.toast('定位功能建设中');
  },

  onRetry() {
    this.loadMe();
  },

  noop() {},
});
