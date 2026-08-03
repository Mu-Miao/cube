export const routeComponentLoaders = {
  '/teen/dashboard': () => import('@/views/Dashboard.vue'),
  '/teen/devices': () => import('@/views/Devices.vue'),
  '/teen/control': () => import('@/views/Control.vue'),
  '/teen/ai-analysis': () => import('@/views/AiAnalysis.vue'),
  '/teen/logs': () => import('@/views/LogCenter.vue'),
  '/teen/admin': () => import('@/views/AdminPanel.vue'),
} as const

export type PreloadableRoutePath = keyof typeof routeComponentLoaders
