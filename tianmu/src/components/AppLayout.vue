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
import { defineAsyncComponent } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { Bell, SwitchButton } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { isDemoMode } from '@/utils/demo'
import { useLayoutNavigation } from '@/composables/useLayoutNavigation'
import { useResizableChat } from '@/composables/useResizableChat'
import VersionSwitcher from '@/components/VersionSwitcher.vue'
import mascotNormalImg from '@/assets/mascot/role_normal.webp'
import cubeLogoImg from '@/assets/brand/tmzc-logo.svg'

defineOptions({ name: 'AppLayout' })

const MascotCompanion = defineAsyncComponent(() => import('@/components/brand/MascotCompanion.vue'))
const MineradioParticleStage = defineAsyncComponent(() => import('@/components/brand/MineradioParticleStage.vue'))
const ChatPanel = defineAsyncComponent(() => import('@/components/ChatPanel.vue'))

const router = useRouter()
const authStore = useAuthStore()
const demoMode = isDemoMode()
const { chatOpen, chatWidth, isDragging, onResizeStart } = useResizableChat()
const { breadcrumbs, currentRoute, menuItems, prefetchRoute } = useLayoutNavigation()

// 退出登录
async function handleLogout() {
  await authStore.signOut()
  await router.push('/login')
  ElMessage.success('已退出登录')
}
</script>

<style scoped src="./styles/AppLayout.css"></style>
