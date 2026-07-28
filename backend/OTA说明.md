## 一、整体架构

设备端通过 MQTT 接收 OTA 指令，通过 HTTP 下载固件 .bin，写入 Flash 后重启。后端要做两件事：

- 跑一个 MQTT 客户端，订阅设备的状态消息，按需下发 OTA 指令
- 提供一个 HTTP 下载地址给设备拉取固件 .bin 文件

## 二、MQTT 对接参数

```
Broker:    broker.emqx.io:1883  (公共 broker，无认证)
Client ID: 任意，建议 backend_xxx
Device ID: CUBE001  (硬编码，src/DataPool.cpp 第 63 行)
```

主题划分：

**后端订阅（设备发的消息在这里）：**

- `cube2026/device/CUBE001/status` ← 握手、心跳、版本检查、OTA 状态
- `cube2026/device/CUBE001/data` ← 传感器数据上报
- `cube2026/device/CUBE001/ack` ← 控制指令 ACK

**后端发布（发指令给设备）：**

- `cube2026/server/CUBE001/control` ← 后端在此发 OTA 指令

## 三、OTA 核心消息格式

### 后端 → 设备（OTA 触发指令）

发布到 `cube2026/server/CUBE001/control`：

```json
{
  "type": "ota_update",
  "url": "http://your-server.com/firmware/v1.0.1/firmware.bin",
  "version": "v1.0.1",
  "md5": "d661674684d564249523f07826253cae"
}
```

三个字段都必填：

- `url`: 固件 .bin 的 HTTP 下载地址（必须是 HTTP，不要 HTTPS，ESP32 走 HTTPS 要配根证书很麻烦）
- `version`: 新版本号，格式 `vX.Y.Z` 或 `X.Y.Z`，必须严格大于设备当前版本
- `md5`: 固件 .bin 的 MD5，32 位十六进制小写，设备会据此校验完整性

### 设备 → 后端（version_check，请求 OTA 检查）

后端在 `cube2026/device/CUBE001/status` 上能收到：

```json
{
  "device_id": "CUBE001",
  "timestamp": 1721234567,
  "type": "version_check",
  "current_version": "v1.0.0"
}
```

设备每次启动后会发一次，后续每 30 秒也会发心跳。

## 四、OTA 触发的两种方式

**方式 A（推荐）— 被动响应：**

- 后端订阅 `cube2026/device/CUBE001/status`
- 收到 `type=version_check` 时，比较 `current_version` 和后端记录的最新版本
- 若后端版本 > 设备版本，下发 `ota_update` 指令

**方式 B — 主动推送：**

- 后端不需要等 `version_check`，直接在 `cube2026/server/CUBE001/control` 发布 `ota_update` 指令（前提：设备 MQTT 在线）。这种方式适合"立即给设备升级"。

## 五、HTTP 固件托管要求

固件文件就是 PlatformIO 编译产物：`.pio/build/esp32-s3-devkitm-1/firmware.bin`，约 2-4 MB。

后端的 HTTP 服务器需要满足：

- GET 请求返回 200 OK，body 是原始二进制
- `Content-Length` 头必须准确，设备据此判断下载进度（缺失则设备默认按 4MB 处理）
- 不要重定向（设备 HTTPClient 默认不跟随）
- 推荐响应头：`Content-Type: application/octet-stream`
- URL 必须可公网访问，不要用局域网地址（ESP32 连的是手机热点，受客户端隔离影响，连不到 PC）

推荐托管方案：

- 后端自己用 Express/Spring Boot 提供静态文件服务 → 最简单
- 阿里云 OSS / 腾讯云 COS → 国内最快
- Gitee Releases（私有 release 也可以） → 免费
- GitHub Releases → 国际，国内访问慢

## 六、版本比较规则（后端必须一致）

设备端已实现此逻辑（`src/OTAManager.cpp` 第 28-40 行），后端也要一致：

1. 去掉 `v` 前缀（`v1.0.1` → `1.0.1`）
2. 按 `.` 切三段，解析成 `(major, minor, patch)` 三个整数
3. 按 major → minor → patch 顺序比较
4. 新版本必须严格大于当前版本，等于或小于都会被设备拒绝（设备会回 `ota_status: skipped`）

## 七、设备端行为说明

- HTTP 超时 30 秒
- 4096 字节分块下载 + 流式写 Flash
- `Update.setMD5(md5)` 已配置，下载完会校验 MD5
- 校验通过后 `ESP.restart()` 重启
- OTA 任务在 FreeRTOS Core 1，UI 仍可刷新，有 OTA 锁屏显示进度
- 整个流程异步执行，主任务不阻塞

## 八、典型交互时序

```
设备启动 → MQTT 连接成功
  ↓
设备 → 后端: handshake (上报 chip_model=ESP32-S3, version=v1.0.0)
设备 → 后端: version_check (current_version=v1.0.0)
  ↓
后端比较: 最新 v1.0.1 > v1.0.0 → 触发 OTA
  ↓
后端 → 设备: ota_update (url, version, md5)
  ↓
设备 → 后端: control_ack (command=ota_update, value=v1.0.1, result=success)
[设备开始下载 + 写 Flash + 重启]
  ↓
[设备重启后 current_version 变为 v1.0.1]
  ↓
设备 → 后端: version_check (current_version=v1.0.1)
后端比较: 无新版本 → 不下发
```
