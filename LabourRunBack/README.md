# LabourRunBack

LabourRun 微信小程序后端。实现内容以 `Docs/02-接口设计.md` 为准。

## 技术栈

- Python 3.14（生产建议 3.12/3.13）
- FastAPI 0.163.1
- Pydantic 2.13.4
- SQLite（标准库 `sqlite3`）
- PyJWT、cryptography、httpx
- pytest + FastAPI TestClient

## 已实现

- 微信登录（真实 `code2Session` / 本地 mock）
- JWT 鉴权
- 首页活动配置 + 报名状态
- 活动主图上传、自动居中裁剪/压缩、首页展示
- 报名创建/修改/取消/取消后再次报名
- 微信运动步数解密、同步、按日存储
- 步数兑换兑换券（每日最多兑换 10000 步，10000 步 = 1.00 兑换券，向下取整到分，可多次兑换）
- 兑换券账户、流水
- 用户资料（昵称）
- 挑战配置与规则
- 统一响应包、错误码、请求 ID

## 未实现（按需求占位）

- 排行榜、邀请/助力、每日提醒
- 商城、订单、积分、优惠券、卡券、收藏、足迹
- 头像上传
- 挑战参赛/保证金/完成判定

这些接口不提供，前端对应区域使用静态占位。

## 管理后台

- 管理端 API：`/api/v1/admin/*`，实现位于 `app/admin/`。
- 管理端前端：`LabourRunAdmin/`（Vue 3 + Vite + Element Plus）。
- 功能：管理员登录、概览、活动管理、挑战管理、报名列表/详情/CSV 导出、审计日志。
- 管理员账号管理页面本期未实现，使用 CLI 创建管理员。
- 管理端与小程序端使用不同 JWT secret，token 不互通。

创建首个管理员：

```bash
cd LabourRunBack
python -m app.admin.bootstrap \
  --username admin \
  --password '请替换为强密码' \
  --display-name '超级管理员' \
  --role super_admin
```

启动管理前端：

```bash
cd ../LabourRunAdmin
npm install
npm run dev
```

开发地址：`http://<服务器局域网IP>:5173/admin/`。Vite 已监听 `0.0.0.0`，可局域网访问；构建 `npm run build` 后，后端会挂载 `dist` 到 `/admin`。

## 目录

```
app/
  main.py          # create_app、异常处理、中间件
  server.py        # uvicorn 入口
  config.py        # 环境变量
  db.py            # SQLite 连接/事务/初始化
  schema.sql       # 表结构
  seed.py          # 活动/挑战/配置种子
  models.py        # Pydantic 模型
  deps.py          # 当前用户依赖
  security.py      # JWT / session_key 加密
  wx.py            # 微信登录、微信运动解密
  routers/         # 小程序路由
  services/        # 小程序业务逻辑
  admin/           # 管理端 API、管理员认证、审计
tests/
  test_api.py
  test_wx.py
```

## 快速开始

```bash
cd LabourRunBack

# 首次创建 Conda 环境（已有可跳过）
conda create -n labourrun python=3.12 -y
conda activate labourrun
python -m pip install -r requirements.txt

# 环境变量按 Docs/04 3.2 使用 conda env config vars 配置
uvicorn app.server:app --reload --host 0.0.0.0 --port 3000
```

本地 mock 使用默认值即可；生产环境变量配置见 `Docs/04-部署与使用.md` 的 3.2 节。

打开：

- Swagger：http://127.0.0.1:3000/docs
- 健康检查：http://127.0.0.1:3000/healthz

默认 `WX_MOCK=1`，无需微信 AppSecret 即可本地联调。

## Mock 联调

```bash
# 登录
curl -s -X POST http://127.0.0.1:3000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"code":"mock:demo"}'

# 同步步数
curl -s -X POST http://127.0.0.1:3000/api/v1/steps/sync \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"mockSteps":6638}'

# 兑换
curl -s -X POST http://127.0.0.1:3000/api/v1/steps/exchange \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"requestId":"req-demo-0001"}'
```

## 环境变量

| 变量 | 说明 | 默认 |
|---|---|---|
| `HOST` | 监听地址 | `127.0.0.1` |
| `PORT` | 端口 | `3000` |
| `DB_PATH` | SQLite 文件 | `./data/labourrun.sqlite` |
| `JWT_SECRET` | JWT 密钥，建议 32+ 字节 | 开发默认值 |
| `JWT_TTL_SECONDS` | token 有效期（秒） | `604800` |
| `WX_APPID` | 小程序 AppID | `wx553877a9e7439113` |
| `WX_SECRET` | 小程序 AppSecret，生产必填 | 空 |
| `WX_MOCK` | 本地 mock 登录/步数 | `1` |
| `LOG_LEVEL` | 日志级别 | `info` |
| `ADMIN_JWT_SECRET` | 管理员 JWT 密钥，建议 32+ 字节 | 开发默认值 |
| `ADMIN_JWT_TTL_SECONDS` | 管理员 token 有效期 | `28800` |
| `ADMIN_ORIGINS` | 管理端跨域白名单，逗号分隔 | 本地 5173 |
| `UPLOAD_DIR` | 上传文件目录 | `./uploads` |
| `PUBLIC_BASE_URL` | 对外访问地址，用于生成图片 URL | `http://192.168.100.20:3000` |
| `ACTIVITY_IMAGE_WIDTH` / `ACTIVITY_IMAGE_HEIGHT` | 活动图片目标尺寸 | `750` / `400` |
| `ACTIVITY_IMAGE_QUALITY` | JPEG 初始质量 | `82` |

## 测试

```bash
pytest -q
```

当前：**28 passed**。

## 兑换规则

```
最大可兑换步数 = min(今日步数, 10000)
可兑步数 = max(最大可兑换步数 − 今日已兑换步数, 0)
兑换券分 = floor(可兑步数 × 100 / 10000)
实际扣除步数 = 兑换券分 × 100
```

- 按整百步兑换，不足 100 步的部分保留在今日可兑步数中，可继续累计后再次兑换。
- 每天最多兑换 10000 步、最多获得 1.00 兑换券；达到上限后再兑换提示“今日已达标”。
- 未兑换步数每日零点自然失效；兑换券余额每天累计。

示例：

- 6638 步 → 0.66 兑换券，扣除 6600 步，剩余 38 步可兑步数。
- 6650 步 → 0.66 兑换券，扣除 6600 步，剩余 50 步可兑步数。
- 6700 步 → 0.67 兑换券，扣除 6700 步，剩余 0 步。
- 10000 步 → 1.00 兑换券；当天达到上限。

## 生产注意事项

- `WX_MOCK=0`，配置 `WX_SECRET` 和强 `JWT_SECRET`。
- 小程序请求域名必须为 HTTPS，并在微信后台配置。
- SQLite 适合单实例/小流量；多实例请换 MySQL/PostgreSQL。
- `data/` 已在 `.gitignore` 中；Conda 环境变量和密钥不要提交。
- 本服务不实现头像上传、排行榜、邀请/助力、每日提醒、商城资产。
