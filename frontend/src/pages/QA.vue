<template>
  <div class="qa-page">
    <div class="qa-container">
      <!-- 左侧：问答区域 -->
      <div class="chat-section">
        <div class="chat-header">
          <h1 class="page-title">
            <span class="title-icon">💬</span>
            智能问答
          </h1>
          <div class="header-actions">
            <!-- 知识库选择器 -->
            <div class="kb-selector-header">
              <div class="kb-dropdown" :class="{ open: showKbDropdown }" @click="showKbDropdown = !showKbDropdown">
                <div class="kb-selected">
                  <svg class="kb-icon" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12,3L1,9L12,15L21,10.09V17H23V9M5,13.18V17.18L12,21L19,17.18V13.18L12,17L5,13.18Z"/>
                  </svg>
                  <span v-if="selectedKBs.length === 0" class="placeholder">选择知识库</span>
                  <span v-else-if="selectedKBs.length === 1" class="kb-name">{{ getKBName(selectedKBs[0]) }}</span>
                  <span v-else class="kb-name">{{ selectedKBs.length }} 个知识库</span>
                  <svg class="dropdown-arrow" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M7,10L12,15L17,10H7Z"/>
                  </svg>
                </div>
                <div v-if="showKbDropdown" class="kb-options">
                  <div class="kb-option" @click.stop="selectAllKBs">
                    <input type="checkbox" :checked="isAllSelected" @click.stop/>
                    <span>全选</span>
                  </div>
                  <div class="kb-divider"></div>
                  <div
                    v-for="kb in knowledgeBases"
                    :key="kb.id"
                    class="kb-option"
                    :class="{ selected: selectedKBs.includes(kb.id) }"
                    @click.stop="toggleKB(kb.id)"
                  >
                    <input type="checkbox" :checked="selectedKBs.includes(kb.id)" @click.stop/>
                    <div class="kb-option-info">
                      <span class="kb-option-name">{{ kb.name }}</span>
                      <span class="kb-option-count">{{ kb.docCount }} 文档</span>
                    </div>
                    <div v-if="kb.status === 'active'" class="kb-status active" title="正常"></div>
                    <div v-else class="kb-status building" title="构建中"></div>
                  </div>
                </div>
              </div>
            </div>
            <button class="btn btn-ghost" @click="clearChat">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
              </svg>
              清空对话
            </button>
          </div>
        </div>

        <!-- 消息列表 -->
        <div class="messages-container" ref="messagesContainer">
          <div v-if="messages.length === 0" class="welcome-message">
            <div class="welcome-icon">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20M12,6A4,4 0 0,0 8,10H10A2,2 0 0,1 12,8A2,2 0 0,1 14,10C14,12 11,11.75 11,15H13C13,12.75 16,12.5 16,10A4,4 0 0,0 12,6Z"/>
              </svg>
            </div>
            <h2>有什么可以帮助您的？</h2>
            <p>基于 RAG 技术，我可以从知识库中为您检索精准答案</p>
            <div class="quick-questions">
              <button
                v-for="(q, index) in quickQuestions"
                :key="index"
                class="quick-btn"
                @click="askQuickQuestion(q)"
              >
                {{ q }}
              </button>
            </div>
          </div>

          <div
            v-for="(msg, index) in messages"
            :key="index"
            class="message"
            :class="msg.type"
          >
            <div class="message-avatar">
              <div v-if="msg.type === 'user'" class="avatar user">我</div>
              <div v-else class="avatar bot">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20M12,6A4,4 0 0,0 8,10H10A2,2 0 0,1 12,8A2,2 0 0,1 14,10C14,12 11,11.75 11,15H13C13,12.75 16,12.5 16,10A4,4 0 0,0 12,6Z"/>
                </svg>
              </div>
            </div>
            <div class="message-content">
              <div class="message-text" v-html="formatMessage(msg.content)"></div>
              <div v-if="msg.sources && msg.sources.length > 0" class="message-sources">
                <div class="sources-title">
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12,3L1,9L12,15L21,10.09V17H23V9M5,13.18V17.18L12,21L19,17.18V13.18L12,17L5,13.18Z"/>
                  </svg>
                  参考来源
                </div>
                <div class="sources-list">
                  <div
                    v-for="(source, sIndex) in msg.sources"
                    :key="sIndex"
                    class="source-item"
                  >
                    <span class="source-name">{{ source.name }}</span>
                    <span class="source-score">{{ source.score }}%</span>
                  </div>
                </div>
              </div>
              <span class="message-time">{{ msg.time }}</span>
            </div>
          </div>

          <!-- 加载中 -->
          <div v-if="isLoading" class="message bot loading">
            <div class="message-avatar">
              <div class="avatar bot">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20M12,6A4,4 0 0,0 8,10H10A2,2 0 0,1 12,8A2,2 0 0,1 14,10C14,12 11,11.75 11,15H13C13,12.75 16,12.5 16,10A4,4 0 0,0 12,6Z"/>
                </svg>
              </div>
            </div>
            <div class="message-content">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="input-section">
          <div class="input-container">
            <textarea
              v-model="inputMessage"
              class="chat-input"
              placeholder="输入您的问题..."
              rows="1"
              @keydown.enter.prevent="sendMessage"
              @input="autoResize"
              ref="inputRef"
            ></textarea>
            <button
              class="send-btn"
              :class="{ active: inputMessage.trim() }"
              @click="sendMessage"
              :disabled="!inputMessage.trim() || isLoading"
            >
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M2,21L23,12L2,3V10L17,12L2,14V21Z"/>
              </svg>
            </button>
          </div>

        <div class="input-tips">
          <span>按 Enter 发送，Shift + Enter 换行</span>
        </div>
        </div>
      </div>

      <!-- 右侧：知识库信息 -->
      <div class="sidebar-section">
        <div class="info-card">
          <h3 class="card-title">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12,3L1,9L12,15L21,10.09V17H23V9M5,13.18V17.18L12,21L19,17.18V13.18L12,17L5,13.18Z"/>
            </svg>
            知识库状态
          </h3>
          <div class="info-item">
            <span class="info-label">文档总数</span>
            <span class="info-value">567</span>
          </div>
          <div class="info-item">
            <span class="info-label">索引状态</span>
            <span class="info-value success">正常</span>
          </div>
          <div class="info-item">
            <span class="info-label">最后更新</span>
            <span class="info-value">2小时前</span>
          </div>
        </div>

        <div class="info-card">
          <h3 class="card-title">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.21,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.21,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.67 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z"/>
            </svg>
            检索设置
          </h3>
          <div class="setting-item">
            <label>检索模式</label>
            <select class="setting-select">
              <option>语义检索</option>
              <option>关键词检索</option>
              <option>混合检索</option>
            </select>
          </div>
          <div class="setting-item">
            <label>返回结果数</label>
            <input type="number" class="setting-input" value="5" min="1" max="20"/>
          </div>
          <div class="setting-item">
            <label>相似度阈值</label>
            <input type="range" class="setting-slider" min="0" max="100" value="70"/>
            <span class="slider-value">70%</span>
          </div>
        </div>

        <div class="info-card">
          <h3 class="card-title">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M13.5,5.5C14.59,5.5 15.5,4.58 15.5,3.5C15.5,2.38 14.59,1.5 13.5,1.5C12.39,1.5 11.5,2.38 11.5,3.5C11.5,4.58 12.39,5.5 13.5,5.5M9.89,19.38L10.89,15L13,17V23H15V15.5L12.89,13.5L13.5,10.5C14.79,12 16.79,13 19,13V11C17.09,11 15.5,10 14.69,8.58L13.69,7C13.29,6.38 12.69,6 12,6C11.69,6 11.5,6.08 11.19,6.08L6,8.28V13H8V9.58L9.79,8.88L8.19,17L3.29,16L2.89,18L9.89,19.38Z"/>
            </svg>
            使用提示
          </h3>
          <ul class="tips-list">
            <li>提问越具体，答案越精准</li>
            <li>可以询问文档中的具体内容</li>
            <li>支持多轮对话，保持上下文</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, computed, onMounted, onUnmounted } from 'vue'

