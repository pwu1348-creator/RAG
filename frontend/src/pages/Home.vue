<template>
  <div class="home-page">
    <!-- 欢迎区域 -->
    <section class="welcome-section">
      <div class="welcome-content">
        <div class="welcome-badge">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4M12,6A6,6 0 0,0 6,12A6,6 0 0,0 12,18A6,6 0 0,0 18,12A6,6 0 0,0 12,6M12,8A4,4 0 0,1 16,12A4,4 0 0,1 12,16A4,4 0 0,1 8,12A4,4 0 0,1 12,8Z"/>
          </svg>
          <span>智能问答系统</span>
        </div>
        <h1 class="welcome-title">
          欢迎回来，<span class="highlight">管理员</span>
        </h1>
        <p class="welcome-desc">
          基于 RAG 技术的智能知识库问答系统，让信息检索更高效、更精准
        </p>
        <div class="welcome-actions">
          <router-link to="/qa" class="btn btn-primary">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20M12,6A4,4 0 0,0 8,10H10A2,2 0 0,1 12,8A2,2 0 0,1 14,10C14,12 11,11.75 11,15H13C13,12.75 16,12.5 16,10A4,4 0 0,0 12,6Z"/>
            </svg>
            开始问答
          </router-link>
          <router-link to="/parser" class="btn btn-secondary">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
            </svg>
            上传文件
          </router-link>
        </div>
      </div>
      <div class="welcome-decoration">
        <div class="decoration-circle circle-1"></div>
        <div class="decoration-circle circle-2"></div>
        <div class="decoration-circle circle-3"></div>
      </div>
    </section>

    <!-- 功能模块 -->
    <section class="features-section">
      <h2 class="section-title">
        <span class="title-icon">🌿</span>
        核心功能
      </h2>
      <div class="features-grid">
        <router-link
          v-for="(feature, index) in features"
          :key="index"
          :to="feature.path"
          class="feature-card"
        >
          <div class="feature-icon" :style="{ background: feature.bgGradient }">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path :d="feature.icon"/>
            </svg>
          </div>
          <h3 class="feature-title">{{ feature.title }}</h3>
          <p class="feature-desc">{{ feature.desc }}</p>
          <div class="feature-arrow">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M4,11V13H16L10.5,18.5L11.92,19.92L19.84,12L11.92,4.08L10.5,5.5L16,11H4Z"/>
            </svg>
          </div>
        </router-link>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const features = ref([
  {
    title: '用户管理',
    desc: '管理系统用户，分配权限，查看用户活动记录',
    path: '/users',
    icon: 'M16,13C15.71,13 15.38,13 15.03,13.05C16.19,13.89 17,15 17,16.5V19H23V16.5C23,14.17 18.33,13 16,13M8,13C5.67,13 1,14.17 1,16.5V19H15V16.5C15,14.17 10.33,13 8,13M8,11A3,3 0 0,0 11,8A3,3 0 0,0 8,5A3,3 0 0,0 5,8A3,3 0 0,0 8,11M16,11A3,3 0 0,0 19,8A3,3 0 0,0 16,5A3,3 0 0,0 13,8A3,3 0 0,0 16,11Z',
    bgGradient: 'linear-gradient(135deg, #a8e6cf 0%, #88d8b0 100%)',
  },
  {
    title: '文件上传',
    desc: '上传文档到数据仓库',
    path: '/parser',
    icon: 'M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z',
    bgGradient: 'linear-gradient(135deg, #7fcdcd 0%, #5cb8b2 100%)',
  },
  {
    title: '智能问答',
    desc: '基于 RAG 技术，精准检索，智能生成回答',
    path: '/qa',
    icon: 'M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20M12,6A4,4 0 0,0 8,10H10A2,2 0 0,1 12,8A2,2 0 0,1 14,10C14,12 11,11.75 11,15H13C13,12.75 16,12.5 16,10A4,4 0 0,0 12,6Z',
    bgGradient: 'linear-gradient(135deg, #b4e7ce 0%, #98d8c8 100%)',
  },
  {
    title: '知识库管理',
    desc: '管理知识库，解析文档',
    path: '/knowledge',
    icon: 'M12,3L1,9L12,15L21,10.09V17H23V9M5,13.18V17.18L12,21L19,17.18V13.18L12,17L5,13.18Z',
    bgGradient: 'linear-gradient(135deg, #e8d5c4 0%, #d4c4b0 100%)',
  },
])
</script>

<style scoped>
.home-page {
  padding: 32px;
  max-width: 1400px;
}

/* 欢迎区域 */
.welcome-section {
  position: relative;
  background: linear-gradient(135deg, rgba(168, 230, 207, 0.4) 0%, rgba(136, 216, 176, 0.3) 50%, rgba(232, 213, 196, 0.3) 100%);
  border-radius: var(--radius-xl);
  padding: 48px;
  margin-bottom: 32px;
  overflow: hidden;
  border: 1px solid rgba(168, 230, 207, 0.4);
}

.welcome-content {
  position: relative;
  z-index: 1;
  max-width: 600px;
}

.welcome-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.9);
  padding: 8px 16px;
  border-radius: var(--radius-full);
  font-size: 13px;
  font-weight: 500;
  color: var(--primary-dark);
  margin-bottom: 20px;
  box-shadow: var(--shadow-sm);
}

