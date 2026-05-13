<template>
  <div class="user-management-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">
          <span class="title-icon">👥</span>
          用户管理
        </h1>
        <p class="page-subtitle">管理系统用户，分配权限，查看用户活动</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-primary" @click="handleAddUser">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"/>
          </svg>
          新增用户
        </button>
        <button class="btn btn-ghost">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M12,16A2,2 0 0,1 14,18A2,2 0 0,1 12,20A2,2 0 0,1 10,18A2,2 0 0,1 12,16M12,10A2,2 0 0,1 14,12A2,2 0 0,1 12,14A2,2 0 0,1 10,12A2,2 0 0,1 12,10M12,4A2,2 0 0,1 14,6A2,2 0 0,1 12,8A2,2 0 0,1 10,6A2,2 0 0,1 12,4Z"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="filter-bar">
      <div class="search-box">
        <svg class="search-icon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z"/>
        </svg>
        <input
          type="text"
          class="input"
          placeholder="搜索用户姓名、邮箱或ID..."
          v-model="searchQuery"
        />
      </div>
      <div class="filter-group">
        <select class="filter-select" v-model="filterRole">
          <option value="">全部角色</option>
          <option value="admin">管理员</option>
          <option value="user">普通用户</option>
          <option value="guest">访客</option>
        </select>
        <select class="filter-select" v-model="filterStatus">
          <option value="">全部状态</option>
          <option value="active">正常</option>
          <option value="inactive">未激活</option>
          <option value="locked">已锁定</option>
        </select>
      </div>
    </div>

    <!-- 用户表格 -->
    <div class="table-card" :class="{ 'fade-out': fadeOut }">
      <table class="data-table">
        <thead>
          <tr>
            <th class="checkbox-col">
              <input type="checkbox" v-model="selectAll" @change="toggleSelectAll"/>
            </th>
            <th>用户账号</th>
            <th style="padding-left: 24px;">头像</th>
            <th style="padding-left: 25px;">状态</th>
            <th style="padding-left: 40px;">创建时间</th>
            <th style="padding-left: 25px;">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in filteredUsers" :key="user.user_id" class="table-row">
            <td class="checkbox-col">
              <input type="checkbox" v-model="selectedUsers" :value="user.user_id"/>
            </td>
            <td class="user-col">
              <div class="user-cell">
                <div class="user-info">
                  <span class="user-name">{{ user.username }}</span>
                  <span class="user-email">{{ user.email }}</span>
                </div>
              </div>
            </td>
            <td class="avatar-col">
              <div class="user-avatar" :style="user.avatar_url ? {} : { background: user.avatarColor || '#667eea' }">
                <img v-if="user.avatar_url" :src="user.avatar_url" class="avatar-img" />
                <span v-else>{{ user.username?.charAt(0) || '?' }}</span>
              </div>
            </td>
            <td>
              <span class="status-badge" :class="user.status">{{ getStatusText(user.status) }}</span>
            </td>
            <td>{{ user.created_at }}</td>
            <td>
              <div class="action-btns">
                <button class="action-btn edit" @click="editUser(user)" title="编辑">
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z"/>
                  </svg>
                </button>
                <button class="action-btn delete" @click="deleteUser(user)" title="删除">
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
                  </svg>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- 分页 -->
      <div class="pagination">
        <div class="pagination-info">
          <span>每页</span>
          <select v-model="pageSize" @change="currentPage = 1; fetchUsers()" class="page-size-select">
            <option :value="10">10</option>
            <option :value="50">50</option>
            <option :value="100">100</option>
          </select>
          <span>条</span>
          <span style="margin-left: 16px;">显示 {{ (currentPage - 1) * pageSize + 1 }} - {{ Math.min(currentPage * pageSize, totalUsers) }} 条，共 {{ totalUsers }} 条</span>
        </div>
        <div class="pagination-btns">
          <button class="page-btn" :disabled="currentPage === 1" @click="currentPage--">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M15.41,7.41L14,6L8,12L14,18L15.41,16.59L10.83,12L15.41,7.41Z"/>
            </svg>
          </button>
          <button
            v-for="page in visiblePages"
            :key="page"
            class="page-btn"
            :class="{ active: page === currentPage }"
            @click="currentPage = page"
          >
            {{ page }}
          </button>
          <button class="page-btn" :disabled="currentPage === totalPages" @click="currentPage++">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <div v-if="showDeleteModal" class="modal-overlay" @click.self="showDeleteModal = false">
      <div class="modal delete-modal">
        <div class="modal-icon">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M12,2C17.53,2 22,6.47 22,12C22,17.53 17.53,22 12,22C6.47,22 2,17.53 2,12C2,6.47 6.47,2 12,2M15.59,7L12,10.59L8.41,7L7,8.41L10.59,12L7,15.59L8.41,17L12,13.41L15.59,17L17,15.59L13.41,12L17,8.41L15.59,7Z"/>
          </svg>
        </div>
        <h3>确认删除</h3>
        <p>确定要删除用户 <strong>{{ deleteTargetUser?.username }}</strong> 吗？此操作不可撤销。</p>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="showDeleteModal = false">取消</button>
          <button class="btn btn-danger" @click="confirmDelete">确认删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { adminApi } from '@/api'

