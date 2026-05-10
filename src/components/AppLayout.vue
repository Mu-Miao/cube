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
import { Monitor, Cpu, Setting, DataAnalysis, Search, Bell, SwitchButton } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'
import { isDemoMode } from '@/utils/demo'

defineOptions({ name: 'AppLayout' })

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const demoMode = isDemoMode()

// 菜单项配置
const menuItems = [
  { path: '/dashboard', label: '控制台', icon: Monitor },
  { path: '/devices', label: '设备管理', icon: Cpu },
  { path: '/control', label: '控制面板', icon: Setting },
  { path: '/ai-analysis', label: 'AI 分析', icon: DataAnalysis },
]

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
}

/* ========== 侧边栏 ========== */
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 220px;
  background: var(--bg-surface);
  border-right: var(--border-default);
  display: flex;
  flex-direction: column;
  z-index: 100;
}

/* Logo区 */
.sidebar-logo {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  gap: 10px;
  border-bottom: var(--border-default);
  position: relative;
}
.logo-bar {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 24px;
  background: var(--color-cube-primary);
  border-radius: 0 2px 2px 0;
}
.logo-icon {
  flex-shrink: 0;
}
.logo-text {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0.5px;
}

/* 导航菜单 */
.sidebar-nav {
  flex: 1;
  padding: 12px 0;
  overflow-y: auto;
}
.nav-item {
  display: flex;
  align-items: center;
  height: 44px;
  padding: 0 16px;
  gap: 10px;
  text-decoration: none;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  transition: all var(--transition-fast);
  position: relative;
  cursor: pointer;
}
.nav-item:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}
.nav-item.active {
  color: var(--color-cube-primary);
  background: rgba(6, 182, 212, 0.08);
}
.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 24px;
  background: var(--color-cube-primary);
  border-radius: 0 2px 2px 0;
}
.nav-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}
.nav-label {
  white-space: nowrap;
}

/* 底部用户区 */
.sidebar-footer {
  padding: 12px 16px;
  border-top: var(--border-default);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  background: linear-gradient(135deg, var(--color-cube-primary), #0891B2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
}
.user-name {
  font-size: 14px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.logout-btn {
  background: none;
  border: none;
  color: var(--text-disabled);
  cursor: pointer;
  padding: 4px;
  border-radius: var(--radius-button);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}
.logout-btn:hover {
  color: var(--color-danger);
  background: var(--color-danger-dim);
}
.logout-icon {
  width: 18px;
  height: 18px;
}

/* ========== 主区域 ========== */
.main-area {
  flex: 1;
  margin-left: 220px;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* 顶栏 */
.top-bar {
  position: sticky;
  top: 0;
  z-index: 50;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--spacing-card);
  background: rgba(11, 15, 25, 0.8);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: var(--border-default);
}

/* 面包屑 */
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
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
  font-weight: 500;
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
  padding: 6px 12px;
  background: var(--bg-surface);
  border: var(--border-default);
  border-radius: var(--radius-button);
  color: var(--text-disabled);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
  min-width: 200px;
}
.search-placeholder:hover {
  border-color: var(--border-hover);
  color: var(--text-secondary);
}
.search-icon {
  width: 16px;
  height: 16px;
}
.search-kbd {
  margin-left: auto;
  padding: 1px 6px;
  background: var(--bg-elevated);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 4px;
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-disabled);
}

/* 图标按钮 */
.icon-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 6px;
  border-radius: var(--radius-button);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}
.icon-btn:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
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
}
</style>
