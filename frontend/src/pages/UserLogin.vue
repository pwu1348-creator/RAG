<template>
  <div class="user-login-page">
    <FallingLeaves :count="20" :interval="900" />
    <div class="watermark">@ 吴世鹏</div>

    <div class="login-split">
      <!-- 左侧：角色区域 -->
      <div class="mud-side" @mousemove="onMouseMove">
        <div class="side-transition"></div>
        <div class="mud-men-wrap">
          <MudMan
            :isTypingUsername="isTypingUsername"
            :isTypingPassword="isTypingPassword"
            :showPassword="showPwd"
            :hasPassword="password.length > 0"
            :mouseX="mouseX"
            :mouseY="mouseY"
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
              <img src="/images/生成马年专属 logo.png" alt="PengMind Logo" class="brand-logo-img" />
            </div>
            <span class="brand-name">PengMind</span>
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
import { ref, onMounted, onUnmounted } from 'vue'
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

// 角色交互状态
const mouseX = ref(0)
const mouseY = ref(0)
const isTypingUsername = ref(false)
const isTypingPassword = ref(false)

// 全局鼠标监听
function onMouseMove(e) {
  mouseX.value = e.clientX
  mouseY.value = e.clientY
}

function onUsernameFocus() {
  usernameFocused.value = true
  isTypingUsername.value = true
  isTypingPassword.value = false
}

function onUsernameBlur() {
  usernameFocused.value = false
  isTypingUsername.value = false
}

function onUsernameInput() {
  isTypingUsername.value = true
}

function onPasswordFocus() {
  passwordFocused.value = true
  isTypingPassword.value = true
  isTypingUsername.value = false
}

function onPasswordBlur() {
  passwordFocused.value = false
  isTypingPassword.value = false
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
  window.addEventListener('mousemove', onMouseMove)
})

onUnmounted(() => {
  window.removeEventListener('mousemove', onMouseMove)
})
</script>

<style scoped>
.user-login-page {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  position: relative;
}

.watermark {
  position: fixed;
  bottom: 16px; right: 24px;
  font-size: 13px;
  color: rgba(80, 140, 180, 0.4);
  pointer-events: none;
  z-index: 100;
  user-select: none;
}

/* 全屏左右分割 */
.login-split {
  display: flex;
  width: 100%;
  height: 100%;
  position: relative;
  z-index: 1;
}

