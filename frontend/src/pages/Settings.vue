<template>
  <div class="settings-page">
    <div class="page-header">
      <h1 class="page-title">
        <span class="title-icon">⚙️</span>
        系统设置
      </h1>
      <p class="page-subtitle">配置系统参数，优化使用体验</p>
    </div>

    <div class="settings-content">
      <!-- 左侧菜单 -->
      <div class="settings-menu">
        <div
          v-for="(menu, index) in menuList"
          :key="index"
          class="menu-item"
          :class="{ active: activeMenu === menu.key }"
          @click="activeMenu = menu.key"
        >
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path :d="menu.icon"/>
          </svg>
          <span>{{ menu.name }}</span>
        </div>
      </div>

      <!-- 右侧内容 -->
      <div class="settings-panel">
        <!-- 通用设置 -->
        <div v-if="activeMenu === 'general'" class="panel-section">
          <h3 class="panel-title">通用设置</h3>
          <div class="setting-group">
            <div class="setting-item">
              <div class="setting-info">
                <label>系统名称</label>
                <p>显示在页面标题和导航栏中的系统名称</p>
              </div>
              <input type="text" class="setting-input" value="RAG 智能问答系统"/>
            </div>

            <div class="setting-item">
              <div class="setting-info">
                <label>语言</label>
                <p>系统界面显示语言</p>
              </div>
              <select class="setting-select">
                <option value="zh">简体中文</option>
                <option value="en">English</option>
              </select>
            </div>
          </div>
        </div>

        <!-- 检索设置 -->
        <div v-if="activeMenu === 'retrieval'" class="panel-section">
          <h3 class="panel-title">检索设置</h3>
          <div class="setting-group">
            <div class="setting-item">
              <div class="setting-info">
                <label>默认检索模式</label>
                <p>设置问答时的默认检索方式</p>
              </div>
              <select class="setting-select">
                <option value="semantic">语义检索</option>
                <option value="keyword">关键词检索</option>
                <option value="hybrid">混合检索</option>
              </select>
            </div>
            <div class="setting-item">
              <div class="setting-info">
                <label>最大返回结果数</label>
                <p>每次检索返回的最大文档片段数量</p>
              </div>
              <input type="number" class="setting-input" value="5" min="1" max="20"/>
            </div>
            <div class="setting-item">
              <div class="setting-info">
                <label>相似度阈值</label>
                <p>低于此阈值的结果将被过滤</p>
              </div>
              <div class="slider-wrapper">
                <input type="range" class="setting-slider" min="0" max="100" value="70"/>
                <span class="slider-value">70%</span>
              </div>
            </div>
            <div class="setting-item">
              <div class="setting-info">
                <label>启用重排序</label>
                <p>使用重排序模型优化检索结果</p>
              </div>
              <label class="toggle">
                <input type="checkbox" checked/>
                <span class="toggle-slider"></span>
              </label>
            </div>
          </div>
        </div>

        <!-- 模型设置 -->
        <div v-if="activeMenu === 'model'" class="panel-section">
          <h3 class="panel-title">模型设置</h3>
          <div class="setting-group">
            <div class="setting-item">
              <div class="setting-info">
                <label>Embedding 模型</label>
                <p>用于文档向量化的模型</p>
              </div>
              <select class="setting-select">
                <option value="bge-large">BGE-Large</option>
                <option value="text2vec">Text2Vec</option>
                <option value="m3e">M3E-Base</option>
              </select>
            </div>
            <div class="setting-item">
              <div class="setting-info">
                <label>LLM 模型</label>
                <p>用于生成回答的大语言模型</p>
              </div>
              <select class="setting-select">
                <option value="gpt-4">GPT-4</option>
                <option value="gpt-3.5">GPT-3.5</option>
                <option value="claude">Claude</option>
                <option value="local">本地模型</option>
              </select>
            </div>
            <div class="setting-item">
              <div class="setting-info">
                <label>Temperature</label>
                <p>控制生成文本的随机性</p>
              </div>
              <div class="slider-wrapper">
                <input type="range" class="setting-slider" min="0" max="100" value="70"/>
                <span class="slider-value">0.7</span>
              </div>
            </div>
            <div class="setting-item">
              <div class="setting-info">
                <label>最大 Token 数</label>
                <p>生成回答的最大长度限制</p>
              </div>
              <input type="number" class="setting-input" value="2048" min="256" max="4096"/>
            </div>
          </div>
        </div>

        <!-- 存储设置 -->
        <div v-if="activeMenu === 'storage'" class="panel-section">
          <h3 class="panel-title">存储设置</h3>
          <div class="setting-group">
            <div class="setting-item">
              <div class="setting-info">
                <label>向量数据库</label>
                <p>存储文档向量的数据库类型</p>
              </div>
              <select class="setting-select">
                <option value="milvus">Milvus</option>
                <option value="weaviate">Weaviate</option>
                <option value="chroma">Chroma</option>
                <option value="qdrant">Qdrant</option>
              </select>
            </div>
            <div class="setting-item">
              <div class="setting-info">
                <label>文档存储路径</label>
                <p>上传文档的本地存储位置</p>
              </div>
              <div class="path-input">
                <input type="text" class="setting-input" value="/data/documents" readonly/>
                <button class="btn btn-ghost">浏览</button>
              </div>
            </div>
            <div class="storage-stats">
              <h4>存储统计</h4>
              <div class="stats-grid">
                <div class="stat-box">
                  <span class="stat-label">文档总数</span>
                  <span class="stat-value">567</span>
                </div>
                <div class="stat-box">
                  <span class="stat-label">存储空间</span>
                  <span class="stat-value">2.3 GB</span>
                </div>
                <div class="stat-box">
                  <span class="stat-label">向量数量</span>
                  <span class="stat-value">125,432</span>
                </div>
              </div>
              <div class="storage-bar">
                <div class="storage-progress" style="width: 45%"></div>
              </div>
              <p class="storage-text">已使用 2.3 GB / 5 GB</p>
            </div>
          </div>
        </div>

        <!-- 安全设置 -->
        <div v-if="activeMenu === 'security'" class="panel-section">
          <h3 class="panel-title">安全设置</h3>
          <div class="setting-group">
            <div class="setting-item">
              <div class="setting-info">
                <label>登录验证</label>
                <p>启用后需要登录才能访问系统</p>
              </div>
              <label class="toggle">
                <input type="checkbox" checked/>
                <span class="toggle-slider"></span>
              </label>
            </div>
            <div class="setting-item">
              <div class="setting-info">
                <label>会话超时时间</label>
                <p>用户无操作后自动登出的时间</p>
              </div>
              <select class="setting-select">
                <option value="15">15 分钟</option>
                <option value="30">30 分钟</option>
                <option value="60">1 小时</option>
                <option value="120">2 小时</option>
              </select>
            </div>
            <div class="setting-item">
              <div class="setting-info">
                <label>API 密钥</label>
                <p>用于外部系统调用的访问密钥</p>
              </div>
              <div class="api-key-input">
                <input type="password" class="setting-input" value="sk-xxxxxxxxxxxxxxxx"/>
                <button class="btn btn-ghost">重置</button>
              </div>
            </div>
          </div>
        </div>

        <div class="panel-footer">
          <button class="btn btn-secondary">重置</button>
          <button class="btn btn-primary">保存设置</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const activeMenu = ref('general')

