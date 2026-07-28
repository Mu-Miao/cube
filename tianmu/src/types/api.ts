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

export type AiSuggestion = { icon: string; title: string; desc: string }
export type AiSuggestions = { suggestions: AiSuggestion[]; source?: 'llm' | 'rule' }
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
