# 智能桌面魔方 - MVP Demo 方案

> 版本：v1.0
> 更新：2026-04-24
> 目标：一天完成可演示的最小系统

---

## 一、目标与范围

### 1.1 核心演示效果

| # | 效果 | 技术实现 |
|---|------|---------|
| 1 | 设备绑定 + 在线状态显示 | REST API |
| 2 | 传感器数据实时推送（WebSocket） | WebSocket 推送 |
| 3 | 网页下发控制指令（灯光开关） | REST API → 硬件轮询 |

### 1.2 一天时间分配

| 时间 | 任务 | 产出 |
|------|------|------|
| 0-1h | 搭建项目架子（前后端骨架） | 可运行空项目 |
| 1-3h | 后端核心 API（认证+设备+数据+控制） | 8个接口 |
| 3-4h | WebSocket 实时推送 | 硬件可对接 |
| 4-6h | 前端：登录 + 控制台（设备卡片+图表） | 可操作的界面 |
| 6-7h | 前端：控制面板（开关灯） | 演示效果 |
| 7-8h | 联调测试 + 硬件对接 | 可演示的 Demo |

### 1.3 不做的功能（砍掉）

- ❌ AI 分析 / 舒适度评分
- ❌ 语音日志 / TTS
- ❌ 管理员后台
- ❌ 历史数据导出
- ❌ 周报生成
- ❌ 微信推送
- ❌ 天气 API
- ❌ 阈值告警

---

## 二、数据库设计（最简3表）

### users（用户表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 主键 |
| username | VARCHAR(50) | UNIQUE, NOT NULL | 用户名 |
| password | VARCHAR(255) | NOT NULL | 密码哈希（bcrypt） |
| role | VARCHAR(20) | DEFAULT 'user' | admin/user |
| is_active | BOOLEAN | DEFAULT True | 是否启用 |
| created_at | DATETIME | DEFAULT NOW | 创建时间 |

### devices（设备表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 主键 |
| device_id | VARCHAR(64) | UNIQUE, NOT NULL | 设备唯一ID（MAC地址） |
| device_name | VARCHAR(100) | | 设备名称（可自定义） |
| token | VARCHAR(128) | | 鉴权Token（握手获取） |
| status | VARCHAR(20) | DEFAULT 'offline' | online/offline |
| chip_model | VARCHAR(50) | | 芯片型号（如 ESP32-S3） |
| firmware_version | VARCHAR(20) | | 固件版本 |
| bound_user_id | INTEGER | FK → users.id | 绑定用户 |
| last_seen | DATETIME | | 最后在线时间 |
| created_at | DATETIME | DEFAULT NOW | 添加时间 |

### sensor_data（传感器数据表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 主键 |
| device_id | VARCHAR(64) | FK, INDEX | 设备ID |
| temperature | DOUBLE | | 温度（℃） |
| humidity | DOUBLE | | 湿度（%RH） |
| illuminance | DOUBLE | | 光照强度（lx） |
| aqi | DOUBLE | | 空气质量指数 |
| tvoc | DOUBLE | | 有机挥发物浓度 |
| eco2 | DOUBLE | | CO2等效浓度（ppm） |
| mold_risk | DOUBLE | | 霉菌风险等级（0-3） |
| gas | DOUBLE | | 燃气浓度（>0=泄漏） |
| wifi_rssi | INTEGER | | WiFi信号强度（dBm） |
| power_voltage | DOUBLE | | 供电电压（V） |
| focus_mode | BOOLEAN | | 专注模式状态 |
| timestamp | DATETIME | NOT NULL | 数据时间 |
| created_at | DATETIME | DEFAULT NOW | 记录时间 |

### device_control（设备控制指令表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 主键 |
| device_id | VARCHAR(64) | INDEX | 设备ID |
| command | VARCHAR(50) | NOT NULL | 指令类型 |
| value | VARCHAR(50) | | 指令值 |
| pending | BOOLEAN | DEFAULT True | 是否待执行 |
| executed_at | DATETIME | | 执行时间 |
| created_at | DATETIME | DEFAULT NOW | 创建时间 |

---

## 三、硬件对接协议（完整版）

硬件团队**必须**按以下协议对接，无需关心 MQTT细节（后端内部处理）。

### 3.1 协议类型枚举

```
handshake         = 设备握手请求
handshake_ack     = 握手响应
data_report       = 传感器数据上报
data_report_ack   = 数据上报响应
heartbeat         = 设备心跳包
heartbeat_ack     = 服务器心跳响应
control_pull      = 设备主动拉取控制指令
control_pull_ack  = 控制指令响应
```

