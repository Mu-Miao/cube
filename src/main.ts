// src/main.ts
// 前端应用入口文件
// 负责初始化 Vue 应用实例，挂载 Pinia 状态管理、Vue Router 路由、Element Plus UI 组件库

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

import App from './App.vue'
import router from './router'

// 导入全局样式：基础重置 + Element Plus 暗色主题覆盖
import '@/assets/styles/main.css'
import '@/assets/styles/element-overrides.css'

const app = createApp(App)

// 注册 Pinia（Vue 3 官方推荐的状态管理库）
app.use(createPinia())

// 注册 Vue Router（管理页面路由和导航守卫）
app.use(router)

// 注册 Element Plus（全套 UI 组件库）
app.use(ElementPlus)

// 挂载应用到 #app DOM 节点
app.mount('#app')
