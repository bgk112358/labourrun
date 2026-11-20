Page({
  data: {
    ticks: Array.from({ length: 44 }, (_, i) => i * (360 / 44)),
    adds: [1, 2, 3, 4]
  },
  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 1 })
    }
  }
})
