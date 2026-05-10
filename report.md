# 智能桌面魔方 - 前端 MVP Demo 汇报

> 生成时间：2026-04-26  
> 依据文档：`MVP_DEMO方案_优化版.md` (v2.0) + `智能桌面魔方_项目规范_v1.0.md`  
> 项目路径：`C:\Users\MZH\Desktop\tianmu`

---

## 一、项目概述

本项目是智能桌面魔方 IoT 设备管理平台的前端 MVP Demo，基于 **Vue 3 + TypeScript + Element Plus + ECharts** 构建，提供用户认证、设备管理、传感器实时监控、远程控制等核心功能。后端通过 REST API + WebSocket 与前端通信。

---

## 二、技术栈

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 框架 | Vue 3 | 3.5+ | 组合式 API (Composition API) |
| 构建 | Vite | 8.0+ | 快速开发服务器和打包 |
| 语言 | TypeScript | 6.0+ | 类型安全 |
| UI | Element Plus | 2.13+ | PC 端组件库 |
| 图表 | ECharts | 6.0+ | 实时折线图 |
| 状态 | Pinia | 3.0+ | 全局状态管理 |
| 路由 | Vue Router | 5.0+ | 页面导航 + 路由守卫 |
| HTTP | Axios | 1.15+ | REST API 请求封装 |
| WebSocket | 原生 API | - | 实时数据推送 |

---

## 三、项目结构

```
tianmu/
├── .env                              # 环境变量（API/WebSocket 地址）
├── package.json                      # 依赖清单
└── src/
    ├── main.ts                       # 应用入口：初始化 Vue + Pinia + Router + Element Plus
    ├── App.vue                       # 根组件：仅 router-view
    ├── router/
    │   └── index.ts                  # 路由配置 + 鉴权守卫
    ├── api/
    │   ├── index.ts                  # Axios 实例：Token 拦截器 + 401 处理
    │   ├── auth.ts                   # 认证 API：注册/登录/登出
    │   └── device.ts                 # 设备 API：列表/绑定/数据/控制
    ├── store/
    │   ├── auth.ts                   # 认证状态：Token/用户名/角色（localStorage 持久化）
    │   └── device.ts                 # 设备状态：设备列表/选中设备
    ├── composables/
    │   └── useWebSocket.ts           # WebSocket 封装：连接/认证/消息分发/自动清理
    ├── utils/
    │   └── format.ts                 # 工具函数：时间/数值/百分比格式化
    ├── assets/styles/
    │   ├── main.css                  # 全局样式：暗色主题变量 + 通用动画
    │   └── element-overrides.css     # Element Plus 暗色主题覆盖
    └── views/
        ├── Login.vue                 # 登录页（含一键演示模式）
        ├── Register.vue              # 注册页（含密码一致性校验）
        ├── Dashboard.vue             # 控制台：设备列表 + 实时数据 + ECharts 趋势图
        └── Control.vue               # 控制面板：灯光/蜂鸣器/继电器/专注模式
```

---

## 四、4 个 MVP 页面功能说明

### 4.1 登录页 `/login`

| 功能 | 说明 |
|------|------|
| 用户名/密码登录 | 表单校验 → 调用后端 `/api/v1/auth/login` → 存储 JWT → 跳转控制台 |
| 一键演示模式 | 不经过后端，直接设置管理员 Token 和用户名，适用于竞赛演示 |
| 注册链接 | 跳转到注册页 |

### 4.2 注册页 `/register`

| 功能 | 说明 |
|------|------|
| 注册表单 | 用户名(3-50 字符)、密码(最少 6 位)、确认密码 |
| 密码一致性校验 | 自定义校验器，两次输入不一致时阻止提交 |
| 注册成功跳转 | 延迟 1 秒后跳转到登录页 |

### 4.3 控制台页 `/dashboard`（核心演示页）

| 功能 | 说明 |
|------|------|
| 统计卡片 | 设备总数 / 在线数 / 离线数 |
| 设备列表表格 | 设备 ID、名称、状态(标签)、芯片型号、固件版本、最后在线时间 |
| 绑定设备 | 弹出对话框输入设备 ID 和名称 → 调用 `/api/v1/device/bind` |
| 实时数据展示 | 6 项传感器指标：温度/湿度/光照/AQI/CO₂/TVOC |
| ECharts 趋势图 | 温度+湿度+光照三条折线，实时更新（最多 60 个数据点） |
| WebSocket 推送 | 订阅 `sensor_data` → 实时更新数据和图表；订阅 `device_status` → 刷新设备列表 |
| 跳转到控制面板 | 点击"控制"按钮，携带设备 ID 跳转 |

