// src/main.ts
// 前端应用入口文件
// 负责初始化 Vue 应用实例，挂载 Pinia 状态管理、Vue Router 路由、Element Plus UI 组件库

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

// 导入全局样式：基础重置 + Element Plus 暗色主题覆盖
import '@/assets/styles/main.css'
import '@/assets/styles/element-overrides.css'

const app = createApp(App)

// 注册 Pinia（Vue 3 官方推荐的状态管理库）
app.use(createPinia())

// 注册 Vue Router（管理页面路由和导航守卫）
router.beforeEach(async (to) => {
  if (to.path.startsWith('/teen')) {
    const { installElementPlus } = await import('@/plugins/elementPlus')
    await installElementPlus(app)
  }
})
app.use(router)

// 等首个路由组件加载完成后再挂载，避免启动 loader 被过早替换成空白/全局背景。
router.isReady().then(() => {
  app.mount('#app')
})
