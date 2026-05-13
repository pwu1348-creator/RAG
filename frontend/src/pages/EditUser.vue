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
      <!-- 头像区域 -->
      <div class="avatar-section">
        <div class="avatar-preview" @click="triggerAvatarUpload" :title="avatarUrl ? '点击更换头像' : '点击上传头像'">
          <img v-if="avatarUrl" :src="avatarUrl" class="avatar-img" />
          <svg v-else viewBox="0 0 24 24" fill="currentColor" class="avatar-placeholder">
            <path d="M12,4A4,4 0 0,1 16,8A4,4 0 0,1 12,12A4,4 0 0,1 8,8A4,4 0 0,1 12,4M12,14C16.42,14 20,15.79 20,18V20H4V18C4,15.79 7.58,14 12,14Z"/>
          </svg>
          <div class="avatar-overlay">
            <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
              <path d="M4,4H7L9,1H15L17,4H20A2,2 0 0,1 22,6V18A2,2 0 0,1 20,20H4A2,2 0 0,1 2,18V6A2,2 0 0,1 4,4M12,7A5,5 0 0,0 7,12A5,5 0 0,0 12,17A5,5 0 0,0 17,12A5,5 0 0,0 12,7M12,9A3,3 0 0,1 15,12A3,3 0 0,1 12,15A3,3 0 0,1 9,12A3,3 0 0,1 12,9Z"/>
            </svg>
          </div>
        </div>
        <span class="avatar-hint">点击上传头像</span>
        <input
          ref="avatarInput"
          type="file"
          accept="image/png,image/jpeg,image/gif,image/webp"
          style="display:none"
          @change="handleAvatarChange"
        />
      </div>

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
import { useToast } from '@/utils/toast'

const route = useRoute()
const router = useRouter()
const { showToast } = useToast()
const submitting = ref(false)
const loading = ref(false)
const avatarInput = ref(null)
const avatarUrl = ref('')
const uploadingAvatar = ref(false)

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
    showToast('无效的用户ID', 'error')
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
      avatarUrl.value = res.data.avatar_url || ''
    }
  } catch (error) {
    console.error('获取用户详情失败:', error)
    showToast('获取用户详情失败: ' + (error.response?.data?.message || error.message || '网络错误，请检查后端服务'), 'error')
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
    showToast('请修正表单中的错误', 'warning')
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
    showToast('用户信息更新成功', 'success')
    router.push('/users?refresh=' + Date.now())
  } catch (error) {
    console.error('更新用户失败:', error)
    showToast('更新用户失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    submitting.value = false
  }
}

const triggerAvatarUpload = () => {
  avatarInput.value?.click()
}

const handleAvatarChange = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  // 前端预览
  const reader = new FileReader()
  reader.onload = (e) => { avatarUrl.value = e.target.result }
  reader.readAsDataURL(file)

  // 上传
  uploadingAvatar.value = true
  try {
    const res = await adminApi.uploadAvatar(route.params.id, file)
    if (res.data?.avatar_url) {
      avatarUrl.value = res.data.avatar_url
    }
  } catch (err) {
    console.error('Avatar upload failed:', err)
    const msg = err.response?.data?.message || err.response?.data?.detail || err.message || '未知错误'
    showToast('头像上传失败: ' + msg, 'error')
  } finally {
    uploadingAvatar.value = false
    event.target.value = ''
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

/* 头像区域 */
.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--gray-200);
}

.avatar-preview {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: var(--gray-100);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: box-shadow 0.2s;
}

.avatar-preview:hover {
  box-shadow: 0 0 0 3px var(--primary-light);
}

.avatar-preview:hover .avatar-overlay {
  opacity: 1;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 48px;
  height: 48px;
  color: var(--gray-400);
}

.avatar-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  opacity: 0;
  transition: opacity 0.2s;
}

.avatar-hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--gray-400);
}
</style>
