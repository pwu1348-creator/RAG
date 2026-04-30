import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      'vue-i18n': 'vue-i18n/dist/vue-i18n.cjs.js'
    }
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      // 问答检索服务 (QA Service) - 端口 8002，baseURL=/api/qa
      '/api/qa': {
        target: 'http://127.0.0.1:8002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/qa/, '/api/v1')
      },
      // 其余所有 /api/v1 请求 → 文件解析/管理服务 端口 8001
      '/api/v1': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true
      }
    }
  }
})