### 3.2 流程总览

```
1. 设备上电 → 握手请求 → 获取 Token
2. 定时心跳 → 携带设备状态
3. 定时数据上报 → 服务器响应
4. 设备定时拉取控制指令 → 执行指令
```

---

### 3.3 Step 1：设备握手（MQTT → 后端）

**设备发送握手请求**（POST 或 MQTT publish）：

```json
{
  "device_id": "AABBCCDDEEFF",
  "timestamp": 1713880000,
  "type": "handshake",
  "chip_model": "ESP32-S3",
  "version": "1.0.0"
}
```

**服务器响应**：

```json
{
  "code": 200,
  "type": "handshake_ack",
  "msg": "握手成功",
  "timestamp": 1713880001,
  "token": "dev_abc123xyz",
  "expire_time": 86400
}
```

> `token` 后续所有请求必须携带。过期后重新握手。

---

### 3.4 Step 2：心跳包（定期发送，建议 30s）

**设备发送**：

```json
{
  "device_id": "AABBCCDDEEFF",
  "token": "dev_abc123xyz",
  "timestamp": 1713880030,
  "type": "heartbeat",
  "status": {
    "wifi_connected": true,
    "mqtt_connected": true,
    "screen_normal": true,
    "sensor_normal": true,
    "focus_mode": false,
    "power_voltage": 3.30
  }
}
```

**服务器响应**：

```json
{
  "code": 200,
  "type": "heartbeat_ack",
  "msg": "ok",
  "timestamp": 1713880031
}
```

---

### 3.5 Step 3：传感器数据上报（建议 5s 一次）

**设备发送**：

```json
{
  "device_id": "AABBCCDDEEFF",
  "token": "dev_abc123xyz",
  "timestamp": 1713880035,
  "type": "data_report",
  "data": {
    "temperature": 25.6,
    "humidity": 60.5,
    "illuminance": 500.0,
    "aqi": 35.0,
    "tvoc": 0.12,
    "eco2": 450.0,
    "mold_risk": 0.0,
    "gas": 0.0,
    "version": "1.0.0"
  },
  "status": {
    "wifi_connected": true,
    "mqtt_connected": true,
    "screen_normal": true,
    "sensor_normal": true,
    "power_voltage": 3.30,
    "focus_mode": false
  }
}
```

**服务器响应**：

```json
{
  "code": 200,
  "type": "data_report_ack",
  "msg": "数据接收成功",
  "timestamp": 1713880036,
  "receive_status": true
}
```

---

### 3.6 Step 4：设备拉取控制指令（建议 3s 一次）

**设备发送**（GET 请求）：

```
GET /api/v1/control/{device_id}/pull?token={token}
```

**服务器响应**：

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "pending": true,
    "command": "light",
    "value": "on",
    "params": {}
  }
}
```

> `pending: false` 表示无待执行指令，设备跳过。

**设备执行完成后通知服务器**（可选，用于状态回传）：

```json
{
  "device_id": "AABBCCDDEEFF",
  "token": "dev_abc123xyz",
  "timestamp": 1713880040,
  "type": "control_ack",
  "command": "light",
  "result": "success"
}
```

---

### 3.7 支持的控制指令

| command | value 示例 | 说明 |
|---------|-----------|------|
| `light` | `on` / `off` | 灯光开关 |
| `light_color` | `red` / `green` / `blue` / `white` | 灯光颜色 |
| `light_brightness` | `0`-`100` | 灯光亮度 |
| `buzzer` | `on` / `off` | 蜂鸣器 |
| `relay_1` | `on` / `off` | 继电器1 |
| `relay_2` | `on` / `off` | 继电器2（如果有） |
| `focus_mode` | `on` / `off` | 专注模式 |
| `screen_brightness` | `0`-`100` | 屏幕亮度 |

---

### 3.8 错误码（设备侧）

| code | 说明 | 处理方式 |
|------|------|---------|
| 200 | 成功 | - |
| 400 | 数据格式错误 | 检查 JSON 格式 |
| 401 | Token无效 | 重新握手获取 Token |
| 402 | 响应超时 | 重试 |
| 403 | 设备未授权 | 检查设备是否已绑定 |
| 500 | 服务器错误 | 联系后端 |

---

## 四、后端 API 接口（8个）

### 4.1 用户认证

#### POST /api/v1/auth/register

```json
// 请求
{ "username": "test", "password": "123456" }

// 响应 200
{ "code": 0, "message": "注册成功", "data": { "id": 1 } }
```

#### POST /api/v1/auth/login

```json
// 请求
{ "username": "test", "password": "123456" }

