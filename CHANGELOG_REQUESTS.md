# 需求与改动记录

本文档记录 Web 控制台项目中已提出并完成的需求，便于后续查阅。新的明确需求完成并提交后，继续追加到本文档。

## 当前版本

- 最新功能提交：`4b9f597 style: refine config viewer presentation`
- 当前形态：Web-only 控制台，前端位于 `front/`，后端按 `web / registration / automation / integrations / mailbox / shared` 分包；支持宿主机手动启动和 Docker Compose 部署
- 验证状态：39 项 Python 单元测试、前端生产构建、Docker Compose、Web 健康检查、有头 Camoufox 冒烟、真实账号重新登录与授权文件重建均通过

## 已完成需求

### 1. 注册流程与邮箱

- 修复注册流程中的 OutlookEmail 停用逻辑；CPA 成功后按配置自动停用邮箱。
- 停用流程支持已有停用状态幂等处理、Session Cookie、密码登录、CSRF 和失败记录。
- 注册成功前统一校验 CPA 转换结果，避免仅保存 SSO 就误计成功。
- 当前注册流程支持 6 种邮箱来源：
  - Cloudflare 临时邮箱
  - DuckMail / Mail.tm
  - YYDS 临时邮箱
  - MailNest 迈巢 Outlook
  - OutlookEmail 邮箱池（`accounts` / `temp`）
  - CloudMail 自建邮箱

### 2. 日志与任务控制

- 修复点击“清空视图”后日志显示等待状态的问题。
- 清空日志视图只清除前端显示，不清除后台日志；任务运行时继续实时接收新日志。
- Web 后台注册任务支持启动、停止、并发和实时日志轮询。
- 增加“终止所有 Camoufox”按钮：
  - 先请求停止当前任务
  - 终止 Camoufox 进程树
  - 清理项目创建的临时浏览器资料目录
  - 紧急终止后阻止异常流程自动重新启动浏览器，下一次手动启动任务时恢复

### 3. JSON 复制与下载

- CPA JSON 支持复制。
- Grok2API JSON 支持复制。
- CPA JSON 和 Grok2API JSON 支持下载。
- 账号详情和账号列表保留对应的 JSON 查看、复制、下载能力。

### 4. Web 登录

- 首次访问时引导创建唯一管理员账号。
- 管理员账号创建后禁止新增其他账号。
- 密码使用 PBKDF2 哈希保存到 `data/web_auth.json`，不写入 `config.json`。
- 业务 API 需要登录；支持退出登录和 7 天 Cookie 会话。

### 5. 无头浏览器

- 系统设置新增“无头浏览器”开关，配置项为 `browser_headless`，默认关闭。
- Camoufox 根据该配置使用有头或无头模式。
- Camoufox 会处理常见无头屏幕、媒体设备和指纹差异，但站点仍可能结合网络环境、指纹一致性和行为进行风控判断。

### 6. 设置页面

- 系统设置按功能拆分子菜单：
  - 基础注册
  - CPA / Auth
  - 邮箱服务
  - Outlook 邮箱池
- 邮箱服务选项改为中文名称，并显示用途说明。
- 邮箱服务配置页根据当前选项显示对应字段，减少无关配置干扰。
- Outlook 来源、邮箱选取方式、Cloudflare 鉴权方式等下拉选项已中文化。
- 后端对邮箱服务商、Outlook 来源、选取模式和 Cloudflare 鉴权方式增加值校验。

### 7. Web-only 精简

- 移除 Tkinter GUI、交互式 CLI 入口和旧 GUI/CLI 运行说明。
- 删除 Windows `start-gui.cmd`、`start-cli.cmd`。
- 删除旧注册结果 GUI 弹窗，Web 删除账号所需的文件清理逻辑现位于 `backend.registration.artifacts`。
- 注册核心从 `grok_register_ttk.py` 重命名为 `registration_core.py`。
- SSO 转换模块保留 Web 所需 OAuth、CPA 和 Grok2API 核心函数，移除独立命令行入口。
- 依赖切换为 Camoufox，项目文档统一改为 Web 启动方式。
- Web 服务不自动启动、不自动重启，由用户手动管理。

### 8. 注册进度与账号查看

- 注册页增加实时任务进度展示：
  - 已完成数量 / 目标数量
  - 成功数量
  - 失败数量
  - 百分比进度条
  - 当前注册阶段
  - 当前处理邮箱
