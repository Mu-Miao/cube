# 智能桌面魔方前端

更新时间：2026-07-27

智能桌面魔方前端基于 Vue 3 + TypeScript + Vite 构建，用于展示和管理桌面魔方 IoT 设备。当前版本已经接入后端核心接口，支持登录注册、设备管理、实时数据监控、远程控制、AI 分析和日志中心。

## 当前状态

前端已经完成三套界面共存的 MVP 演示闭环，并在最近一轮补充了实时硬件状态、趋势数据和构建体积优化：

- `/public` 为默认大众版入口，`/senior` 为长辈版，`/teen/*` 为需要登录的完整控制台。
- 登录、注册与三套界面共用后端认证和设备数据。
- 设备卡片、传感器卡片、控制开关、颜色选择器增加 hover、状态光和更强的交互反馈。
- API 响应已适配后端统一结构 `{ code, message, data }`。
- 后端校验错误会转换成可读的中文字段提示，版本 API 客户端也能处理纯文本或非标准 JSON 错误。
- 大众版、长辈版和完整控制台均接入 WebSocket 实时传感器数据与硬件控制状态。
- WebSocket 在登录后携带最新 Token 建连，连接建立前的订阅会排队发送，退出登录时主动断开。
- 控制台趋势图改用后端分桶聚合接口，支持 1 小时、6 小时、24 小时和 7 天范围。
- 灯光、亮度、色温、通知、专注模式和屏幕亮度会按设备心跳或最新数据同步，避免页面状态与实机状态脱节。
- 时间显示统一使用 Asia/Shanghai（UTC+8）。
- AI 分析页已接入评分、风险预警、智能建议、周报接口。
- 日志中心已接入操作日志、语音日志接口。
- ESP32-S3 实机联调已完成，包括握手、心跳、数据上报、控制轮询和 ACK 回传。
- Element Plus、ECharts 和部分重组件改为按路由或按需加载；ECharts 只注册当前使用的图表、组件和 Canvas 渲染器，图片资源已压缩。
- 管理员后台页面文件保留，当前正在开发中，不作为 MVP 演示主入口。

最近验证结果：

```bash
npm run build
npx eslint src
npm run test:unit -- --run
```

当前前端 2 个测试文件、5 项单元测试通过，类型检查与生产构建通过。

详细的首屏优化说明和最近一次构建结果见 [`PERFORMANCE_OPTIMIZATION.md`](./PERFORMANCE_OPTIMIZATION.md)。

## 技术栈

| 类型 | 技术 |
|---|---|
| 框架 | Vue 3 |
| 语言 | TypeScript |
| 构建工具 | Vite |
| UI 组件 | Element Plus |
| 图表 | ECharts |
| 状态管理 | Pinia |
| 路由 | Vue Router |
| HTTP | Axios |
| 实时通信 | WebSocket |
| 测试 | Vitest |

## 快速启动

```bash
cd /Users/sensen/Desktop/cube/tianmu
npm install
npm run dev
```

默认访问：

```text
http://localhost:5173
```

如果 5173 被占用，可以换端口：

```bash
npm run dev -- --port 5174
```

## 环境变量

复制 `.env.example` 后按实际后端地址修改：

```bash
cp .env.example .env
```

| 变量 | 默认值 | 说明 |
|---|---|---|
| `VITE_API_BASE_URL` | `/api/v1` | REST API 基础路径 |
| `VITE_WS_BASE_URL` | 空 | WebSocket 地址；为空时自动使用当前域名的 `/ws` |
| `VITE_APP_TITLE` | `智能桌面魔方 MVP` | 应用标题 |
| `VITE_APP_VERSION` | `1.0.0` | 前端版本 |

## 页面功能

| 页面 | 路由 | 说明 |
|---|---|---|
| 大众版 | `/public`（默认） | 轻量日常查看、登录注册、设备与建议 |
| 长辈版 | `/senior` | 大字号、简化交互、设备状态与健康建议 |
| 登录 | `/login` | 使用大众版界面完成登录 |
| 注册 | `/register` | 使用大众版界面完成注册和输入校验 |
| 控制台 | `/teen/dashboard` | 设备概览、实时传感器数据、快捷控制、趋势图、燃气告警 |
| 设备管理 | `/teen/devices` | 设备搜索、筛选、排序、绑定、解绑、跳转控制 |
| 控制面板 | `/teen/control` | 灯光、颜色、亮度、继电器、蜂鸣器、专注模式、屏幕亮度、控制日志 |
| AI 分析 | `/teen/ai-analysis` | 环境评分、风险预警、智能建议、周报图表 |
| 日志中心 | `/teen/logs` | 操作日志、语音日志 |
| 管理员后台 | 开发中 | 页面文件保留，当前不作为 MVP 演示主入口 |

## 项目结构