// 响应 200
{
  "code": 0,
  "data": {
    "access_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 86400
  }
}
```

---

### 4.2 设备管理

#### POST /api/v1/device/bind

```json
// 请求
{ "device_id": "AABBCCDDEEFF", "device_name": "我的魔方" }

// 响应 200
{ "code": 0, "message": "绑定成功" }
```

#### GET /api/v1/device/list

```json
// 响应 200
{
  "code": 0,
  "data": [
    {
      "device_id": "AABBCCDDEEFF",
      "device_name": "我的魔方",
      "status": "online",
      "last_seen": "2026-04-24T00:00:00Z",
      "chip_model": "ESP32-S3",
      "firmware_version": "1.0.0"
    }
  ]
}
```

---

### 4.3 数据接口

#### POST /api/v1/data/upload（硬件数据上报）

```json
// 请求
{
  "device_id": "AABBCCDDEEFF",
  "token": "dev_abc123xyz",
  "timestamp": 1713880000,
  "type": "data_report",
  "data": {
    "temperature": 25.6,
    "humidity": 60.5,
    "illuminance": 500.0,
    "aqi": 35.0,
    "tvoc": 0.12,
    "eco2": 450.0,
    "mold_risk": 0.0,
    "gas": 0.0,
    "version": "1.0.0"
  },
  "status": {
    "wifi_connected": true,
    "mqtt_connected": true,
    "screen_normal": true,
    "sensor_normal": true,
    "power_voltage": 3.30,
    "focus_mode": false
  }
}

// 响应 200
{ "code": 0, "message": "success", "receive_status": true }
```

#### GET /api/v1/data/{device_id}/latest

```json
// 响应 200
{
  "code": 0,
  "data": {
    "temperature": 25.6,
    "humidity": 60.5,
    "illuminance": 500.0,
    "aqi": 35.0,
    "tvoc": 0.12,
    "eco2": 450.0,
    "mold_risk": 0.0,
    "gas": 0.0,
    "wifi_rssi": -65,
    "timestamp": "2026-04-24T00:00:00Z"
  }
}
```

---

### 4.4 控制接口

#### POST /api/v1/control/{device_id}（下发控制指令）

```json
// 请求（前端调用）
{
  "command": "light",
  "value": "on"
}

// 响应 200
{ "code": 0, "message": "指令已下发" }
```

#### GET /api/v1/control/{device_id}/pull（设备拉取指令）

```json
// 响应 200（有待执行指令）
{
  "code": 0,
  "data": {
    "pending": true,
    "command": "light",
    "value": "on",
    "params": {}
  }
}

// 响应 200（无待执行指令）
{
  "code": 0,
  "data": {
    "pending": false
  }
}
```

---

## 五、WebSocket 实时推送

### 5.1 连接方式

```
ws://host:8000/ws?token={jwt_token}
```

**认证流程**：

```json
// 客户端发送
{ "type": "auth", "token": "eyJ..." }

// 服务端响应
{ "type": "auth_result", "code": 0, "message": "ok" }
```

**心跳（客户端 → 服务端，每 30s）**：

```json
// 客户端发送
{ "type": "ping" }

