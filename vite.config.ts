import { fileURLToPath, URL } from 'node:url'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const viteDebug = env.VITE_DEBUG === 'true' || mode === 'debug'

  return {
    plugins: [vue(), vueJsx(), ...(viteDebug ? [vueDevTools()] : [])],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      port: 5173,
      host: '0.0.0.0',
      strictPort: true,
      allowedHosts: ['tianmuzc.site', 'www.tianmuzc.site'],
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
    preview: {
      port: 4173,
      host: '0.0.0.0',
      allowedHosts: ['tianmuzc.site', 'www.tianmuzc.site'],
    },
    build: {
      chunkSizeWarningLimit: 600,
      modulePreload: {
        resolveDependencies(_: string, deps: string[]) {
          return deps.filter((dep) => !dep.includes('element-plus') && !dep.includes('elementPlus'))
        },
      },
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (!id.includes('node_modules')) return
            if (id.includes('/zrender/')) return 'zrender'
            if (id.includes('/echarts/')) return 'echarts'
            if (id.includes('/three/') || id.includes('/@types/three/')) return 'three'
            if (id.includes('/element-plus/') || id.includes('/@element-plus/')) return 'element-plus'
            if (
              id.includes('/vue/') ||
              id.includes('/vue-router/') ||
              id.includes('/pinia/')
            ) {
              return 'vue'
            }
            if (id.includes('/axios/')) return 'api-client'
            return 'vendor'
          },
        },
      },
    },
  }
})
