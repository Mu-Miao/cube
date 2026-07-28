<!-- AppLayout.vue -->
<!-- 全局三栏布局：左侧固定导航 + 顶部工具栏 + 右侧内容区 -->
<template>
  <div class="app-layout" :class="{ 'app-layout--dragging': isDragging }">
    <MineradioParticleStage class="layout-particle-stage" :density="0.32" :intensity="0.34" />

    <!-- 左侧固定导航 -->
    <aside class="sidebar">
      <!-- Logo区 -->
      <div class="sidebar-logo">
        <div class="logo-bar"></div>
        <div class="logo-icon">
          <img :src="cubeLogoImg" alt="天幕智创 TMZC Logo" class="logo-image" />
        </div>
        <span class="logo-text">智能魔方</span>
      </div>

      <!-- 导航菜单 -->
      <nav class="sidebar-nav">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: currentRoute === item.path }"
          @pointerenter="prefetchRoute(item.path)"
          @pointerdown.passive="prefetchRoute(item.path)"
          @focus="prefetchRoute(item.path)"
        >
          <component :is="item.icon" class="nav-icon" />
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>

      <!-- 底部用户区 -->
      <div class="sidebar-footer">
        <MascotCompanion class="sidebar-mascot" compact state="normal" title="小眠" />
        <div class="user-info">
          <div class="user-avatar">
            {{ authStore.username ? authStore.username.charAt(0).toUpperCase() : 'U' }}
          </div>
          <span class="user-name">{{ authStore.username || '用户' }}</span>
        </div>
        <button class="logout-btn" @click="handleLogout" title="退出登录">
          <SwitchButton class="logout-icon" />
        </button>
      </div>
    </aside>

    <!-- 右侧主区域 -->
    <div class="main-area" :class="{ 'main-area--chat-open': chatOpen }" :style="chatOpen ? { marginRight: chatWidth + 'px' } : undefined">
      <!-- 顶部工具栏 -->
      <header class="top-bar">
        <div class="breadcrumb">
          <span class="breadcrumb-item" v-for="(crumb, index) in breadcrumbs" :key="index">
            <span v-if="index > 0" class="breadcrumb-separator">/</span>
            <span :class="{ 'breadcrumb-current': index === breadcrumbs.length - 1 }">
              {{ crumb }}
            </span>
          </span>
        </div>
        <div class="top-bar-right">
          <VersionSwitcher variant="toolbar" />
          <!-- 通知图标 -->
          <button class="icon-btn" title="通知">
            <Bell />
          </button>
          <!-- 小眠聊天按钮 -->
          <button class="icon-btn chat-toggle-btn" :class="{ 'chat-toggle-btn--active': chatOpen }" title="和小眠聊天" @click="chatOpen = !chatOpen">
            <img :src="mascotNormalImg" alt="小眠" class="chat-toggle-icon" />
          </button>
          <!-- 演示模式标签 -->
          <el-tag v-if="demoMode" type="warning" effect="dark" size="small" class="demo-tag">
            演示模式
          </el-tag>
        </div>
      </header>

      <!-- 内容区 -->
      <main class="content-area">
        <router-view v-slot="{ Component, route }">
          <transition name="page-load" appear>
            <component :is="Component" :key="route.fullPath" class="route-view" />
          </transition>
        </router-view>
      </main>
    </div>

    <!-- 拖拽手柄 -->
    <div
      v-show="chatOpen"
      class="chat-resize-handle"
      :class="{ 'chat-resize-handle--dragging': isDragging }"
      :style="{ right: (chatWidth - 3) + 'px' }"
      @mousedown="onResizeStart"
    />

    <!-- 小眠 AI 聊天面板 -->
    <ChatPanel v-if="chatOpen" :visible="chatOpen" :width="chatWidth" @toggle="chatOpen = !chatOpen" />
  </div>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent, ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import {
  Monitor,
  Cpu,
  Setting,
  DataAnalysis,
  Bell,
  SwitchButton,
  Tickets,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'
import { isDemoMode } from '@/utils/demo'
import { routeComponentLoaders, type PreloadableRoutePath } from '@/router/routeLoaders'
import VersionSwitcher from '@/components/VersionSwitcher.vue'
import mascotNormalImg from '@/assets/mascot/role_normal.webp'
import cubeLogoImg from '@/assets/brand/tmzc-logo.svg'

defineOptions({ name: 'AppLayout' })

const MascotCompanion = defineAsyncComponent(() => import('@/components/brand/MascotCompanion.vue'))
const MineradioParticleStage = defineAsyncComponent(() => import('@/components/brand/MineradioParticleStage.vue'))
const ChatPanel = defineAsyncComponent(() => import('@/components/ChatPanel.vue'))

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const demoMode = isDemoMode()
const chatOpen = ref(false)
const prefetchedRoutes = new Set<string>()
const navHighlightOverride = ref<string | null>(null)
let routeWarmupTimer = 0

// ====== 聊天面板拖拽调整宽度 ======
const chatWidth = ref(380)
const isDragging = ref(false)
const MIN_CHAT_WIDTH = 280
const MAX_CHAT_WIDTH = 680

function onResizeStart(e: MouseEvent) {
  e.preventDefault()
  isDragging.value = true
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function onResizeMove(e: MouseEvent) {
  if (!isDragging.value) return
  // 从右边算：窗口宽度 - 鼠标位置 = 面板宽度
  const newWidth = window.innerWidth - e.clientX
  chatWidth.value = Math.max(MIN_CHAT_WIDTH, Math.min(MAX_CHAT_WIDTH, newWidth))
}

function onResizeEnd() {
  if (!isDragging.value) return
  isDragging.value = false
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

onMounted(() => {
  window.addEventListener('mousemove', onResizeMove)
  window.addEventListener('mouseup', onResizeEnd)
  window.addEventListener('cube:navigation-highlight', handleNavigationHighlight)
  scheduleRouteWarmup()
})

onUnmounted(() => {
  window.removeEventListener('mousemove', onResizeMove)
  window.removeEventListener('mouseup', onResizeEnd)
  window.removeEventListener('cube:navigation-highlight', handleNavigationHighlight)
  window.clearTimeout(routeWarmupTimer)
})

watch(
  () => route.path,
  () => {
    navHighlightOverride.value = null
  },
)

// 菜单项配置
const baseMenuItems = [
  { path: '/teen/dashboard', label: '控制台', icon: Monitor },
  { path: '/teen/devices', label: '设备管理', icon: Cpu },
  { path: '/teen/control', label: '控制面板', icon: Setting },
  { path: '/teen/ai-analysis', label: 'AI 分析', icon: DataAnalysis },
  { path: '/teen/logs', label: '日志中心', icon: Tickets },
]
const menuItems = computed(() => baseMenuItems)

function isPreloadableRoute(path: string): path is PreloadableRoutePath {
  return path in routeComponentLoaders
}

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
      window.setTimeout(() => {
        prefetchRoute(path)
      }, index * 180)
    })
  }, 600)
}

