import axios from 'axios'
import { isDemoMode } from '@/utils/demoMode'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'
let accessToken = ''
let refreshPromise: Promise<string> | null = null
const accessTokenListeners = new Set<(token: string) => void>()

export function createDemoAccessToken() {
  const encode = (value: Record<string, unknown>) => (
    btoa(JSON.stringify(value)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
  )
  return `${encode({ alg: 'none', typ: 'JWT' })}.${encode({
    username: 'admin',
    role: 'admin',
    demo: true,
  })}.demo`
}

export function getAccessToken() {
  return accessToken
}

export function setAccessToken(token: string) {
  accessToken = token
  accessTokenListeners.forEach((listener) => listener(token))
}

export function clearAccessToken() {
  accessToken = ''
  accessTokenListeners.forEach((listener) => listener(''))
}

export function onAccessTokenChange(listener: (token: string) => void) {
  accessTokenListeners.add(listener)
  return () => accessTokenListeners.delete(listener)
}

export function getSessionIdentity(): {
  username: string
  role: 'user' | 'admin'
} {
  if (!accessToken) return { username: '', role: 'user' }
  try {
    const payloadPart = accessToken.split('.')[1]
    if (!payloadPart) return { username: '', role: 'user' }
    const normalized = payloadPart.replace(/-/g, '+').replace(/_/g, '/')
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=')
    const payload = JSON.parse(atob(padded)) as {
      username?: unknown
      role?: unknown
    }
    return {
      username: typeof payload.username === 'string' ? payload.username : '',
      role: payload.role === 'admin' ? 'admin' : 'user',
    }
  } catch {
    return { username: '', role: 'user' }
  }
}

export async function refreshAccessToken(): Promise<string> {
  if (!refreshPromise) {
    refreshPromise = axios
      .post(
        `${API_BASE}/auth/refresh`,
        {},
        { withCredentials: true },
      )
      .then((response) => {
        const token = response.data?.data?.access_token as string | undefined
        if (!token) throw new Error('刷新登录状态失败')
        setAccessToken(token)
        return token
      })
      .finally(() => {
        refreshPromise = null
      })
  }
  return refreshPromise
}

export async function bootstrapSession() {
  if (isDemoMode()) {
    setAccessToken(createDemoAccessToken())
    return true
  }
  try {
    await refreshAccessToken()
    return true
  } catch {
    clearAccessToken()
    return false
  }
}

export function notifyAuthExpired() {
  clearAccessToken()
  window.dispatchEvent(new CustomEvent('cube:auth-expired'))
}