const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const messagesContainer = ref(null)
const inputRef = ref(null)
const showKbDropdown = ref(false)
const selectedKBs = ref([])

// 知识库列表
const knowledgeBases = ref([
  { id: 1, name: '产品文档库', docCount: 128, status: 'active' },
  { id: 2, name: '技术规范库', docCount: 86, status: 'active' },
  { id: 3, name: '培训资料库', docCount: 45, status: 'building' },
  { id: 4, name: '项目文档库', docCount: 234, status: 'active' },
])

// 计算是否全选
const isAllSelected = computed(() => {
  return selectedKBs.value.length === knowledgeBases.value.length
})

// 获取知识库名称
const getKBName = (id) => {
  const kb = knowledgeBases.value.find(k => k.id === id)
  return kb ? kb.name : ''
}

// 切换知识库选择
const toggleKB = (id) => {
  const index = selectedKBs.value.indexOf(id)
  if (index > -1) {
    selectedKBs.value.splice(index, 1)
  } else {
    selectedKBs.value.push(id)
  }
}

// 全选/取消全选
const selectAllKBs = () => {
  if (isAllSelected.value) {
    selectedKBs.value = []
  } else {
    selectedKBs.value = knowledgeBases.value.map(kb => kb.id)
  }
}

// 点击外部关闭下拉框
const handleClickOutside = (e) => {
  if (!e.target.closest('.kb-dropdown')) {
    showKbDropdown.value = false
  }
}

