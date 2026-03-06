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
    port: 3000,
    proxy: {
      // 文件解析服务 (Parser Service) - 端口 8001
      '/api/parser': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/parser/, '/api/v1')
      },
      // 问答检索服务 (QA Service) - 端口 8002
      '/api/qa': {
        target: 'http://localhost:8002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/qa/, '/api/v1')
      },
      // 知识库管理服务 - 端口 8001
      '/api/knowledge-bases': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api/v1')
      },
      // 认证服务 - 端口 8001
      '/api/auth': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/auth/, '/api/v1/auth')
      },
      // 管理服务 - 端口 8001
      '/api/admin': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/admin/, '/api/v1/admin')
      }
    }
  }
})
