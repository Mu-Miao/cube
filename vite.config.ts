import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
// import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), vueJsx()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173, // 设置默认端口
    host: '0.0.0.0', // 允许外部访问
    strictPort: true, // 如果端口被占用则报错，而不是自动换端口
    // 开发代理：将 /api 请求转发到后端 FastAPI 服务
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
    allowedHosts: ['frp-bar.com'],
  },
})
