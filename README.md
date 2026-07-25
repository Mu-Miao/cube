# 智能桌面魔方 - 后端服务

更新时间：2026-07-26

基于 FastAPI + SQLAlchemy + MQTT + WebSocket 的 IoT 后端，为智能桌面魔方硬件设备提供设备管理、传感器数据采集、远程控制、告警检测等服务。

## 当前状态

后端已经完成 MVP 演示所需的主要服务能力：

- 用户注册、登录、JWT 鉴权、管理员权限校验。
- 设备握手、心跳、绑定、解绑、列表、重命名。
- 传感器数据上报、最新数据查询、历史数据查询。
- 远程控制指令下发、设备拉取指令、执行结果 ACK。
- 操作日志和语音日志查询/记录。
- 管理员用户管理、设备管理、系统统计。
- AI 分析接口：环境综合评分、风险预警、智能建议、周报数据。
- MQTT 设备消息处理。
- OTA 固件上传、版本检查、MQTT 更新推送、MD5 校验和设备结果回传；已完成 ESP32-S3 实机更新验证。
- WebSocket 实时推送传感器数据、设备状态、控制结果和告警。

最近验证结果：

```bash
python -m pytest tests/
```

测试通过，当前测试覆盖认证、设备、数据、控制、OTA、AI 分析等核心流程。

## 技术栈

- **Web 框架**: FastAPI + Uvicorn
- **数据库**: SQLite (aiosqlite 异步)
- **认证**: JWT (python-jose) + bcrypt
- **设备通信**: MQTT (aiomqtt) + HTTP 轮询
- **实时推送**: WebSocket
- **外部服务**: httpx 异步 HTTP 客户端

## 项目结构

```
backend/
├── app/
│   ├── main.py                      # FastAPI 入口 + WebSocket 端点
│   ├── config.py                    # Pydantic Settings 配置
│   ├── api/
│   │   ├── deps.py                  # 依赖注入（JWT 认证 / 管理员权限）
│   │   └── v1/
│   │       ├── auth.py              # 注册 / 登录
│   │       ├── device.py            # 握手 / 心跳 / 绑定 / 解绑 / 列表 / 重命名
│   │       ├── data.py              # 数据上报 / 最新 / 历史
│   │       ├── control.py           # 控制指令下发 / 拉取 / ACK
│   │       ├── log.py               # 操作日志 / 语音日志 查询与创建
│   │       ├── admin.py             # 管理员 API（用户/设备管理/统计）
│   │       ├── ai.py                # AI 分析（评分/风险/建议/周报）
│   │       └── ota.py               # 固件上传、MQTT OTA 推送、推送日志
│   ├── models/
│   │   ├── user.py                  # 用户（含 role 字段）
│   │   ├── device.py                # 设备
│   │   ├── sensor_data.py           # 传感器数据
│   │   ├── operation_log.py         # 操作日志
│   │   ├── voice_log.py             # 语音日志
│   │   └── ota_log.py               # OTA 推送与设备确认结果
│   ├── schemas/                     # Pydantic 请求/响应模型
│   ├── services/
│   │   ├── auth_service.py          # JWT 编解码 / 密码哈希
│   │   ├── device_service.py        # 设备解绑逻辑
│   │   ├── data_service.py          # 数据查询服务层
│   │   ├── alert_service.py         # 告警阈值检测
│   │   ├── cleanup_service.py       # 过期数据清理
│   │   ├── tts_service.py           # 语音合成（正在开发中，非 MVP）
│   │   ├── weather_service.py       # 天气服务（正在开发中，非 MVP）
│   │   └── wechat_service.py        # 企业微信推送（正在开发中，非 MVP）
│   ├── mqtt/
│   │   ├── client.py                # MQTT 客户端
│   │   ├── handlers.py              # MQTT 消息处理
│   │   └── topics.py                # Topic 定义
│   ├── websocket/
│   │   ├── manager.py               # 连接管理 / 消息广播
│   │   └── handlers.py              # 消息类型分发
│   ├── utils/
│   │   └── helpers.py               # 工具函数
│   └── db/
│       └── session.py               # 异步数据库会话
├── scripts/
│   ├── create_admin.py              # 创建管理员账号
│   ├── init_db.py                   # 初始化数据库
│   ├── seed_demo.py                 # 生成本地演示账号、设备和历史数据
│   ├── simulate_ota_device.py       # 模拟版本检查、固件下载、MD5 和 ACK
│   └── tianmu_proxy.py              # 前后端单域名 HTTP/WebSocket 反向代理
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env                             # 环境变量配置
```

