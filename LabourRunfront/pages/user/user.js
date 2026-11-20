Page({
  data: {
    orders: [
      { label: '待付款', icon: 'wallet' },
      { label: '待发货', icon: 'box' },
      { label: '待收货', icon: 'truck' },
      { label: '已完成', icon: 'doc' },
      { label: '售后', icon: 'back' }
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
      { label: '客服', icon: '✆' }
    ]
  },
  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 2 })
    }
  }
})
