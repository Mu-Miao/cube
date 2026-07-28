// src/utils/demo.ts
// 演示模式数据模拟工具
// 在不连接后端的情况下提供模拟数据，用于竞赛演示和 MVP 功能展示

export { isDemoMode, enableDemoMode, disableDemoMode } from './demoMode'

// ============================================================
// 模拟设备数据
// ============================================================

/** 模拟设备信息：2 个设备，1 个在线 ESP32-S3，1 个离线 */
export const mockDevices = [
  {
    device_id: 'ESP32-S3-DEMO-001',       // 设备唯一标识
    device_name: '演示设备-在线',           // 设备显示名称
    status: 'online' as const,             // 在线状态
    last_seen: new Date().toISOString(),   // 最后在线时间
    chip_model: 'ESP32-S3',               // 芯片型号
    firmware_version: 'v1.0.0',           // 固件版本
  },
  {
    device_id: 'ESP32-S3-DEMO-002',
    device_name: '演示设备-离线',
    status: 'offline' as const,
    last_seen: new Date(Date.now() - 3600000).toISOString(), // 1 小时前
    chip_model: 'ESP32-S3',
    firmware_version: 'v1.0.0',
  },
]

// ============================================================
// 模拟传感器数据生成器（带小幅波动模拟真实效果）
// ============================================================

/** 传感器数据基础值 */
const sensorBase = {
  temperature: 25,    // 温度基础值 25℃
  humidity: 60,       // 湿度基础值 60%RH
  illuminance: 450,   // 光照基础值 450lx
  aqi: 75,            // AQI 基础值
  pm25: 22,           // PM2.5 估算值（μg/m³）
  eco2: 520,          // CO2 基础值 520ppm
  tvoc: 120,          // TVOC 基础值
  mold_risk: 1,       // 霉菌风险 0-3
  gas: 0,             // 燃气浓度 0=正常
  wifi_rssi: -42,     // WiFi 信号强度 dBm
}

/** 传感器数据波动范围配置 */
const sensorRange = {
  temperature:  { min: 22, max: 28, step: 0.3 },     // 温度在 22-28℃ 之间波动
  humidity:     { min: 50, max: 70, step: 0.5 },     // 湿度在 50-70%RH 之间波动
  illuminance:  { min: 300, max: 600, step: 15 },    // 光照在 300-600lx 之间波动
  aqi:          { min: 50, max: 100, step: 3 },      // AQI 在 50-100 之间波动
  pm25:         { min: 8, max: 55, step: 2 },        // PM2.5 估算值在 8-55 μg/m³ 之间波动
  eco2:         { min: 400, max: 650, step: 10 },    // CO2 在 400-650ppm 之间波动
  tvoc:         { min: 80, max: 180, step: 5 },      // TVOC 在 80-180 之间波动
  mold_risk:    { min: 0, max: 3, step: 1 },         // 霉菌风险 0-3
  gas:          { min: 0, max: 0, step: 0 },         // 燃气固定 0
  wifi_rssi:    { min: -50, max: -35, step: 1 },     // WiFi 信号 -50 到 -35 dBm
}

// 当前传感器值（用于波动计算，初始为基础值）
const currentSensorValues = { ...sensorBase }

/**
 * 生成模拟传感器数据
 * 每次调用时数据有小幅度随机波动，模拟真实传感器效果
 * 波动范围受 sensorRange 限制，不会超出合理区间
 *
 * @param deviceId - 设备 ID（用于生成不同设备的数据）
 * @returns 传感器数据对象
 */
export function generateMockSensorData(deviceId?: string): Record<string, unknown> {
  // 对每个传感器值进行小幅随机波动
  for (const key of Object.keys(sensorRange) as (keyof typeof sensorRange)[]) {
    const range = sensorRange[key]
    if (range.step === 0) continue  // 固定值不波动

    // 在基础值附近随机波动（正态分布近似）
    const delta = (Math.random() - 0.5) * 2 * range.step
    currentSensorValues[key] += delta

    // 限制在合理范围内
    currentSensorValues[key] = Math.max(range.min, Math.min(range.max, currentSensorValues[key]))
  }

  const defaultDeviceId = mockDevices[0]?.device_id ?? 'DEMO-CUBE-001'

  return {
    device_id: deviceId || defaultDeviceId,
    temperature: Math.round(currentSensorValues.temperature * 10) / 10,
    humidity: Math.round(currentSensorValues.humidity * 10) / 10,
    illuminance: Math.round(currentSensorValues.illuminance),
    aqi: Math.round(currentSensorValues.aqi),
    pm25: Math.round(currentSensorValues.pm25 * 10) / 10,
    eco2: Math.round(currentSensorValues.eco2),
    tvoc: Math.round(currentSensorValues.tvoc),
    mold_risk: Math.round(currentSensorValues.mold_risk),
    gas: Math.round(currentSensorValues.gas),
    wifi_rssi: Math.round(currentSensorValues.wifi_rssi),
    timestamp: new Date().toISOString(),
  }
}

// ============================================================
// 模拟 WebSocket 行为
// ============================================================