## 快速开始

### 环境要求

- Python 3.13+
- MQTT Broker（默认使用公共 broker.emqx.io）
- 推荐使用虚拟环境或 Conda 环境隔离依赖

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python scripts/init_db.py

# 启动服务
uvicorn app.main:app --reload --port 8000
```

访问 `http://localhost:8000/docs` 查看 Swagger API 文档。

### 前后端单域名代理

`scripts/tianmu_proxy.py` 是项目自带的轻量 Python 反向代理，适合本地演示或把 SakuraFrp 等隧道的入口统一转发到一个本机端口。脚本不包含域名账号、隧道密钥、证书或其他私密配置，可以随代码公开。

启动前先确保：

- FastAPI 后端运行在 `127.0.0.1:8000`。
- 前端生产预览运行在 `127.0.0.1:4173`。

然后在 `backend/` 目录启动代理：

```bash
/opt/miniconda3/envs/backend/bin/python scripts/tianmu_proxy.py
```

代理监听 `127.0.0.1:8080`，路由规则如下：

| 请求 | 上游 |
|---|---|
| `/api/*`、`/health`、`/docs`、`/redoc`、`/openapi.json`、`/firmware/*` | FastAPI `127.0.0.1:8000` |
| `/ws` | FastAPI WebSocket `127.0.0.1:8000/ws` |
| 其他路径 | Vite Preview `127.0.0.1:4173` |

公网使用时，让隧道或网关把 HTTPS/WSS 请求转到 `127.0.0.1:8080`。域名、TLS 证书和隧道凭据应在部署平台或本机环境中配置，不要写进仓库。这个脚本是项目级轻量代理，不替代需要限流、审计、高可用等能力的正式生产网关。

### Docker 部署（正在开发中，非当前 MVP）

```bash
docker-compose up -d
```

当前比赛 MVP 以本地启动和演示数据脚本为准，Docker/Gunicorn/Nginx 生产部署文件保留但不作为当前交付范围。

### 创建管理员

```bash
python scripts/create_admin.py <username> <password> [email]
```

### 生成演示数据

用于答辩或硬件未就绪时快速准备完整演示环境：

```bash
python scripts/seed_demo.py --yes
```

脚本会创建/更新以下账号，并刷新 `DEMO-CUBE-*` 演示设备、7 天历史数据、最近实时数据、操作日志和语音日志：

| 账号      | 密码           | 角色   |
| ------- | ------------ | ---- |
| `demo`  | `demo123456` | 普通用户 |
| `admin` | `demo123456` | 管理员  |

演示设备：

| 设备 ID           | 名称      | 状态  | 用途                 |
| --------------- | ------- | --- | ------------------ |
| `DEMO-CUBE-001` | 魔方终端-客厅 | 在线  | 正常环境数据             |
| `DEMO-CUBE-002` | 魔方终端-书桌 | 在线  | 高风险数据，用于展示 AI 风险预警 |
| `DEMO-CUBE-003` | 魔方终端-卧室 | 离线  | 离线设备状态展示           |

### 运行测试

```bash
python -m pytest tests/
```

如果使用 Conda 环境，可按实际环境路径执行：

```bash
/opt/miniconda3/envs/backend/bin/python -m pytest tests/
```

## API 概览

### 认证

| 方法   | 路径                      | 说明   |
| ---- | ----------------------- | ---- |
| POST | `/api/v1/auth/register` | 用户注册 |
| POST | `/api/v1/auth/login`    | 用户登录 |

### 设备管理

