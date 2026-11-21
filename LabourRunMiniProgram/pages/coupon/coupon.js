const auth = require('../../utils/auth');
const api = require('../../utils/api');
const format = require('../../utils/format');

function mapItem(item) {
  const amount = item.amount || '0.00';
  return {
    id: item.id,
    typeText:
      item.type === 'exchange'
        ? '步数兑换'
        : item.type === 'reward'
          ? '奖品兑换'
          : item.type,
    amount: format.formatMoney(amount),
    balanceAfter: format.formatMoney(item.balanceAfter),
    timeText: format.formatTime(item.createdAt),
    positive: Number(amount) >= 0,
  };
}

Page({
  data: {
    balance: '0.00',
    list: [],
    page: 1,
    pageSize: 20,
    total: 0,
    loading: true,
    loadingMore: false,
    finished: false,
    error: '',
  },

  onLoad() {
    this.requesting = false;
  },

  onShow() {
    this.loadBalance();
    this.loadLedger(true);
  },

  loadBalance() {
    auth
      .ensureLogin()
      .then(function () {
        return api.getSteps();
      })
      .then((data) => {
        const account = (data && data.couponAccount) || {};
        this.setData({
          balance: account.balance || '0.00',
        });
      })
      .catch(function () {
        // 余额加载失败不阻塞流水列表
      });
  },

  loadLedger(reset) {
    if (reset) {
      if (this.requesting) return;
      this.requesting = true;
      this.setData({ loading: true, error: '' });
    } else {
      if (this.data.loadingMore || this.data.finished) return;
      this.setData({ loadingMore: true });
    }

    const page = reset ? 1 : this.data.page + 1;
    auth
      .ensureLogin()
      .then(() => {
        return api.getLedger({
          page,
          pageSize: this.data.pageSize,
        });
      })
      .then((data) => {
        const incoming = (data.list || []).map(mapItem);
        const list = reset ? incoming : this.data.list.concat(incoming);
        this.requesting = false;
        this.setData({
          list,
          page: data.page || page,
          total: data.total || list.length,
          loading: false,
          loadingMore: false,
          finished: list.length >= (data.total || list.length),
          error: '',
        });
      })
      .catch((error) => {
        this.requesting = false;
        this.setData({
          loading: false,
          loadingMore: false,
          error: (error && error.message) || '加载失败',
        });
        wx.showToast({
          title: (error && error.message) || '加载失败',
          icon: 'none',
        });
      });
  },

  onReachBottom() {
    if (this.data.finished || this.data.loading) return;
    this.loadLedger(false);
  },

  onRetry() {
    this.loadLedger(true);
  },
});
