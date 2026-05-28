import api from './index'

export interface OperationLogItem {
  id: number
  user_id: number | null
  device_id: string | null
  action: string
  detail: string | null
  ip_address: string | null
  created_at: string
}

export interface VoiceLogItem {
  id: number
  user_id: number | null
  device_id: string | null
  command_text: string
  intent: string | null
  executed: boolean
  response_text: string | null
  created_at: string
}

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export const getOperationLogs = (params?: {
  device_id?: string
  action?: string
  page?: number
  page_size?: number
}) => {
  return api.get('/log/operation', { params }) as Promise<PageResult<OperationLogItem>>
}

export const getVoiceLogs = (params?: {
  device_id?: string
  intent?: string
  page?: number
  page_size?: number
}) => {
  return api.get('/log/voice', { params }) as Promise<PageResult<VoiceLogItem>>
}
