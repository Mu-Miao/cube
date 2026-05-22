# 智能桌面魔方 — 后端服务

基于 FastAPI + SQLAlchemy + MQTT + WebSocket 的 IoT 后端，为智能桌面魔方硬件设备提供设备管理、传感器数据采集、远程控制、告警检测等服务。

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
│   │       └── ai.py                # AI 分析（评分/风险/建议/周报）
│   ├── models/
│   │   ├── user.py                  # 用户（含 role 字段）
│   │   ├── device.py                # 设备
│   │   ├── sensor_data.py           # 传感器数据
│   │   ├── operation_log.py         # 操作日志
│   │   └── voice_log.py             # 语音日志
│   ├── schemas/                     # Pydantic 请求/响应模型
│   ├── services/
│   │   ├── auth_service.py          # JWT 编解码 / 密码哈希
│   │   ├── device_service.py        # 设备解绑逻辑
│   │   ├── data_service.py          # 数据查询服务层
│   │   ├── alert_service.py         # 告警阈值检测
│   │   ├── cleanup_service.py       # 过期数据清理
│   │   ├── tts_service.py           # 语音合成（骨架）
│   │   ├── weather_service.py       # 天气服务（骨架）
│   │   └── wechat_service.py        # 企业微信推送（骨架）
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
│   └── init_db.py                   # 初始化数据库
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

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload --port 8000
```

访问 `http://localhost:8000/docs` 查看 Swagger API 文档。

### Docker 部署

```bash
docker-compose up -d
```

### 创建管理员

```bash
python scripts/create_admin.py <username> <password> [email]
```

## API 概览

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/auth/register` | 用户注册 |
| POST | `/api/v1/auth/login` | 用户登录 |

### 设备管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/device/auth` | 设备握手 |
| POST | `/api/v1/device/{device_id}/heartbeat` | 设备心跳 |
| POST | `/api/v1/device/bind` | 绑定设备 |
| POST | `/api/v1/device/unbind` | 解绑设备 |
| GET | `/api/v1/device/list` | 设备列表 |
| PUT | `/api/v1/device/{device_id}/rename` | 重命名设备 |

### 传感器数据

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/data/upload` | 数据上报（设备侧） |
| GET | `/api/v1/data/{device_id}/latest` | 最新数据 |
| GET | `/api/v1/data/{device_id}/history` | 历史数据 |

### 设备控制

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/control/{device_id}` | 下发控制指令 |
| GET | `/api/v1/control/{device_id}/pull` | 设备拉取指令 |
| POST | `/api/v1/control/{device_id}/ack` | 执行结果通知 |

### 日志

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/log/operation` | 查询操作日志 |
| GET | `/api/v1/log/voice` | 查询语音日志 |
| POST | `/api/v1/log/voice` | 创建语音日志 |

### 管理员

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/admin/users` | 用户列表 |
| PUT | `/api/v1/admin/users/{user_id}/status` | 启用/禁用用户 |
| GET | `/api/v1/admin/devices` | 设备列表 |
| DELETE | `/api/v1/admin/devices/{device_id}` | 强制删除设备 |
| GET | `/api/v1/admin/stats` | 系统统计 |

### AI 分析

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/ai/{device_id}/score` | 环境综合评分 |
| GET | `/api/v1/ai/{device_id}/risks` | 风险预警 |
| GET | `/api/v1/ai/{device_id}/suggestions` | AI 建议 |
| GET | `/api/v1/ai/{device_id}/weekly-report` | 周报数据 |

### WebSocket

端点: `ws://localhost:8000/ws`

消息类型: `auth`（认证）、`subscribe`（订阅设备）、`ping`（心跳）

推送类型: `sensor_data`、`device_status`、`device_heartbeat`、`control_result`、`alert`

## 告警阈值

| 指标 | 警告阈值 | 严重阈值 |
|------|----------|----------|
| 燃气 (gas) | 0.5 | 1.0 |
| TVOC | 0.5 mg/m³ | 1.0 mg/m³ |
| CO₂ (eco2) | 1000 ppm | 2000 ppm |
| 霉菌风险 (mold_risk) | 2 | 3 |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DEBUG` | `true` | 调试模式 |
| `SECRET_KEY` | - | JWT 签名密钥 |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/cube.db` | 数据库连接 |
| `MQTT_BROKER_URL` | `broker.emqx.io` | MQTT Broker |
| `MQTT_BROKER_PORT` | `1883` | MQTT 端口 |
| `DATA_RETENTION_DAYS` | `30` | 数据保留天数 |
| `TTS_API_URL` | 空 | 语音合成 API |
| `WEATHER_API_URL` | 空 | 天气 API |
| `WECHAT_WEBHOOK_URL` | 空 | 企业微信 Webhook |
