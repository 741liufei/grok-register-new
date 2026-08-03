# Grok Register Web 控制台

基于 **FastAPI + shadcn 风格 React** 的轻量 Web UI，用于：

- 启动注册账号
- 展示账号 / 注册结果
- 管理账号（筛选、复制、删除记录与关联文件）
- 编辑注册核心使用的 `config.json`

## 结构说明

- `backend/registration_core.py` 仅保留 Web 后台需要的注册核心
- 账号注册 / SSO→auth 转换实现由 Web 后台直接复用
- 后端使用单进程 FastAPI + uvicorn workers=1，数据继续使用 SQLite

## 复用关系

| 能力 | 来源 |
| --- | --- |
| 注册主流程 | `backend.registration_core.run_registration` |
| 停止控制 | 运行时替换 `RegistrationStopController`（见 `backend/job_manager.py`） |
| 日志 | 运行时包装 `registration_log` |
| 结果存储 | `RegistrationStore` / `get_registration_store()` |
| 删除关联文件 | `registration_files` 中的纯函数工具 |
| 配置 | `load_config` / `save_config` / `config.json` |

## 启动

```bash
# 依赖（已写入 requirements.txt）
.venv/bin/python -m pip install -r requirements.txt

# 若需重新构建前端
cd front && npm install && npm run build && cd ..

# 启动 Web
./start-web.sh
# 或
.venv/bin/python -m backend.server --host 127.0.0.1 --port 8787
```

### 公网账号密码登录

首次打开公网域名时会进入初始化页面，只能创建一个管理员账号；创建后不提供新增账号功能。账号密码以哈希形式保存到 `data/web_auth.json`（已加入 `.gitignore`），不会写入 `config.json`。

HTTPS 反代部署默认使用安全 Cookie；本机纯 HTTP 调试时可设置 `GROK_WEB_COOKIE_SECURE=0`。删除 `data/web_auth.json` 会触发重新初始化，请仅在明确需要时操作。

浏览器打开：http://127.0.0.1:8787  
API 文档：http://127.0.0.1:8787/api/docs

## 目录

```text
front/                 # React + Tailwind（shadcn 风格）前端
  src/                 # 前端源码
  dist/                # 生产构建产物
backend/               # FastAPI 后端与注册核心
  server.py            # 入口
  app.py               # FastAPI 路由
  job_manager.py       # 后台注册任务与日志 hooks
  email_providers/     # 邮箱服务商
data/                  # 账号、授权和认证运行数据
logs/                  # 运行日志
backend/tests/         # 后端单元测试
```

## 主要 API

- `GET /api/stats` 统计 + 任务状态
- `GET /api/accounts` 账号列表
- `POST /api/accounts/delete` 删除记录（可选删关联文件）
- `GET/PUT /api/config` 读写配置
- `POST /api/job/start` 启动注册
- `POST /api/job/stop` 停止注册
- `POST /api/browser/kill-all` 请求停止任务并终止全部 Camoufox 进程
- `GET /api/job/logs` 轮询日志
- `POST /api/connectivity` 连通性检查

设置页已按“基础注册 / CPA / Auth / 邮箱服务 / Outlook 邮箱池”拆分子菜单。邮箱服务下拉使用中文名称，并只显示当前服务商需要的配置字段；当前 6 种邮箱来源均已接入注册流程。

设置页可启用“无头浏览器”，让 Camoufox 不显示窗口运行。该模式会处理常见无头指纹差异，但站点风控仍可能结合环境与行为判断，默认保持关闭。

注册页的“终止所有 Camoufox”用于异常兜底：先请求停止当前任务，再终止 Camoufox 进程树并清理本项目创建的临时资料目录。紧急终止后，下一次手动启动注册任务才会重新允许浏览器启动。

## Caddy 反代

本机 Caddy 已将下列域名反代到 `127.0.0.1:8787`：

- https://register.lvyrix.com
- https://register.ota.dpdns.org

配置文件：`/etc/caddy/conf.d/ota-services.caddy`

```bash
# 改完后
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

请确保 Web 服务常驻监听：

```bash
.venv/bin/python -m backend.server --host 127.0.0.1 --port 8787
# 或 0.0.0.0:8787
```
