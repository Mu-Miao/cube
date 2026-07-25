// src/router/index.ts
// Vue Router 路由配置
// 定义所有页面的路由路径、懒加载组件、鉴权元信息
// 导航守卫：未登录时拦截需要认证的路由

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import { isDemoMode } from '@/utils/demoMode'
import { routeComponentLoaders } from './routeLoaders'

const router = createRouter({
  // 使用 HTML5 History 模式（无 # 号的路由）
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // 登录页（无需认证）
    {
      path: '/login',
      name: 'login',
      component: () => import('@/versions/public/App.vue'),
      meta: { requiresAuth: false },
    },
    // 注册页（无需认证）
    {
      path: '/register',
      name: 'register',
      component: () => import('@/versions/public/App.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/public',
      name: 'public-version',
      component: () => import('@/versions/public/App.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/senior',
      name: 'senior-version',
      component: () => import('@/versions/senior/App.vue'),
      meta: { requiresAuth: false },
    },
    // 带布局的主页面（需要登录认证）
    {
      path: '/teen',
      component: () => import('@/components/AppLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          redirect: '/teen/dashboard',
        },
        {
          path: 'dashboard',
          name: 'dashboard',
          component: routeComponentLoaders['/teen/dashboard'],
          meta: { title: '控制台' },
        },
        {
          path: 'devices',
          name: 'devices',
          component: routeComponentLoaders['/teen/devices'],
          meta: { title: '设备管理' },
        },
        {
          path: 'control',
          name: 'control',
          component: routeComponentLoaders['/teen/control'],
          meta: { title: '控制面板' },
        },
        {
          path: 'ai-analysis',
          name: 'ai-analysis',
          component: routeComponentLoaders['/teen/ai-analysis'],
          meta: { title: 'AI 分析' },
        },
        {
          path: 'logs',
          name: 'logs',
          component: routeComponentLoaders['/teen/logs'],
          meta: { title: '日志中心' },
        },
      ],
    },
    {
      path: '/',
      redirect: '/public',
    },
    {
      path: '/dashboard',
      redirect: '/public',
    },
    {
      path: '/devices',
      redirect: '/public',
    },
    {
      path: '/control',
      redirect: '/public',
    },
    {
      path: '/ai-analysis',
      redirect: '/public',
    },
    {
      path: '/logs',
      redirect: '/public',
    },
    // 404 兜底：默认进入大众版
    {
      path: '/:pathMatch(.*)*',
      redirect: '/public',
    },
  ],
})

// 全局导航守卫：在路由跳转前执行
router.beforeEach((to) => {
  const authStore = useAuthStore()
  // 与 API、WebSocket 共用同一套演示模式判断，避免状态不一致。
  const isDemo = isDemoMode()
  const storedToken = localStorage.getItem('token')

  if (!authStore.isLoggedIn && storedToken) {
    authStore.setAuth({
      token: storedToken,
      username: localStorage.getItem('username') || '用户',
      role: (localStorage.getItem('role') as 'user' | 'admin') || 'user',
    })
  }

  // 需要认证但用户未登录：重定向到登录页
  if (to.meta.requiresAuth && !authStore.isLoggedIn && !isDemo) {
    return { name: 'login' }
  }

  // 已登录用户访问登录页或注册页：进入大众版控制台
  if ((to.name === 'login' || to.name === 'register') && authStore.isLoggedIn) {
    return { path: '/public' }
  }
})

export default router
