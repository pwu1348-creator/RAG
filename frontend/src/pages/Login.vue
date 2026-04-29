<template>
  <div class="login-page" @mousemove="handleMouseMove">
    <!-- 飘落叶子 -->
    <FallingLeaves :count="25" :interval="800" />
    
    <!-- 水印 -->
    <div class="watermark">@ 吴世鹏</div>
    
    <!-- 鼠标尾迹 -->
    <div class="cursor-trail-container">
      <div 
        v-for="(trail, index) in trails" 
        :key="trail.id"
        class="cursor-trail"
        :style="{
          left: trail.x + 'px',
          top: trail.y + 'px',
          opacity: trail.opacity,
          transform: `scale(${trail.scale})`
        }"
      ></div>
    </div>

    <div class="login-container">
      <!-- 几何立方体装饰 -->
      <div class="cube-decoration cube-top-right"></div>
      <div class="cube-decoration cube-bottom-right"></div>
      <div class="cube-decoration cube-bottom-left"></div>
      <div class="cube-decoration cube-right-center"></div>
      
      <div class="login-left">
        <!-- 泥巴人 -->
        <div class="mud-man-area" ref="mudManAreaRef">
          <MudMan
            :state="mudManState"
            :mouseX="mouseX"
            :mouseY="mouseY"
            :centerX="mudManCenterX"
            :centerY="mudManCenterY"
            :leaning="mudManLeaning"
          />
        </div>
      </div>

      <div class="login-right">
        <div class="login-box">
          <div class="login-logo">
            <img 
              src="/images/生成马年专属 logo.png" 
              alt="logo" 
              class="logo-img" 
            />
          </div>
          <div class="login-title">RAG知识库系统</div>
          <div v-if="error" class="error-message">{{ error }}</div>
          <form class="login-form" @submit.prevent="handleLogin">
            <div class="form-group">
              <label>用户名</label>
              <div class="input-wrapper">
                <svg class="input-icon" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M20,4H4C2.89,4 2,4.89 2,6V18A2,2 0 0,0 4,20H20A2,2 0 0,0 22,18V6C22,4.89 21.1,4 20,4M20,8L12,13L4,8V6L12,11L20,6V8Z"/>
                </svg>
                <input
                  type="text"
                  class="input"
                  placeholder="请输入用户名"
                  v-model="username"
                  @focus="onUsernameFocus"
                  @blur="onInputBlur"
                  required
                />
              </div>
            </div>
            <div class="form-group">
              <label>密码</label>
              <div class="input-wrapper">
                <svg class="input-icon" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12,17A2,2 0 0,0 14,15C14,13.89 13.1,13 12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17M18,8A2,2 0 0,1 20,10V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V10C4,8.89 4.9,8 6,8H7V6A5,5 0 0,1 17,6V8H18M6,20H18V10H6V20M12,6A3,3 0 0,0 9,9V8H15V9A3,3 0 0,0 12,6Z"/>
                </svg>
                <input
                  :type="showPassword ? 'text' : 'password'"
                  class="input"
                  placeholder="请输入密码"
                  v-model="password"
                  @focus="onPasswordFocus"
                  @blur="onInputBlur"
                  required
                />
                <button
                  type="button"
                  class="toggle-password"
                  @click="showPassword = !showPassword"
                >
                  <svg v-if="showPassword" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9M12,17A5,5 0 0,1 7,12A5,5 0 0,1 12,7A5,5 0 0,1 17,12A5,5 0 0,1 12,17M12,4.5C7,4.5 2.73,7.61 1,12C2.73,16.39 7,19.5 12,19.5C17,19.5 21.27,16.39 23,12C21.27,7.61 17,4.5 12,4.5Z"/>
                  </svg>
                  <svg v-else viewBox="0 0 24 24" fill="currentColor">
                    <path d="M11.83,9L15,12.16C15,12.11 15,12.05 15,12A3,3 0 0,0 12,9C11.94,9 11.89,9 11.83,9M7.53,9.8L9.08,11.35C9.03,11.56 9,11.77 9,12A3,3 0 0,0 12,15C12.22,15 12.44,14.97 12.65,14.92L14.2,16.47C13.53,16.8 12.79,17 12,17A5,5 0 0,1 7,12C7,11.21 7.2,10.47 7.53,9.8M2,4.27L4.28,6.55L4.73,7C3.08,8.3 1.78,10 1,12C2.73,16.39 7,19.5 12,19.5C13.55,19.5 15.03,19.2 16.38,18.66L16.81,19.08L19.73,22L21,20.73L3.27,3M12,7A5,5 0 0,1 17,12C17,12.64 16.87,13.26 16.64,13.82L19.57,16.75C21.07,15.5 22.27,13.86 23,12C21.27,7.61 17,4.5 12,4.5C10.6,4.5 9.26,4.75 8,5.2L10.17,7.35C10.74,7.13 11.35,7 12,7Z"/>
                  </svg>
                </button>
              </div>
            </div>
            <div class="form-options">
              <label class="remember-me">
                <input type="checkbox" v-model="rememberMe"/>
                <span>记住我</span>
              </label>
            </div>
            <button type="submit" class="btn btn-primary login-btn" :disabled="loading">
              <span v-if="loading">登录中...</span>
              <span v-else>立即登录</span>
              <svg v-if="!loading" viewBox="0 0 24 24" fill="currentColor">
                <path d="M4,11V13H16L10.5,18.5L11.92,19.92L19.84,12L11.92,4.08L10.5,5.5L16,11H4Z"/>
              </svg>
            </button>
          </form>
        </div>
        <div class="login-footer">
          <p>© 2026 RAG System · 智能知识库管理平台</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import FallingLeaves from '../components/FallingLeaves.vue'