// 添加事件监听
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

const quickQuestions = [
  '系统的主要功能有哪些？',
  '如何上传文档？',
  '支持哪些文件格式？',
  '如何提高检索准确率？',
]

const formatMessage = (content) => {
  // 简单的 Markdown 格式转换
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
}

const autoResize = () => {
  const textarea = inputRef.value
  textarea.style.height = 'auto'
  textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px'
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const sendMessage = () => {
  const message = inputMessage.value.trim()
  if (!message || isLoading.value) return

  // 添加用户消息
  messages.value.push({
    type: 'user',
    content: message,
    time: new Date().toLocaleTimeString()
  })

  inputMessage.value = ''
  inputRef.value.style.height = 'auto'
  scrollToBottom()

  // 模拟 AI 回复
  isLoading.value = true
  scrollToBottom()

  setTimeout(() => {
    messages.value.push({
      type: 'bot',
      content: `根据知识库检索，我为您找到以下答案：\n\n**关于您的问题**：\n${message}\n\n**检索结果**：\n根据相关文档，这是一个基于 RAG（检索增强生成）技术的智能问答系统。系统通过以下步骤为您提供答案：\n\n1. **文档解析**：自动解析上传的各类文档\n2. **向量化存储**：将文档内容转换为向量并存储\n3. **语义检索**：根据您的问题检索相关内容\n4. **智能生成**：结合检索内容生成精准回答`,
      time: new Date().toLocaleTimeString(),
      sources: [
        { name: '产品手册.pdf', score: 95 },
        { name: '技术文档.docx', score: 88 },
      ]
    })
    isLoading.value = false
    scrollToBottom()
  }, 2000)
}

const askQuickQuestion = (question) => {
  inputMessage.value = question
  sendMessage()
}

const clearChat = () => {
  messages.value = []
}
</script>

<style scoped>
.qa-page {
  height: 100vh;
  overflow: hidden;
}

.qa-container {
  display: flex;
  height: 100%;
}

/* 聊天区域 */
.chat-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 32px;
  border-bottom: 1px solid rgba(168, 230, 207, 0.3);
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--gray-800);
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  font-size: 26px;
}

.header-actions .btn svg {
  width: 18px;
  height: 18px;
}

