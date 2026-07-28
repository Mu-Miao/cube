# 智能桌面魔方 - 后端服务

更新时间：2026-07-28

基于 FastAPI + SQLAlchemy + MQTT + WebSocket 的 IoT 后端，为智能桌面魔方硬件设备提供设备管理、传感器数据采集、远程控制、告警检测等服务。

## 当前状态

后端已经完成 MVP 演示所需的主要服务能力：

- 用户注册、登录、15 分钟 Access Token、HttpOnly Refresh Cookie 轮换与注销、管理员权限校验。
- 管理员生成一次性设备配对码；设备首次握手消费配对码，后续凭证轮换，数据库仅保存 SHA-256 摘要和过期时间。
- 传感器数据上报、最新数据查询、历史数据查询和 1 小时至 7 天的分桶趋势聚合。
- 设备在线状态由握手与心跳维护，后台任务会扫描心跳超时设备、标记离线并通过 WebSocket 广播。
- 心跳和数据上报同步灯光、亮度、专注模式等硬件控制状态。
- API、WebSocket、日志和周报时间统一转换为 Asia/Shanghai（UTC+8）。
- Redis Stream 持久化控制指令，包含 `command_id`、ACK、超时重试；HTTP 拉取作为 MQTT 主通道的兼容路径。
- 操作日志和语音日志查询/记录。
- 管理员用户管理、设备管理、系统统计。
- AI 分析接口：环境综合评分、风险预警、智能建议、周报数据。
- MQTT 设备消息处理。
- OTA 固件上传、签名下载、版本检查、MQTT 更新推送、MD5 校验和设备结果回传；旧协议已完成 ESP32-S3 实机更新验证，新配对与签名协议仍需重新做实机回归。
- WebSocket 完成 JWT 认证和设备归属校验后，支持连接上限、ping/pong、超时关闭和 Redis Pub/Sub 多 Worker 广播。

最近验证结果：

```bash
python -m pytest tests/
```

当前共 54 项测试通过，覆盖认证刷新与轮换、配对码、设备凭证、数据范围、控制 ACK/重试、签名 OTA、AI 分析、心跳状态、超时离线、WebSocket 权限与趋势聚合等核心流程。

## 技术栈

- **Web 框架**: FastAPI + Uvicorn
- **数据库**: PostgreSQL (asyncpg，生产) / SQLite WAL (aiosqlite，本地开发)
- **迁移**: Alembic
- **认证**: 短时 JWT + HttpOnly Refresh Cookie + bcrypt
- **设备通信**: MQTT (aiomqtt) + HTTP 轮询
- **队列/广播**: Redis Streams + Redis Pub/Sub
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
│   │       ├── data.py              # 数据上报 / 最新 / 历史 / 趋势聚合
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
│   │   ├── device_service.py        # 设备解绑 / 心跳超时离线判定
│   │   ├── control_status.py        # 硬件控制状态归一化与持久化
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
│   │   ├── helpers.py               # 通用工具函数
│   │   └── timezone.py              # Asia/Shanghai 时间转换
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
- 本地开发可只使用 SQLite；生产环境必须提供外部 PostgreSQL、Redis 和私有 MQTT Broker
- 生产 MQTT 必须启用账号密码、CA 验证和 TLS 8883
- 推荐使用虚拟环境或 Conda 环境隔离依赖

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库
alembic upgrade head

# 启动服务
uvicorn app.main:app --reload --port 8000
```

访问 `http://localhost:8000/docs` 查看 Swagger API 文档。

`DEBUG=false` 时 `/docs`、`/redoc` 和 OpenAPI JSON 会关闭，SQL echo 也会关闭。应用启动会拒绝不安全密钥、SQLite、多 Worker 缺少 Redis、公开 MQTT Broker、非 TLS 8883、缺少 CA、HTTP 固件地址和宽松 CORS。

### 数据库迁移

开发库和生产库统一由 Alembic 管理：

```bash
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```

如果是早期版本已经存在表、但还没有 `alembic_version` 的 SQLite 数据库，先备份，
确认包含 `users`、`devices`、`sensor_data` 等基础表后，将其标记为基础版本再升级：

```bash
mkdir -p data/backups
cp -p data/cube.db data/backups/cube-before-alembic.db
alembic stamp 20260728_0001
alembic upgrade head
```