- 后端根据注册日志持续更新进度状态，兼容单线程和多 worker 并发注册。
- 浏览器批量启动失败时，进度会按受影响任务数量累计，并限制不超过目标数量。
- 账号管理的大屏 Web 表格将“操作 / 查看”列固定在最右侧；横向滚动查看其它字段时仍可直接打开账号详情。

### 9. 前后端目录分离

- React 前端源码和生产构建产物统一放在 `front/`，Vite 输出到 `front/dist/`。
- FastAPI、后台任务、注册核心和邮箱服务商统一放在 `backend/`。
- 后端从根目录读取配置，并将账号、授权和认证数据统一放入 `data/`，运行日志统一放入 `logs/`，不再与前后端代码混放。
- 后端单元测试统一放入 `backend/tests/`。
- 根目录 `start-web.sh` 改为通过 `python -m backend.web.cli` 启动，Web 服务仍由用户手动管理。

### 10. 后端测试与运行数据归类

- 原根目录 `tests/` 迁移到 `backend/tests/`，明确属于后端测试。
- 原 `accounts/`、`cpa_auth/`、`grok2api_auth/` 及历史授权备份统一迁移到 `data/`。
- Web 管理员认证文件和 Next Action 缓存改为保存到 `data/`。
- 原 `log/` 统一为 `logs/`，日志和运行数据仍保持 Git 忽略。

### 11. Docker Compose 与镜像发布

- 增加多阶段 `Dockerfile`：构建 React 前端、Python 虚拟环境并在镜像构建阶段下载 Camoufox。
- 增加 `compose.yaml`、`.env.example`、`.dockerignore` 和容器启动脚本。
- 容器通过 Xvfb 提供虚拟显示器，Camoufox 始终以有头模式启动；即使配置中打开无头模式，容器环境也会强制关闭。
- 支持只有 SSH 终端、没有桌面环境的 Linux 服务器运行。
- `data/` 与 `logs/` 映射到宿主机持久化，首次启动自动生成容器配置。
- 增加有头 Camoufox 冒烟脚本，验证页面访问、屏幕尺寸和 `navigator.webdriver=false`。
- 增加 GitHub Actions：先运行后端测试和前端构建，再用 Buildx 构建并发布 GHCR 镜像；默认分支发布 amd64，`v*` 标签发布 amd64/arm64。
- GHCR 镜像名称自动转为小写，避免仓库名称大小写导致发布失败。
- 本地实测 amd64 镜像内容大小约 1.04 GB，Docker 含层占用约 3.36 GB。

### 12. 项目文档精简

- 重写 `README.md`，保留功能概览、快速启动、配置路径、常用命令和必要排错。
- 重写 `DEPLOYMENT.md`，集中说明 Docker Compose、GHCR、本机部署和反向代理。
- 明确本机读取根目录 `config.json`，Docker 读取 `data/config.json`。

### 13. Docker 宿主机代理

- Docker Compose 增加 `host.docker.internal` 到宿主机的映射。
- 配置中的 `127.0.0.1`、`localhost` 等本地代理地址在容器内自动转换为宿主机地址。
- 代理连接检查、浏览器代理和 OAuth/CPA 请求统一使用转换后的地址。

### 14. 仓库与镜像名称修正

- 项目仓库统一为 `https://github.com/kaibush/grok-register`。
- 本地 Docker 镜像名统一为 `grok-register:local`。
- GHCR 示例统一为 `ghcr.io/kaibush/grok-register:latest`。

### 15. README 界面截图

- 使用当前 `grok-register:local` 镜像在隔离端口启动干净演示实例。
- 通过真实 Web 页面生成仪表盘、启动注册和账号管理三张 1440×1050 PNG 截图。
- 截图保存到 `docs/images/`，README 增加“界面预览”并更新项目结构。
- 截图环境使用独立临时数据目录，不包含本地账号、密钥、注册记录或运行日志。

### 16. 可选 OutlookEmail Compose 服务

