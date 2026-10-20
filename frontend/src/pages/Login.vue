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

    <div class="login-split">
      <!-- 左侧：场景图片 -->
      <div class="login-left">
        <div class="scene-image">
          <img src="/images/b1eedd3e7a04e3594f1f9398fbbb99c4.jpg" alt="场景图片" class="scene-img" />
        </div>
      </div>

      <!-- 右侧：登录表单 + 文案 -->
      <div class="login-right">
        <!-- 背景文案装饰 -->
        <div class="slogans">
          <div class="slogan-item slogan-left">
            <span class="slogan-text">以智为翼，与 AI 共赴新境</span>
          </div>
          <div class="slogan-item slogan-right">
            <span class="slogan-text">知识沉淀于此，智能服务于你</span>
          </div>
          <div class="slogan-item slogan-left">
            <span class="slogan-text">每一次交互，都是与未来的温柔对话</span>
          </div>
          <div class="slogan-item slogan-right">
            <span class="slogan-text">智联万物，知见未来</span>
          </div>
        </div>
        <div class="login-box" :class="{ 'shake': shaking }">
          <div class="login-logo">
            <img 
              src="/images/生成马年专属 logo.png" 
              alt="logo" 
              class="logo-img" 
            />
          </div>
          <div class="login-title">RAG知识库系统</div>
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
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import FallingLeaves from '../components/FallingLeaves.vue'
import { useUserStore } from '../stores/user'
import { useToast } from '../utils/toast'

const router = useRouter()
const userStore = useUserStore()
const { showToast } = useToast()

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const rememberMe = ref(false)
const loading = ref(false)
const shaking = ref(false)

// 鼠标移动
const trails = ref([])
let trailId = 0
let trailTimeout = null