/* 消息容器 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 32px;
}

.welcome-message {
  text-align: center;
  padding: 60px 20px;
}

.welcome-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, rgba(168, 230, 207, 0.3) 0%, rgba(136, 216, 176, 0.3) 100%);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 24px;
  color: var(--primary-dark);
}

.welcome-icon svg {
  width: 40px;
  height: 40px;
}

.welcome-message h2 {
  font-size: 24px;
  font-weight: 600;
  color: var(--gray-800);
  margin-bottom: 8px;
}

.welcome-message p {
  font-size: 14px;
  color: var(--gray-500);
  margin-bottom: 32px;
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
  max-width: 600px;
  margin: 0 auto;
}

.quick-btn {
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(168, 230, 207, 0.4);
  border-radius: var(--radius-full);
  font-size: 14px;
  color: var(--gray-600);
  cursor: pointer;
  transition: all 0.3s ease;
}

.quick-btn:hover {
  background: var(--primary-light);
  border-color: var(--primary);
  color: var(--primary-dark);
  transform: translateY(-2px);
}

/* 消息样式 */
.message {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  animation: fadeIn 0.3s ease;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.avatar.user {
  background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
  color: white;
}

.avatar.bot {
  background: linear-gradient(135deg, var(--earth) 0%, var(--earth-dark) 100%);
  color: white;
}

.avatar.bot svg {
  width: 24px;
  height: 24px;
}

.message-content {
  max-width: 70%;
  padding: 16px 20px;
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.95);
  box-shadow: var(--shadow-sm);
}

.message.user .message-content {
  background: linear-gradient(135deg, var(--primary-light) 0%, rgba(136, 216, 176, 0.3) 100%);
}

.message-text {
  font-size: 15px;
  line-height: 1.7;
  color: var(--gray-800);
}

.message-time {
  display: block;
  font-size: 11px;
  color: var(--gray-400);
  margin-top: 8px;
}

/* 来源引用 */
.message-sources {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(168, 230, 207, 0.3);
}

.sources-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--primary-dark);
  margin-bottom: 8px;
}

.sources-title svg {
  width: 14px;
  height: 14px;
}

.sources-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.source-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(168, 230, 207, 0.2);
  border-radius: var(--radius-sm);
  font-size: 12px;
}

.source-name {
  color: var(--gray-700);
}

.source-score {
  color: var(--primary-dark);
  font-weight: 600;
}

/* 加载动画 */
.typing-indicator {
  display: flex;
  gap: 6px;
  padding: 8px 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: var(--primary);
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

/* 输入区域 */
.input-section {
  padding: 20px 32px 32px;
  border-top: 1px solid rgba(168, 230, 207, 0.3);
}

.input-container {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  background: rgba(255, 255, 255, 0.95);
  border: 2px solid rgba(168, 230, 207, 0.4);
  border-radius: var(--radius-xl);
  padding: 12px 16px;
  transition: all 0.3s ease;
}

.input-container:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 4px rgba(168, 230, 207, 0.2);
}

.chat-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 15px;
  color: var(--gray-800);
  resize: none;
  outline: none;
  line-height: 1.5;
  max-height: 120px;
}

.chat-input::placeholder {
  color: var(--gray-400);
}

.send-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: var(--gray-200);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--gray-400);
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.send-btn.active {
  background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
  color: white;
  box-shadow: var(--shadow);
}