const menuList = [
  { key: 'general', name: '通用设置', icon: 'M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.21,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.21,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.67 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z' },
  { key: 'retrieval', name: '检索设置', icon: 'M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z' },
  { key: 'model', name: '模型设置', icon: 'M12,16A3,3 0 0,1 9,13C9,11.88 9.61,10.9 10.5,10.39L20.21,4.77L14.68,14.35C14.18,15.33 13.17,16 12,16M12,3C13.81,3 15.5,3.5 16.97,4.32L14.87,5.53C14,5.19 13,5 12,5A8,8 0 0,0 4,13C4,15.21 4.89,17.21 6.34,18.65H6.35C6.74,19.04 6.74,19.67 6.35,20.06C5.96,20.45 5.32,20.45 4.93,20.07V20.07C3.12,18.26 2,15.76 2,13A10,10 0 0,1 12,3M22,13C22,15.76 20.88,18.26 19.07,20.07V20.07C18.68,20.45 18.05,20.45 17.66,20.06C17.27,19.67 17.27,19.04 17.66,18.65V18.65C19.11,17.2 20,15.21 20,13C20,12 19.81,11 19.46,10.1L20.67,8C21.5,9.5 22,11.18 22,13Z' },
  { key: 'storage', name: '存储设置', icon: 'M12,3L1,9L12,15L21,10.09V17H23V9M5,13.18V17.18L12,21L19,17.18V13.18L12,17L5,13.18Z' },
  { key: 'security', name: '安全设置', icon: 'M12,1L3,5V11C3,16.55 6.84,21.74 12,23C17.16,21.74 21,16.55 21,11V5L12,1M12,7A3,3 0 0,1 15,10A3,3 0 0,1 12,13A3,3 0 0,1 9,10A3,3 0 0,1 12,7M17.13,17.13C15.5,18.87 13.27,20 12,20C10.73,20 8.5,18.87 6.87,17.13C7.5,15.17 9.5,13.75 12,13.75C14.5,13.75 16.5,15.17 17.13,17.13Z' },
]
</script>