- 将 `ghcr.io/assast/outlookemail:latest` 作为 `outlookemail` profile 接入 `compose.yaml`，默认启动不加载该服务。
- OutlookEmail 的唯一 Web 端口 `5000` 映射到宿主机全部 IPv4/IPv6 网卡，主容器通过 `http://outlook-email:5000` 访问。
- 增加独立的 `outlookemail-data/` 持久化目录、登录密码、SECRET_KEY、Docker 更新和 OAuth 环境变量。
- Docker 首次生成配置时预填内部 API Base；本机 Python 模板保持为空。
- README、部署文档和 Web 设置提示补充 profile 启动、API Key、temp 来源和端口说明。
- 实测上游 amd64/arm64 镜像可拉取；隔离容器、健康检查、内部 DNS、IPv4/IPv6 端口映射均通过。

### 17. 后端分包重构

- 后端重新按职责划分为 `backend/web`、`backend/registration`、`backend/automation`、`backend/integrations`、`backend/mailbox` 和 `backend/shared`。
- Web 路由、注册编排、浏览器控制、OAuth 交换、邮箱服务与公共路径不再混放在单个模块中。
- 保留现有运行数据、配置路径和启动入口，重构后无需迁移用户配置。

### 18. 浏览器失败截图

- 注册过程中发生浏览器异常时，自动截取失败现场并保存到 `data/screenshots/registration-failures/`。
- SQLite 记录保存截图路径，账号管理详情可查看受保护的原图。
- 删除账号及其关联文件时同步清理失败截图。
- 失败截图按 Batch、worker、邮箱、失败类型和时间命名，便于定位具体任务。

### 19. OutlookEmail 会话与验证码修复

- OutlookEmail Web Session Cookie 按 API 主机作用域写入 Cookie Jar，兼容本机地址与 Docker 内部主机名。
- Session 失效时支持通过管理密码重新登录并刷新 CSRF/Cookie，不再重复拼接显式 Cookie Header。
- 读取验证码时以提交邮箱的时间为边界，忽略提交前已经存在的旧验证码邮件。
- 增加多种 API 时间格式解析测试，避免时区和时间戳差异导致误取过期验证码。

### 20. 授权文件即时流式导出

- 账号管理操作区支持分别下载 CPA 和 Grok2API JSON。
- 前端使用原生下载链接，让点击后立即进入浏览器下载队列。
- 后端使用 `StreamingResponse` 按 64 KiB 分块输出，并设置 `Content-Length`、`Content-Disposition`、`Cache-Control` 和 `X-Content-Type-Options`。
- 列表接口提前返回文件可用状态，文件不存在时禁用下载入口并返回明确的 404。
- 保留详情弹框中的 JSON 复制与下载能力。

### 21. 已注册账号重新登录与文件恢复

- 账号管理增加“重新登录并刷新 SSO”，只使用 SQLite 保存的邮箱和密码，不重复注册、不启用邮箱池账号。
- 重新登录入口使用 `https://accounts.x.ai/sign-in`，通过稳定的 `data-testid` 元素填写邮箱和密码。
- 自动处理延迟出现的 Cookie 横幅和密码页 Turnstile，等待自然登录跳转后读取新的 SSO。
- 获取 SSO 后原子重建 `data/accounts/{email}.txt`，并重新生成 CPA 与 Grok2API 授权文件。
- 重新登录在独立后台线程执行，状态、结果和失败截图写回原 SQLite 记录。
- 已使用实际账号完成“邮箱密码登录 → Turnstile → 新 SSO → Device Flow → 两类授权文件”的端到端验证。

### 22. 账号管理交互与响应式布局

- 账号详情从桌面右侧常驻面板改为弹框；桌面居中显示，手机端使用底部弹层。
- 操作列固定为风格一致的“查看”和“更多”两个按钮。
- “更多”菜单集中提供 CPA 下载、Grok2API 下载和重新登录；桌面使用紧凑浮层，手机使用底部操作面板。
- 全局桌面内容最大宽度由 1440px 提升至 1920px，桌面左右内边距缩小，仪表盘、账号管理、注册台和系统设置统一减少宽屏空白。

### 23. 设置页配置查看

- 系统设置增加“查看配置”按钮，以受登录保护的接口读取磁盘上的真实配置文件。
- 弹框显示实际绝对路径、文件状态、大小、更新时间、JSON 解析错误和格式化配置内容。
- 敏感配置默认以明文显示，方便确认；同时提供临时隐藏敏感值、复制路径、复制 JSON 和刷新功能。
- 桌面端使用居中弹框，手机端使用底部全宽面板；JSON 使用浅色代码区域，支持独立滚动。