| 方法   | 路径                                     | 说明    |
| ---- | -------------------------------------- | ----- |
| POST | `/api/v1/device/auth`                  | 设备握手  |
| POST | `/api/v1/device/{device_id}/heartbeat` | 设备心跳  |
| POST | `/api/v1/device/bind`                  | 绑定设备  |
| POST | `/api/v1/device/unbind`                | 解绑设备  |
| GET  | `/api/v1/device/list`                  | 设备列表  |
| PUT  | `/api/v1/device/{device_id}/rename`    | 重命名设备 |

### 传感器数据

| 方法   | 路径                                 | 说明        |
| ---- | ---------------------------------- | --------- |
| POST | `/api/v1/data/upload`              | 数据上报（设备侧） |
| GET  | `/api/v1/data/{device_id}/latest`  | 最新数据      |
| GET  | `/api/v1/data/{device_id}/history` | 历史数据      |

设备数据上报同时兼容两种 JSON 结构：

```json
{
  "device_id": "DEMO-CUBE-001",
  "token": "dev_xxx",
  "timestamp": 1713880035,
  "type": "data_report",
  "data": {
    "temperature": 25.6,
    "humidity": 60.5,
    "illuminance": 500,
    "aqi": 35,
    "tvoc": 120,
    "eco2": 450,
    "mold_risk": 0,
    "gas": 0,
    "version": "1.0"
  },
  "status": {
    "focus_mode": false
  }
}
```

也兼容硬件 MQTT 当前使用的嵌套结构：

```json
{
  "device_id": "DEMO-CUBE-001",
  "token": "dev_xxx",
  "timestamp": 1713880035,
  "type": "data_report",
  "data": {
    "data": {
      "temperature": 25.6,
      "humidity": 60.5,
      "illuminance": 500,
      "aqi": 35,
      "tvoc": 120,
      "eco2": 450,
      "mold_risk": 0,
      "gas": 0,
      "version": "1.0"
    },
    "status": {
      "wifi_connected": true,
      "mqtt_connected": true,
      "screen_normal": true,
      "sensor_normal": true,
      "focus_mode": false
    }
  }
}
```

`wifi_rssi` 为可选字段；如果硬件未上报，后端会保存为空。

### 设备控制

| 方法   | 路径                                 | 说明     |
| ---- | ---------------------------------- | ------ |
| POST | `/api/v1/control/{device_id}`      | 下发控制指令 |
| GET  | `/api/v1/control/{device_id}/pull` | 设备拉取指令 |
| POST | `/api/v1/control/{device_id}/ack`  | 执行结果通知 |

当前 MVP 只保留硬件可执行的控制主线：灯光、亮度、蜂鸣器、专注模式、屏幕亮度。空调、音频等泛智能家居控制已砍出当前范围。

### 日志

| 方法   | 路径                      | 说明     |
| ---- | ----------------------- | ------ |
| GET  | `/api/v1/log/operation` | 查询操作日志 |
| GET  | `/api/v1/log/voice`     | 查询语音日志 |
| POST | `/api/v1/log/voice`     | 创建语音日志 |

### OTA 固件更新

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/ota/firmware?version=<version>` | 管理员上传 `.bin`，返回 URL、MD5 和文件大小 |
| POST | `/api/v1/ota/push` | 向单个设备或全部在线设备发送 `type: "ota_update"` |
| GET | `/api/v1/ota/logs` | 查询 OTA 下发和设备确认结果 |
| GET | `/firmware/<filename>.bin` | ESP32 固件下载地址 |

设备也可以主动发送 `version_check`。后端会从 `data/firmware/` 选择最高版本，计算 MD5，并返回 `code=200` 的更新信息或 `code=204` 的“已是最新版本”。ESP32 更新完成后返回 `control_ack`，最近一条对应 OTA 日志会更新为 `success` 或 `failed`。

当前 OTA 主链路已经与 ESP32-S3 实机联调完成，包括版本检查、MQTT 指令、固件下载、MD5 校验、烧录、重启和 ACK 回传。`.bin` 固件属于部署产物，保存在 `data/firmware/`，不会提交到 Git。

### 管理员

| 方法     | 路径                                     | 说明      |
| ------ | -------------------------------------- | ------- |
| GET    | `/api/v1/admin/users`                  | 用户列表    |
| PUT    | `/api/v1/admin/users/{user_id}/status` | 启用/禁用用户 |
| GET    | `/api/v1/admin/devices`                | 设备列表    |
| DELETE | `/api/v1/admin/devices/{device_id}`    | 强制删除设备  |
| GET    | `/api/v1/admin/stats`                  | 系统统计    |

### AI 分析

| 方法  | 路径                                     | 说明     |
| --- | -------------------------------------- | ------ |
| GET | `/api/v1/ai/{device_id}/score`         | 环境综合评分 |
| GET | `/api/v1/ai/{device_id}/risks`         | 风险预警   |
| GET | `/api/v1/ai/{device_id}/suggestions`   | AI 建议  |
| GET | `/api/v1/ai/{device_id}/weekly-report` | 周报数据   |

### WebSocket

端点: `ws://localhost:8000/ws`

