import { formatApiError } from '@/api/errors'

export type ApiResponse<T = unknown> = {
  code?: number
  message?: string
  data?: T
}

export type LoginResult = {
  access_token: string
  token_type: string
  expires_in: number
}

export type DeviceInfo = {
  device_id: string
  device_name: string
  status: 'online' | 'offline'
  last_seen?: string
  chip_model?: string
  firmware_version?: string
}

export type SensorData = {
  device_id?: string
  temperature: number | null
  humidity: number | null
  illuminance?: number | null
  aqi: number | null
  pm25?: number | null
  tvoc?: number | null
  eco2?: number | null
  mold_risk?: number | null
  gas?: number | null
  wifi_rssi?: number | null
  light?: boolean | null
  light_brightness?: number | null
  color_temperature?: number | null
  wechat_notify?: boolean | null
  auto_screen_brightness?: boolean | null
  screen_brightness?: number | null
  focus_mode?: boolean | null
  timestamp?: string
}

export type AiSuggestion = {
  icon: string
  title: string
  desc: string
}

export type AiSuggestions = {
  suggestions: AiSuggestion[]
  source?: 'llm' | 'rule'
}

export type EnvironmentScore = {
  score: number
  level: 'excellent' | 'good' | 'fair' | 'poor' | 'no_data'
  summary?: string
}

export type RiskWarnings = {
  risks: Array<{
    field: string
    level: 'warning' | 'critical'
    title: string
    message: string
  }>
  highest_level: 'none' | 'warning' | 'critical'
}

export type WeeklyReport = {
  days: Array<{
    date: string
    temperature: number | null
    humidity: number | null
    aqi: number | null
    sample_count: number
  }>
  summary?: string | null
  source?: 'llm' | 'rule'
}

export type OperationLog = {
  id: number
  device_id?: string
  action: string
  detail?: string
  ip_address?: string
  created_at?: string
}

export type OperationLogPage = {
  items: OperationLog[]
  total: number
  page: number
  page_size: number
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'
const TOKEN_KEY = 'token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

export function getApiBase() {
  return API_BASE
}

function unwrap<T>(payload: unknown): T {
  const body = payload as ApiResponse<T>

  if (body && typeof body === 'object' && 'code' in body) {
    if (body.code !== undefined && body.code !== 0 && body.code !== 200) {
      throw new Error(body.message || `接口返回错误：${body.code}`)
    }

    return body.data as T
  }

  return payload as T
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken()
  const headers = new Headers(options.headers)

  if (!headers.has('Content-Type') && options.body) {
    headers.set('Content-Type', 'application/json')
  }

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  const text = await response.text()
  let payload: unknown = null
  let isJson = !text

  if (text) {
    try {
      payload = JSON.parse(text)
      isJson = true
    } catch {
      payload = text
    }
  }

  if (response.status === 401) {
    clearToken()
    throw new Error('登录已过期，请重新登录')
  }

  if (!response.ok) {
    const responseSummary = text.trim().replace(/\s+/g, ' ').slice(0, 120)
    const fallback = isJson
      ? `请求失败：${response.status}`
      : `请求失败：${response.status}（${responseSummary || '响应不是 JSON'}）`
    throw new Error(formatApiError({ response: { status: response.status, data: payload } }, fallback))
  }

  if (!isJson) {
    throw new Error('服务器响应格式错误，请稍后重试')
  }

  return unwrap<T>(payload)
}

export const api = {
  login(username: string, password: string) {
    return request<LoginResult>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    })
  },
  register(username: string, password: string) {
    return request<{ id: number }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    })
  },
  getDevices() {
    return request<DeviceInfo[]>('/device/list')
  },
  bindDevice(device_id: string, device_name: string) {
    return request<null>('/device/bind', {
      method: 'POST',
      body: JSON.stringify({ device_id, device_name }),
    })
  },
  unbindDevice(device_id: string) {
    return request<null>('/device/unbind', {
      method: 'POST',
      body: JSON.stringify({ device_id }),
    })
  },
  getLatestData(deviceId: string) {
    return request<SensorData | null>(`/data/${encodeURIComponent(deviceId)}/latest`)
  },
  sendControl(deviceId: string, command: string, value: string, params: Record<string, unknown> = {}) {
    return request<null>(`/control/${encodeURIComponent(deviceId)}`, {
      method: 'POST',
      body: JSON.stringify({ command, value, params }),
    })
  },
  getScore(deviceId: string) {
    return request<EnvironmentScore>(`/ai/${encodeURIComponent(deviceId)}/score`)
  },
  getRisks(deviceId: string) {
    return request<RiskWarnings>(`/ai/${encodeURIComponent(deviceId)}/risks`)
  },
  getSuggestions(deviceId: string, forceLlm = false) {
    const query = forceLlm ? '?force_llm=true' : ''
    return request<AiSuggestions>(`/ai/${encodeURIComponent(deviceId)}/suggestions${query}`)
  },
  getWeeklyReport(deviceId: string, forceLlm = false) {
    const query = forceLlm ? '?force_llm=true' : ''
    return request<WeeklyReport>(`/ai/${encodeURIComponent(deviceId)}/weekly-report${query}`)
  },
  getOperationLogs(deviceId?: string) {
    const query = deviceId ? `?device_id=${encodeURIComponent(deviceId)}&page_size=20` : '?page_size=20'
    return request<OperationLogPage>(`/log/operation${query}`)
  },
}
