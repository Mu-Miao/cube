type FrontendEnv = {
  apiBaseUrl: string
  wsBaseUrl: string
  appTitle: string
  appVersion: string
  debug: boolean
}

function requireString(name: string, fallback: string) {
  const value = (import.meta.env[name] as string | undefined)?.trim() || fallback
  if (!value) throw new Error(`缺少前端环境变量：${name}`)
  return value
}

export function validateEnv(): FrontendEnv {
  const apiBaseUrl = requireString('VITE_API_BASE_URL', '/api/v1')
  const wsBaseUrl = (import.meta.env.VITE_WS_BASE_URL as string | undefined)?.trim() || ''
  if (!apiBaseUrl.startsWith('/') && !/^https?:\/\//.test(apiBaseUrl)) {
    throw new Error('VITE_API_BASE_URL 必须是绝对 URL 或以 / 开头的路径')
  }
  if (wsBaseUrl && !/^wss?:\/\//.test(wsBaseUrl)) {
    throw new Error('VITE_WS_BASE_URL 必须以 ws:// 或 wss:// 开头')
  }
  return {
    apiBaseUrl,
    wsBaseUrl,
    appTitle: requireString('VITE_APP_TITLE', '智能桌面魔方'),
    appVersion: requireString('VITE_APP_VERSION', '0.0.0'),
    debug: import.meta.env.VITE_DEBUG === 'true',
  }
}

export const env = validateEnv()