不要对空数据库执行 `stamp`；空数据库直接运行 `alembic upgrade head`。初始迁移使用
固定的显式表结构，不再调用当前 ORM 的 `Base.metadata.create_all()`，因此历史迁移不会
随着未来模型变化而漂移。

把现有 SQLite 数据一次性迁到一个空 PostgreSQL 库，并逐表核对条数：

```bash
python scripts/migrate_sqlite_to_postgres.py \
  --sqlite-url sqlite+aiosqlite:///./data/cube.db \
  --postgres-url postgresql+asyncpg://cube:password@127.0.0.1:5432/cube
```

脚本发现 PostgreSQL 目标表已有数据时会拒绝覆盖。生产多 Worker 通过 `WEB_CONCURRENCY` 配置；SQLite 固定为 1，PostgreSQL 才允许大于 1。

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
| `/api/*`、`/health`、`/docs`、`/redoc`、`/openapi.json` | FastAPI `127.0.0.1:8000` |
| `/ws` | FastAPI WebSocket `127.0.0.1:8000/ws` |
| 其他路径 | Vite Preview `127.0.0.1:4173` |

公网使用时，让隧道或网关把 HTTPS/WSS 请求转到 `127.0.0.1:8080`。域名、TLS 证书和隧道凭据应在部署平台或本机环境中配置，不要写进仓库。这个脚本是项目级轻量代理，不替代需要限流、审计、高可用等能力的正式生产网关。

### Docker 部署

```bash
cp .env.example .env
# 填写外部 PostgreSQL、Redis、私有 MQTT、证书路径和 HTTPS 域名
docker compose up -d
```

Compose 不捆绑 PostgreSQL、Redis 或 Mosquitto，只连接外部服务。容器使用非 root 用户并包含 `/health` 健康检查；`MQTT_CA_CERT_HOST_PATH` 指向宿主机 CA 文件。

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
| POST | `/api/v1/auth/login`    | 登录并写入 Refresh Cookie |
| POST | `/api/v1/auth/refresh`  | 轮换 Refresh Cookie 并恢复 Access Token |
| POST | `/api/v1/auth/logout`   | 撤销 Refresh Token 并清除 Cookie |

### 设备管理

| 方法   | 路径                                     | 说明    |
| ---- | -------------------------------------- | ----- |
| POST | `/api/v1/device/auth`                  | 首次配对或凭证轮换握手 |
| POST | `/api/v1/device/{device_id}/heartbeat` | 设备心跳  |
| POST | `/api/v1/device/bind`                  | 绑定设备  |
| POST | `/api/v1/device/unbind`                | 解绑设备  |
| GET  | `/api/v1/device/list`                  | 设备列表  |
| PUT  | `/api/v1/device/{device_id}/rename`    | 重命名设备 |

### 设备配对与凭证协议

管理员先为明确的 `device_id` 生成一次性配对码：

```json
POST /api/v1/admin/device-pairing-codes
{"device_id":"CUBE-001"}
```

配对码只在响应中出现一次，默认 10 分钟过期。设备首次通过 HTTP `/api/v1/device/auth` 或 MQTT `cube2026/device/{device_id}/data` 发送 `type=handshake` 和 `pairing_code`；后端原子消费配对码并返回设备 Token。后续握手发送当前 `token`，成功后旧 Token 立即失效并返回新 Token。心跳、数据、控制拉取/ACK 和版本检查都必须携带当前有效 Token。

数据库只保存 `sha256$...` 摘要与 `token_expires_at`，不保存原始 Token。`ALLOW_LEGACY_DEVICE_HANDSHAKE` 仅用于本地迁移兼容，生产环境必须保持关闭。

### 传感器数据