// 当前路由路径（用于判断 active 状态）
const currentRoute = computed(() => navHighlightOverride.value || route.path)

function handleNavigationHighlight(event: Event) {
  const detail = (event as CustomEvent<{ path?: string | null }>).detail
  const path = detail?.path
  navHighlightOverride.value = typeof path === 'string' && path ? path : null
}

// 面包屑：根据当前路由自动生成
const breadcrumbs = computed(() => {
  const matched = route.matched.filter((item) => item.meta?.title)
  if (matched.length > 0) {
    return matched.map((item) => item.meta.title as string)
  }
  // 兜底：根据路由名称生成
  const routeNameMap: Record<string, string> = {
    dashboard: '控制台',
    devices: '设备管理',
    control: '控制面板',
    'ai-analysis': 'AI 分析',
    logs: '日志中心',
  }
  const name = route.name as string
  if (name && routeNameMap[name]) {
    return ['首页', routeNameMap[name]]
  }
  return ['首页']
})

// 退出登录
function handleLogout() {
  authStore.clearAuth()
  router.push('/login')
  ElMessage.success('已退出登录')
}
</script>

<style scoped>
.app-layout {
  position: relative;
  display: flex;
  width: 100%;
  min-height: 100vh;
  background: transparent;
  overflow: clip;
}