/** 模拟 WebSocket 消息处理器类型 */
type MessageHandler = (data: Record<string, unknown>) => void

/** 模拟 WebSocket 实例接口 */
interface MockWebSocket {
  connected: boolean
  handlers: Map<string, MessageHandler[]>
  intervalId: number | null
}

// 模拟 WebSocket 单例
let mockWs: MockWebSocket | null = null

/**
 * 模拟 WebSocket 连接
 * 不创建真实 WebSocket，而是设置模拟状态和定时器
 *
 * @returns 模拟 WebSocket 实例
 */
export function mockConnect(): MockWebSocket {
  if (mockWs) return mockWs  // 避免重复连接

  mockWs = {
    connected: false,
    handlers: new Map(),
    intervalId: null,
  }

  // 模拟连接建立（延迟 100ms 模拟网络延迟）
  setTimeout(() => {
    if (!mockWs) return
    mockWs.connected = true
    console.log('[Demo] WebSocket 模拟连接已建立')

    // 模拟认证成功，返回认证结果
    dispatchMessage('auth_result', { status: 'success', message: '认证成功' })

    // 启动定时数据推送：每 5 秒推送一次模拟传感器数据
    mockWs.intervalId = window.setInterval(() => {
      if (!mockWs || !mockWs.connected) return
      const sensorData = generateMockSensorData()
      dispatchMessage('sensor_data', sensorData)

      // 同时推送设备状态（保持在线）
      dispatchMessage('device_status', {
        device_id: mockDevices[0]?.device_id ?? 'DEMO-CUBE-001',
        status: 'online',
        timestamp: new Date().toISOString(),
      })
    }, 5000)
  }, 100)

  return mockWs
}

/**
 * 注册消息处理器（模拟订阅）
 * 与真实 WebSocket 的 on() 方法行为一致
 */
export function mockOn(type: string, handler: MessageHandler): void {
  if (!mockWs) return
  const handlers = mockWs.handlers.get(type) || []
  handlers.push(handler)
  mockWs.handlers.set(type, handlers)
}

/**
 * 向模拟 WebSocket 发送消息（模拟发送）
 * 可用于模拟控制指令的发送
 */
export function mockSend(type: string, data: Record<string, unknown>): void {
  console.log(`[Demo] WebSocket 模拟发送:`, { type, data })

  // 模拟订阅消息：记录订阅的设备
  if (type === 'subscribe') {
    console.log(`[Demo] 已订阅设备: ${(data as { device_id?: string }).device_id}`)
  }
}

/**
 * 断开模拟 WebSocket 连接
 * 清除定时器和状态
 */
export function mockDisconnect(): void {
  if (!mockWs) return

  if (mockWs.intervalId !== null) {
    clearInterval(mockWs.intervalId)
    mockWs.intervalId = null
  }
  mockWs.connected = false
  mockWs.handlers.clear()
  mockWs = null
  console.log('[Demo] WebSocket 模拟连接已断开')
}

/**
 * 内部方法：分发模拟消息到所有注册的处理器
 */
function dispatchMessage(type: string, data: Record<string, unknown>): void {
  if (!mockWs) return
  const handlers = mockWs.handlers.get(type) || []
  handlers.forEach((handler) => handler(data))
}

// ============================================================
// 模拟 API 响应
// ============================================================

/**
 * 模拟设备列表 API 响应
 * 返回模拟的 2 个设备数据（直接返回 data，与真实 API 拦截器配合）
 */
export function mockGetDeviceList(): Promise<typeof mockDevices> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(mockDevices)
    }, 200) // 模拟网络延迟 200ms
  })
}

/**
 * 模拟绑定设备 API 响应
 * 绑定成功后将设备加入设备列表
 */
export function mockBindDevice(params: { device_id: string; device_name: string }): Promise<{ message: string }> {
  return new Promise((resolve) => {
    setTimeout(() => {
      // 将新设备加入模拟设备列表
      mockDevices.push({
        device_id: params.device_id,
        device_name: params.device_name,
        status: 'online',
        last_seen: new Date().toISOString(),
        chip_model: 'ESP32-S3',
        firmware_version: 'v1.0.0',
      })
      resolve({ message: '绑定成功' })
    }, 300)
  })
}

/**
 * 模拟获取最新传感器数据 API 响应
 * 返回带波动的传感器数据
 */
export function mockGetLatestData(deviceId: string): Promise<Record<string, unknown>> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(generateMockSensorData(deviceId))
    }, 200)
  })
}

/**
 * 模拟发送控制指令 API 响应
 * 返回成功响应
 */
export function mockSendControlCommand(
  deviceId: string,
  data: { command: string; value: string }
): Promise<{ message: string; device_id: string; command: string; value: string }> {
  return new Promise((resolve) => {
    setTimeout(() => {
      console.log(`[Demo] 控制指令已下发:`, { deviceId, command: data.command, value: data.value })
      resolve({
        message: '指令已加入队列',
        device_id: deviceId,
        command: data.command,
        value: data.value,
      })
    }, 200)
  })
}