import MudMan from '../components/MudMan.vue'
import { useUserStore } from '../stores/user'

const router = useRouter()
const { t } = useI18n()
const userStore = useUserStore()

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const rememberMe = ref(false)
const loading = ref(false)
const error = ref('')

// 鼠标位置
const mouseX = ref(0)
const mouseY = ref(0)

// 泥巴人状态：idle | username | password
const mudManState = ref('idle')
// 泥巴人倾斜方向：'' | 'left' | 'right'
const mudManLeaning = ref('')
// 泥巴人中心坐标（用于眼球跟随计算）
const mudManCenterX = ref(0)
const mudManCenterY = ref(0)
const mudManAreaRef = ref(null)

// 更新泥巴人中心坐标
const updateMudManCenter = () => {
  if (mudManAreaRef.value) {
    const rect = mudManAreaRef.value.getBoundingClientRect()
    mudManCenterX.value = rect.left + rect.width / 2
    mudManCenterY.value = rect.top + rect.height / 2
  }
}

// 鼠标移动
const trails = ref([])
let trailId = 0
let trailTimeout = null

const handleMouseMove = (e) => {
  mouseX.value = e.clientX
  mouseY.value = e.clientY

  const newTrail = {
    id: trailId++,
    x: e.clientX,
    y: e.clientY,
    opacity: 0.6,
    scale: 1
  }
  trails.value.push(newTrail)
  setTimeout(() => {
    const trail = trails.value.find(t => t.id === newTrail.id)
    if (trail) { trail.opacity = 0.3; trail.scale = 0.8 }
  }, 100)
  setTimeout(() => {
    const trail = trails.value.find(t => t.id === newTrail.id)
    if (trail) { trail.opacity = 0.1; trail.scale = 0.5 }
  }, 200)
  if (trails.value.length > 15) trails.value.shift()
  if (trailTimeout) clearTimeout(trailTimeout)
  trailTimeout = setTimeout(() => {
    trails.value = trails.value.slice(-10)
  }, 500)
}

// 输入框聚焦/失焦
// 登录框在右侧 → 泥巴人在左侧 → 输入时身体向左倾（远离输入框）
const onUsernameFocus = () => {
  mudManState.value = 'username'
  mudManLeaning.value = 'left'
}

const onPasswordFocus = () => {
  mudManState.value = 'password'
  mudManLeaning.value = 'left'
}

const onInputBlur = () => {
  mudManState.value = 'idle'
  mudManLeaning.value = ''
}

onMounted(() => {
  nextTick(() => {
    updateMudManCenter()
  })
  window.addEventListener('resize', updateMudManCenter)
})

onUnmounted(() => {
  if (trailTimeout) clearTimeout(trailTimeout)
  window.removeEventListener('resize', updateMudManCenter)
})

const handleLogin = async () => {
  error.value = ''
  loading.value = true
  try {
    const result = await userStore.login({
      username: username.value,
      password: password.value
    })
    if (result.success) {
      router.push('/')
    } else {
      error.value = result.error || '登录失败'
    }
  } catch (err) {
    error.value = '网络错误'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  cursor: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="%237fcdcd" opacity="0.8"/></svg>') 12 12, auto;
  position: relative;
}

.watermark {
  position: fixed;
  bottom: 20px;
  right: 30px;
  font-size: 14px;
  color: rgba(127, 205, 205, 0.5);
  font-weight: 500;
  pointer-events: none;
  z-index: 100;
  user-select: none;
  letter-spacing: 1px;
}

.cursor-trail-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 9999;
}

.cursor-trail {
  position: absolute;
  width: 16px;
  height: 16px;
  background: radial-gradient(circle, rgba(127, 205, 205, 0.4) 0%, rgba(127, 205, 205, 0) 70%);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: opacity 0.2s ease-out, transform 0.2s ease-out;
  pointer-events: none;
}

