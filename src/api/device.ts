// src/api/device.ts
// 设备管理 API 封装
// 提供设备列表、绑定、传感器数据查询、控制指令下发等接口的类型定义和请求方法

import api from './index'

/** 绑定设备请求参数 */
export interface BindDeviceParams {
  device_id: string    // 设备唯一标识（MAC 地址）
  device_name: string  // 设备显示名称
}

/** 设备信息（后端返回的设备列表项） */
export interface DeviceInfo {
  device_id: string       // 设备唯一标识
  device_name: string     // 设备名称
  status: 'online' | 'offline'  // 在线状态
  last_seen: string       // 最后在线时间
  chip_model: string      // 芯片型号（如 ESP32-S3）
  firmware_version: string // 固件版本号
}

/** 传感器数据（后端返回的最新传感器读数） */
export interface SensorData {
  temperature: number   // 温度（℃）
  humidity: number      // 湿度（%RH）
  illuminance: number   // 光照强度（lx）
  aqi: number           // 空气质量指数
  tvoc: number          // 有机挥发物浓度
  eco2: number          // CO₂ 等效浓度（ppm）
  mold_risk: number     // 霉菌风险等级（0-3）
  gas: number           // 燃气浓度（0=正常）
  wifi_rssi: number     // WiFi 信号强度（dBm）
  timestamp: string     // 数据时间
}

/** 控制指令请求参数 */
export interface ControlCommand {
  command: string  // 指令名称（light, buzzer, relay_1 等）
  value: string    // 指令值（on/off, 颜色, 亮度 等）
}

/**
 * 获取当前用户的设备列表
 * GET /api/v1/device/list
 * 需要 JWT 认证
 */
export const getDeviceList = () => {
  return api.get<DeviceInfo[]>('/device/list')
}

/**
 * 绑定设备到当前用户
 * POST /api/v1/device/bind
 * 需要 JWT 认证
 */
export const bindDevice = (data: BindDeviceParams) => {
  return api.post('/device/bind', data)
}

/**
 * 获取指定设备的最新传感器数据
 * GET /api/v1/data/{device_id}/latest
 * 需要 JWT 认证
 */
export const getLatestData = (deviceId: string) => {
  return api.get<SensorData>(`/data/${deviceId}/latest`)
}

/**
 * 向设备下发控制指令
 * POST /api/v1/control/{device_id}
 * 需要 JWT 认证
 * 指令会加入设备队列，设备通过控制拉取接口获取并执行
 */
export const sendControlCommand = (deviceId: string, data: ControlCommand) => {
  return api.post(`/control/${deviceId}`, data)
}

/**
 * 解绑设备
 * POST /api/v1/device/unbind
 * 需要 JWT 认证
 */
export const unbindDevice = (data: { device_id: string }) => {
  return api.post('/device/unbind', data)
}
