# LabourRunMiniProgram

LabourRun 微信小程序前端，已接入 `LabourRunBack` 接口。

## 功能

- 静默登录、token 存储、401 自动重新登录
- 首页：后台配置的活动主图（无图时回退装饰区）、活动公告/规则、报名、修改、取消、再次报名
- 首页奖品兑换：三档奖品、兑换券不足提示、扣券生成唯一兑换码、已兑换查看奖励详情
- 步数宝：兑换券余额、今日可兑步数、步数同步、多次兑换、挑战摘要
- 首页、步数宝、我支持下拉刷新
- 挑战详情：后台配置与规则
- 兑换券明细：流水列表、分页加载
- 我：昵称读取/修改，其他入口按需求占位

## 配置

编辑 `config/index.js`：

```js
const ENV = 'dev';

dev: {
  apiBaseUrl: 'http://192.168.100.20:3000/api/v1',
  useMockLogin: true,
  mockLoginCode: 'mock:miniapp-demo',
  useMockSteps: true,
  mockSteps: 6638,
}
```

- `useMockLogin=true`：使用固定 mock code，不调用 `wx.login`，保证多次启动为同一用户。
- `useMockSteps=true`：同步步数提交固定 `mockSteps`。
- 生产环境将 `ENV` 改为 `'prod'`，并配置 `prod.apiBaseUrl`、`useMockLogin=false`、`useMockSteps=false`。

## 本地运行

1. 启动后端（局域网联调需 `--host 0.0.0.0`）：

```bash
source /home/ubuntu/miniconda3/etc/profile.d/conda.sh
conda activate labourrun
cd ../LabourRunBack
python -m uvicorn app.server:app --host 0.0.0.0 --port 3000
```

2. 微信开发者工具导入 `LabourRunMiniProgram`。
3. 项目已设置 `urlCheck=false`；如未生效，在“详情 → 本地设置”勾选“不校验合法域名……”。
4. 确保 `config/index.js` 的 `apiBaseUrl` 指向可访问的后端地址。

## 验证

在仓库根目录执行：

```bash
# 语法与配置
find LabourRunMiniProgram -name '*.js' -not -path '*/@eaDir/*' -print0 | xargs -0 -n1 node --check
python3 -c "import json; from pathlib import Path; [json.loads(p.read_text()) for p in Path('LabourRunMiniProgram').rglob('*.json') if '@eaDir' not in str(p)]"

# API 数据流
node tools/verify-miniapp.js

# 页面方法级验证
node tools/verify-miniapp-pages.js
```

`tools/verify-miniapp.js` 会 mock `wx`，加载小程序的登录/请求/API 模块，对真实后端验证完整流程，包括 401 重登。

`tools/verify-miniapp-pages.js` 会加载各页面 JS，模拟 `Page`/`wx`，验证报名、同步、步数兑换、奖品兑换、流水、昵称、挑战页面以及首页/步数宝/我下拉刷新的方法逻辑。

## 说明

- 头像上传、排行榜、邀请/助力、每日提醒、商城资产、挑战参赛流程按当前需求保持占位。
- 生产环境必须配置微信合法域名、HTTPS 和后端 `WX_MOCK=0`、`WX_SECRET`。
