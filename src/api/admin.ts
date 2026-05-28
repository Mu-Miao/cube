import api from './index'

export interface AdminStats {
  user_count: number
  device_count: number
  online_count: number
  data_count: number
}

export interface AdminUser {
  id: number
  username: string
  email: string | null
  role: 'user' | 'admin'
  is_active: boolean
  created_at: string | null
}

export interface AdminDevice {
  id: number
  device_id: string
  device_name: string
  status: 'online' | 'offline'
  bound_user_id: number | null
  chip_model: string | null
  firmware_version: string | null
  last_seen: string | null
}

export const getAdminStats = () => {
  return api.get('/admin/stats') as Promise<AdminStats>
}

export const getAdminUsers = () => {
  return api.get('/admin/users') as Promise<AdminUser[]>
}

export const updateUserStatus = (userId: number, isActive: boolean) => {
  return api.put(`/admin/users/${userId}/status`, { is_active: isActive }) as Promise<unknown>
}

export const getAdminDevices = () => {
  return api.get('/admin/devices') as Promise<AdminDevice[]>
}

export const deleteAdminDevice = (deviceId: string) => {
  return api.delete(`/admin/devices/${deviceId}`) as Promise<unknown>
}
