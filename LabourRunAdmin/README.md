# LabourRunAdmin

LabourRun 后台管理前端。设计见 `Docs/03-后台管理设计.md`，管理 API 在 `LabourRunBack/app/admin/`。

## 技术栈

- Vue 3
- Vite
- TypeScript
- Element Plus
- Pinia
- Vue Router
- Axios

## 页面

- 登录
- 概览
- 活动管理（公告、规则、时间、状态、活动图片上传）
- 挑战管理（目标、保证金、参与人数、规则）
- 报名管理（列表、搜索、详情、CSV 导出）
- 审计日志（列表、详情、前后快照）

管理员账号管理页面本期未实现，使用后端 CLI 创建管理员。

## 开发

```bash
cd LabourRunAdmin
npm install
npm run dev
```

开发地址：`http://<服务器局域网IP>:5173/admin/`

Vite 已配置 `server.host = '0.0.0.0'`，支持局域网访问；请确保防火墙放行 TCP 5173（仅开发环境）。Vite 已配置 `/api` 代理到 `http://127.0.0.1:3000`。请先启动后端：

```bash
cd ../LabourRunBack
conda activate labourrun
uvicorn app.server:app --reload --port 3000
```

环境变量按 `Docs/04-部署与使用.md` 3.2 节使用 `conda env config vars` 配置。

## 构建

```bash
npm run typecheck
npm run build
```

`npm run build` 会先执行 `vue-tsc --noEmit`，再输出 `dist/`。后端 `LabourRunBack/app/main.py` 会在 `LabourRunAdmin/dist` 存在时把它挂载到 `/admin`。

访问：`http://127.0.0.1:3000/admin`

## 创建管理员

```bash
cd ../LabourRunBack
python -m app.admin.bootstrap \
  --username admin \
  --password '请替换为强密码' \
  --display-name '超级管理员' \
  --role super_admin
```

密码至少 10 位，且同时包含字母和数字。

## 说明

- 管理端 token 存 `sessionStorage`，8 小时过期。
- 管理端和小程序使用不同 JWT secret，token 不能互相访问。
- 报名列表手机号脱敏；只有 super_admin 可以导出完整手机号。
- 活动/挑战保存后立即生效。