### 24. 终态轮询停止与失败提醒

- `/api/accounts/relogin/status` 仅在重新登录运行期间轮询，成功或失败后立即停止。
- 重新登录失败会在账号管理页显示持久提醒，并支持手动关闭；刷新页面后仍能读取上次失败终态。
- `/api/job` 与 `/api/job/logs` 只在注册任务运行或停止收尾期间轮询。
- 点击停止后等待后端返回 `running=false`，随后自动清理轮询定时器；再次启动任务时恢复轮询。

## 主要提交

| 提交 | 内容 |
| --- | --- |
| `4b9f597` | 配置查看弹框文案与浅色 JSON 展示优化 |
| `25002e8` | 重新登录和注册任务进入终态后停止 Web 轮询，增加持久失败提醒 |
| `7a0583c` | 系统设置增加真实配置路径、明文 JSON 与文件信息查看 |
| `df7a1c7` | OutlookEmail 按提交时间过滤旧验证码邮件 |
| `75b288b` | 统一桌面端“查看 / 更多”操作按钮风格 |
| `2d6e051` | 主页面桌面宽屏利用率优化，减少左右空白 |
| `c15c7bc` | 账号操作拆分为“查看 / 更多”，下载和重登录收进更多菜单 |
| `1669edf` | 已注册账号重新登录、SSO 刷新、授权文件恢复与详情弹框 |
| `9f7aa49` | 授权文件存在性检查与 64 KiB StreamingResponse 流式下载 |
| `26a68b0` | CPA / Grok2API 即时导出入口 |
| `c410ff1` | OutlookEmail Web Session Cookie 按 API 主机作用域修复 |
| `ea036e8` | 注册浏览器异常截图、SQLite 记录与账号详情查看 |
| `b2c9e60` | 后端按 web / registration / automation / integrations / mailbox / shared 分包 |
| `600cd61` | README 增加 Linux.do 社区友情链接 |
| `2602538` | OutlookEmail 作为可选 Compose profile 接入 |
| `54d5039` | Docker 宿主机代理映射与 README / 部署文档精简 |
| `3dac2dd` | Docker Compose、Xvfb 有头 Camoufox、本地镜像与 GHCR 自动构建 |
| `786b0ef` | 后端测试、运行数据和日志目录归类 |
| `eed58ad` | 前端迁移到 `front/`，后端与注册核心迁移到 `backend/` |
| `ca3c95a` | 注册实时进度、成功失败统计和账号表格右侧固定查看列 |
| `196bf79` | 设置子菜单、邮箱选项中文化与实际支持说明 |
| `75d37eb` | 无头浏览器开关、Camoufox 紧急终止按钮与进程清理 |
| `3a2c2f1` | 移除 Web 无关的 GUI、CLI 和桌面启动文件 |
| `1a90777` | 唯一管理员账号登录与初始化 |
| `437986c` | 登录、JSON 下载、注册日志改进 |
| `f93cc1b` | OutlookEmail 停用与 CPA JSON 复制 |

## 验证记录

- Python 模块编译：通过。
- Python 单元测试：当前 39 项通过。
- 前端生产构建：`cd front && npm run build` 通过。
- Docker 镜像本地构建：通过。
- Docker Compose 启动与 `/api/health` 健康检查：通过。
- Xvfb 下有头 Camoufox 冒烟：通过，`navigator.webdriver=false`。
- Web 任务 hooks 冒烟测试：通过。
- 账号密码重新登录、Turnstile、SSO 获取、Device Flow 与 CPA/Grok2API 文件重建：真实验证通过。
- CPA/Grok2API 授权文件 64 KiB 分块流式读取：实际文件完整性验证通过。
- GitHub Actions 默认分支 Docker 构建与 GHCR 发布：通过。
- `8787` 服务：不由代码自动启动；检查时保持用户现有服务状态。

## 后续追加规则

- 新增明显功能或完成一组明确需求后，更新本文档的“已完成需求”“主要提交”和“验证记录”。
- 完成验证后提交 Git，并在文档中记录提交号。
- 不自动启动或重启 Web 服务，除非用户明确要求。
- 修改前先检查当前工作区和已有提交，保留用户未提交的独立改动。
