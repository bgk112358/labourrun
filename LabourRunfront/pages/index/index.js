Page({
  data: {
    rules: [
      { no: '01', text: '一、本次活动为线上步行挑战赛，参赛者需每日完成指定步数。' },
      { no: '02', text: '二、每日步数于零点自动清零，请及时兑换您的步数奖励。' },
      { no: '03', text: '三、参赛者不得使用任何外挂或作弊手段，一经发现将取消资格。' },
      { no: '04', text: '四、活动最终解释权归主办方所有，如有疑问请联系客服。' }
    ]
  },
  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 0 })
    }
  }
})