const router = useRouter()
const route = useRoute()

const searchQuery = ref('')
const filterRole = ref('')
const filterStatus = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const totalUsers = ref(0)
const selectAll = ref(false)
const selectedUsers = ref([])
const loading = ref(false)
const fadeOut = ref(false)
const showDeleteModal = ref(false)
const deleteTargetUser = ref(null)

// 用户数据
const users = ref([])

// 获取用户列表
const fetchUsers = async () => {
  fadeOut.value = true
  setTimeout(async () => {
    loading.value = true
    try {
      const params = {
        page: currentPage.value,
        size: pageSize.value,
        keyword: searchQuery.value || undefined,
        status: filterStatus.value || undefined
      }
      const res = await adminApi.getUserList(params)
      if (res.data) {
        users.value = res.data.users || []
        totalUsers.value = res.data.total || 0
      }
    } catch (error) {
      console.error('获取用户列表失败:', error)
    } finally {
      loading.value = false
      fadeOut.value = false
    }
  }, 150)
}

// 新增用户 - 跳转到新增页面
const handleAddUser = () => {
  router.push('/users/add')
}

// 删除用户
const handleDeleteUser = (user) => {
  deleteTargetUser.value = user
  showDeleteModal.value = true
}

const confirmDelete = async () => {
  if (!deleteTargetUser.value) return
  try {
    await adminApi.deleteUser(deleteTargetUser.value.user_id)
    showDeleteModal.value = false
    deleteTargetUser.value = null
    fetchUsers()
  } catch (error) {
    console.error('删除用户失败:', error)
    alert('删除用户失败: ' + (error.message || '未知错误'))
  }
}

const filteredUsers = computed(() => {
  let result = users.value
  
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(u => 
      u.username.toLowerCase().includes(query) || 
      u.email.toLowerCase().includes(query)
    )
  }
  
  if (filterRole.value) {
    result = result.filter(u => u.role === filterRole.value)
  }
  
  if (filterStatus.value) {
    result = result.filter(u => u.status === filterStatus.value)
  }
  
  return result
})

const totalPages = computed(() => Math.ceil(totalUsers.value / pageSize.value))

const visiblePages = computed(() => {
  const pages = []
  const start = Math.max(1, currentPage.value - 2)
  const end = Math.min(totalPages.value, start + 4)
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  return pages
})

watch([currentPage, pageSize], () => {
  fetchUsers()
})

const toggleSelectAll = () => {
  if (selectAll.value) {
    selectedUsers.value = filteredUsers.value.map(u => u.user_id)
  } else {
    selectedUsers.value = []
  }
}