/* 拖拽时禁止子元素抢夺鼠标事件 */
.app-layout--dragging .sidebar,
.app-layout--dragging .main-area,
.app-layout--dragging .chat-panel {
  pointer-events: none;
}

.app-layout--dragging .chat-resize-handle {
  pointer-events: auto;
}

.layout-particle-stage {
  z-index: 0;
}

/* ========== 侧边栏 — 液态玻璃 ========== */
.sidebar {
  position: fixed;
  left: 10px;
  top: 10px;
  bottom: 10px;
  width: 236px;
  background:
    linear-gradient(155deg, rgba(87, 186, 255, 0.1), rgba(5, 20, 45, 0.42) 36%, rgba(69, 51, 160, 0.09)),
    rgba(3, 16, 36, 0.38);
  border: 1px solid rgba(193, 231, 255, 0.28);
  border-radius: 28px;
  box-shadow:
    14px 18px 55px rgba(0, 2, 14, 0.34),
    inset 0 1px 0 rgba(244, 252, 255, 0.34),
    inset 1px 0 0 rgba(122, 215, 255, 0.13),
    inset 0 -1px 0 rgba(77, 95, 255, 0.14);
  backdrop-filter: blur(var(--glass-blur-heavy)) saturate(var(--glass-saturation));
  -webkit-backdrop-filter: blur(var(--glass-blur-heavy)) saturate(var(--glass-saturation));
  display: flex;
  flex-direction: column;
  z-index: 100;
  overflow: hidden;
  transform-origin: left center;
  animation: sidebar-unfold 980ms cubic-bezier(0.16, 1, 0.3, 1) both;
  will-change: clip-path, transform, opacity;
}

/* 右侧高光边线 */
.sidebar::after {
  content: '';
  position: absolute;
  top: 0;
  right: -1px;
  width: 1px;
  height: 100%;
  background: linear-gradient(
    180deg,
    transparent 5%,
    rgba(255, 255, 255, 0.55) 20%,
    rgba(34, 211, 238, 0.48) 50%,
    rgba(137, 105, 255, 0.38) 80%,
    transparent 95%
  );
  opacity: 0.6;
}