/* 左侧泥巴人区域 - 占 57%，亮绿色 */
.mud-side {
  width: 57%;
  height: 100%;
  background: linear-gradient(160deg, #d4f5e0 0%, #b8ecd0 30%, #a0e8c0 60%, #c5f2d8 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

/* 左右过渡渐变 - 白色过渡到深绿 */
.side-transition {
  position: absolute;
  top: 0;
  right: 0;
  width: 100px;
  height: 100%;
  background: linear-gradient(to right, transparent 0%, rgba(255, 255, 255, 0.4) 35%, rgba(240, 255, 245, 0.6) 55%, rgba(18, 46, 37, 0.8) 85%, #122e25 100%);
  z-index: 3;
  pointer-events: none;
}

.mud-side::before {
  content: '';
  position: absolute;
  top: -120px; left: -120px;
  width: 350px; height: 350px;
  background: rgba(255,255,255,0.2);
  border-radius: 50%;
}
.mud-side::after {
  content: '';
  position: absolute;
  bottom: 80px; right: -80px;
  width: 250px; height: 250px;
  background: rgba(255,255,255,0.12);
  border-radius: 50%;
}

.mud-men-wrap {
  position: relative;
  width: 418px;
  height: 304px;
  flex-shrink: 0;
  overflow: visible;
}

.mud-men-wrap :deep(.chars-wrap) {
  transform: scale(0.76);
  transform-origin: bottom center;
  position: absolute;
  bottom: 0;
  left: 50%;
  translate: -50% 0;
}

.mud-title {
  text-align: center;
  z-index: 2;
  margin-top: 24px;
}

.mud-title-text {
  display: block;
  font-size: 22px;
  font-weight: 700;
  color: #2d6a4f;
  margin-bottom: 8px;
}

.mud-title-sub {
  display: block;
  font-size: 14px;
  color: #40a070;
  line-height: 1.5;
}

/* 右侧表单 - 占 43%，深绿色高级渐变 */
.form-side {
  width: 43%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(160deg, #122e25 0%, #1a3d32 25%, #0f2b22 50%, #1c4438 75%, #122e25 100%);
  padding: 48px 44px;
  position: relative;
  overflow: hidden;
}

/* 装饰光晕 - 绿色金色柔光 */
.form-side::before {
  content: '';
  position: absolute;
  top: -150px; right: -150px;
  width: 400px; height: 400px;
  background: radial-gradient(circle, rgba(80, 200, 140, 0.12) 0%, transparent 60%);
  pointer-events: none;
  animation: greenGlow 7s ease-in-out infinite alternate;
}
.form-side::after {
  content: '';
  position: absolute;
  bottom: -100px; left: -100px;
  width: 350px; height: 350px;
  background: radial-gradient(circle, rgba(200, 170, 60, 0.08) 0%, transparent 60%);
  pointer-events: none;
  animation: greenGlow2 5s ease-in-out infinite alternate;
}

@keyframes greenGlow {
  0% { opacity: 0.5; transform: scale(1); }
  100% { opacity: 1; transform: scale(1.08); }
}

@keyframes greenGlow2 {
  0% { opacity: 0.4; }
  100% { opacity: 0.9; }
}

.form-inner {
  width: 100%;
  max-width: 320px;
  position: relative;
  z-index: 2;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 32px;
}

.brand-icon {
  width: 40px; height: 40px;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  overflow: hidden;
}

.brand-logo-img {
  width: 40px;
  height: 40px;
  object-fit: contain;
  border-radius: 10px;
  pointer-events: none;
  user-select: none;
}

.brand-name {
  font-size: 20px;
  font-weight: 700;
  color: rgba(200, 240, 220, 0.9);
}

.form-title {
  font-size: 28px;
  font-weight: 700;
  color: rgba(220, 250, 235, 0.95);
  margin-bottom: 8px;
  text-shadow: 0 0 15px rgba(80, 200, 140, 0.2);
}

.form-sub {
  font-size: 14px;
  color: rgba(150, 210, 180, 0.7);
  margin-bottom: 32px;
}

.error-tip {
  padding: 10px 14px;
  background: rgba(239,68,68,0.12);
  border: 1px solid rgba(239,68,68,0.35);
  border-radius: 10px;
  color: #fca5a5;
  font-size: 13px;
  margin-bottom: 18px;
}

.field {
  margin-bottom: 20px;
}

.field label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: rgba(160, 220, 190, 0.85);
  margin-bottom: 7px;
}

.input-box {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.07);
  border: 1.5px solid rgba(80, 180, 130, 0.3);
  border-radius: 12px;
  padding: 0 14px;
  transition: all 0.25s;
  backdrop-filter: blur(4px);
}

.input-box.focused {
  border-color: rgba(80, 200, 140, 0.6);
  background: rgba(255, 255, 255, 0.12);
  box-shadow: 0 0 0 4px rgba(80, 180, 130, 0.12);
}

.field-icon {
  width: 18px; height: 18px;
  color: rgba(100, 200, 150, 0.7);
  flex-shrink: 0;
  margin-right: 10px;
}

.input-box input {
  flex: 1;
  border: none;
  background: transparent;
  padding: 14px 0;
  font-size: 14px;
  color: rgba(220, 250, 235, 0.95);
  outline: none;
}

.input-box input::placeholder { color: rgba(140, 200, 170, 0.4); }

/* 隐藏浏览器原生密码显示眼睛按钮 */
.input-box input[type="password"]::-ms-reveal,
.input-box input[type="password"]::-ms-clear {
  display: none;
}
.input-box input[type="password"]::-webkit-credentials-auto-fill-button,
.input-box input[type="password"]::-webkit-textfield-decoration-container {
  display: none !important;
}

.eye-btn {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  color: rgba(120, 200, 160, 0.5);
  display: flex;
  align-items: center;
  transition: color 0.2s;
}
.eye-btn:hover { color: rgba(120, 220, 170, 0.9); }
.eye-btn svg { width: 18px; height: 18px; }

.form-opts {
  display: flex;
  align-items: center;
  margin-bottom: 28px;
}

.remember {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
  color: rgba(150, 210, 180, 0.7);
  cursor: pointer;
}

.remember input {
  width: 16px; height: 16px;
  accent-color: #4a9e7a;
}

.login-btn {
  width: 100%;
  padding: 15px;
  background: linear-gradient(135deg, #2d8a5e 0%, #3da876 50%, #2d8a5e 100%);
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
  box-shadow: 0 4px 15px rgba(45, 138, 94, 0.3), 0 1px 3px rgba(0, 0, 0, 0.1);
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(45, 138, 94, 0.45), 0 2px 6px rgba(0, 0, 0, 0.12);
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
  margin-top: 32px;
  font-size: 11px;
  color: rgba(120, 180, 150, 0.4);
}

/* 移动端：隐藏左侧 */
@media (max-width: 768px) {
  .mud-side { display: none; }
  .form-side { width: 100%; padding: 36px 28px; }
}
</style>
