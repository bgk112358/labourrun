const api = require('../../utils/api');
const format = require('../../utils/format');

Page({
  data: {
    challenge: null,
    rules: [],
    statusText: '',
    loading: true,
    error: '',
  },

  onLoad() {
    this.loadChallenge();
  },

  loadChallenge() {
    this.setData({ loading: true, error: '' });
    api
      .getChallenge()
      .then((challenge) => {
        this.setData({
          challenge,
          rules: challenge.rules || [],
          statusText: format.statusText(challenge.status),
          loading: false,
        });
      })
      .catch((error) => {
        this.setData({
          loading: false,
          error: (error && error.message) || '加载失败',
        });
        wx.showToast({
          title: (error && error.message) || '加载失败',
          icon: 'none',
        });
      });
  },

  onRetry() {
    this.loadChallenge();
  },

  onShareAppMessage() {
    return {
      title: '邀请你参加 LabourRun 步数挑战',
      path: '/pages/index/index',
    };
  },
});
