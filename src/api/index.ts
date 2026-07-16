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
  // AI 生成可能需要等待本地模型冷启动，统一给足 120 秒。
  timeout: 120000,
})

// 请求拦截器：演示模式拦截返回模拟数据，正常模式附加 JWT Token
service.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    // === 演示模式：拦截请求并返回模拟数据 ===
    if (isDemoMode()) {
      const url = config.url || ''
      const method = config.method?.toUpperCase()
      const params = config.params as { force_llm?: boolean } | undefined

      // 认证接口必须允许真实请求通过，否则用户从演示模式回到登录页时会被 mock 拦截。
      if (url.includes('/auth/')) {
        const token = localStorage.getItem('token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      }

      if (url.includes('/ai/') && params?.force_llm) {
        return Promise.reject({
          response: {
            data: {
              detail: '当前处于演示模式，强制 LLM 分析不会请求后端。请关闭 demo 模式后重试。',
            },
          },
        })
      }

      // AI 读取接口在演示模式下返回明确的规则引擎数据。
      if (url.includes('/ai/') && url.endsWith('/score') && method === 'GET') {
        return Promise.reject({
          __mock__: true,
          response: { data: { score: 85, level: 'good', summary: '当前室内环境整体舒适，空气质量良好。' } },
        })
      }

      if (url.includes('/ai/') && url.endsWith('/risks') && method === 'GET') {
        return Promise.reject({
          __mock__: true,
          response: { data: { risks: [], highest_level: 'none' } },
        })
      }

      if (url.includes('/ai/') && url.endsWith('/suggestions') && method === 'GET') {
        return Promise.reject({
          __mock__: true,
          response: {
            data: {
              source: 'rule',
              suggestions: [
                { icon: 'wind', title: '空气质量良好', desc: '建议定时开窗，保持空气流通' },
                { icon: 'temp', title: '温度适宜', desc: '当前温度适合工作与休息' },
              ],
            },
          },
        })
      }

      if (url.includes('/ai/') && url.endsWith('/weekly-report') && method === 'GET') {
        const today = new Date()
        const days = Array.from({ length: 7 }, (_, index) => {
          const date = new Date(today)
          date.setDate(today.getDate() - (6 - index))
          return {
            date: date.toISOString().slice(0, 10),
            temperature: 24 + (index % 3) * 0.5,
            humidity: 56 + (index % 4),
            aqi: 42 + index * 2,
            sample_count: 48,
          }
        })
        return Promise.reject({
          __mock__: true,
          response: {
            data: { days, summary: '本周环境整体稳定，各项指标处于舒适范围。', source: 'rule' },
          },
        })
      }

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

      // 未实现的模拟接口必须明确报错，避免路径拼错或漏做 mock 时表现成“成功”。
      return Promise.reject({
        response: {
          status: 501,
          data: { detail: `演示模式暂未实现该接口：${method || 'UNKNOWN'} ${url}` },
        },
      })
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