<style scoped>
.settings-page {
  padding: 32px;
  max-width: 1200px;
}

.page-header {
  margin-bottom: 28px;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--gray-800);
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.title-icon {
  font-size: 32px;
}

.page-subtitle {
  font-size: 14px;
  color: var(--gray-500);
}

/* 设置内容 */
.settings-content {
  display: flex;
  gap: 24px;
}

/* 左侧菜单 */
.settings-menu {
  width: 240px;
  flex-shrink: 0;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  margin-bottom: 4px;
  border-radius: var(--radius);
  cursor: pointer;
  color: var(--gray-600);
  transition: all 0.2s ease;
}

.menu-item:hover {
  background: rgba(168, 230, 207, 0.1);
  color: var(--primary-dark);
}

.menu-item.active {
  background: linear-gradient(135deg, rgba(168, 230, 207, 0.3) 0%, rgba(136, 216, 176, 0.3) 100%);
  color: var(--primary-dark);
  font-weight: 500;
}

.menu-item svg {
  width: 22px;
  height: 22px;
}

/* 右侧面板 */
.settings-panel {
  flex: 1;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: var(--radius-lg);
  padding: 32px;
  box-shadow: var(--shadow);
  border: 1px solid rgba(168, 230, 207, 0.3);
}

.panel-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--gray-800);
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--gray-100);
}

.setting-group {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
}

.setting-info {
  flex: 1;
}

.setting-info label {
  display: block;
  font-size: 15px;
  font-weight: 500;
  color: var(--gray-800);
  margin-bottom: 4px;
}

.setting-info p {
  font-size: 13px;
  color: var(--gray-500);
}

.setting-input,
.setting-select {
  width: 280px;
  padding: 10px 14px;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius);
  font-size: 14px;
  background: white;
  outline: none;
  transition: all 0.2s ease;
}

.setting-input:focus,
.setting-select:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(168, 230, 207, 0.2);
}

/* Logo 上传 */
.logo-upload {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo-preview {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, var(--primary-light) 0%, rgba(136, 216, 176, 0.3) 100%);
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary-dark);
}

.logo-preview svg {
  width: 32px;
  height: 32px;
}

/* 路径输入 */
.path-input,
.api-key-input {
  display: flex;
  gap: 8px;
  width: 280px;
}

.path-input .setting-input,
.api-key-input .setting-input {
  flex: 1;
  width: auto;
}

/* 滑块 */
.slider-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 280px;
}

.setting-slider {
  flex: 1;
}

.slider-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--primary-dark);
  min-width: 40px;
}

/* 开关 */
.toggle {
  position: relative;
  width: 48px;
  height: 26px;
}

.toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--gray-300);
  border-radius: var(--radius-full);
  transition: 0.3s;
}

.toggle-slider::before {
  content: '';
  position: absolute;
  height: 20px;
  width: 20px;
  left: 3px;
  bottom: 3px;
  background: white;
  border-radius: 50%;
  transition: 0.3s;
}

.toggle input:checked + .toggle-slider {
  background: var(--primary);
}

.toggle input:checked + .toggle-slider::before {
  transform: translateX(22px);
}

/* 存储统计 */
.storage-stats {
  background: rgba(250, 250, 250, 0.8);
  border-radius: var(--radius);
  padding: 20px;
  margin-top: 8px;
}

.storage-stats h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-800);
  margin-bottom: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  background: white;
  border-radius: var(--radius);
}

.stat-box .stat-label {
  font-size: 12px;
  color: var(--gray-500);
  margin-bottom: 4px;
}

.stat-box .stat-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--gray-800);
}

.storage-bar {
  height: 8px;
  background: var(--gray-200);
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-bottom: 8px;
}

.storage-progress {
  height: 100%;
  background: linear-gradient(90deg, var(--primary) 0%, var(--secondary) 100%);
  border-radius: var(--radius-full);
  transition: width 0.3s ease;
}

.storage-text {
  font-size: 13px;
  color: var(--gray-500);
  text-align: center;
}

/* 面板底部 */
.panel-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--gray-100);
}

@media (max-width: 968px) {
  .settings-content {
    flex-direction: column;
  }
  
  .settings-menu {
    width: 100%;
    display: flex;
    gap: 8px;
    overflow-x: auto;
  }
  
  .menu-item {
    white-space: nowrap;
    margin-bottom: 0;
  }
  
  .setting-item {
    flex-direction: column;
    gap: 12px;
  }
  
  .setting-input,
  .setting-select,
  .slider-wrapper,
  .path-input,
  .api-key-input {
    width: 100%;
  }
}

@media (max-width: 768px) {
  .settings-page {
    padding: 20px;
  }
  
  .settings-panel {
    padding: 20px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
