import service from './index'
import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from './session'
import type {
  AiSuggestions,
  DeviceInfo,
  EnvironmentScore,
  LoginResult,
  OperationLogPage,
  RiskWarnings,
  SensorData,
  WeeklyReport,
} from '@/types/api'

export const getToken = getAccessToken
export const setToken = setAccessToken
export const clearToken = clearAccessToken
export const getApiBase = () => import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const versionApi = {
  login(username: string, password: string) {
    return service.post('/auth/login', { username, password }) as Promise<LoginResult>
  },
  register(username: string, password: string) {
    return service.post('/auth/register', { username, password }) as Promise<{ id: number }>
  },
  logout() {
    return service.post('/auth/logout')
  },
  getDevices: () => service.get('/device/list') as Promise<DeviceInfo[]>,
  bindDevice: (device_id: string, device_name: string) =>
    service.post('/device/bind', { device_id, device_name }),
  unbindDevice: (device_id: string) => service.post('/device/unbind', { device_id }),
  renameDevice: (deviceId: string, device_name: string) =>
    service.put(`/device/${encodeURIComponent(deviceId)}/rename`, { device_name }),
  getLatestData: (deviceId: string) =>
    service.get(`/data/${encodeURIComponent(deviceId)}/latest`) as Promise<SensorData | null>,
  getHistory: (deviceId: string, hours = 24, limit = 80) =>
    service.get(`/data/${encodeURIComponent(deviceId)}/history`, {
      params: { hours, limit },
    }) as Promise<SensorData[]>,
  sendControl: (
    deviceId: string,
    command: string,
    value: string,
    params: Record<string, unknown> = {},
  ) => service.post(`/control/${encodeURIComponent(deviceId)}`, { command, value, params }),
  getScore: (deviceId: string) =>
    service.get(`/ai/${encodeURIComponent(deviceId)}/score`) as Promise<EnvironmentScore>,
  getRisks: (deviceId: string) =>
    service.get(`/ai/${encodeURIComponent(deviceId)}/risks`) as Promise<RiskWarnings>,
  getSuggestions: (deviceId: string, forceLlm = false) =>
    service.get(`/ai/${encodeURIComponent(deviceId)}/suggestions`, {
      params: { force_llm: forceLlm || undefined },
    }) as Promise<AiSuggestions>,
  getWeeklyReport: (deviceId: string, forceLlm = false) =>
    service.get(`/ai/${encodeURIComponent(deviceId)}/weekly-report`, {
      params: { force_llm: forceLlm || undefined },
    }) as Promise<WeeklyReport>,
  getOperationLogs: (deviceId?: string) =>
    service.get('/log/operation', {
      params: { device_id: deviceId, page_size: 20 },
    }) as Promise<OperationLogPage>,
}