### 4.4 控制面板页 `/control`

| 功能 | 说明 |
|------|------|
| 设备选择 | 下拉框选择目标设备，显示在线状态 |
| 灯光开关 | Switch 开关 → `light: on/off` |
| 灯光颜色 | 4 色选择器 → `light_color: red/green/blue/white` |
| 灯光亮度 | 滑块 0-100 → `light_brightness: 0-100` |
| 蜂鸣器 | Switch 开关 → `buzzer: on/off` |
| 继电器 1 | Switch 开关 → `relay_1: on/off` |
| 专注模式 | Switch 开关 → `focus_mode: on/off` |
| 控制日志 | 表格记录最近 20 条操作：时间/指令/值/状态 |

---

## 五、前后端接口对照

| 前端操作 | 后端 API | 认证方式 |
|---------|---------|---------|
| 用户登录 | `POST /api/v1/auth/login` | 无 |
| 用户注册 | `POST /api/v1/auth/register` | 无 |
| 获取设备列表 | `GET /api/v1/device/list` | JWT Token |
| 绑定设备 | `POST /api/v1/device/bind` | JWT Token |
| 获取最新传感器数据 | `GET /api/v1/data/{id}/latest` | JWT Token |
| 下发控制指令 | `POST /api/v1/control/{id}` | JWT Token |
| WebSocket 连接 | `ws://localhost:8000/ws` | URL 参数 Token |

---

## 六、关键设计

| 设计 | 方案 |
|------|------|
| 认证状态持久化 | JWT Token 存 localStorage，刷新页面不丢失登录 |
| 路由守卫 | `beforeEach` 检查认证状态，未登录跳转 `/login` |
| 请求拦截器 | Axios 自动附加 `Authorization: Bearer <Token>` |
| 401 处理 | Token 过期自动清除并跳转登录页 |
| WebSocket 消息分发 | 基于 `type` 字段的回调映射表，支持多种消息类型 |
| 组件卸载清理 | `onUnmounted` 自动断开 WebSocket，销毁 ECharts 实例 |
| 设备选中 | 从路由 query 参数传递设备 ID（Dashboard → Control） |

---

## 七、MVP 交付检查清单

- [x] 登录页（含表单校验 + 一键演示）
- [x] 注册页（含密码一致性校验）
- [x] Dashboard：设备卡片（在线/离线统计）
- [x] Dashboard：实时数据展示（6 项指标）
- [x] Dashboard：ECharts 折线图（WebSocket 驱动实时更新）
- [x] 控制面板：灯光开关/颜色/亮度
- [x] 控制面板：蜂鸣器/继电器/专注模式
- [x] 控制日志（本地记录最近 20 条）
- [x] 路由鉴权守卫
- [x] API 拦截器（Token 自动附加 + 401 处理）
- [x] 所有文件含完整注释
- [x] `.env` 环境配置

---

## 八、启动方式

```bash
cd C:\Users\MZH\Desktop\tianmu

# 安装依赖（如果尚未安装）
npm install

# 启动开发服务器
npm run dev
```

启动后访问 `http://localhost:5173`。

**一键演示模式**：登录页点击"一键演示(管理员)"，无需后端即可进入系统查看界面。

**连接后端模式**：确保后端 `uvicorn app.main:app --reload` 已启动，然后正常输入用户名密码登录。

---

## 九、与完整项目的差距

根据 `智能桌面魔方_项目规范_v1.0.md`，当前前端 vs 完整规范的差距：

| 缺失页面/功能 | 规范章节 | 说明 |
|-------------|---------|------|
| 设备详情页 `/devices/:id` | 3.5 节 | 实时数据 + 历史图表 + 阈值配置 + 设备信息 |
| 设备列表页 `/devices` | 3.5 节 | 独立设备列表页（含筛选/搜索/解绑） |
| 操作日志页 `/logs/operation` | 3.5 节 | 操作日志列表 + 筛选 + 导出 |
| 语音日志页 `/logs/voice` | 3.5 节 | 语音日志 + 重新执行 |
| AI 分析页 `/ai` | 3.5 节 | 舒适度评分 + AI 建议 + 周报 |
| 管理员页 `/admin/*` | 3.5 节 | 用户管理 + 设备管理 + 系统概览 |
| 个人设置页 `/settings` | 3.5 节 | 修改密码 + 通知 + 主题 |
| 分页/历史数据查询 | 6.3.3 节 | 前端需支持分页组件 |
| 批量控制 | 6.3.4 节 | 批量下发控制指令 |
| 控制历史 | 6.3.4 节 | 查看历史控制记录 |

> 这些功能在 MVP Demo 阶段不需要实现，属于完整项目的后续迭代内容。
