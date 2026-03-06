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
          <label>用户名 *</label>
          <input 
            type="text" 
            v-model="form.username" 
            placeholder="请输入用户名" 
            required
          />
        </div>

        <div class="form-group">
          <label>密码 *</label>
          <input 
            type="password" 
            v-model="form.password" 
            placeholder="请输入密码" 
            required
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
          <label>真实姓名</label>
          <input 
            type="text" 
            v-model="form.real_name" 
            placeholder="请输入真实姓名"
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
          <label>部门</label>
          <input 
            type="text" 
            v-model="form.department" 
            placeholder="请输入部门"
          />
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
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { adminApi } from '@/api'

const router = useRouter()
const submitting = ref(false)

const form = reactive({
  username: '',
  password: '',
  email: '',
  real_name: '',
  phone: '',
  department: ''
})

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
      email: form.email || undefined,
      real_name: form.real_name || undefined,
      phone: form.phone || undefined,
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

.form-group input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid var(--gray-200);
  border-radius: var(--radius);
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.form-group input:focus {
  border-color: var(--primary);
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
