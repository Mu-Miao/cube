export const routeComponentLoaders = {
  '/dashboard': () => import('@/views/Dashboard.vue'),
  '/devices': () => import('@/views/Devices.vue'),
  '/control': () => import('@/views/Control.vue'),
  '/ai-analysis': () => import('@/views/AiAnalysis.vue'),
  '/logs': () => import('@/views/LogCenter.vue'),
  '/admin': () => import('@/views/AdminPanel.vue'),
} as const

export type PreloadableRoutePath = keyof typeof routeComponentLoaders
