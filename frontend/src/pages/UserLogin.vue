<template>
  <div class="user-login-page">
    <FallingLeaves :count="20" :interval="900" />
    <div class="watermark">@ 吴世鹏</div>

    <div class="login-card">
      <!-- 左侧：泥巴人 -->
      <div class="mud-side">
        <div class="mud-men-wrap">
          <MudMan
            v-for="(m, i) in mudMen"
            :key="i"
            :state="m.state"
            :style="m.style"
          />
        </div>
        <div class="mud-title">
          <span class="mud-title-text">智能问答助手</span>
          <span class="mud-title-sub">基于 RAG 技术，精准检索文档知识</span>
        </div>
      </div>

      <!-- 右侧：登录表单 -->
      <div class="form-side">
        <div class="form-inner">
          <div class="brand">
            <div class="brand-icon">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12,3L1,9L12,15L21,10.09V17H23V9M5,13.18V17.18L12,21L19,17.18V13.18L12,17L5,13.18Z"/>
              </svg>
            </div>
            <span class="brand-name">RAG 知识库</span>
          </div>

          <h2 class="form-title">用户登录</h2>
          <p class="form-sub">欢迎回来，请输入您的账号信息</p>

          <div v-if="errorMsg" class="error-tip">{{ errorMsg }}</div>

          <form @submit.prevent="handleLogin">
            <!-- 账号 -->
            <div class="field">
              <label>账号</label>
              <div class="input-box" :class="{ focused: usernameFocused }">
                <svg class="field-icon" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12,4A4,4 0 0,1 16,8A4,4 0 0,1 12,12A4,4 0 0,1 8,8A4,4 0 0,1 12,4M12,14C16.42,14 20,15.79 20,18V20H4V18C4,15.79 7.58,14 12,14Z"/>
                </svg>
                <input
                  ref="usernameRef"
                  v-model="username"
                  type="text"
                  placeholder="请输入账号"
                  autocomplete="username"
                  @focus="onUsernameFocus"
                  @blur="onUsernameBlur"
                  @input="onUsernameInput"
                />
              </div>
            </div>

            <!-- 密码 -->
            <div class="field">
              <label>密码</label>
              <div class="input-box" :class="{ focused: passwordFocused }">
                <svg class="field-icon" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12,17A2,2 0 0,0 14,15C14,13.89 13.1,13 12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17M18,8A2,2 0 0,1 20,10V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V10C4,8.89 4.9,8 6,8H7V6A5,5 0 0,1 17,6V8H18M12,6A3,3 0 0,0 9,9V8H15V9A3,3 0 0,0 12,6Z"/>
                </svg>
                <input
                  ref="passwordRef"
                  v-model="password"
                  :type="showPwd ? 'text' : 'password'"
                  placeholder="请输入密码"
                  autocomplete="current-password"
                  @focus="onPasswordFocus"
                  @blur="onPasswordBlur"
                />
                <button type="button" class="eye-btn" @click="showPwd = !showPwd" tabindex="-1">
                  <svg v-if="showPwd" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9M12,17A5,5 0 0,1 7,12A5,5 0 0,1 12,7A5,5 0 0,1 17,12A5,5 0 0,1 12,17M12,4.5C7,4.5 2.73,7.61 1,12C2.73,16.39 7,19.5 12,19.5C17,19.5 21.27,16.39 23,12C21.27,7.61 17,4.5 12,4.5Z"/>
                  </svg>
                  <svg v-else viewBox="0 0 24 24" fill="currentColor">
                    <path d="M11.83,9L15,12.16C15,12.11 15,12.05 15,12A3,3 0 0,0 12,9C11.94,9 11.89,9 11.83,9M7.53,9.8L9.08,11.35C9.03,11.56 9,11.77 9,12A3,3 0 0,0 12,15C12.22,15 12.44,14.97 12.65,14.92L14.2,16.47C13.53,16.8 12.79,17 12,17A5,5 0 0,1 7,12C7,11.21 7.2,10.47 7.53,9.8M2,4.27L4.28,6.55L4.73,7C3.08,8.3 1.78,10 1,12C2.73,16.39 7,19.5 12,19.5C13.55,19.5 15.03,19.2 16.38,18.66L16.81,19.08L19.73,22L21,20.73L3.27,3M12,7A5,5 0 0,1 17,12C17,12.64 16.87,13.26 16.64,13.82L19.57,16.75C21.07,15.5 22.27,13.86 23,12C21.27,7.61 17,4.5 12,4.5C10.6,4.5 9.26,4.75 8,5.2L10.17,7.35C10.74,7.13 11.35,7 12,7Z"/>
                  </svg>
                </button>
              </div>
            </div>

            <div class="form-opts">
              <label class="remember">
                <input type="checkbox" v-model="rememberMe" />
                <span>记住我</span>
              </label>
            </div>

            <button type="submit" class="login-btn" :disabled="loading">
              <span v-if="loading" class="loading-dot"></span>
              <span>{{ loading ? '登录中...' : '立即登录' }}</span>
              <svg v-if="!loading" viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
                <path d="M4,11V13H16L10.5,18.5L11.92,19.92L19.84,12L11.92,4.08L10.5,5.5L16,11H4Z"/>
              </svg>
            </button>
          </form>

          <p class="footer-tip">© 2026 RAG System · 智能知识库问答平台</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import FallingLeaves from '../components/FallingLeaves.vue'