.login-container {
  display: flex;
  width: 100%;
  max-width: 1000px;
  min-height: 550px;
  background: linear-gradient(135deg, rgba(200, 240, 230, 0.95) 0%, rgba(255, 255, 255, 0.98) 50%, rgba(200, 240, 230, 0.95) 100%);
  backdrop-filter: blur(20px);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  overflow: hidden;
  position: relative;
  z-index: 10;
}

/* 几何立方体装饰 */
.cube-decoration {
  position: absolute;
  width: 60px;
  height: 60px;
  opacity: 0.15;
  z-index: 1;
}

.cube-decoration::before,
.cube-decoration::after {
  content: '';
  position: absolute;
  background: #7fcdcd;
}

.cube-decoration::before {
  width: 100%;
  height: 100%;
  transform: rotateX(45deg) rotateZ(45deg);
  border-radius: 4px;
}

.cube-decoration::after {
  width: 60%;
  height: 60%;
  top: 20%;
  left: 20%;
  transform: rotateX(45deg) rotateZ(45deg);
  background: rgba(127, 205, 205, 0.5);
  border-radius: 3px;
}

.cube-top-right { top: 20px; right: 20px; }
.cube-bottom-right { bottom: 20px; right: 40px; width: 40px; height: 40px; }
.cube-bottom-left { bottom: 20px; left: 20px; width: 50px; height: 50px; }

.cube-decoration {
  animation: cubeFloat 6s ease-in-out infinite;
}
.cube-top-right { animation-delay: 0s; }
.cube-bottom-right { animation-delay: 2s; }
.cube-bottom-left { animation-delay: 4s; }
.cube-right-center { animation-delay: 3s; }

@keyframes cubeFloat {
  0%, 100% { transform: translateY(0) rotate(0deg); opacity: 0.1; }
  50% { transform: translateY(-10px) rotate(5deg); opacity: 0.2; }
}

.cube-right-center {
  top: 50%;
  right: 30%;
  transform: translateY(-50%);
  width: 35px;
  height: 35px;
}

/* 左侧：泥巴人区域 */
.login-left {
  flex: 1;
  background: linear-gradient(135deg, rgba(200, 240, 230, 0.9) 0%, rgba(220, 245, 235, 0.95) 100%);
  padding: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  border-radius: var(--radius-xl) 0 0 var(--radius-xl);
}

.mud-man-area {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  min-height: 280px;
}

/* 右侧登录 */
.login-right {
  flex: 1;
  padding: 50px 60px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
}

.login-box {
  width: 100%;
  max-width: 320px;
  margin: 0 auto;
}

.login-title {
  text-align: center;
  font-size: 24px;
  font-weight: 700;
  color: var(--gray-800);
  margin-bottom: 24px;
}

.login-logo {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
  user-select: none;
  -webkit-user-select: none;
}

.logo-img {
  width: 120px;
  height: auto;
  user-select: none;
  -webkit-user-select: none;
  pointer-events: none;
}

.error-message {
  padding: 12px 16px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: var(--radius);
  color: #ef4444;
  font-size: 14px;
  margin-bottom: 20px;
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

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 14px;
  width: 20px;
  height: 20px;
  color: var(--primary);
  pointer-events: none;
}

.input {
  width: 100%;
  padding: 14px 14px 14px 46px;
  border: 2px solid rgba(127, 205, 205, 0.3);
  border-radius: var(--radius);
  font-size: 14px;
  color: var(--gray-800);
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.9);
}

.input::placeholder {
  color: var(--gray-400);
}

.input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 4px rgba(127, 205, 205, 0.2);
  background: white;
}

.toggle-password {
  position: absolute;
  right: 14px;
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  color: var(--gray-400);
  transition: color 0.2s;
}

.toggle-password:hover {
  color: var(--primary);
}

.toggle-password svg {
  width: 20px;
  height: 20px;
  position: static;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
}

.remember-me {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: var(--gray-600);
}

.remember-me input {
  width: 18px;
  height: 18px;
  accent-color: var(--primary);
}

.login-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  border: none;
  border-radius: var(--radius);
  font-size: 16px;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(127, 205, 205, 0.4);
}

.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.login-btn svg {
  width: 20px;
  height: 20px;
}

.login-footer {
  text-align: center;
  margin-top: 40px;
}

.login-footer p {
  font-size: 12px;
  color: var(--gray-400);
}

@media (max-width: 768px) {
  .login-container {
    flex-direction: column;
  }
  .login-left {
    min-height: 260px;
  }
  .login-right {
    padding: 30px;
  }
}
</style>
