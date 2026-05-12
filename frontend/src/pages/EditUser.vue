<template>
  <div class="edit-user-page">
    <div class="page-header">
      <button class="back-btn" @click="$router.back()">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M20,11V13H8L13.5,18.5L12.08,19.92L4.16,12L12.08,4.08L13.5,5.5L8,11H20Z"/>
        </svg>
        返回
      </button>
      <h1 class="page-title">编辑用户</h1>
    </div>

    <!-- 加载中状态 -->
    <div v-if="loading" class="loading-card">
      <div class="loading-spinner"></div>
      <span>加载用户信息中...</span>
    </div>

    <div v-else class="form-card">
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>账号 <span class="required">*</span></label>
          <div class="input-wrapper">
            <input
              type="text"
              v-model="form.username"
              placeholder="请输入登录账号"
              @blur="validateUsername"
              :class="{ 'input-error': errors.username }"
              required
            />
            <span class="field-hint error" v-if="errors.username">{{ errors.username }}</span>
            <span class="field-hint" v-else>不少于6位纯数字</span>
          </div>
        </div>

        <div class="form-group">
          <label>邮箱</label>
          <div class="input-wrapper">
            <input
              type="text"
              v-model="form.email"
              placeholder="请输入邮箱地址"
              @blur="validateEmail"
              :class="{ 'input-error': errors.email }"
            />
            <span class="field-hint error" v-if="errors.email">{{ errors.email }}</span>
            <span class="field-hint" v-else>例如：user@example.com</span>
          </div>
        </div>

        <div class="form-group">
          <label>部门</label>
          <input
            type="text"
            v-model="form.department"
            placeholder="请输入部门"
          />
        </div>

        <div class="form-group">
          <label>重置密码</label>
          <div class="input-wrapper">
            <input
              type="password"
              v-model="form.password"
              placeholder="留空则不修改密码"
              @blur="validatePassword"
              :class="{ 'input-error': errors.password }"
            />
            <span class="field-hint error" v-if="errors.password">{{ errors.password }}</span>
            <span class="field-hint" v-else>至少8位，必须包含字母和数字（留空则不修改）</span>
          </div>
        </div>

        <div class="form-actions">
          <button type="button" class="btn btn-ghost" @click="$router.back()">取消</button>
          <button type="submit" class="btn btn-primary" :disabled="submitting || hasErrors">
            {{ submitting ? '保存中...' : '保存修改' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { adminApi } from '@/api'
import { hashPassword } from '@/utils/crypto'

const route = useRoute()
const router = useRouter()
const submitting = ref(false)
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  email: '',
  department: ''
})

const errors = reactive({
  username: '',
  password: '',
  email: ''
})

const hasErrors = computed(() => {
  return !!(errors.username || errors.password || errors.email)
})

// 验证账号：不少于6位纯数字
const validateUsername = () => {
  if (!form.username) {
    errors.username = ''
    return
  }
  if (!/^\d{6,}$/.test(form.username)) {
    errors.username = '账号必须是不少于6位的纯数字'
  } else {
    errors.username = ''
  }
}

// 验证密码：至少8位，必须包含字母和数字（编辑时可留空）
const validatePassword = () => {
  if (!form.password) {
    errors.password = ''
    return
  }
  if (form.password.length < 8) {
    errors.password = '密码长度不能少于8位'
  } else if (!/[a-zA-Z]/.test(form.password)) {
    errors.password = '密码必须包含字母'
  } else if (!/\d/.test(form.password)) {
    errors.password = '密码必须包含数字'
  } else if (!/^[a-zA-Z0-9]+$/.test(form.password)) {
    errors.password = '密码只能包含字母和数字'
  } else {
    errors.password = ''
  }
}

// 验证邮箱格式
const validateEmail = () => {
  if (!form.email) {
    errors.email = ''
    return
  }
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
  if (!emailRegex.test(form.email)) {
    errors.email = '请输入正确的邮箱格式，例如 user@example.com'
  } else {
    errors.email = ''
  }
}

const fetchUserDetail = async () => {
  const userId = route.params.id

  if (!userId) {
    alert('无效的用户ID')
    router.push('/users')
    return
  }

  loading.value = true
  try {
    const res = await adminApi.getUserDetail(userId)
    if (res.data) {
      form.username = res.data.username || ''
      form.email = res.data.email || ''
      form.department = res.data.department || ''
    }
  } catch (error) {
    console.error('获取用户详情失败:', error)
    alert('获取用户详情失败: ' + (error.response?.data?.message || error.message || '网络错误，请检查后端服务'))
    router.push('/users')
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  const userId = route.params.id

  // 触发验证
  validateUsername()
  validateEmail()
  if (form.password) validatePassword()

  if (hasErrors.value) {
    alert('请修正表单中的错误')
    return
  }

  submitting.value = true
  try {
    const updateData = {
      username: form.username || undefined,
      email: form.email || undefined,
      department: form.department || undefined
    }

    if (form.password) {
      const encryptedPassword = await hashPassword(form.password)
      await adminApi.resetUserPassword(userId, encryptedPassword)
    }

    await adminApi.updateUser(userId, updateData)
    alert('用户信息更新成功')
    router.push('/users?refresh=' + Date.now())
  } catch (error) {
    console.error('更新用户失败:', error)
    alert('更新用户失败: ' + (error.message || '未知错误'))
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchUserDetail()
})
</script>

<style scoped>
.edit-user-page {
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

.input-wrapper {
  position: relative;
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

.form-group input:disabled {
  background: var(--gray-100);
  color: var(--gray-500);
}

.form-group input.input-error {
  border-color: #ef4444;
}

.field-hint {
  display: block;
  margin-top: 6px;
  font-size: 12px;
  color: var(--gray-400);
}

.field-hint.error {
  color: #ef4444;
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

/* 加载状态 */
.loading-card {
  background: white;
  border-radius: var(--radius-xl);
  padding: 64px 32px;
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  color: var(--gray-500);
  font-size: 14px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--gray-200);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
