// src/api/index.ts
// Axios 实例封装
// 配置基础 URL、超时时间、请求拦截器（自动附加 JWT Token）、响应拦截器（401 自动跳转登录）
// 支持演示模式：拦截所有 API 请求并返回模拟数据

import axios from 'axios'
import type {
  AxiosError,
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  InternalAxiosRequestConfig,
} from 'axios'
import { interceptDemoRequest } from './demoInterceptor'
import {
  getAccessToken,
  notifyAuthExpired,
  refreshAccessToken,
} from './session'

// 创建 Axios 实例，所有 API 请求共享此实例
const service: AxiosInstance = axios.create({
  // API 基础地址，从环境变量读取
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  // AI 生成可能需要等待本地模型冷启动，统一给足 120 秒。
  timeout: 120000,
  withCredentials: true,
})

// 请求拦截器：演示模式拦截返回模拟数据，正常模式附加 JWT Token
service.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const intercepted = await interceptDemoRequest(config)

    // === 正常模式：附加 JWT Token ===
    const token = getAccessToken()
    if (token) {
      intercepted.headers.Authorization = `Bearer ${token}`
    }
    return intercepted
  },
  async (error: AxiosError & { __mock__?: boolean }) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：演示模式模拟响应直接返回，正常模式处理 401 错误、统一解包 { code, message, data }
service.interceptors.response.use(
  (response: AxiosResponse) => {
    if ((response.config as InternalAxiosRequestConfig & { preserveResponse?: boolean }).preserveResponse) {
      return response
    }
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
  async (error) => {
    // 演示模式模拟请求：返回模拟的 data
    if (error.__mock__) {
      return error.response.data
    }

    const original = error.config as (InternalAxiosRequestConfig & { _retried?: boolean }) | undefined
    const isAuthEndpoint = original?.url?.includes('/auth/')
    if (error.response?.status === 401 && original && !original._retried && !isAuthEndpoint) {
      original._retried = true
      try {
        const token = await refreshAccessToken()
        original.headers.Authorization = `Bearer ${token}`
        return service(original)
      } catch {
        notifyAuthExpired()
      }
    } else if (error.response?.status === 401 && !isAuthEndpoint) {
      notifyAuthExpired()
    }
    return Promise.reject(error)
  }
)

/** Use when a caller explicitly needs status or response headers instead of the unwrapped API data. */
export function requestRaw<T>(config: AxiosRequestConfig): Promise<AxiosResponse<T>> {
  return service.request<T, AxiosResponse<T>>({
    ...config,
    preserveResponse: true,
  } as AxiosRequestConfig & { preserveResponse: true })
}

export default service