/* Logo区 */
.sidebar-logo {
  height: 72px;
  display: flex;
  align-items: center;
  padding: 0 18px;
  gap: 12px;
  border-bottom: 1px solid rgba(190, 229, 255, 0.1);
  position: relative;
  animation: sidebar-item-in 720ms cubic-bezier(0.16, 1, 0.3, 1) 260ms both;
}
.logo-bar {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 30px;
  background: linear-gradient(180deg, var(--color-cube-primary), var(--color-cube-accent));
  border-radius: 0 4px 4px 0;
  box-shadow: 0 0 16px rgba(34, 211, 238, 0.4);
}
.logo-icon {
  flex-shrink: 0;
  width: 46px;
  height: 46px;
  display: grid;
  place-items: center;
  position: relative;
  border-radius: 15px;
  background:
    radial-gradient(circle at 35% 24%, rgba(255, 255, 255, 0.22), transparent 36%),
    linear-gradient(145deg, rgba(34, 211, 238, 0.18), rgba(91, 63, 255, 0.08));
  box-shadow:
    inset 0 0 0 1px rgba(188, 235, 255, 0.2),
    0 10px 24px rgba(0, 0, 0, 0.18),
    0 0 22px rgba(34, 211, 238, 0.12);
}
.logo-icon::before {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: inherit;
  padding: 1px;
  background: linear-gradient(
    135deg,
    rgba(34, 211, 238, 0.5),
    transparent 36%,
    rgba(163, 230, 53, 0.3)
  );
  mask:
    linear-gradient(#000 0 0) content-box,
    linear-gradient(#000 0 0);
  mask-composite: exclude;
  opacity: 0.7;
}
.logo-image {
  position: relative;
  z-index: 1;
  width: 42px;
  height: 42px;
  object-fit: contain;
  filter:
    drop-shadow(0 7px 10px rgba(0, 0, 0, 0.22))
    drop-shadow(0 0 12px rgba(34, 211, 238, 0.26));
}
.logo-text {
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 0;
}

/* 导航菜单 */
.sidebar-nav {
  flex: 1;
  padding: 14px 10px;
  overflow-y: auto;
}
.nav-item {
  display: flex;
  align-items: center;
  height: 46px;
  padding: 0 14px;
  gap: 12px;
  margin-bottom: 4px;
  text-decoration: none;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  border: 1px solid transparent;
  border-radius: 14px;
  transition:
    transform var(--transition-spring),
    color var(--transition-fast),
    background var(--transition-base),
    border-color var(--transition-base),
    box-shadow var(--transition-base);
  position: relative;
  cursor: pointer;
  overflow: hidden;
  animation: sidebar-item-in 720ms cubic-bezier(0.16, 1, 0.3, 1) both;
}

.nav-item:nth-child(1) { animation-delay: 360ms; }
.nav-item:nth-child(2) { animation-delay: 450ms; }
.nav-item:nth-child(3) { animation-delay: 540ms; }
.nav-item:nth-child(4) { animation-delay: 630ms; }
.nav-item:nth-child(5) { animation-delay: 720ms; }
.nav-item:nth-child(6) { animation-delay: 810ms; }
.nav-item:hover {
  color: var(--text-primary);
  background: rgba(125, 207, 255, 0.09);
  border-color: rgba(188, 232, 255, 0.16);
  transform: translateX(3px);
}
.nav-item.active {
  color: var(--color-cube-primary);
  background:
    linear-gradient(105deg, rgba(89, 211, 255, 0.2), rgba(105, 165, 255, 0.09) 48%, rgba(149, 103, 255, 0.14)),
    rgba(81, 178, 255, 0.08);
  border-color: rgba(154, 230, 255, 0.5);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.34),
    inset 0 -1px 0 rgba(57, 132, 255, 0.18),
    0 0 22px rgba(40, 194, 255, 0.16),
    0 10px 24px rgba(0, 4, 20, 0.18);
  backdrop-filter: blur(20px) saturate(1.9);
  -webkit-backdrop-filter: blur(20px) saturate(1.9);
}
.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 24px;
  background: linear-gradient(180deg, var(--color-cube-primary), var(--color-cube-accent));
  border-radius: 0 4px 4px 0;
  box-shadow: 0 0 12px rgba(34, 211, 238, 0.4);
}
.nav-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}
.nav-label {
  white-space: nowrap;
  position: relative;
  z-index: 1;
}

/* 底部用户区 */
.sidebar-footer {
  padding: 14px 16px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  display: grid;
  grid-template-columns: 1fr 32px;
  gap: 12px;
  background: linear-gradient(180deg, rgba(79, 176, 255, 0.025), rgba(67, 113, 255, 0.07));
  animation: sidebar-item-in 720ms cubic-bezier(0.16, 1, 0.3, 1) 920ms both;
}

.sidebar-mascot {
  grid-column: 1 / -1;
  width: 100%;
}

.sidebar-footer .user-info,
.sidebar-footer .logout-btn {
  position: relative;
  z-index: 1;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.user-avatar {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-full);
  background: linear-gradient(135deg, var(--color-cube-primary), var(--color-cube-violet));
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
  box-shadow: 0 0 16px rgba(34, 211, 238, 0.15);
}
.user-name {
  font-size: 14px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.logout-btn {
  width: 32px;
  height: 32px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--text-disabled);
  cursor: pointer;
  padding: 0;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}
.logout-btn:hover {
  color: var(--color-danger);
  background: var(--color-danger-dim);
  border-color: rgba(248, 113, 113, 0.2);
}
.logout-icon {
  width: 18px;
  height: 18px;
}