import MudMan from '../components/MudMan.vue'

const router = useRouter()

const username = ref('')
const password = ref('')
const showPwd = ref(false)
const rememberMe = ref(false)
const loading = ref(false)
const errorMsg = ref('')
const usernameFocused = ref(false)
const passwordFocused = ref(false)
const usernameRef = ref(null)
const passwordRef = ref(null)

// 泥巴人状态: idle | peek | username | password
const mudState = ref('idle')

// 三个泥巴人，位置错落
const mudMen = computed(() => [
  { state: mudState.value, style: { left: '10px', bottom: '20px', transform: 'scale(0.85)' } },
  { state: mudState.value, style: { left: '90px', bottom: '30px', transform: 'scale(1)' } },
  { state: mudState.value, style: { left: '175px', bottom: '15px', transform: 'scale(0.9)' } },
])

let idleTimer = null

function resetIdleTimer() {
  clearTimeout(idleTimer)
  idleTimer = setTimeout(() => {
    if (mudState.value !== 'password') {
      mudState.value = 'peek'
    }
  }, 2000)
}

function onUsernameFocus() {
  usernameFocused.value = true
  mudState.value = 'username'
  clearTimeout(idleTimer)
}

function onUsernameBlur() {
  usernameFocused.value = false
  resetIdleTimer()
}

function onUsernameInput() {
  mudState.value = 'username'
  resetIdleTimer()
}

function onPasswordFocus() {
  passwordFocused.value = true
  mudState.value = 'password'
  clearTimeout(idleTimer)
}

function onPasswordBlur() {
  passwordFocused.value = false
  resetIdleTimer()
}

async function handleLogin() {
  if (!username.value || !password.value) {
    errorMsg.value = '请输入账号和密码'
    return
  }
  errorMsg.value = ''
  loading.value = true

  try {
    const { default: axios } = await import('axios')
    // 用户登录走 QA Service (8002)，QA Service 未启动则无法登录
    const res = await axios.post('/api/qa/auth/user/login', {
      username: username.value,
      password: password.value,
    })
    const data = res.data
    if (data.code === 200 && data.data?.success) {
      localStorage.setItem('user_token', data.data.token)
      localStorage.setItem('user_info', JSON.stringify(data.data.user || {}))
      if (rememberMe.value) {
        localStorage.setItem('user_remember', username.value)
      }
      router.push('/user/chat')
    } else {
      errorMsg.value = data.data?.message || data.message || '账号或密码错误'
    }
  } catch (e) {
    errorMsg.value = e.response?.data?.message || '网络错误，请稍后重试'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  const remembered = localStorage.getItem('user_remember')
  if (remembered) {
    username.value = remembered
    rememberMe.value = true
  }
  // 初始偷看
  idleTimer = setTimeout(() => { mudState.value = 'peek' }, 1500)
})

onUnmounted(() => {
  clearTimeout(idleTimer)
})
</script>

<style scoped>
.user-login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e8f8f0 0%, #f0faf5 40%, #e0f4ec 100%);
  padding: 20px;
  position: relative;
  overflow: hidden;
}

/* 背景装饰圆 */
.user-login-page::before {
  content: '';
  position: fixed;
  width: 600px; height: 600px;
  background: radial-gradient(circle, rgba(168,230,207,0.25) 0%, transparent 70%);
  top: -200px; right: -200px;
  pointer-events: none;
}
.user-login-page::after {
  content: '';
  position: fixed;
  width: 400px; height: 400px;
  background: radial-gradient(circle, rgba(136,216,176,0.2) 0%, transparent 70%);
  bottom: -100px; left: -100px;
  pointer-events: none;
}

