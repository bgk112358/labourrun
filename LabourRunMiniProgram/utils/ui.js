function toast(title) {
  wx.showToast({
    title: title || '操作失败',
    icon: 'none',
    duration: 2000,
  });
}

function showError(error) {
  toast((error && error.message) || '操作失败，请稍后重试');
}

function confirm(title, content) {
  return new Promise((resolve) => {
    wx.showModal({
      title: title || '提示',
      content: content || '',
      success(res) {
        resolve(Boolean(res && res.confirm));
      },
      fail() {
        resolve(false);
      },
    });
  });
}

module.exports = {
  toast,
  showError,
  confirm,
};