// 服务端响应
{ "type": "pong" }
```

### 5.2 推送消息类型

| type | 方向 | 说明 |
|------|------|------|
| `sensor_data` | 服务端 → 客户端 | 传感器数据更新（设备上报后立即推送） |
| `device_status` | 服务端 → 客户端 | 设备上下线状态变更 |
| `control_result` | 服务端 → 客户端 | 指令执行结果通知 |

### 5.3 消息示例

**传感器数据推送**：

```json
{
  "type": "sensor_data",
  "data": {
    "device_id": "AABBCCDDEEFF",
    "temperature": 25.6,
    "humidity": 60.5,
    "illuminance": 500.0,
    "aqi": 35.0,
    "wifi_rssi": -65,
    "timestamp": "2026-04-24T00:00:00Z"
  },
  "timestamp": 1713880000000
}
```

**设备状态变更**：

```json
{
  "type": "device_status",
  "data": {
    "device_id": "AABBCCDDEEFF",
    "status": "online"
  },
  "timestamp": 1713880000000
}
```

---

## 六、前端页面（4个页面）

### 6.1 页面清单

| 页面 | 路由 | 说明 |
|------|------|------|
| 登录页 | `/login` | 用户名+密码登录 |
| 注册页 | `/register` | 注册 |
| 控制台 | `/dashboard` | 设备卡片+实时数据+图表 |
| 控制面板 | `/control` | 灯光/蜂鸣器/继电器控制 |

### 6.2 控制台页面

```
┌─────────────────────────────────────────────────────┐
│  控制台                              [用户名] [退出] │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ 设备总数  │ │  在线    │ │  离线    │           │
│  │    3     │ │    2     │ │    1     │           │
│  └──────────┘ └──────────┘ └──────────┘           │
│                                                     │
│  ┌─ 我的设备 ───────────────────────────────┐       │
│  │ [CUBE-001] 🟢在线   温度:25.6℃ 湿度:60% │       │
│  │ [CUBE-002] 🔴离线   最后在线:10分钟前    │       │
│  └──────────────────────────────────────────┘       │
│                                                     │
│  ┌─ 实时数据 (CUBE-001) ────────────────────┐      │
│  │  温度    湿度    光照    AQI    CO2      │      │
│  │  25.6   60.5%   500lx   35     450ppm   │      │
│  └──────────────────────────────────────────┘      │
│                                                     │
│  ┌─ 24小时趋势 ─────────────────────────────┐      │
│  │         [ECharts 折线图]                  │      │
│  │  每5秒自动刷新（WebSocket驱动）          │      │
│  └──────────────────────────────────────────┘      │
│                                                     │
│  [跳转到控制面板 →]                                │
└─────────────────────────────────────────────────────┘
```

### 6.3 控制面板页面

```
┌─────────────────────────────────────────────────────┐
│  控制面板                           [返回控制台]     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  设备选择：[CUBE-001 ▼]  当前状态：🟢在线          │
│                                                     │
│  ┌─ 灯光控制 ──────────────────────────────────┐  │
│  │  开关：[  ●开  ○关 ]                        │  │
│  │  颜色：[🔴][🟢][🔵][⚪]                    │  │
│  │  亮度：━━━━━━●━━━ 70%                      │  │
│  │  [发送指令]                                  │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌─ 其他控制 ──────────────────────────────────┐  │
│  │  蜂鸣器：[  ●开  ○关 ]                     │  │
│  │  继电器1：[  ●开  ○关 ]                    │  │
│  │  专注模式：[  ●开  ○关 ]                    │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌─ 控制日志 ──────────────────────────────────┐  │
│  │  14:00:01  灯光→开        ✅成功           │  │
│  │  14:00:05  灯光→红色      ✅成功           │  │
│  │  14:00:10  蜂鸣器→关      ✅成功           │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 七、前后端接口对照

| 硬件动作 | 后端接口 | 前端动作 |
|---------|---------|---------|
| 设备上电发送握手 | 生成 Token | 无需前端 |
| 定时心跳 | 更新设备在线状态 | WebSocket 推送状态变更 |
| 定时上报数据 | 存储数据 | WebSocket 推送最新数据，图表自动更新 |
| 设备拉取指令 | 返回待执行指令 | 无感知 |
| 用户点击开关灯 | POST /control/{id} | 显示发送成功/失败 |
| 设备执行后无回传 | - | 前端显示"已发送"（不等待确认） |

---

## 八、环境变量

### 8.1 后端 .env（MVP 最小配置）

```env
DEBUG=true
DATABASE_URL=sqlite:///./data/cube.db

SECRET_KEY=mvp-secret-key-2026
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# MQTT（硬件对接用）
MQTT_BROKER_URL=127.0.0.1
MQTT_BROKER_PORT=1883
```

### 8.2 前端 .env

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_BASE_URL=ws://localhost:8000
```

---

## 九、依赖清单

### 9.1 后端（requirements.txt）

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
aiosqlite==0.19.0
pydantic==2.5.3
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
aiomqtt==2.0.0
httpx==0.26.0
python-multipart==0.0.6
loguru==0.7.2
python-dotenv==1.0.0
```

### 9.2 前端（package.json）

```json
{
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.0",
    "pinia": "^2.1.0",
    "element-plus": "^2.5.0",
    "echarts": "^5.5.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "typescript": "^5.3.0",
    "@vitejs/plugin-vue": "^5.0.0",
    "vite-plugin-electron": "^0.28.0"
  }
}
```

---

## 十、MVP 交付检查清单

- [ ] 用户可以注册/登录
- [ ] 用户可以绑定设备（DID）
- [ ] 控制台显示所有设备及状态
- [ ] 控制台实时显示传感器数据（WebSocket 推送）
- [ ] 24小时折线图正常渲染（ECharts）
- [ ] 用户可以下发灯光开关指令
- [ ] 硬件按协议上报数据后页面实时更新
- [ ] 设备离线状态正确显示