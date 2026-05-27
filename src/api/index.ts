// src/api/index.ts
// Axios 实例封装
// 配置基础 URL、超时时间、请求拦截器（自动附加 JWT Token）、响应拦截器（401 自动跳转登录）
// 支持演示模式：拦截所有 API 请求并返回模拟数据

import axios from 'axios'
import type { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import { isDemoMode, mockGetDeviceList, mockBindDevice, mockGetLatestData, mockSendControlCommand } from '@/utils/demo'

// 创建 Axios 实例，所有 API 请求共享此实例
const service: AxiosInstance = axios.create({
  // API 基础地址，从环境变量读取
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  // 请求超时时间 10 秒
  timeout: 10000,
})

// 请求拦截器：演示模式拦截返回模拟数据，正常模式附加 JWT Token
service.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    // === 演示模式：拦截请求并返回模拟数据 ===
    if (isDemoMode()) {
      const url = config.url || ''
      const method = config.method?.toUpperCase()

      // GET /device/list → 返回模拟设备列表
      if (url.includes('/device/list') && method === 'GET') {
        const mockData = await mockGetDeviceList()
        return Promise.reject({ __mock__: true, response: { data: mockData } })
      }

      // POST /device/bind → 返回模拟绑定成功
      if (url.includes('/device/bind') && method === 'POST') {
        const params = config.data as { device_id: string; device_name: string }
        const mockData = await mockBindDevice(params)
        return Promise.reject({ __mock__: true, response: { data: mockData } })
      }

      // GET /data/{device_id}/latest → 返回模拟传感器数据
      const latestMatch = url.match(/\/data\/([^/]+)\/latest/)
      if (latestMatch && latestMatch[1] && method === 'GET') {
        const deviceId = latestMatch[1]
        const mockData = await mockGetLatestData(deviceId)
        return Promise.reject({ __mock__: true, response: { data: mockData } })
      }

      // POST /control/{device_id} → 返回模拟控制指令响应
      const controlMatch = url.match(/\/control\/([^/]+)/)
      if (controlMatch && controlMatch[1] && method === 'POST') {
        const deviceId = controlMatch[1]
        const commandData = config.data as { command: string; value: string }
        const mockData = await mockSendControlCommand(deviceId, commandData)
        return Promise.reject({ __mock__: true, response: { data: mockData } })
      }

      // 其他未匹配的请求也返回空成功响应(避免演示时报错)
      return Promise.reject({ __mock__: true, response: { data: {} } })
    }

    // === 正常模式：附加 JWT Token ===
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：演示模式模拟响应直接返回，正常模式处理 401 错误、统一解包 { code, message, data }
service.interceptors.response.use(
  (response: AxiosResponse) => {
    const body = response.data as { code?: number; message?: string; data?: unknown }

    // 后端统一使用 { code, message, data } 包装格式
    if (body && typeof body === 'object' && 'code' in body) {
      if (body.code !== undefined && body.code !== 0) {
        return Promise.reject({ response: { data: { detail: body.message } } })
      }
      return body.data
    }

    return response.data
  },
  (error) => {
    // 演示模式模拟请求：返回模拟的 data
    if (error.__mock__) {
      return error.response.data
    }

    // 正常模式：401 未授权 → 清除 Token 并跳转登录页
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default service
