<!-- AppLayout.vue -->
<!-- 全局三栏布局：左侧固定导航 + 顶部工具栏 + 右侧内容区 -->
<template>
  <div class="app-layout">
    <!-- 左侧固定导航 -->
    <aside class="sidebar">
      <!-- Logo区 -->
      <div class="sidebar-logo">
        <div class="logo-bar"></div>
        <div class="logo-icon">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="2" y="2" width="28" height="28" rx="6" stroke="#06B6D4" stroke-width="2" fill="rgba(6,182,212,0.08)"/>
            <rect x="8" y="8" width="6" height="6" rx="1" fill="#06B6D4"/>
            <rect x="18" y="8" width="6" height="6" rx="1" fill="#06B6D4" opacity="0.6"/>
            <rect x="8" y="18" width="6" height="6" rx="1" fill="#06B6D4" opacity="0.6"/>
            <rect x="18" y="18" width="6" height="6" rx="1" fill="#06B6D4" opacity="0.3"/>
          </svg>
        </div>
        <span class="logo-text">魔方</span>
      </div>

      <!-- 导航菜单 -->
      <nav class="sidebar-nav">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: currentRoute === item.path }"
        >
          <component :is="item.icon" class="nav-icon" />
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>

      <!-- 底部用户区 -->
      <div class="sidebar-footer">
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
    <div class="main-area">
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
          <!-- 搜索框占位 -->
          <div class="search-placeholder">
            <Search class="search-icon" />
            <span>搜索...</span>
            <kbd class="search-kbd">⌘K</kbd>
          </div>
          <!-- 通知图标 -->
          <button class="icon-btn" title="通知">
            <Bell />
          </button>
          <!-- 演示模式标签 -->
          <el-tag
            v-if="demoMode"
            type="warning"
            effect="dark"
            size="small"
            class="demo-tag"
          >
            演示模式
          </el-tag>
        </div>
      </header>

      <!-- 内容区 -->
      <main class="content-area">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Monitor, Cpu, Setting, DataAnalysis, Search, Bell, SwitchButton, Tickets, UserFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'
import { isDemoMode } from '@/utils/demo'

defineOptions({ name: 'AppLayout' })

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const demoMode = isDemoMode()

// 菜单项配置
const baseMenuItems = [
  { path: '/dashboard', label: '控制台', icon: Monitor },
  { path: '/devices', label: '设备管理', icon: Cpu },
  { path: '/control', label: '控制面板', icon: Setting },
  { path: '/ai-analysis', label: 'AI 分析', icon: DataAnalysis },
  { path: '/logs', label: '日志中心', icon: Tickets },
]
const menuItems = computed(() => {
  const items = [...baseMenuItems]
  if (authStore.isAdmin || demoMode) {
    items.push({ path: '/admin', label: '管理员', icon: UserFilled })
  }
  return items
})

// 当前路由路径（用于判断 active 状态）
const currentRoute = computed(() => route.path)

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
    admin: '管理员后台',
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
  display: flex;
  width: 100%;
  min-height: 100vh;
  background: transparent;
}

/* ========== 侧边栏 ========== */
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 236px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.055), rgba(255, 255, 255, 0.01)),
    linear-gradient(150deg, rgba(6, 182, 212, 0.08), transparent 38%),
    var(--bg-control);
  border-right: var(--border-glass);
  box-shadow: 18px 0 42px rgba(0, 0, 0, 0.22);
  backdrop-filter: blur(20px) saturate(1.24);
  -webkit-backdrop-filter: blur(20px) saturate(1.24);
  display: flex;
  flex-direction: column;
  z-index: 100;
  overflow: hidden;
}

.sidebar::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 1px;
  height: 100%;
  background: linear-gradient(180deg, transparent, rgba(6, 182, 212, 0.58), rgba(163, 230, 53, 0.24), transparent);
  opacity: 0.74;
}

