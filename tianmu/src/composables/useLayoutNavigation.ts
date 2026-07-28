import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Cpu, DataAnalysis, Monitor, Setting, Tickets } from '@element-plus/icons-vue'

import {
  routeComponentLoaders,
  type PreloadableRoutePath,
} from '@/router/routeLoaders'

const baseMenuItems = [
  { path: '/teen/dashboard', label: '控制台', icon: Monitor },
  { path: '/teen/devices', label: '设备管理', icon: Cpu },
  { path: '/teen/control', label: '控制面板', icon: Setting },
  { path: '/teen/ai-analysis', label: 'AI 分析', icon: DataAnalysis },
  { path: '/teen/logs', label: '日志中心', icon: Tickets },
]

const routeNameMap: Record<string, string> = {
  dashboard: '控制台',
  devices: '设备管理',
  control: '控制面板',
  'ai-analysis': 'AI 分析',
  logs: '日志中心',
}

function isPreloadableRoute(path: string): path is PreloadableRoutePath {
  return path in routeComponentLoaders
}

export function useLayoutNavigation() {
  const route = useRoute()
  const prefetchedRoutes = new Set<string>()
  const navHighlightOverride = ref<string | null>(null)
  let routeWarmupTimer = 0

  const menuItems = computed(() => baseMenuItems)
  const currentRoute = computed(() => navHighlightOverride.value || route.path)
  const breadcrumbs = computed(() => {
    const matched = route.matched.filter((item) => item.meta?.title)
    if (matched.length > 0) {
      return matched.map((item) => item.meta.title as string)
    }
    const name = route.name as string
    return name && routeNameMap[name] ? ['首页', routeNameMap[name]] : ['首页']
  })

  function prefetchRoute(path: string) {
    if (!isPreloadableRoute(path) || prefetchedRoutes.has(path)) return
    prefetchedRoutes.add(path)
    void routeComponentLoaders[path]().catch(() => {
      prefetchedRoutes.delete(path)
    })
  }

  function scheduleRouteWarmup() {
    routeWarmupTimer = window.setTimeout(() => {
      const paths = menuItems.value
        .map((item) => item.path)
        .filter((path) => path !== currentRoute.value)
      paths.forEach((path, index) => {
        window.setTimeout(() => prefetchRoute(path), index * 180)
      })
    }, 600)
  }

  function handleNavigationHighlight(event: Event) {
    const path = (event as CustomEvent<{ path?: string | null }>).detail?.path
    navHighlightOverride.value = typeof path === 'string' && path ? path : null
  }

  onMounted(() => {
    window.addEventListener('cube:navigation-highlight', handleNavigationHighlight)
    scheduleRouteWarmup()
  })

  onUnmounted(() => {
    window.removeEventListener('cube:navigation-highlight', handleNavigationHighlight)
    window.clearTimeout(routeWarmupTimer)
  })

  watch(
    () => route.path,
    () => {
      navHighlightOverride.value = null
    },
  )

  return {
    breadcrumbs,
    currentRoute,
    menuItems,
    prefetchRoute,
  }
}
