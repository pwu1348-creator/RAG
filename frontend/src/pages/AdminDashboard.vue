<template>
  <div class="admin-dashboard">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ 'collapsed': sidebarCollapsed }">
      <div class="sidebar-header">
        <div class="logo">
          <img src="/images/生成马年专属 logo.png" alt="logo" class="logo-img" />
          <span v-if="!sidebarCollapsed">管理后台</span>
        </div>
        <button class="toggle-btn" @click="sidebarCollapsed = !sidebarCollapsed">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6" v-if="!sidebarCollapsed"/>
            <polyline points="9 18 15 12 9 6" v-else/>
          </svg>
        </button>
      </div>
      
      <nav class="sidebar-nav">
        <router-link to="/admin/dashboard" class="nav-item" :class="{ active: $route.path === '/admin/dashboard' }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7"/>
            <rect x="14" y="3" width="7" height="7"/>
            <rect x="14" y="14" width="7" height="7"/>
            <rect x="3" y="14" width="7" height="7"/>
          </svg>
          <span v-if="!sidebarCollapsed">概览</span>
        </router-link>
        
        <router-link to="/admin/users" class="nav-item" :class="{ active: $route.path === '/admin/users' }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
          <span v-if="!sidebarCollapsed">用户管理</span>
        </router-link>
        
        <router-link to="/admin/documents" class="nav-item" :class="{ active: $route.path === '/admin/documents' }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
            <polyline points="10 9 9 9 8 9"/>
          </svg>
          <span v-if="!sidebarCollapsed">文档管理</span>
        </router-link>
        
        <router-link to="/admin/settings" class="nav-item" :class="{ active: $route.path === '/admin/settings' }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
          <span v-if="!sidebarCollapsed">系统设置</span>
        </router-link>
      </nav>
      
      <div class="sidebar-footer">
        <div class="user-info" v-if="!sidebarCollapsed">
          <div class="avatar">{{ currentUser?.username?.[0]?.toUpperCase() || 'A' }}</div>
          <div class="info">
            <span class="name">{{ currentUser?.username || 'Admin' }}</span>
            <span class="role">{{ currentUser?.role === 'admin' ? '管理员' : '用户' }}</span>
          </div>
        </div>
        <button class="logout-btn" @click="handleLogout">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
            <polyline points="16 17 21 12 16 7"/>
            <line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
          <span v-if="!sidebarCollapsed">退出</span>
        </button>
      </div>
    </aside>
    
    <!-- 主内容区 -->
    <main class="main-content">
      <!-- 顶部栏 -->
      <header class="top-bar">
        <h2 class="page-title">{{ $route.meta.title || '管理后台' }}</h2>
        <div class="top-actions">
          <button class="action-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
            </svg>
          </button>
          <button class="action-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
          </button>
        </div>
      </header>
      
      <!-- 内容区 -->
      <div class="content-wrapper">
        <!-- 统计卡片 -->
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon documents">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ stats.documents }}</span>
              <span class="stat-label">文档总数</span>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon users">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ stats.users }}</span>
              <span class="stat-label">用户总数</span>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon knowledge-bases">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ stats.knowledgeBases }}</span>
              <span class="stat-label">知识库总数</span>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon chunks">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <line x1="3" y1="9" x2="21" y2="9"/>
                <line x1="9" y1="21" x2="9" y2="9"/>
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ stats.chunks }}</span>
              <span class="stat-label">文本块总数</span>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon storage">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <ellipse cx="12" cy="5" rx="9" ry="3"/>
                <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
                <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ stats.storage }}</span>
              <span class="stat-label">存储空间</span>
            </div>
          </div>
        </div>
        
        <!-- 用户管理区域 -->
        <div class="section">
          <div class="section-header">
            <h3 class="section-title">用户管理</h3>
            <button class="btn-primary" @click="showCreateUserModal = true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              新建用户
            </button>
          </div>
          
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>用户名</th>
                  <th>角色</th>
                  <th>状态</th>
                  <th>创建时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in users" :key="user.id">
                  <td>{{ user.id }}</td>
                  <td>{{ user.username }}</td>
                  <td>
                    <span class="badge" :class="user.role">{{ user.role === 'admin' ? '管理员' : '普通用户' }}</span>
                  </td>
                  <td>
                    <span class="badge" :class="user.is_active ? 'active' : 'inactive'">
                      {{ user.is_active ? '正常' : '禁用' }}
                    </span>
                  </td>
                  <td>{{ formatDate(user.created_at) }}</td>
                  <td>
                    <button class="action-btn-small" @click="deleteUser(user.id)" :disabled="user.username === 'admin'">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"/>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                      </svg>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </main>
    
    <!-- 新建用户弹窗 -->
    <div v-if="showCreateUserModal" class="modal-overlay" @click.self="showCreateUserModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>新建用户</h3>
          <button class="close-btn" @click="showCreateUserModal = false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>用户名</label>
            <input v-model="newUser.username" type="text" placeholder="请输入用户名"/>
          </div>
          <div class="form-group">
            <label>密码</label>
            <input v-model="newUser.password" type="password" placeholder="请输入密码"/>
          </div>
          <div class="form-group">
            <label>角色</label>
            <select v-model="newUser.role">
              <option value="user">普通用户</option>
              <option value="admin">管理员</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showCreateUserModal = false">取消</button>
          <button class="btn-primary" @click="createUser" :disabled="isCreating">
            {{ isCreating ? '创建中...' : '创建' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { adminApi } from '@/api'

const router = useRouter()
const sidebarCollapsed = ref(false)
const currentUser = ref(null)
const users = ref([])
const showCreateUserModal = ref(false)
const isCreating = ref(false)

const stats = ref({
  documents: 0,
  users: 0,
  chunks: 0,
  storage: '0 B',
  activeUsers: 0,
  completedDocuments: 0,
  knowledgeBases: 0
})

const newUser = ref({
  username: '',
  password: '',
  role: 'user'
})

// 获取当前用户信息
const fetchCurrentUser = async () => {
  try {
    const res = await adminApi.getDashboard()
    currentUser.value = res.data
  } catch (error) {
    console.error('获取用户信息失败:', error)
  }
}

// 获取统计数据
const fetchStatistics = async () => {
  try {
    const res = await adminApi.getStatistics()
    const data = res.data
    stats.value.users = data.total_users || 0
    stats.value.activeUsers = data.active_users || 0
    stats.value.documents = data.total_documents || 0
    stats.value.completedDocuments = data.completed_documents || 0
    stats.value.chunks = data.total_chunks || 0
    stats.value.storage = data.total_storage || '0 B'
    stats.value.knowledgeBases = data.total_knowledge_bases || 0
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

// 同步统计数据
const syncStatistics = async () => {
  try {
    await adminApi.syncStatistics()
    await fetchStatistics()
  } catch (error) {
    console.error('同步统计数据失败:', error)
  }
}

// 获取用户列表
const fetchUsers = async () => {
  try {
    const res = await adminApi.getUserList()
    users.value = res.data.items || res.data.list || []
  } catch (error) {
    console.error('获取用户列表失败:', error)
  }
}

// 创建用户
const createUser = async () => {
  if (!newUser.value.username || !newUser.value.password) {
    alert('请填写完整信息')
    return
  }
  
  isCreating.value = true
  try {
    await adminApi.createUser(newUser.value)
    showCreateUserModal.value = false
    newUser.value = { username: '', password: '', role: 'user' }
    await fetchUsers()
    alert('用户创建成功')
  } catch (error) {
    alert(error.message || '创建失败')
  } finally {
    isCreating.value = false
  }
}

// 删除用户
const deleteUser = async (userId) => {
  if (!confirm('确定要删除该用户吗？')) return
  
  try {
    await adminApi.deleteUser(userId)
    await fetchUsers()
    alert('删除成功')
  } catch (error) {
    alert(error.message || '删除失败')
  }
}

// 退出登录
const handleLogout = () => {
  localStorage.removeItem('admin_token')
  localStorage.removeItem('admin_user')
  router.push('/admin/login')
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

onMounted(() => {
  fetchCurrentUser()
  fetchUsers()
  fetchStatistics()
})
</script>

<style scoped>
.admin-dashboard {
  display: flex;
  min-height: 100vh;
  background: #f5f7fa;
}

/* 侧边栏 */
.sidebar {
  width: 260px;
  background: white;
  border-right: 1px solid #e8f5e9;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
}

.sidebar.collapsed {
  width: 80px;
}

.sidebar-header {
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e8f5e9;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #2e7d32;
  font-weight: 600;
  font-size: 18px;
}

.logo-img {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  object-fit: contain;
  user-select: none;
  -webkit-user-select: none;
}

.logo svg {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
}

.toggle-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #81c784;
  padding: 4px;
}

.toggle-btn svg {
  width: 20px;
  height: 20px;
}

/* 导航 */
.sidebar-nav {
  flex: 1;
  padding: 16px 12px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 12px;
  color: #666;
  text-decoration: none;
  margin-bottom: 4px;
  transition: all 0.3s;
}

.nav-item svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.nav-item:hover {
  background: #e8f5e9;
  color: #2e7d32;
}

.nav-item.active {
  background: linear-gradient(135deg, #a8e6cf 0%, #88d8a3 100%);
  color: white;
}

/* 侧边栏底部 */
.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #e8f5e9;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.avatar {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #a8e6cf 0%, #88d8a3 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 16px;
}

.info {
  display: flex;
  flex-direction: column;
}

.name {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.role {
  font-size: 12px;
  color: #81c784;
}

.logout-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px;
  background: #ffebee;
  border: none;
  border-radius: 10px;
  color: #e53935;
  cursor: pointer;
  transition: all 0.3s;
}

.logout-btn:hover {
  background: #ffcdd2;
}

.logout-btn svg {
  width: 18px;
  height: 18px;
}

/* 主内容区 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 顶部栏 */
.top-bar {
  height: 64px;
  background: white;
  border-bottom: 1px solid #e8f5e9;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #2e7d32;
}

.top-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: #f5f7fa;
  border-radius: 10px;
  cursor: pointer;
  color: #666;
  transition: all 0.3s;
}

.action-btn:hover {
  background: #e8f5e9;
  color: #2e7d32;
}

.action-btn svg {
  width: 20px;
  height: 20px;
}

/* 内容区 */
.content-wrapper {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon.documents {
  background: #e3f2fd;
  color: #1976d2;
}

.stat-icon.users {
  background: #e8f5e9;
  color: #388e3c;
}

.stat-icon.chunks {
  background: #fff3e0;
  color: #f57c00;
}

.stat-icon.storage {
  background: #fce4ec;
  color: #c2185b;
}

.stat-icon.knowledge-bases {
  background: #e1f5fe;
  color: #0288d1;
}

.stat-icon svg {
  width: 28px;
  height: 28px;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #999;
}

/* 区块 */
.section {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

/* 按钮 */
.btn-primary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: linear-gradient(135deg, #a8e6cf 0%, #88d8a3 100%);
  border: none;
  border-radius: 10px;
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(168, 230, 207, 0.4);
}

.btn-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-primary svg {
  width: 18px;
  height: 18px;
}

.btn-secondary {
  padding: 10px 20px;
  background: #f5f7fa;
  border: none;
  border-radius: 10px;
  color: #666;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-secondary:hover {
  background: #e8f5e9;
  color: #2e7d32;
}

/* 表格 */
.table-container {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 14px 16px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
}

.data-table th {
  font-weight: 600;
  color: #666;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.data-table td {
  color: #333;
  font-size: 14px;
}

.badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.badge.admin {
  background: #e3f2fd;
  color: #1976d2;
}

.badge.user {
  background: #f5f5f5;
  color: #666;
}

.badge.active {
  background: #e8f5e9;
  color: #388e3c;
}

.badge.inactive {
  background: #ffebee;
  color: #e53935;
}

.action-btn-small {
  width: 32px;
  height: 32px;
  border: none;
  background: #ffebee;
  border-radius: 8px;
  cursor: pointer;
  color: #e53935;
  transition: all 0.3s;
}

.action-btn-small:hover:not(:disabled) {
  background: #ffcdd2;
}

.action-btn-small:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn-small svg {
  width: 16px;
  height: 16px;
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 20px;
  width: 100%;
  max-width: 420px;
  overflow: hidden;
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #999;
  padding: 4px;
}

.close-btn svg {
  width: 20px;
  height: 20px;
}

.modal-body {
  padding: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #666;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e8f5e9;
  border-radius: 12px;
  font-size: 14px;
  transition: all 0.3s;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #a8e6cf;
}

.modal-footer {
  padding: 16px 24px 24px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式 */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: -260px;
    z-index: 100;
    height: 100vh;
  }
  
  .sidebar.collapsed {
    left: 0;
    width: 260px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
