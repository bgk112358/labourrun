Component({
  data: {
    selected: 0,
    safeBottom: 0,
    list: [
      { pagePath: '/pages/index/index', text: '首页' },
      { pagePath: '/pages/steps/steps', text: '步数宝' },
      { pagePath: '/pages/user/user', text: '我' }
    ]
  },
  lifetimes: {
    attached() {
      let info = {}
      try {
        info = wx.getWindowInfo ? wx.getWindowInfo() : wx.getSystemInfoSync()
      } catch (e) {
        info = wx.getSystemInfoSync()
      }
      const safeBottom = info.safeArea
        ? Math.max(0, info.screenHeight - info.safeArea.bottom)
        : 0
      this.setData({ safeBottom })
    }
  },
  methods: {
    switchTab(e) {
      const { path, index } = e.currentTarget.dataset
      if (index === this.data.selected) return
      wx.switchTab({ url: path, fail() {} })
    }
  }
})
