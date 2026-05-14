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
          <button class="btn btn-tutorial" @click="showTutorialModal = true">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M11,18H13V16H11V18M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,6A4,4 0 0,0 8,10H10A2,2 0 0,1 12,8A2,2 0 0,1 14,10C14,11 13,11.5 12.5,12C11.5,13 11,14 11,15H13C13,13.5 14.5,13 15.5,12C16.5,11 16,9.5 16,10A4,4 0 0,0 12,6Z"/>
            </svg>
            使用教程
          </button>
        </div>
      </div>
      <div class="welcome-decoration">
        <div class="decoration-circle circle-1"></div>
        <div class="decoration-circle circle-2"></div>
        <div class="decoration-circle circle-3"></div>
      </div>
    </section>

    <!-- 使用教程弹窗 -->
    <div v-if="showTutorialModal" class="tutorial-overlay" @click.self="showTutorialModal = false">
      <div class="tutorial-modal">
        <div class="tutorial-header">
          <h3>📖 使用教程</h3>
          <button class="tutorial-close" @click="showTutorialModal = false">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
            </svg>
          </button>
        </div>
        <div class="tutorial-content">
          <p class="tutorial-intro">欢迎使用 RAG 智能问答系统，请按照以下步骤完成配置：</p>
          
          <div class="tutorial-step">
            <div class="step-number">1</div>
            <div class="step-detail">
              <h4>创建用户与部门管理</h4>
              <p>进入<strong>用户管理</strong>页面，创建系统用户并为其分配所属部门。当知识库关联了某个部门后，该部门下的所有用户均可访问并使用该知识库进行问答。</p>
            </div>
          </div>

          <div class="tutorial-step">
            <div class="step-number">2</div>
            <div class="step-detail">
              <h4>上传与管理文件</h4>
              <p>进入<strong>文档管理</strong>页面，上传需要纳入知识库的文件资料。系统支持统一管理所有已上传的文档，方便后续关联至不同知识库。</p>
            </div>
          </div>

          <div class="tutorial-step">
            <div class="step-number">3</div>
            <div class="step-detail">
              <h4>创建知识库并关联资源</h4>
              <p>进入<strong>知识库管理</strong>页面，创建知识库并设置其归属（个人或部门）。将已上传的文件关联至知识库后，执行文档解析操作，系统将自动对文档内容进行切片和向量化处理。</p>
            </div>
          </div>

          <div class="tutorial-step">
            <div class="step-number">4</div>
            <div class="step-detail">
              <h4>开始智能问答</h4>
              <p>文档解析完成后，用户或管理员即可选择对应的知识库发起问答。系统将基于知识库内容进行检索，为您提供精准的回答。</p>
            </div>
          </div>
        </div>
        <div class="tutorial-footer">
          <button class="btn btn-primary" @click="showTutorialModal = false">我知道了</button>
        </div>
      </div>
    </div>

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

const showTutorialModal = ref(false)

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
    title: '知识库管理',
    desc: '管理知识库，解析文档',
    path: '/knowledge',
    icon: 'M12,3L1,9L12,15L21,10.09V17H23V9M5,13.18V17.18L12,21L19,17.18V13.18L12,17L5,13.18Z',
    bgGradient: 'linear-gradient(135deg, #e8d5c4 0%, #d4c4b0 100%)',
  },
  {
    title: '智能问答',
    desc: '基于 RAG 技术，精准检索，智能生成回答',
    path: '/qa',
    icon: 'M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20M12,6A4,4 0 0,0 8,10H10A2,2 0 0,1 12,8A2,2 0 0,1 14,10C14,12 11,11.75 11,15H13C13,12.75 16,12.5 16,10A4,4 0 0,0 12,6Z',
    bgGradient: 'linear-gradient(135deg, #b4e7ce 0%, #98d8c8 100%)',
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

/* 使用教程按钮 */
.btn-tutorial {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: linear-gradient(135deg, #a8e6cf 0%, #88d8b0 100%);
  color: white;
  border: none;
  border-radius: var(--radius);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 14px rgba(168, 230, 207, 0.4);
}

.btn-tutorial:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(168, 230, 207, 0.5);
}

/* 教程弹窗 */
.tutorial-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  backdrop-filter: blur(4px);
}

.tutorial-modal {
  background: white;
  border-radius: 20px;
  width: 100%;
  max-width: 580px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  animation: modalIn 0.3s ease;
}

@keyframes modalIn {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.tutorial-header {
  padding: 24px 28px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.tutorial-header h3 {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.tutorial-close {
  width: 32px;
  height: 32px;
  border: none;
  background: #f5f5f5;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  transition: all 0.3s;
}

.tutorial-close:hover {
  background: #e8f5e9;
  color: #2e7d32;
}

.tutorial-close svg {
  width: 18px;
  height: 18px;
}

.tutorial-content {
  padding: 28px;
  overflow-y: auto;
}

.tutorial-intro {
  font-size: 15px;
  color: #555;
  margin-bottom: 24px;
  line-height: 1.6;
}

.tutorial-step {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  padding: 18px;
  background: linear-gradient(135deg, #f8fdf9 0%, #f0faf3 100%);
  border-radius: 14px;
  border: 1px solid #e8f5e9;
  transition: all 0.3s;
}

.tutorial-step:hover {
  border-color: #a8e6cf;
  box-shadow: 0 4px 12px rgba(168, 230, 207, 0.2);
}

.tutorial-step:last-child {
  margin-bottom: 0;
}

.step-number {
  width: 36px;
  height: 36px;
  min-width: 36px;
  background: linear-gradient(135deg, #a8e6cf 0%, #88d8b0 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 15px;
  box-shadow: 0 3px 8px rgba(168, 230, 207, 0.4);
}

.step-detail h4 {
  font-size: 15px;
  font-weight: 600;
  color: #2e7d32;
  margin-bottom: 8px;
}

.step-detail p {
  font-size: 14px;
  color: #555;
  line-height: 1.7;
  margin: 0;
}

.step-detail strong {
  color: #1b5e20;
}

.tutorial-footer {
  padding: 16px 28px 24px;
  display: flex;
  justify-content: flex-end;
}

.tutorial-footer .btn-primary {
  padding: 12px 32px;
  background: linear-gradient(135deg, #a8e6cf 0%, #88d8b0 100%);
  border: none;
  border-radius: 12px;
  color: white;
  font-weight: 600;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.3s;
}

.tutorial-footer .btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(168, 230, 207, 0.5);
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