.watermark {
  position: fixed;
  bottom: 16px; right: 24px;
  font-size: 13px;
  color: rgba(127,205,205,0.45);
  pointer-events: none;
  z-index: 100;
  user-select: none;
}

/* 卡片 */
.login-card {
  display: flex;
  width: 100%;
  max-width: 900px;
  min-height: 520px;
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  box-shadow: 0 20px 60px rgba(100,180,140,0.18), 0 4px 20px rgba(0,0,0,0.06);
  overflow: hidden;
  position: relative;
  z-index: 10;
}

/* 左侧泥巴人区域 */
.mud-side {
  width: 340px;
  flex-shrink: 0;
  background: linear-gradient(160deg, #c8f0dc 0%, #a8e6cf 40%, #88d8b0 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  padding: 32px 24px 36px;
  position: relative;
  overflow: hidden;
}

.mud-side::before {
  content: '';
  position: absolute;
  top: -60px; left: -60px;
  width: 200px; height: 200px;
  background: rgba(255,255,255,0.15);
  border-radius: 50%;
}
.mud-side::after {
  content: '';
  position: absolute;
  bottom: 80px; right: -40px;
  width: 150px; height: 150px;
  background: rgba(255,255,255,0.1);
  border-radius: 50%;
}

.mud-men-wrap {
  position: relative;
  width: 280px;
  height: 200px;
  flex-shrink: 0;
}

.mud-title {
  text-align: center;
  z-index: 2;
  margin-top: 16px;
}

.mud-title-text {
  display: block;
  font-size: 20px;
  font-weight: 700;
  color: #2d6a4f;
  margin-bottom: 6px;
}

.mud-title-sub {
  display: block;
  font-size: 13px;
  color: #52b788;
  line-height: 1.5;
}

/* 右侧表单 */
.form-side {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 56px;
}

.form-inner {
  width: 100%;
  max-width: 320px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 28px;
}

.brand-icon {
  width: 36px; height: 36px;
  background: linear-gradient(135deg, #a8e6cf, #52b788);
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  color: white;
}

.brand-icon svg { width: 20px; height: 20px; }

.brand-name {
  font-size: 18px;
  font-weight: 700;
  color: #2d6a4f;
}

.form-title {
  font-size: 26px;
  font-weight: 700;
  color: #1b4332;
  margin-bottom: 6px;
}

.form-sub {
  font-size: 14px;
  color: #74c69d;
  margin-bottom: 28px;
}

.error-tip {
  padding: 10px 14px;
  background: rgba(239,68,68,0.08);
  border: 1px solid rgba(239,68,68,0.25);
  border-radius: 10px;
  color: #ef4444;
  font-size: 13px;
  margin-bottom: 18px;
}

.field {
  margin-bottom: 18px;
}

.field label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #2d6a4f;
  margin-bottom: 7px;
}

.input-box {
  display: flex;
  align-items: center;
  background: rgba(240,250,245,0.8);
  border: 2px solid rgba(168,230,207,0.4);
  border-radius: 12px;
  padding: 0 14px;
  transition: all 0.25s;
}

.input-box.focused {
  border-color: #52b788;
  background: white;
  box-shadow: 0 0 0 4px rgba(82,183,136,0.12);
}

.field-icon {
  width: 18px; height: 18px;
  color: #74c69d;
  flex-shrink: 0;
  margin-right: 10px;
}

.input-box input {
  flex: 1;
  border: none;
  background: transparent;
  padding: 13px 0;
  font-size: 14px;
  color: #1b4332;
  outline: none;
}

.input-box input::placeholder { color: #b7e4c7; }

.eye-btn {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  color: #74c69d;
  display: flex;
  align-items: center;
  transition: color 0.2s;
}
.eye-btn:hover { color: #52b788; }
.eye-btn svg { width: 18px; height: 18px; }

.form-opts {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
}

.remember {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
  color: #52b788;
  cursor: pointer;
}

.remember input {
  width: 16px; height: 16px;
  accent-color: #52b788;
}

.login-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #52b788 0%, #2d6a4f 100%);
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.25s;
  box-shadow: 0 4px 14px rgba(82,183,136,0.35);
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 22px rgba(82,183,136,0.45);
}

.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.loading-dot {
  width: 16px; height: 16px;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.footer-tip {
  text-align: center;
  margin-top: 28px;
  font-size: 11px;
  color: #b7e4c7;
}

@media (max-width: 700px) {
  .mud-side { display: none; }
  .form-side { padding: 36px 28px; }
}
</style>
