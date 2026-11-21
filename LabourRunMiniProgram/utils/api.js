const request = require('./request');

module.exports = {
  getHome() {
    return request({ url: '/home' });
  },

  createRegistration(data) {
    return request({
      url: '/registrations',
      method: 'POST',
      data,
    });
  },

  updateRegistration(id, data) {
    return request({
      url: '/registrations/' + id,
      method: 'PATCH',
      data,
    });
  },

  cancelRegistration(id) {
    return request({
      url: '/registrations/' + id + '/cancel',
      method: 'POST',
    });
  },

  getSteps() {
    return request({ url: '/steps' });
  },

  syncSteps(data) {
    return request({
      url: '/steps/sync',
      method: 'POST',
      data,
    });
  },

  exchangeSteps(data) {
    return request({
      url: '/steps/exchange',
      method: 'POST',
      data,
    });
  },

  getLedger(params) {
    return request({
      url: '/coupons/ledger',
      data: params || {},
    });
  },

  getMe() {
    return request({ url: '/me' });
  },

  updateMe(data) {
    return request({
      url: '/me',
      method: 'PATCH',
      data,
    });
  },

  getChallenge() {
    return request({ url: '/challenges/current' });
  },

  redeemReward(rewardId, data) {
    return request({
      url: '/rewards/' + rewardId + '/redeem',
      method: 'POST',
      data,
    });
  },
};