.welcome-badge svg {
  width: 16px;
  height: 16px;
}

.welcome-title {
  font-size: 36px;
  font-weight: 700;
  color: var(--gray-800);
  margin-bottom: 16px;
  line-height: 1.3;
}

.welcome-title .highlight {
  background: linear-gradient(135deg, var(--primary-dark) 0%, var(--secondary-dark) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.welcome-desc {
  font-size: 16px;
  color: var(--gray-600);
  margin-bottom: 28px;
  line-height: 1.7;
}

.welcome-actions {
  display: flex;
  gap: 16px;
}

.welcome-actions .btn {
  padding: 14px 28px;
  font-size: 15px;
}

.welcome-actions .btn svg {
  width: 20px;
  height: 20px;
}

/* 装饰圆圈 */
.welcome-decoration {
  position: absolute;
  right: 0;
  top: 0;
  width: 400px;
  height: 100%;
  pointer-events: none;
}

.decoration-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.6;
}

.circle-1 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, rgba(168, 230, 207, 0.5) 0%, rgba(136, 216, 176, 0.3) 100%);
  right: -80px;
  top: -80px;
  animation: float 6s ease-in-out infinite;
}

.circle-2 {
  width: 200px;
  height: 200px;
  background: linear-gradient(135deg, rgba(232, 213, 196, 0.5) 0%, rgba(212, 196, 176, 0.3) 100%);
  right: 100px;
  bottom: -40px;
  animation: float 8s ease-in-out infinite reverse;
}

.circle-3 {
  width: 150px;
  height: 150px;
  background: linear-gradient(135deg, rgba(180, 231, 206, 0.4) 0%, rgba(152, 216, 200, 0.2) 100%);
  right: 50px;
  top: 50%;
  animation: float 7s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) scale(1);
  }
  50% {
    transform: translateY(-20px) scale(1.05);
  }
}

/* 统计区域 */
.stats-section {
  margin-bottom: 32px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: var(--radius-lg);
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: var(--shadow);
  border: 1px solid rgba(168, 230, 207, 0.3);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.stat-icon svg {
  width: 28px;
  height: 28px;
}

.stat-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--gray-800);
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: var(--gray-500);
  margin-top: 4px;
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 600;
  padding: 6px 10px;
  border-radius: var(--radius-sm);
}

.stat-trend.up {
  background: rgba(129, 199, 132, 0.15);
  color: var(--success);
}

.stat-trend.down {
  background: rgba(229, 115, 115, 0.15);
  color: var(--error);
}

.stat-trend svg {
  width: 16px;
  height: 16px;
}

/* 功能区域 */
.features-section {
  margin-bottom: 32px;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--gray-800);
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  font-size: 24px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

.feature-card {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: var(--radius-lg);
  padding: 28px;
  text-decoration: none;
  color: inherit;
  box-shadow: var(--shadow);
  border: 1px solid rgba(168, 230, 207, 0.3);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.feature-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-xl);
  border-color: rgba(168, 230, 207, 0.6);
}

.feature-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--primary) 0%, var(--secondary) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.feature-card:hover::before {
  opacity: 1;
}

.feature-icon {
  width: 64px;
  height: 64px;
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-bottom: 20px;
}

.feature-icon svg {
  width: 32px;
  height: 32px;
}

.feature-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--gray-800);
  margin-bottom: 10px;
}

.feature-desc {
  font-size: 14px;
  color: var(--gray-500);
  line-height: 1.6;
  flex: 1;
}

.feature-arrow {
  position: absolute;
  right: 20px;
  bottom: 20px;
  width: 36px;
  height: 36px;
  background: var(--gray-100);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--gray-400);
  transition: all 0.3s ease;
}

.feature-card:hover .feature-arrow {
  background: var(--primary);
  color: white;
  transform: translateX(4px);
}

.feature-arrow svg {
  width: 20px;
  height: 20px;
}

/* 活动区域 */
.activity-section {
  margin-bottom: 32px;
}

.activity-card {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: var(--radius-lg);
  padding: 28px;
  box-shadow: var(--shadow);
  border: 1px solid rgba(168, 230, 207, 0.3);
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: rgba(250, 250, 250, 0.8);
  border-radius: var(--radius);
  transition: all 0.3s ease;
}

.activity-item:hover {
  background: rgba(168, 230, 207, 0.1);
  transform: translateX(4px);
}

.activity-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--gray-600);
  flex-shrink: 0;
}

.activity-icon svg {
  width: 22px;
  height: 22px;
}

.activity-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.activity-text {
  font-size: 14px;
  color: var(--gray-700);
}

.activity-time {
  font-size: 12px;
  color: var(--gray-400);
}

/* 响应式 */
@media (max-width: 1200px) {
  .stats-grid,
  .features-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .home-page {
    padding: 20px;
  }
  
  .welcome-section {
    padding: 28px;
  }
  
  .welcome-title {
    font-size: 24px;
  }
  
  .welcome-actions {
    flex-direction: column;
  }
  
  .stats-grid,
  .features-grid {
    grid-template-columns: 1fr;
  }
  
  .welcome-decoration {
    display: none;
  }
}
</style>