/* Logo区 */
.sidebar-logo {
  height: 72px;
  display: flex;
  align-items: center;
  padding: 0 18px;
  gap: 12px;
  border-bottom: var(--border-default);
  position: relative;
}
.logo-bar {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 30px;
  background: linear-gradient(180deg, var(--color-cube-primary), var(--color-cube-accent));
  border-radius: 0 2px 2px 0;
  box-shadow: 0 0 20px rgba(6, 182, 212, 0.5);
}
.logo-icon {
  flex-shrink: 0;
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  position: relative;
  border-radius: 10px;
  background: rgba(6, 182, 212, 0.08);
  box-shadow: inset 0 0 0 1px rgba(6, 182, 212, 0.22), 0 0 24px rgba(6, 182, 212, 0.12);
}
.logo-icon::before {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: inherit;
  padding: 1px;
  background: linear-gradient(135deg, var(--color-cube-primary), transparent 36%, var(--color-cube-accent));
  mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  mask-composite: exclude;
  opacity: 0.8;
}
.logo-icon svg {
  position: relative;
  z-index: 1;
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
  padding: 0 12px;
  gap: 12px;
  margin-bottom: 6px;
  text-decoration: none;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  border: 1px solid transparent;
  border-radius: 10px;
  transition:
    transform var(--transition-spring),
    color var(--transition-fast),
    background var(--transition-base),
    border-color var(--transition-base),
    box-shadow var(--transition-base);
  position: relative;
  cursor: pointer;
  overflow: hidden;
}
.nav-item::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.08), transparent);
  transform: translateX(-120%);
  transition: transform var(--transition-slow);
}
.nav-item:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.045);
  border-color: rgba(255, 255, 255, 0.08);
  transform: translateX(3px);
}
.nav-item:hover::after {
  transform: translateX(120%);
}
.nav-item.active {
  color: var(--color-cube-primary);
  background:
    linear-gradient(90deg, rgba(6, 182, 212, 0.16), rgba(163, 230, 53, 0.06)),
    rgba(255, 255, 255, 0.035);
  border-color: rgba(6, 182, 212, 0.28);
  box-shadow: inset 0 0 22px rgba(6, 182, 212, 0.08), 0 10px 24px rgba(0, 0, 0, 0.12);
}
.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 26px;
  background: linear-gradient(180deg, var(--color-cube-primary), var(--color-cube-accent));
  border-radius: 0 2px 2px 0;
  box-shadow: 0 0 16px rgba(6, 182, 212, 0.45);
}
.nav-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  position: relative;
  z-index: 1;
  filter: drop-shadow(0 0 8px rgba(6, 182, 212, 0.12));
}
.nav-label {
  white-space: nowrap;
  position: relative;
  z-index: 1;
}

/* 底部用户区 */
.sidebar-footer {
  padding: 14px 16px 16px;
  border-top: var(--border-default);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.018);
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
  box-shadow: 0 0 18px rgba(6, 182, 212, 0.22);
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
  background: rgba(255, 255, 255, 0.035);
  border: 1px solid rgba(255, 255, 255, 0.06);
  color: var(--text-disabled);
  cursor: pointer;
  padding: 0;
  border-radius: var(--radius-button);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}
.logout-btn:hover {
  color: var(--color-danger);
  background: var(--color-danger-dim);
  border-color: rgba(239, 68, 68, 0.25);
}
.logout-icon {
  width: 18px;
  height: 18px;
}

/* ========== 主区域 ========== */
.main-area {
  flex: 1;
  margin-left: 236px;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* 顶栏 */
.top-bar {
  position: sticky;
  top: 0;
  z-index: 50;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background:
    linear-gradient(90deg, rgba(6, 182, 212, 0.06), transparent 34%, rgba(163, 230, 53, 0.035)),
    rgba(7, 9, 13, 0.78);
  backdrop-filter: blur(18px) saturate(1.2);
  -webkit-backdrop-filter: blur(18px) saturate(1.2);
  border-bottom: var(--border-glass);
  box-shadow: 0 14px 34px rgba(0, 0, 0, 0.18);
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

/* 搜索框占位 */
.search-placeholder {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 36px;
  padding: 0 10px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.055), rgba(255, 255, 255, 0.012)),
    rgba(13, 18, 25, 0.82);
  border: var(--border-default);
  border-radius: 10px;
  color: var(--text-disabled);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-base);
  min-width: 200px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.035);
}
.search-placeholder:hover {
  border-color: rgba(6, 182, 212, 0.36);
  color: var(--text-secondary);
  box-shadow: 0 0 22px rgba(6, 182, 212, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.045);
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
  border-radius: 4px;
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-disabled);
}

/* 图标按钮 */
.icon-btn {
  width: 36px;
  height: 36px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.052), rgba(255, 255, 255, 0.012)),
    rgba(13, 18, 25, 0.82);
  border: var(--border-default);
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}
.icon-btn:hover {
  color: var(--text-primary);
  border-color: rgba(6, 182, 212, 0.32);
  box-shadow: 0 0 20px rgba(6, 182, 212, 0.12);
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
  padding: var(--spacing-page);
  min-width: 0;
}

@media (max-width: 860px) {
  .sidebar {
    width: 78px;
  }

  .main-area {
    margin-left: 78px;
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

  .search-placeholder {
    display: none;
  }
}
</style>
