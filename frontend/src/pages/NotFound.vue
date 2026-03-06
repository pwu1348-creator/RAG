<template>
  <div class="not-found-page">
    <FallingLeaves />
    <div class="not-found-content">
      <div class="error-code">404</div>
      <div class="error-icon">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M12,2C6.48,2 2,6.48 2,12C2,17.52 6.48,22 12,22C17.52,22 22,17.52 22,12C22,6.48 17.52,2 12,2M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M8,16H10V10H8V16M14,16H16V10H14V16M12,6C11.17,6 10.5,6.67 10.5,7.5C10.5,8.33 11.17,9 12,9C12.83,9 13.5,8.33 13.5,7.5C13.5,6.67 12.83,6 12,6Z"/>
        </svg>
      </div>
      <h1 class="error-title">页面走丢了</h1>
      <p class="error-desc">抱歉，您访问的页面不存在或已被移除</p>
      <div class="error-actions">
        <router-link to="/" class="btn btn-primary">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M10,20V14H14V20H19V12H22L12,3L2,12H5V20H10Z"/>
          </svg>
          返回首页
        </router-link>
        <button class="btn btn-ghost" @click="$router.back()">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M20,11V13H8L13.5,18.5L12.08,19.92L4.16,12L12.08,4.08L13.5,5.5L8,11H20Z"/>
          </svg>
          返回上一页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import FallingLeaves from '../components/FallingLeaves.vue'
</script>

<style scoped>
.not-found-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}

.not-found-content {
  text-align: center;
  max-width: 480px;
}

.error-code {
  font-size: 120px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 50%, var(--earth) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
  margin-bottom: 20px;
  opacity: 0.8;
}

.error-icon {
  width: 100px;
  height: 100px;
  background: linear-gradient(135deg, rgba(168, 230, 207, 0.3) 0%, rgba(232, 213, 196, 0.3) 100%);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 32px;
  color: var(--primary-dark);
  animation: float 3s ease-in-out infinite;
}

.error-icon svg {
  width: 50px;
  height: 50px;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

.error-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--gray-800);
  margin-bottom: 12px;
}

.error-desc {
  font-size: 16px;
  color: var(--gray-500);
  margin-bottom: 32px;
}

.error-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.error-actions .btn svg {
  width: 20px;
  height: 20px;
}

@media (max-width: 480px) {
  .error-code {
    font-size: 80px;
  }
  
  .error-icon {
    width: 80px;
    height: 80px;
  }
  
  .error-icon svg {
    width: 40px;
    height: 40px;
  }
  
  .error-actions {
    flex-direction: column;
  }
}
</style>
