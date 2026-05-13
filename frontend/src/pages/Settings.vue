<template>
  <div class="settings-page">
    <div class="page-header">
      <h1 class="page-title">
        <span class="title-icon">ℹ️</span>
        系统信息
      </h1>
      <p class="page-subtitle">查看当前系统配置信息</p>
    </div>

    <div class="settings-content">
      <!-- 左侧菜单 -->
      <div class="settings-menu">
        <div
          v-for="(menu, index) in menuList"
          :key="index"
          class="menu-item"
          :class="{ active: activeMenu === menu.key }"
          @click="activeMenu = menu.key"
        >
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path :d="menu.icon"/>
          </svg>
          <span>{{ menu.name }}</span>
        </div>
      </div>

      <!-- 右侧内容 -->
      <div class="settings-panel">
        <!-- 加载状态 -->
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner"></div>
          <p>加载系统信息中...</p>
        </div>

        <!-- 错误状态 -->
        <div v-else-if="error" class="error-state">
          <p>{{ error }}</p>
          <button class="btn btn-primary" @click="fetchSystemInfo">重试</button>
        </div>

        <!-- 通用信息 -->
        <div v-else-if="activeMenu === 'general'" class="panel-section">
          <h3 class="panel-title">通用信息</h3>
          <div class="info-group">
            <div class="info-item" v-for="(item, key) in systemInfo.general" :key="key">
              <div class="info-label">{{ item.description }}</div>
              <div class="info-value">{{ formatValue(item.value, item.type) }}</div>
            </div>
            <div v-if="!systemInfo.general || Object.keys(systemInfo.general).length === 0" class="empty-state">
              暂无通用信息
            </div>
          </div>
        </div>

        <!-- 模型信息 -->
        <div v-else-if="activeMenu === 'model'" class="panel-section">
          <h3 class="panel-title">模型信息</h3>
          <div class="info-group">
            <div class="info-item" v-for="(item, key) in systemInfo.model" :key="key">
              <div class="info-label">{{ item.description }}</div>
              <div class="info-value">{{ formatValue(item.value, item.type) }}</div>
            </div>
            <div v-if="!systemInfo.model || Object.keys(systemInfo.model).length === 0" class="empty-state">
              暂无模型信息
            </div>
          </div>
        </div>

        <!-- 检索信息 -->
        <div v-else-if="activeMenu === 'retrieval'" class="panel-section">
          <h3 class="panel-title">检索信息</h3>
          <div class="info-group">
            <div class="info-item" v-for="(item, key) in systemInfo.retrieval" :key="key">
              <div class="info-label">{{ item.description }}</div>
              <div class="info-value">{{ formatValue(item.value, item.type) }}</div>
            </div>
            <div v-if="!systemInfo.retrieval || Object.keys(systemInfo.retrieval).length === 0" class="empty-state">
              暂无检索信息
            </div>
          </div>
        </div>

        <div class="panel-footer">
          <span class="footer-hint">以上信息为只读，如需修改请编辑后端配置文件 (.env)</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { settingsApi } from '../api/admin'

const activeMenu = ref('general')
const loading = ref(true)
const error = ref('')
const systemInfo = ref({
  general: {},
  model: {},
  retrieval: {}
})

const menuList = [
  { key: 'general', name: '通用信息', icon: 'M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.21,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.21,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.67 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z' },
  { key: 'model', name: '模型信息', icon: 'M12,16A3,3 0 0,1 9,13C9,11.88 9.61,10.9 10.5,10.39L20.21,4.77L14.68,14.35C14.18,15.33 13.17,16 12,16M12,3C13.81,3 15.5,3.5 16.97,4.32L14.87,5.53C14,5.19 13,5 12,5A8,8 0 0,0 4,13C4,15.21 4.89,17.21 6.34,18.65H6.35C6.74,19.04 6.74,19.67 6.35,20.06C5.96,20.45 5.32,20.45 4.93,20.07V20.07C3.12,18.26 2,15.76 2,13A10,10 0 0,1 12,3M22,13C22,15.76 20.88,18.26 19.07,20.07V20.07C18.68,20.45 18.05,20.45 17.66,20.06C17.27,19.67 17.27,19.04 17.66,18.65V18.65C19.11,17.2 20,15.21 20,13C20,12 19.81,11 19.46,10.1L20.67,8C21.5,9.5 22,11.18 22,13Z' },
  { key: 'retrieval', name: '检索信息', icon: 'M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z' },
]