/* ========== 主区域 ========== */
.main-area {
  position: relative;
  z-index: 1;
  flex: 1;
  margin-left: 246px;
  width: calc(100% - 246px);
  min-width: 0;
  max-width: calc(100% - 246px);
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* 顶栏 — 液态玻璃 */
.top-bar {
  position: sticky;
  top: 10px;
  z-index: 110;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  margin: 0 14px;
  background:
    linear-gradient(110deg, rgba(94, 190, 255, 0.08), rgba(5, 18, 42, 0.38) 42%, rgba(117, 83, 255, 0.08)),
    rgba(4, 17, 38, 0.38);
  backdrop-filter: blur(var(--glass-blur-heavy)) saturate(var(--glass-saturation));
  -webkit-backdrop-filter: blur(var(--glass-blur-heavy)) saturate(var(--glass-saturation));
  border: 1px solid rgba(190, 231, 255, 0.2);
  border-radius: 20px;
  box-shadow: 0 14px 42px rgba(0, 3, 18, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.26);
  animation: topbar-reveal 820ms cubic-bezier(0.16, 1, 0.3, 1) 260ms both;
  will-change: transform, opacity;
}

/* 面包屑 */
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  min-width: 0;
}
.breadcrumb-separator {
  color: var(--text-disabled);
  margin: 0 2px;
}
.breadcrumb-item {
  color: var(--text-disabled);
}
.breadcrumb-current {
  color: var(--text-primary);
  font-weight: 600;
}

/* 顶栏右侧 */
.top-bar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 搜索框占位 — 液态玻璃 */
.search-placeholder {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 36px;
  padding: 0 12px;
  background: rgba(115, 196, 255, 0.07);
  border: 1px solid rgba(190, 231, 255, 0.18);
  border-radius: 12px;
  color: var(--text-disabled);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-base);
  min-width: 200px;
  box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.05);
}
.search-placeholder:hover {
  border-color: rgba(34, 211, 238, 0.3);
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.08);
  box-shadow: 0 0 16px rgba(34, 211, 238, 0.06),
    inset 0 1px 1px rgba(255, 255, 255, 0.06);
}
.search-icon {
  width: 16px;
  height: 16px;
}
.search-kbd {
  margin-left: auto;
  padding: 2px 6px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-disabled);
}

/* 图标按钮 — 液态玻璃 */
.icon-btn {
  width: 36px;
  height: 36px;
  background: rgba(115, 196, 255, 0.075);
  border: 1px solid rgba(190, 231, 255, 0.2);
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25), 0 8px 18px rgba(0, 4, 20, 0.12);
  backdrop-filter: blur(18px) saturate(1.9);
  -webkit-backdrop-filter: blur(18px) saturate(1.9);
}
.icon-btn:hover {
  color: var(--text-primary);
  border-color: rgba(34, 211, 238, 0.25);
  background: rgba(255, 255, 255, 0.1);
  box-shadow: 0 0 16px rgba(34, 211, 238, 0.08);
  transform: translateY(-1px);
}

/* 演示模式标签 */
.demo-tag {
  animation: glow-pulse 2s ease-in-out infinite;
  border: 1px solid var(--border-accent) !important;
}

/* 内容区 */
.content-area {
  flex: 1;
  padding: 28px var(--spacing-page) var(--spacing-page);
  min-width: 0;
}

.route-view {
  display: block;
  min-width: 0;
}

.page-load-enter-active {
  transition:
    opacity 260ms ease,
    transform 320ms cubic-bezier(0.2, 0.8, 0.2, 1);
}

.page-load-leave-active {
  position: absolute;
  inset: 28px var(--spacing-page) auto var(--spacing-page);
  width: calc(100% - var(--spacing-page) * 2);
  transition:
    opacity 120ms ease,
    transform 120ms ease;
  pointer-events: none;
}

.page-load-enter-from {
  opacity: 0;
  transform: translateY(8px) scale(0.998);
}

.page-load-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.998);
}

.content-area :deep(.devices-page > *),
.content-area :deep(.ai-analysis-page > *),
.content-area :deep(.log-center-page > *),
.content-area :deep(.admin-page > *),
.content-area :deep(.control-page > *) {
  animation: page-block-rise 860ms cubic-bezier(0.16, 1, 0.3, 1) both;
  will-change: transform, opacity;
}

