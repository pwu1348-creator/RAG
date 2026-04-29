<template>
  <div class="add-user-page">
    <div class="page-header">
      <button class="back-btn" @click="$router.back()">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M20,11V13H8L13.5,18.5L12.08,19.92L4.16,12L12.08,4.08L13.5,5.5L8,11H20Z"/>
        </svg>
        返回
      </button>
      <h1 class="page-title">新增用户</h1>
    </div>

    <div class="form-card">
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>用户名 <span class="required">*</span></label>
          <input
            type="text"
            v-model="form.username"
            placeholder="请输入用户名"
            required
          />
        </div>

        <div class="form-group">
          <label>密码 <span class="required">*</span></label>
          <input
            type="password"
            v-model="form.password"
            placeholder="请输入密码"
            required
          />
        </div>

        <div class="form-group">
          <label>手机号</label>
          <input
            type="text"
            v-model="form.phone"
            placeholder="请输入手机号"
          />
        </div>

        <div class="form-group">
          <label>邮箱</label>
          <input
            type="email"
            v-model="form.email"
            placeholder="请输入邮箱"
          />
        </div>

        <div class="form-group">
          <label>部门</label>
          <div class="select-wrapper">
            <select v-model="form.department" class="select">
              <option value="">-- 请选择部门 --</option>
              <option
                v-for="dept in departments"
                :key="dept.id"
                :value="dept.name"
              >{{ dept.name }}</option>
            </select>
            <svg class="select-arrow" viewBox="0 0 24 24" fill="currentColor">
              <path d="M7,10L12,15L17,10H7Z"/>
            </svg>
          </div>
          <div class="dept-hint" v-if="departments.length === 0">
            暂无部门，请先前往
            <router-link to="/departments" class="dept-link">部门管理</router-link>
            创建部门
          </div>
        </div>

        <div class="form-actions">
          <button type="button" class="btn btn-ghost" @click="$router.back()">取消</button>
          <button type="submit" class="btn btn-primary" :disabled="submitting">
            {{ submitting ? '提交中...' : '确认添加' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { adminApi } from '@/api'

const router = useRouter()
const submitting = ref(false)
const departments = ref([])

const form = reactive({
  username: '',
  password: '',
  phone: '',
  email: '',
  department: ''
})

// 从 localStorage 读取部门列表
const loadDepartments = () => {
  try {
    const raw = localStorage.getItem('rag_departments')
    departments.value = raw ? JSON.parse(raw) : []
  } catch {
    departments.value = []
  }
}

const handleSubmit = async () => {
  if (!form.username || !form.password) {
    alert('请填写用户名和密码')
    return
  }

  submitting.value = true
  try {
    await adminApi.createUser({
      username: form.username,
      password: form.password,
      phone: form.phone || undefined,
      email: form.email || undefined,
      department: form.department || undefined
    })
    alert('用户创建成功')
    router.push('/users?refresh=' + Date.now())
  } catch (error) {
    console.error('创建用户失败:', error)
    alert('创建用户失败: ' + (error.message || '未知错误'))
  } finally {
    submitting.value = false
  }
}

onMounted(loadDepartments)
</script>

<style scoped>
.add-user-page {
  padding: 32px;
  max-width: 600px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 32px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: none;
  border: none;
  color: var(--primary);
  cursor: pointer;
  font-size: 14px;
  margin-bottom: 16px;
}

.back-btn svg {
  width: 20px;
  height: 20px;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--gray-800);
}

.form-card {
  background: white;
  border-radius: var(--radius-xl);
  padding: 32px;
  box-shadow: var(--shadow);
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--gray-700);
  margin-bottom: 8px;
}

.required {
  color: #ef4444;
}

.form-group input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid var(--gray-200);
  border-radius: var(--radius);
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.form-group input:focus {
  border-color: var(--primary);
}

/* 下拉选择 */
.select-wrapper {
  position: relative;
}

.select {
  width: 100%;
  padding: 12px 40px 12px 16px;
  border: 2px solid var(--gray-200);
  border-radius: var(--radius);
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
  background: white;
  appearance: none;
  -webkit-appearance: none;
  cursor: pointer;
  color: var(--gray-800);
}

.select:focus {
  border-color: var(--primary);
}

.select-arrow {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  color: var(--gray-400);
  pointer-events: none;
}

.dept-hint {
  margin-top: 8px;
  font-size: 13px;
  color: var(--gray-400);
}

.dept-link {
  color: var(--primary);
  text-decoration: none;
  font-weight: 500;
}

.dept-link:hover {
  text-decoration: underline;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 32px;
}

.btn {
  padding: 12px 24px;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.btn-primary {
  background: var(--primary);
  color: white;
}

.btn-primary:hover {
  background: var(--primary-dark, #0d9488);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-ghost {
  background: var(--gray-100);
  color: var(--gray-700);
}

.btn-ghost:hover {
  background: var(--gray-200);
}
</style>