.send-btn.active:hover {
  transform: scale(1.05);
  box-shadow: var(--shadow-lg);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-btn svg {
  width: 20px;
  height: 20px;
}

.input-tips {
  text-align: center;
  margin-top: 8px;
  font-size: 12px;
  color: var(--gray-400);
}

/* 头部知识库选择器 */
.kb-selector-header {
  position: relative;
}

.kb-selector-header .kb-dropdown {
  position: relative;
  flex: 1;
  max-width: 320px;
}

.kb-selector-header .kb-selected {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(168, 230, 207, 0.4);
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 160px;
}

.kb-selector-header .kb-selected:hover {
  border-color: var(--primary);
  background: white;
  box-shadow: var(--shadow-sm);
}

.kb-selector-header .kb-dropdown.open .kb-selected {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(168, 230, 207, 0.2);
}

.kb-selector-header .kb-icon {
  width: 18px;
  height: 18px;
  color: var(--primary-dark);
}

.kb-selector-header .kb-selected .placeholder {
  color: var(--gray-500);
  font-size: 13px;
}

.kb-selector-header .kb-selected .kb-name {
  font-size: 13px;
  color: var(--gray-800);
  font-weight: 500;
  flex: 1;
}

.kb-selector-header .dropdown-arrow {
  width: 16px;
  height: 16px;
  color: var(--gray-400);
  transition: transform 0.2s ease;
}

.kb-selector-header .kb-dropdown.open .dropdown-arrow {
  transform: rotate(180deg);
}

.kb-selector-header .kb-options {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 280px;
  background: white;
  border: 1px solid rgba(168, 230, 207, 0.4);
  border-radius: var(--radius);
  box-shadow: var(--shadow-lg);
  z-index: 1000;
  max-height: 320px;
  overflow-y: auto;
  animation: dropdownSlideIn 0.2s ease;
}

@keyframes dropdownSlideIn {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.kb-selector-header .kb-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.kb-selector-header .kb-option:hover {
  background: rgba(168, 230, 207, 0.15);
}

.kb-selector-header .kb-option.selected {
  background: rgba(168, 230, 207, 0.25);
}

.kb-selector-header .kb-option input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: var(--primary);
  cursor: pointer;
}

.kb-selector-header .kb-option span {
  font-size: 14px;
  color: var(--gray-700);
}

.kb-selector-header .kb-option-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.kb-selector-header .kb-option-name {
  font-size: 14px;
  color: var(--gray-800);
  font-weight: 500;
}

.kb-selector-header .kb-option-count {
  font-size: 12px;
  color: var(--gray-500);
}

.kb-selector-header .kb-status {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.kb-selector-header .kb-status.active {
  background: var(--success);
}

.kb-selector-header .kb-status.building {
  background: var(--warning);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.kb-selector-header .kb-divider {
  height: 1px;
  background: var(--gray-200);
  margin: 4px 0;
}

/* 侧边栏 */
.sidebar-section {
  width: 320px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  border-left: 1px solid rgba(168, 230, 207, 0.3);
  padding: 24px;
  overflow-y: auto;
}

.info-card {
  background: rgba(255, 255, 255, 0.9);
  border-radius: var(--radius-lg);
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: var(--shadow-sm);
  border: 1px solid rgba(168, 230, 207, 0.3);
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--gray-800);
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.card-title svg {
  width: 20px;
  height: 20px;
  color: var(--primary-dark);
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--gray-100);
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 13px;
  color: var(--gray-500);
}

.info-value {
  font-size: 13px;
  font-weight: 600;
  color: var(--gray-800);
}

.info-value.success {
  color: var(--success);
}

/* 设置项 */
.setting-item {
  margin-bottom: 16px;
}

.setting-item label {
  display: block;
  font-size: 13px;
  color: var(--gray-600);
  margin-bottom: 8px;
}

.setting-select,
.setting-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius);
  font-size: 13px;
  background: white;
  outline: none;
}

.setting-select:focus,
.setting-input:focus {
  border-color: var(--primary);
}

.setting-slider {
  width: 100%;
  margin-bottom: 4px;
}

.slider-value {
  font-size: 12px;
  color: var(--primary-dark);
  font-weight: 600;
}

/* 提示列表 */
.tips-list {
  list-style: none;
  padding: 0;
}

.tips-list li {
  font-size: 13px;
  color: var(--gray-600);
  padding: 8px 0;
  padding-left: 20px;
  position: relative;
}

.tips-list li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: var(--primary);
  font-weight: bold;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式 */
@media (max-width: 1024px) {
  .sidebar-section {
    display: none;
  }
}

@media (max-width: 768px) {
  .chat-header {
    padding: 16px 20px;
  }
  
  .messages-container {
    padding: 20px;
  }
  
  .message-content {
    max-width: 85%;
  }
  
  .input-section {
    padding: 16px 20px 24px;
  }
}
</style>