.content-area :deep(.devices-page > *:nth-child(1)),
.content-area :deep(.ai-analysis-page > *:nth-child(1)),
.content-area :deep(.log-center-page > *:nth-child(1)),
.content-area :deep(.admin-page > *:nth-child(1)),
.content-area :deep(.control-page > *:nth-child(1)) {
  animation-delay: 80ms;
}

.content-area :deep(.devices-page > *:nth-child(2)),
.content-area :deep(.ai-analysis-page > *:nth-child(2)),
.content-area :deep(.log-center-page > *:nth-child(2)),
.content-area :deep(.admin-page > *:nth-child(2)),
.content-area :deep(.control-page > *:nth-child(2)) {
  animation-delay: 220ms;
}

.content-area :deep(.devices-page > *:nth-child(3)),
.content-area :deep(.ai-analysis-page > *:nth-child(3)),
.content-area :deep(.log-center-page > *:nth-child(3)),
.content-area :deep(.admin-page > *:nth-child(3)),
.content-area :deep(.control-page > *:nth-child(3)) {
  animation-delay: 360ms;
}

.content-area :deep(.devices-page > *:nth-child(n + 4)),
.content-area :deep(.ai-analysis-page > *:nth-child(n + 4)),
.content-area :deep(.log-center-page > *:nth-child(n + 4)),
.content-area :deep(.admin-page > *:nth-child(n + 4)),
.content-area :deep(.control-page > *:nth-child(n + 4)) {
  animation-delay: 500ms;
}

@keyframes sidebar-unfold {
  from {
    opacity: 0;
    clip-path: inset(0 100% 0 0 round 28px);
    transform: translateX(-18px) scaleX(0.92);
  }
  to {
    opacity: 1;
    clip-path: inset(0 0 0 0 round 28px);
    transform: translateX(0) scaleX(1);
  }
}

