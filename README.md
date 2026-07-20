# 智能桌面魔方前端

更新时间：2026-05-28

智能桌面魔方前端基于 Vue 3 + TypeScript + Vite 构建，用于展示和管理桌面魔方 IoT 设备。当前版本已经接入后端核心接口，支持登录注册、设备管理、实时数据监控、远程控制、AI 分析和日志中心。

## 当前状态

前端已经完成 MVP 演示闭环，并在最近一轮进行了界面视觉优化：

- 全局深色仪表盘主题、玻璃面板、流光边线和扫描背景。
- 登录、注册、主框架、控制台、设备管理、控制面板、AI 分析、日志中心统一视觉风格。
- 设备卡片、传感器卡片、控制开关、颜色选择器增加 hover、状态光和更强的交互反馈。
- API 响应已适配后端统一结构 `{ code, message, data }`。
- AI 分析页已接入评分、风险预警、智能建议、周报接口。
- 日志中心已接入操作日志、语音日志接口。
- 管理员后台页面文件保留，当前正在开发中，不作为 MVP 演示主入口。

最近验证结果：

```bash
npm run build
npx eslint .
npm run test:unit -- --run
```

以上命令均已通过。构建时存在 Vite 大 chunk 提醒，主要来自 ECharts / Element Plus 依赖体积，不影响当前运行。

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
| 登录 | `/login` | 用户登录、一键演示模式 |
| 注册 | `/register` | 用户注册、密码一致性校验 |
| 控制台 | `/dashboard` | 设备概览、实时传感器数据、快捷控制、趋势图、燃气告警 |
| 设备管理 | `/devices` | 设备搜索、筛选、排序、绑定、解绑、跳转控制 |
| 控制面板 | `/control` | 灯光、颜色、亮度、继电器、蜂鸣器、专注模式、屏幕亮度、控制日志 |
| AI 分析 | `/ai-analysis` | 环境评分、风险预警、智能建议、周报图表 |
| 日志中心 | `/logs` | 操作日志、语音日志 |
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
│   ├── composables/
│   │   └── useWebSocket.ts
│   ├── router/
│   │   └── index.ts
│   ├── store/
│   │   ├── auth.ts
│   │   └── device.ts
│   ├── utils/
│   │   ├── demo.ts
│   │   └── format.ts
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
    └── App.spec.ts
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
npx eslint .
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

公网演示使用单域名 `https://tianmuzc.site`：前端运行在 `4173`，Caddy 监听 `127.0.0.1:8080` 并把 `/api/*`、`/ws`、`/health`、`/firmware/*` 转发到后端 `8000`。这种模式下 `VITE_WS_BASE_URL` 保持为空，浏览器会自动连 `wss://tianmuzc.site/ws`。

## 还需要继续做

| 优先级 | 事项 | 说明 |
|---|---|---|
| 高 | 实机联调 | ESP32-S3 握手、心跳、数据上报、控制轮询、ACK 回传 |
| 高 | WebSocket 真实数据流测试 | 用硬件或模拟脚本验证实时刷新、断线重连、订阅切换 |
| 高 | 演示数据脚本 | 自动创建用户、设备、传感器历史数据、风险数据 |
| 中 | 前端测试扩展 | 按需补登录、设备、控制、AI、日志主流程测试 |
| 开发中 | 告警闭环 | 告警中心或告警持久化展示已砍出当前 MVP |
| 开发中 | 生产部署 | 前端静态部署、后端 CORS/API 地址、Nginx 代理已砍出当前 MVP |
| 低 | 分包优化 | 对 ECharts、Element Plus 做路由级懒加载或 chunk 拆分 |

## 当前注意点

- 当前 UI 已经偏“炫酷仪表盘”风格，但仍保持操作台布局，不是营销落地页。
- 构建产物中 ECharts 和 Element Plus chunk 较大，后续可做动态导入优化。
- 管理员后台文件保留但入口正在开发中，不作为当前 MVP 演示范围。
- 硬件未联调前，真实实时数据、控制 ACK、MQTT 链路仍需要现场验证。