const handleMouseMove = (e) => {
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

onMounted(() => {})

onUnmounted(() => {
  if (trailTimeout) clearTimeout(trailTimeout)
})

const triggerShake = () => {
  shaking.value = true
  setTimeout(() => { shaking.value = false }, 600)
}

const handleLogin = async () => {
  loading.value = true
  try {
    const result = await userStore.login({
      username: username.value,
      password: password.value
    })
    if (result.success) {
      showToast('登录成功', 'success')
      router.push('/')
    } else {
      triggerShake()
      showToast(result.error || '账号或密码错误', 'error')
    }
  } catch (err) {
    triggerShake()
    showToast('网络错误，请稍后重试', 'error')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  position: relative;
  cursor: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="%234a9e7a" opacity="0.7"/></svg>') 12 12, auto;
}

.watermark {
  position: fixed;
  bottom: 20px;
  right: 30px;
  font-size: 14px;
  color: rgba(80, 150, 110, 0.45);
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
  background: radial-gradient(circle, rgba(100, 190, 140, 0.4) 0%, rgba(100, 190, 140, 0) 70%);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: opacity 0.2s ease-out, transform 0.2s ease-out;
  pointer-events: none;
}

/* 全屏左右分割布局 */
.login-split {
  display: flex;
  width: 100%;
  height: 100%;
  position: relative;
  z-index: 1;
}

/* 左侧：图片区域 - 比例 42% */
.login-left {
  width: 42%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

/* 左右过渡渐变 - 白色过渡 */
.login-left::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 100px;
  height: 100%;
  background: linear-gradient(to right, transparent 0%, rgba(255, 255, 255, 0.5) 50%, rgba(240, 253, 244, 0.9) 80%, #eefbf3 100%);
  z-index: 2;
  pointer-events: none;
}

.scene-image {
  width: 100%;
  height: 100%;
}

.scene-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  user-select: none;
  pointer-events: none;
  -webkit-user-drag: none;
}

/* 文案区域 - 放在右侧背景中 */
.slogans {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 80px 40px;
  z-index: 0;
  pointer-events: none;
}

.slogan-item {
  opacity: 0;
  animation: fadeSlideIn 1.2s ease forwards;
}

.slogan-item:nth-child(1) { animation-delay: 0.5s; }
.slogan-item:nth-child(2) { animation-delay: 1.0s; }
.slogan-item:nth-child(3) { animation-delay: 1.5s; }
.slogan-item:nth-child(4) { animation-delay: 2.0s; }

.slogan-left {
  text-align: left;
  padding-left: 10px;
}

.slogan-right {
  text-align: right;
  padding-right: 10px;
}

.slogan-text {
  font-size: 14px;
  font-weight: 300;
  color: rgba(60, 120, 80, 0.3);
  letter-spacing: 3px;
  line-height: 1.6;
  position: relative;
  display: inline-block;
  padding: 6px 0;
  font-style: italic;
}

@keyframes fadeSlideIn {
  from {
    opacity: 0;
    transform: translateY(15px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 右侧：登录表单 - 浅绿色 + 金色闪光 */
.login-right {
  width: 58%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(160deg, #eefbf3 0%, #e0f5e9 25%, #f0faf4 50%, #e8f8ee 75%, #f5fdf8 100%);
  padding: 50px 60px;
  position: relative;
  overflow: hidden;
}

/* 金色闪光光晕 */
.login-right::before {
  content: '';
  position: absolute;
  top: -30%;
  left: -30%;
  width: 160%;
  height: 160%;
  background: radial-gradient(ellipse at 25% 20%, rgba(212, 175, 55, 0.12) 0%, transparent 45%),
              radial-gradient(ellipse at 75% 75%, rgba(180, 140, 40, 0.08) 0%, transparent 40%),
              radial-gradient(ellipse at 60% 30%, rgba(255, 215, 0, 0.06) 0%, transparent 35%);
  animation: goldShimmer 6s ease-in-out infinite alternate;
  pointer-events: none;
}

/* 绿色柔光 */
.login-right::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle at 15% 85%, rgba(80, 200, 120, 0.1) 0%, transparent 40%),
              radial-gradient(circle at 85% 15%, rgba(100, 210, 140, 0.08) 0%, transparent 35%),
              radial-gradient(circle at 50% 50%, rgba(212, 175, 55, 0.04) 0%, transparent 50%);
  animation: greenGlow 8s ease-in-out infinite alternate;
  pointer-events: none;
}

@keyframes goldShimmer {
  0% { transform: translate(0, 0) rotate(0deg); opacity: 0.7; }
  50% { opacity: 1; }
  100% { transform: translate(1%, 1%) rotate(0.5deg); opacity: 0.8; }
}

@keyframes greenGlow {
  0% { opacity: 0.5; }
  100% { opacity: 1; }
}

.login-box {
  width: 100%;
  max-width: 360px;
  position: relative;
  z-index: 1;
}

.login-box.shake {
  animation: shakeForm 0.5s cubic-bezier(0.36, 0.07, 0.19, 0.97) both;
}

@keyframes shakeForm {
  0%, 100% { transform: translateX(0); }
  10%, 50%, 90% { transform: translateX(-6px); }
  30%, 70% { transform: translateX(6px); }
}

.login-title {
  text-align: center;
  font-size: 26px;
  font-weight: 700;
  color: #2d6a4f;
  margin-bottom: 28px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
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


.form-group {
  margin-bottom: 22px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #3d7a5a;
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
  color: rgba(60, 140, 90, 0.6);
  pointer-events: none;
}

.input {
  width: 100%;
  padding: 14px 14px 14px 46px;
  border: 1.5px solid rgba(80, 160, 120, 0.25);
  border-radius: var(--radius);
  font-size: 14px;
  color: #2d5a42;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(8px);
}

.input::placeholder {
  color: rgba(80, 140, 100, 0.4);
}

.input:focus {
  outline: none;
  border-color: rgba(80, 180, 120, 0.5);
  box-shadow: 0 0 0 4px rgba(80, 180, 120, 0.1), 0 2px 8px rgba(80, 160, 120, 0.1);
  background: rgba(255, 255, 255, 0.9);
}

.toggle-password {
  position: absolute;
  right: 14px;
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  color: rgba(80, 140, 100, 0.5);
  transition: color 0.2s;
}

.toggle-password:hover {
  color: rgba(60, 140, 90, 0.8);
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
  color: #4a8a66;
}

.remember-me input {
  width: 18px;
  height: 18px;
  accent-color: #4a9e7a;
}

.login-btn {
  width: 100%;
  padding: 15px;
  background: linear-gradient(135deg, #4a9e7a 0%, #3d9970 40%, #5ab88a 100%);
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
  box-shadow: 0 4px 15px rgba(74, 158, 122, 0.25), 0 1px 3px rgba(0, 0, 0, 0.08);
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(74, 158, 122, 0.35), 0 2px 6px rgba(0, 0, 0, 0.1);
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
  position: relative;
  z-index: 1;
}

.login-footer p {
  font-size: 12px;
  color: rgba(80, 140, 100, 0.5);
}

/* 移动端：隐藏左侧 */
@media (max-width: 768px) {
  .login-left { display: none; }
  .login-right { width: 100%; padding: 30px; }
}
</style>