```text
tianmu/
├── README.md
├── package.json
├── vite.config.ts
├── vitest.config.ts
├── playwright.config.ts
├── .env.example
├── src/
│   ├── main.ts
│   ├── App.vue
│   ├── api/
│   │   ├── index.ts          # Axios 实例、Token 注入、响应解包
│   │   ├── errors.ts         # 后端错误与字段校验信息格式化
│   │   ├── auth.ts           # 登录、注册
│   │   ├── device.ts         # 设备、数据、控制接口
│   │   ├── ai.ts             # AI 评分、建议、风险、周报
│   │   ├── log.ts            # 操作日志、语音日志
│   │   └── admin.ts          # 管理员统计、用户、设备接口
│   ├── assets/styles/
│   │   ├── main.css          # 全局主题变量、背景、动画、工具类
│   │   └── element-overrides.css
│   ├── components/
│   │   ├── AppLayout.vue
│   │   ├── DeviceOverviewCard.vue
│   │   ├── SensorCard.vue
│   │   ├── SensorMiniCard.vue
│   │   ├── ControlToggle.vue
│   │   ├── LightColorPicker.vue
│   │   ├── GasAlertBanner.vue
│   │   └── DeviceStatusDot.vue
│   ├── plugins/
│   │   └── elementPlus.ts    # Teen 路由按需注册 Element Plus
│   ├── versions/
│   │   ├── public/           # 大众版
│   │   └── senior/           # 长辈版
│   ├── composables/
│   │   └── useWebSocket.ts
│   ├── router/
│   │   └── index.ts
│   ├── store/
│   │   ├── auth.ts
│   │   └── device.ts
│   ├── utils/
│   │   ├── demo.ts
│   │   ├── format.ts
│   │   └── slimEcharts.ts    # 按需注册 ECharts 图表、组件和渲染器
│   └── views/
│       ├── Login.vue
│       ├── Register.vue
│       ├── Dashboard.vue
│       ├── Devices.vue
│       ├── Control.vue
│       ├── AiAnalysis.vue
│       ├── LogCenter.vue
│       └── AdminPanel.vue
└── src/__tests__/
    ├── App.spec.ts
    └── version-api-client.spec.ts
```

## 常用命令

```bash
# 启动开发服务器
npm run dev

# 类型检查 + 生产构建
npm run build

# 单元测试
npm run test:unit -- --run

# ESLint 检查
npx eslint src
```

## 演示模式

登录页点击“一键演示（管理员）”可以不依赖真实后端进入系统，用于答辩、现场演示或前端 UI 检查。

演示模式会启用管理员菜单，因此可以直接查看：

- 控制台
- 设备管理
- 控制面板
- AI 分析
- 日志中心
- 管理员后台文件保留，当前正在开发中，不作为 MVP 演示范围

## 与后端联调

后端默认运行在：

```text
http://localhost:8000
ws://localhost:8000/ws
```

前端通过 `.env` 中的 `VITE_API_BASE_URL` 和 `VITE_WS_BASE_URL` 连接后端。开发环境如果走 Vite 代理，可保持 `VITE_API_BASE_URL=/api/v1`。

### 单域名部署

生产预览可运行在 `127.0.0.1:4173`，再使用后端仓库的 `scripts/tianmu_proxy.py` 统一代理前后端：

```bash
# 终端 1：前端
npm run build
npm run preview -- --host 127.0.0.1 --port 4173

# 终端 2：后端（在 backend/ 目录）
uvicorn app.main:app --host 127.0.0.1 --port 8000

# 终端 3：Python 代理（在 backend/ 目录）
/opt/miniconda3/envs/backend/bin/python scripts/tianmu_proxy.py
```

Python 代理监听 `127.0.0.1:8080`：`/api/*`、`/ws`、`/health` 和 `/firmware/*` 转到后端 `8000`，其他请求转到前端 `4173`。外层隧道或网关只需指向 `8080`。代理脚本本身不保存域名账号、证书或隧道密钥；这些信息应留在部署平台或本机环境中。

同域部署时保持 `VITE_API_BASE_URL=/api/v1`、`VITE_WS_BASE_URL` 为空，浏览器会自动使用当前域名的 `/api/v1` 和 `ws(s)://当前域名/ws`。使用自定义公网域名时，还需要把该域名加入 `vite.config.ts` 的 `allowedHosts`。

## 还需要继续做

| 优先级 | 事项 | 说明 |
|---|---|---|
| 高 | WebSocket 公网稳定性复核 | 按实际域名持续验证断线重连、订阅恢复和多页面切换 |
| 中 | 前端测试扩展 | 按需补登录、设备、控制、AI、日志主流程测试 |
| 开发中 | 告警闭环 | 告警中心或告警持久化展示已砍出当前 MVP |
| 中 | 公网部署复核 | 按实际域名验证 HTTPS、API、WebSocket 和 OTA 下载 |
| 低 | 网络加载复核 | 按生产网络瀑布图继续检查 Element Plus、字体和图片资源 |

## 当前注意点

- 当前 UI 已经偏“炫酷仪表盘”风格，但仍保持操作台布局，不是营销落地页。
- ECharts 已改为按需模块并拆分加载，Element Plus 进入对应功能页时仍需下载相关 chunk。
- 管理员后台文件保留但入口正在开发中，不作为当前 MVP 演示范围。
- ESP32-S3 实机数据、控制和 OTA 主链路已经联调；后续重点是 WebSocket 公网稳定性和部署复核。
