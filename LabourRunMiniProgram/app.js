const auth = require('./utils/auth')

App({
  globalData: {
    statusBarHeight: 20,
    navContentHeight: 44
  },
  onLaunch() {
    let info = {}
    try {
      info = wx.getWindowInfo ? wx.getWindowInfo() : wx.getSystemInfoSync()
    } catch (e) {
      info = wx.getSystemInfoSync()
    }
    const statusBarHeight = info.statusBarHeight || 20
    let navContentHeight = 44
    try {
      const menu = wx.getMenuButtonBoundingClientRect()
      if (menu && menu.top && menu.height) {
        navContentHeight = (menu.top - statusBarHeight) * 2 + menu.height
      }
    } catch (e) {}
    this.globalData.statusBarHeight = statusBarHeight
    this.globalData.navContentHeight = navContentHeight

    // 启动时预热登录；页面 onShow 仍会兜底调用 ensureLogin
    this.loginReady = auth.ensureLogin().catch(function () {
      return null
    })
  }
})
