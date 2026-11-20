Component({
  properties: {
    title: { type: String, value: '' },
    background: { type: String, value: '#FFFFFF' },
    color: { type: String, value: '#1A1A1A' },
    showBack: { type: Boolean, value: true }
  },
  data: {
    statusBarHeight: 20,
    navContentHeight: 44
  },
  lifetimes: {
    attached() {
      const g = getApp().globalData
      this.setData({
        statusBarHeight: g.statusBarHeight,
        navContentHeight: g.navContentHeight
      })
    }
  },
  methods: {
    onBack() {
      wx.navigateBack({ fail() {} })
    }
  }
})