公网单域名部署时通过当前域名访问：

```text
wss://<your-domain>/ws
```

消息类型: `auth`（认证）、`subscribe`（订阅设备）、`ping`（心跳）

推送类型: `sensor_data`、`device_status`、`device_heartbeat`、`control_result`、`alert`

## 前端联调

前端仓库位于同级目录 `../tianmu`，默认通过以下地址连接后端：

| 项目        | 默认值                            |
| --------- | ------------------------------ |
| REST API  | `http://localhost:8000/api/v1` |
| WebSocket | `ws://localhost:8000/ws`       |

前端 `.env` 示例：

```text
VITE_API_BASE_URL=/api/v1
VITE_WS_BASE_URL=
```

开发时可以使用 Vite 代理，也可以把 `VITE_API_BASE_URL` 改成完整后端地址。公网单域名方案下 `VITE_WS_BASE_URL` 保持为空，前端会按当前页面协议自动使用 `ws://当前域名/ws` 或 `wss://当前域名/ws`。

## 告警阈值

| 指标               | 警告阈值      | 严重阈值      |
| ---------------- | --------- | --------- |
| TVOC             | 0.5 mg/m³ | 1.0 mg/m³ |
| CO₂ (eco2)       | 1000 ppm  | 2000 ppm  |
| 霉菌风险 (mold_risk) | 2         | 3         |

## 环境变量

| 变量                    | 默认值                                  | 说明           |
| --------------------- | ------------------------------------ | ------------ |
| `DEBUG`               | `true`                               | 调试模式         |
| `SECRET_KEY`          | -                                    | JWT 签名密钥     |
| `FIRMWARE_PUBLIC_BASE_URL` | 空                                   | OTA 固件公网下载地址；实机 OTA 时必须设置为设备可访问的 HTTPS 地址 |
| `CORS_ORIGINS`        | 本地开发源                              | 允许访问后端的前端源；跨域部署时按实际域名配置 |
| `DATABASE_URL`        | `sqlite+aiosqlite:///./data/cube.db` | 数据库连接        |
| `MQTT_BROKER_URL`     | `broker.emqx.io`                     | MQTT Broker  |
| `MQTT_BROKER_PORT`    | `1883`                               | MQTT 端口      |
| `DATA_RETENTION_DAYS` | `30`                                 | 数据保留天数       |
| `TTS_API_URL`         | 空                                    | 语音合成 API，正在开发中，非 MVP |
| `WEATHER_API_URL`     | 空                                    | 天气 API，正在开发中，非 MVP |
| `WECHAT_WEBHOOK_URL`  | 空                                    | 企业微信 Webhook，正在开发中，非 MVP |

## 正在开发中 / 非当前 MVP

以下能力保留在项目中，但当前不作为比赛 MVP 交付范围：

- `app/services/tts_service.py`：TTS 语音合成预留。
- `app/services/weather_service.py`：天气服务预留。
- `app/services/wechat_service.py`：微信推送预留。
- `alembic.ini`：正式数据库迁移流程预留。
- `Dockerfile`、`docker-compose.yml`：生产部署预留。

## 仓库说明

当前后端仓库分支为 `backend`。前端在同一 GitHub 仓库的 `tianmu` 分支中维护，两个目录是独立工作区，提交和推送需要分别执行。