| 方法   | 路径                                 | 说明        |
| ---- | ---------------------------------- | --------- |
| POST | `/api/v1/data/upload`              | 数据上报（设备侧） |
| GET  | `/api/v1/data/{device_id}/latest`  | 最新数据      |
| GET  | `/api/v1/data/{device_id}/history` | 历史数据      |
| GET  | `/api/v1/data/{device_id}/trend?hours=1` | 分桶趋势数据；`hours` 支持 `1`、`6`、`24`、`168` |

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
    "focus_mode": false,
    "light": true,
    "light_brightness": 70,
    "color_temperature": 4200,
    "wechat_notify": true,
    "auto_screen_brightness": true,
    "screen_brightness": 60
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
      "focus_mode": false,
      "light": true,
      "light_brightness": 70,
      "color_temperature": 4200,
      "wechat_notify": true,
      "auto_screen_brightness": true,
      "screen_brightness": 60
    }
  }
}
```

`wifi_rssi` 为可选字段；如果硬件未上报，后端会保存为空。

趋势接口会对时间范围内的全部上报记录分桶求平均值，并返回 `sample_count`。1 小时、6 小时、24 小时和 7 天范围分别使用 1 分钟、5 分钟、15 分钟和 1 小时的时间桶。

在线状态只由设备握手和心跳刷新；普通传感器数据上报不会把已失联设备重新标记为在线。后台任务会周期性扫描并广播离线状态，查询和控制接口也会即时复核。Demo 设备不参与心跳超时离线判定。

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
| GET | `/api/v1/ota/firmware/<filename>?expires=...&signature=...` | 短时 HMAC 签名下载地址 |

设备也可以主动发送 `version_check`。后端会从 `data/firmware/` 选择最高版本，计算 MD5，并返回 `code=200` 的更新信息或 `code=204` 的“已是最新版本”。ESP32 更新完成后返回 `control_ack`，最近一条对应 OTA 日志会更新为 `success` 或 `failed`。

当前 OTA 主链路已经与 ESP32-S3 实机联调完成，包括版本检查、MQTT 指令、固件下载、MD5 校验、烧录、重启和 ACK 回传。`.bin` 固件属于部署产物，保存在 `data/firmware/`，不会提交到 Git。

### 管理员

| 方法     | 路径                                     | 说明      |
| ------ | -------------------------------------- | ------- |
| GET    | `/api/v1/admin/users`                  | 用户列表    |
| PUT    | `/api/v1/admin/users/{user_id}/status` | 启用/禁用用户 |
| GET    | `/api/v1/admin/devices`                | 设备列表    |
| POST   | `/api/v1/admin/device-pairing-codes`   | 为设备生成一次性配对码 |
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
| `DEBUG`               | `true`                               | 调试模式；生产必须为 `false` |
| `WEB_CONCURRENCY`     | `1`                                  | Uvicorn Worker 数；SQLite 只能为 1 |
| `SECRET_KEY`          | -                                    | 至少 32 位 JWT/HMAC 签名密钥 |
| `FIRMWARE_PUBLIC_BASE_URL` | 空                                   | OTA 固件公网下载地址；实机 OTA 时必须设置为设备可访问的 HTTPS 地址 |
| `CORS_ORIGINS`        | 本地开发源                              | 允许访问后端的前端源；跨域部署时按实际域名配置 |
| `DATABASE_URL`        | `sqlite+aiosqlite:///./data/cube.db` | 数据库连接        |
| `REDIS_URL`           | 空                                    | Redis Streams / PubSub；生产必填 |
| `MQTT_BROKER_URL`     | 空                                    | 私有 MQTT Broker |
| `MQTT_BROKER_PORT`    | `8883`                               | MQTT TLS 端口 |
| `MQTT_CA_CERT`        | 空                                    | Broker CA 证书；生产必填 |
| `DEVICE_HEARTBEAT_TIMEOUT_SECONDS` | `90`                    | 设备心跳超时判定秒数 |
| `DATA_RETENTION_DAYS` | `30`                                 | 数据保留天数       |
| `TTS_API_URL`         | 空                                    | 语音合成 API，正在开发中，非 MVP |
| `WEATHER_API_URL`     | 空                                    | 天气 API，正在开发中，非 MVP |
| `WECHAT_WEBHOOK_URL`  | 空                                    | 企业微信 Webhook，正在开发中，非 MVP |

## 正在开发中 / 非当前 MVP

以下能力保留在项目中，但当前不作为比赛 MVP 交付范围：

- `app/services/tts_service.py`：TTS 语音合成预留。
- `app/services/weather_service.py`：天气服务预留。
- `app/services/wechat_service.py`：微信推送预留。

## 仓库说明

当前后端仓库分支为 `backend`。前端在同一 GitHub 仓库的 `tianmu` 分支中维护，两个目录是独立工作区，提交和推送需要分别执行。