@keyframes sidebar-item-in {
  from {
    opacity: 0;
    transform: translateX(-14px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes topbar-reveal {
  from {
    opacity: 0;
    transform: translateY(-14px) scale(0.992);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes page-block-rise {
  from {
    opacity: 0;
    transform: translateY(24px) scale(0.992);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* 聊天面板打开时 — margin-right 由 inline style 动态控制 */

/* 拖拽手柄 */
.chat-resize-handle {
  position: fixed;
  top: 0;
  bottom: 0;
  width: 6px;
  cursor: col-resize;
  z-index: 95;
  /* 手柄位置跟随 chatWidth：right = chatWidth - 3px (居中) */
  /* 通过 JS 的 :style 绑定无法在 scoped CSS 里直接计算，
     所以我们用 JS 设置 right 值 */
}

.chat-resize-handle:hover,
.chat-resize-handle--dragging {
  background: linear-gradient(180deg,
    transparent 10%,
    rgba(34, 211, 238, 0.25) 50%,
    transparent 90%
  );
}

/* 聊天切换按钮 */
.chat-toggle-btn {
  position: relative;
  overflow: visible;
}

.chat-toggle-icon {
  width: 22px;
  height: 22px;
  object-fit: contain;
  border-radius: 4px;
  filter: drop-shadow(0 0 4px rgba(34, 211, 238, 0.3));
  transition: transform 0.2s, filter 0.2s;
}

.chat-toggle-btn:hover .chat-toggle-icon {
  transform: scale(1.12);
  filter: drop-shadow(0 0 8px rgba(34, 211, 238, 0.5));
}

.chat-toggle-btn--active {
  color: var(--color-cube-primary) !important;
  background: rgba(34, 211, 238, 0.1) !important;
  border-color: rgba(34, 211, 238, 0.25) !important;
  box-shadow: 0 0 16px rgba(34, 211, 238, 0.1) !important;
}

@media (prefers-reduced-motion: reduce) {
  .sidebar,
  .sidebar-logo,
  .nav-item,
  .sidebar-footer,
  .top-bar,
  .content-area :deep(.devices-page > *),
  .content-area :deep(.ai-analysis-page > *),
  .content-area :deep(.log-center-page > *),
  .content-area :deep(.admin-page > *),
  .content-area :deep(.control-page > *) {
    animation: none !important;
  }

  .page-load-enter-active,
  .page-load-leave-active {
    transition: none !important;
  }

  .page-load-enter-from,
  .page-load-leave-to {
    opacity: 1;
    filter: none;
    transform: none;
  }
}

@media (max-width: 860px) {
  .sidebar {
    width: 78px;
  }

  .main-area {
    margin-left: 88px;
    width: calc(100% - 88px);
    max-width: calc(100% - 88px);
  }

  .main-area--chat-open {
    margin-right: 0;
  }

  .chat-toggle-btn {
    display: none;
  }

  .logo-text,
  .nav-label,
  .user-name {
    display: none;
  }

  .sidebar-logo,
  .nav-item,
  .sidebar-footer {
    justify-content: center;
  }

  .sidebar-footer {
    display: flex;
  }

  .sidebar-mascot {
    display: none;
  }

  .search-placeholder {
    display: none;
  }
}

@media (max-width: 520px) {
  .app-layout {
    display: block;
    width: 100%;
    min-width: 0;
    overflow-x: clip;
  }

  .sidebar {
    position: fixed;
    left: max(10px, env(safe-area-inset-left));
    right: max(10px, env(safe-area-inset-right));
    top: auto;
    bottom: max(10px, env(safe-area-inset-bottom));
    width: auto;
    height: 70px;
    z-index: 180;
    display: block;
    padding: 8px;
    border-radius: 22px;
    overflow: visible;
    transform: none;
    animation: none;
    background:
      linear-gradient(145deg, rgba(255, 255, 255, 0.09), rgba(4, 17, 38, 0.48)),
      rgba(7, 14, 28, 0.78);
    box-shadow:
      0 18px 54px rgba(0, 0, 0, 0.38),
      inset 0 1px 0 rgba(255, 255, 255, 0.22);
  }

  .sidebar::after,
  .sidebar-logo,
  .sidebar-footer {
    display: none;
  }

  .sidebar-nav {
    width: 100%;
    height: 100%;
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 4px;
    padding: 0;
    overflow: visible;
  }

  .nav-item {
    height: 54px;
    min-width: 0;
    display: grid;
    grid-template-rows: 22px 16px;
    place-items: center;
    align-content: center;
    gap: 3px;
    margin: 0;
    padding: 0 2px;
    border-radius: 16px;
    font-size: 11px;
    line-height: 1;
    animation: none;
    transform: none;
  }

  .nav-item:hover {
    transform: none;
  }

  .nav-item.active::before {
    display: none;
  }

  .nav-icon {
    width: 20px;
    height: 20px;
  }

  .nav-label {
    display: block;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 11px;
  }

  .main-area {
    margin-left: 0;
    width: 100%;
    max-width: 100%;
    min-width: 0;
  }

  .main-area--chat-open {
    margin-right: 0 !important;
  }

  .top-bar {
    top: 0;
    height: 58px;
    margin: 0;
    padding-inline: 16px;
    border-radius: 0;
    border-inline: 0;
    border-top: 0;
    background:
      linear-gradient(180deg, rgba(3, 12, 28, 0.94), rgba(3, 12, 28, 0.66));
  }

  .breadcrumb {
    font-size: 13px;
  }

  .breadcrumb-item:not(:last-child),
  .breadcrumb-separator {
    display: none;
  }

  .top-bar-right {
    display: flex;
    gap: 8px;
  }

  .top-bar-right .icon-btn,
  .top-bar-right .demo-tag {
    display: none;
  }

  .top-bar-right :deep(.version-switcher__panel) {
    right: 0;
    width: min(282px, calc(100vw - 28px));
  }

  .content-area {
    padding: 18px 12px calc(94px + env(safe-area-inset-bottom));
    width: 100%;
    min-width: 0;
  }
}
</style>