function formatValue(value, type) {
  if (value === null || value === undefined || value === '') return '未配置'
  if (type === 'boolean') return value ? '是' : '否'
  if (type === 'json') {
    if (Array.isArray(value)) return value.join(', ')
    return JSON.stringify(value)
  }
  return String(value)
}

async function fetchSystemInfo() {
  loading.value = true
  error.value = ''
  try {
    const res = await settingsApi.getSystemInfo()
    systemInfo.value = res.data || {}
  } catch (e) {
    error.value = e.message || '获取系统信息失败'
    console.error('Fetch system info error:', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchSystemInfo()
})
</script>

<style scoped>
.settings-page {
  padding: 32px;
  max-width: 1200px;
}

.page-header {
  margin-bottom: 28px;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--gray-800);
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.title-icon {
  font-size: 32px;
}

.page-subtitle {
  font-size: 14px;
  color: var(--gray-500);
}

/* 设置内容 */
.settings-content {
  display: flex;
  gap: 24px;
}

/* 左侧菜单 */
.settings-menu {
  width: 240px;
  flex-shrink: 0;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  margin-bottom: 4px;
  border-radius: var(--radius);
  cursor: pointer;
  color: var(--gray-600);
  transition: all 0.2s ease;
}

.menu-item:hover {
  background: rgba(168, 230, 207, 0.1);
  color: var(--primary-dark);
}

.menu-item.active {
  background: linear-gradient(135deg, rgba(168, 230, 207, 0.3) 0%, rgba(136, 216, 176, 0.3) 100%);
  color: var(--primary-dark);
  font-weight: 500;
}

.menu-item svg {
  width: 22px;
  height: 22px;
}

/* 右侧面板 */
.settings-panel {
  flex: 1;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: var(--radius-lg);
  padding: 32px;
  box-shadow: var(--shadow);
  border: 1px solid rgba(168, 230, 207, 0.3);
}

.panel-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--gray-800);
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--gray-100);
}

/* 信息展示 */
.info-group {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid var(--gray-100);
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 14px;
  color: var(--gray-600);
  font-weight: 500;
}

.info-value {
  font-size: 14px;
  color: var(--gray-800);
  font-weight: 600;
  background: rgba(168, 230, 207, 0.15);
  padding: 6px 14px;
  border-radius: var(--radius);
  max-width: 400px;
  word-break: break-all;
}

/* 加载状态 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  color: var(--gray-500);
}

.loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--gray-200);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 错误状态 */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  color: var(--gray-500);
  gap: 16px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 40px 0;
  color: var(--gray-400);
  font-size: 14px;
}

/* 面板底部 */
.panel-footer {
  display: flex;
  justify-content: center;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--gray-100);
}

.footer-hint {
  font-size: 13px;
  color: var(--gray-400);
}

.btn {
  padding: 8px 20px;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
}

.btn-primary {
  background: var(--primary);
  color: white;
}

.btn-primary:hover {
  opacity: 0.9;
}

@media (max-width: 968px) {
  .settings-content {
    flex-direction: column;
  }
  
  .settings-menu {
    width: 100%;
    display: flex;
    gap: 8px;
    overflow-x: auto;
  }
  
  .menu-item {
    white-space: nowrap;
    margin-bottom: 0;
  }
  
  .info-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .info-value {
    max-width: 100%;
  }
}

@media (max-width: 768px) {
  .settings-page {
    padding: 20px;
  }
  
  .settings-panel {
    padding: 20px;
  }
}
</style>