const getRoleText = (role) => {
  const map = { admin: '管理员', user: '普通用户', guest: '访客' }
  return map[role] || role
}

const getStatusText = (status) => {
  const map = { active: '正常', inactive: '未激活', locked: '已锁定' }
  return map[status] || status
}

const editUser = (user) => {
  router.push(`/users/edit/${user.user_id}`)
}

const deleteUser = handleDeleteUser

// 页面加载时获取数据
onMounted(() => {
  if (route.query.refresh) {
    fetchUsers()
  }
  fetchUsers()
})
</script>

<style scoped>
.user-management-page {
  padding: 32px;
  max-width: 1400px;
}

/* 页面标题 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
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

.header-actions {
  display: flex;
  gap: 12px;
}

.header-actions .btn svg {
  width: 20px;
  height: 20px;
}

/* 统计行 */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 28px;
}

.stat-item {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: var(--radius-lg);
  padding: 20px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: var(--shadow);
  border: 1px solid rgba(168, 230, 207, 0.3);
}

.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-icon svg {
  width: 26px;
  height: 26px;
}

.stat-icon.total { background: linear-gradient(135deg, #a8e6cf 0%, #88d8b0 100%); }
.stat-icon.active { background: linear-gradient(135deg, #7fcdcd 0%, #5cb8b2 100%); }
.stat-icon.new { background: linear-gradient(135deg, #b4e7ce 0%, #98d8c8 100%); }
.stat-icon.online { background: linear-gradient(135deg, #e8d5c4 0%, #d4c4b0 100%); }

.stat-data {
  display: flex;
  flex-direction: column;
}

.stat-number {
  font-size: 24px;
  font-weight: 700;
  color: var(--gray-800);
}

.stat-label {
  font-size: 13px;
  color: var(--gray-500);
}

/* 筛选栏 */
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  gap: 16px;
}

.search-box {
  position: relative;
  flex: 1;
  max-width: 400px;
}

.search-icon {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  color: var(--gray-400);
}

.search-box .input {
  padding-left: 48px;
}

.filter-group {
  display: flex;
  gap: 12px;
}

.filter-select {
  padding: 12px 36px 12px 16px;
  border: 2px solid var(--gray-200);
  border-radius: var(--radius);
  background: white;
  font-size: 14px;
  color: var(--gray-700);
  cursor: pointer;
  outline: none;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%239e9e9e'%3E%3Cpath d='M7,10L12,15L17,10H7Z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  background-size: 20px;
}

.filter-select:focus {
  border-color: var(--primary);
}

/* 表格卡片 */
.table-card {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow);
  border: 1px solid rgba(168, 230, 207, 0.3);
  overflow: hidden;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.fade-out {
  animation: fadeOut 0.15s ease forwards;
}

@keyframes fadeOut {
  from { opacity: 1; }
  to { opacity: 0; }
}

.table-row {
  transition: all 0.2s ease;
}

.table-row:hover {
  background: rgba(168, 230, 207, 0.05);
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  animation: fadeIn 0.2s ease;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  background: rgba(250, 250, 250, 0.8);
  padding: 16px;
  text-align: left;
  font-size: 13px;
  font-weight: 600;
  color: var(--gray-600);
  border-bottom: 1px solid var(--gray-200);
}

.data-table td {
  padding: 16px;
  border-bottom: 1px solid var(--gray-100);
  vertical-align: middle;
  font-size: 14px;
  color: var(--gray-700);
}

.table-row:hover {
  background: rgba(168, 230, 207, 0.05);
}

.checkbox-col {
  width: 48px;
  text-align: center;
}

.checkbox-col input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: var(--primary);
  cursor: pointer;
}

.avatar-col { 
  text-align: center;
}

/* 用户单元格 */
.user-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 16px;
  overflow: hidden;
  flex-shrink: 0;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-info {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-weight: 600;
  color: var(--gray-800);
}

.user-email {
  font-size: 12px;
  color: var(--gray-500);
}

/* 角色和状态徽章 */
.role-badge {
  padding: 6px 12px;
  border-radius: var(--radius-full);
  font-size: 12px;
  font-weight: 500;
}

.role-badge.admin {
  background: rgba(168, 230, 207, 0.3);
  color: var(--primary-dark);
}

.role-badge.user {
  background: rgba(232, 213, 196, 0.5);
  color: #8d6e63;
}

.role-badge.guest {
  background: var(--gray-100);
  color: var(--gray-600);
}

.status-badge {
  padding: 6px 12px;
  border-radius: var(--radius-full);
  font-size: 12px;
  font-weight: 500;
}

.status-badge.active {
  background: rgba(129, 199, 132, 0.2);
  color: #2e7d32;
}

.status-badge.inactive {
  background: rgba(255, 183, 77, 0.2);
  color: #ef6c00;
}

.status-badge.locked {
  background: rgba(229, 115, 115, 0.2);
  color: #c62828;
}

/* 时间单元格 */
.time-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--gray-500);
}

.time-cell svg {
  width: 16px;
  height: 16px;
}

/* 操作按钮 */
.action-btns {
  display: flex;
  gap: 8px;
}

.action-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn svg {
  width: 18px;
  height: 18px;
}

.action-btn.edit {
  background: rgba(168, 230, 207, 0.2);
  color: var(--primary-dark);
}

.action-btn.edit:hover {
  background: var(--primary);
  color: white;
}

.action-btn.delete {
  background: rgba(229, 115, 115, 0.1);
  color: var(--error);
}

.action-btn.delete:hover {
  background: var(--error);
  color: white;
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-top: 1px solid var(--gray-100);
}

.pagination-info {
  font-size: 13px;
  color: var(--gray-500);
  display: flex;
  align-items: center;
}

.page-size-select {
  margin: 0 4px;
  padding: 4px 8px;
  border: 1px solid var(--gray-300);
  border-radius: var(--radius);
  font-size: 13px;
  background: white;
  cursor: pointer;
}

.page-size-select:hover {
  border-color: var(--primary);
}

.pagination-btns {
  display: flex;
  gap: 8px;
}

.page-btn {
  min-width: 36px;
  height: 36px;
  padding: 0 12px;
  border: 1px solid var(--gray-200);
  background: white;
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--gray-600);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.page-btn:hover:not(:disabled) {
  border-color: var(--primary);
  color: var(--primary-dark);
}

.page-btn.active {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-btn svg {
  width: 20px;
  height: 20px;
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
  animation: fadeIn 0.2s ease;
  backdrop-filter: blur(4px);
}

.modal {
  background: white;
  border-radius: var(--radius-xl);
  width: 100%;
  max-width: 400px;
  box-shadow: var(--shadow-xl);
  animation: modalSlideIn 0.3s ease;
  text-align: center;
  padding: 32px;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.delete-modal .modal-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 20px;
  background: #fee2e2;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.delete-modal .modal-icon svg {
  width: 32px;
  height: 32px;
  color: #ef4444;
}

.delete-modal h3 {
  font-size: 20px;
  font-weight: 600;
  color: var(--gray-800);
  margin-bottom: 12px;
}

.delete-modal p {
  color: var(--gray-600);
  font-size: 14px;
  margin-bottom: 24px;
}

.delete-modal p strong {
  color: var(--gray-800);
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover {
  background: #dc2626;
}

/* 响应式 */
@media (max-width: 1200px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .user-management-page {
    padding: 20px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .stats-row {
    grid-template-columns: 1fr;
  }
  
  .filter-bar {
    flex-direction: column;
  }
  
  .search-box {
    max-width: 100%;
  }
  
  .data-table {
    font-size: 12px;
  }
  
  .data-table th,
  .data-table td {
    padding: 12px 8px;
  }
}
</style>
