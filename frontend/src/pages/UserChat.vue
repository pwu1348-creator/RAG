<template>
  <div class="user-chat-page">
    <!-- 左侧边栏 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <!-- 品牌 -->
      <div class="sidebar-brand">
        <div class="brand-icon"><img src="/images/生成马年专属 logo.png" alt="PengMind" class="brand-logo-img" /></div>
        <span v-if="!sidebarCollapsed" class="brand-name">PengMind</span>
        <button class="collapse-btn" @click="sidebarCollapsed = !sidebarCollapsed">
          <svg viewBox="0 0 24 24" fill="currentColor" :style="sidebarCollapsed ? 'transform:rotate(180deg)' : ''"><path d="M15.41,7.41L14,6L8,12L14,18L15.41,16.59L10.83,12L15.41,7.41Z"/></svg>
        </button>
      </div>

      <!-- 新建对话 -->
      <button class="new-chat-btn" @click="newChat">
        <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"/></svg>
        <span v-if="!sidebarCollapsed">新建对话</span>
      </button>

      <!-- 导航 -->
      <nav class="sidebar-nav" v-if="!sidebarCollapsed">
        <div class="nav-section-title">对话历史</div>
        <div
          v-for="s in sessions"
          :key="s.id"
          class="session-item"
          :class="{ active: currentSessionId === s.id }"
          @click="switchSession(s.id)"
        >
          <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M20,2H4C2.9,2 2,2.9 2,4V22L6,18H20C21.1,18 22,17.1 22,16V4C22,2.9 21.1,2 20,2Z"/></svg>
          <span class="session-name">{{ s.name }}</span>
          <button class="del-btn" @click.stop="deleteSession(s.id)">
            <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14"><path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/></svg>
          </button>
        </div>
        <div v-if="sessions.length === 0" class="no-sessions">暂无对话记录</div>
      </nav>

      <!-- 底部：助手设置 + 个人信息 -->
      <div class="sidebar-footer" v-if="!sidebarCollapsed">
        <button class="footer-btn" @click="showAssistantPanel = true">
          <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.21,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.21,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.67 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z"/></svg>
          助手设置
        </button>
        <button class="footer-btn" @click="showProfilePanel = true">
          <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M12,4A4,4 0 0,1 16,8A4,4 0 0,1 12,12A4,4 0 0,1 8,8A4,4 0 0,1 12,4M12,14C16.42,14 20,15.79 20,18V20H4V18C4,15.79 7.58,14 12,14Z"/></svg>
          个人信息
        </button>
        <button class="footer-btn logout" @click="handleLogout">
          <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M16,17V14H9V10H16V7L21,12L16,17M14,2A2,2 0 0,1 16,4V6H14V4H5V20H14V18H16V20A2,2 0 0,1 14,22H5A2,2 0 0,1 3,20V4A2,2 0 0,1 5,2H14Z"/></svg>
          退出登录
        </button>
      </div>
      <!-- 折叠时图标 -->
      <div class="sidebar-footer-icons" v-else>
        <button class="icon-btn" @click="showAssistantPanel = true" title="助手设置">
          <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20"><path d="M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.21,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.21,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.67 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z"/></svg>
        </button>
        <button class="icon-btn logout" @click="handleLogout" title="退出">
          <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20"><path d="M16,17V14H9V10H16V7L21,12L16,17M14,2A2,2 0 0,1 16,4V6H14V4H5V20H14V18H16V20A2,2 0 0,1 14,22H5A2,2 0 0,1 3,20V4A2,2 0 0,1 5,2H14Z"/></svg>
        </button>
      </div>
    </aside>

    <!-- 主聊天区 -->
    <main class="chat-main">
      <!-- 顶栏 -->
      <div class="chat-topbar">
        <div class="topbar-left">
          <div class="assistant-avatar">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20M12,6A4,4 0 0,0 8,10H10A2,2 0 0,1 12,8A2,2 0 0,1 14,10C14,12 11,11.75 11,15H13C13,12.75 16,12.5 16,10A4,4 0 0,0 12,6Z"/></svg>
          </div>
          <div>
            <div class="assistant-name">{{ assistantConfig.name || '智能助手' }}</div>
            <div class="assistant-kb">{{ assistantConfig.kbName || '未选择知识库' }}</div>
          </div>
        </div>
        <div class="topbar-right">
          <span class="user-badge">{{ userInfo.username || '用户' }}</span>
        </div>
      </div>

      <!-- 消息区 -->
      <div class="messages-area" ref="scrollRef">
        <!-- 欢迎 -->
        <div v-if="currentMessages.length === 0" class="welcome-screen">
          <div class="welcome-avatar">
            <svg viewBox="0 0 24 24" fill="currentColor" width="48" height="48"><path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20M12,6A4,4 0 0,0 8,10H10A2,2 0 0,1 12,8A2,2 0 0,1 14,10C14,12 11,11.75 11,15H13C13,12.75 16,12.5 16,10A4,4 0 0,0 12,6Z"/></svg>
          </div>
          <h2>你好，{{ userInfo.username || '同学' }} 👋</h2>
          <p>我是 <strong>{{ assistantConfig.name || '智能助手' }}</strong>，有什么可以帮你的？</p>
          <div v-if="!assistantConfig.kbId" class="no-kb-tip">
            <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M13,9H11V7H13M13,17H11V11H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z"/></svg>
            请先在左侧「助手设置」中选择知识库
          </div>
          <div class="quick-list">
            <button v-for="(q,i) in quickQuestions" :key="i" class="quick-chip" @click="sendQuick(q)">{{ q }}</button>
          </div>
        </div>

        <!-- 消息列表 -->
        <div v-for="(msg, i) in currentMessages" :key="i" class="msg-row" :class="msg.role">
          <div class="msg-avatar-wrap">
            <div v-if="msg.role === 'user'" class="msg-avatar user-av">{{ (userInfo.username || 'U')[0].toUpperCase() }}</div>
            <div v-else class="msg-avatar bot-av">AI助手</div>
          </div>
          <div class="msg-content">
            <!-- 思考链区域（仅 assistant 消息） -->
            <div v-if="msg.role === 'assistant' && (msg.thinking || msg.thinkingDone)" class="think-block">
              <button class="think-toggle" @click="toggleThink(msg)">
                <span v-if="!msg.thinkingDone" class="think-status thinking">
                  <span class="think-dots"><span></span><span></span><span></span></span>
                  思考中
                </span>
                <span v-else class="think-status done">
                  <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14"><path d="M9,20.42L2.79,14.21L5.62,11.38L9,14.77L18.88,4.88L21.71,7.71L9,20.42Z"/></svg>
                  思考结束
                </span>
                <svg class="think-chevron" :class="{ open: msg.thinkOpen }" viewBox="0 0 24 24" fill="currentColor" width="14" height="14"><path d="M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z"/></svg>
              </button>
              <div v-if="msg.thinkOpen" class="think-content">
                <div class="think-text" v-html="renderText(msg.thinking)"></div>
                <div v-if="!msg.thinkingDone" class="typing-cursor"></div>
              </div>
            </div>
            <div class="msg-bubble" :class="msg.role">
              <!-- 检索阶段（无 thinking 无 content）：三点等待动画 -->
              <div v-if="msg.streaming && !msg.content && !msg.thinking" class="typing-dots"><span></span><span></span><span></span></div>
              <!-- 思考结束、正式内容还未到达时：也显示三点 -->
              <div v-else-if="msg.streaming && !msg.content && msg.thinkingDone" class="typing-dots"><span></span><span></span><span></span></div>
              <!-- 正式内容 -->
              <div v-else class="msg-text" v-html="renderText(msg.content)"></div>
              <div v-if="msg.streaming && msg.content" class="typing-cursor"></div>
            </div>
            <div v-if="msg.sources && msg.sources.length" class="sources-row">
              <div class="sources-trigger">
                <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14"><path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/></svg>
                参考来源 ({{ msg.sources.length }})
                <div class="sources-popup">
                  <div class="popup-title">检索到的相关段落</div>
                  <div v-for="(src, si) in msg.sources" :key="si" class="popup-chunk">
                    <div class="popup-chunk-header">
                      <span class="popup-chunk-idx">段落 {{ si + 1 }}</span>
                      <span v-if="src.score" class="popup-chunk-score">{{ (src.score * 100).toFixed(0) }}%</span>
                      <span v-if="src.page_idx" class="popup-chunk-page">P{{ src.page_idx }}</span>
                    </div>
                    <div class="popup-chunk-text">{{ src.content_preview || '无内容' }}</div>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="msg.error" class="msg-error">{{ msg.error }}</div>
            <span class="msg-time">{{ fmtTime(msg.time) }}</span>
          </div>
        </div>

        <!-- 思考中占位行：仅在没有任何 assistant 消息正在 streaming 时才显示 -->
        <div v-if="isStreaming && !currentMessages.some(m => m.role === 'assistant' && m.streaming)" class="msg-row bot">
          <div class="msg-avatar-wrap"><div class="msg-avatar bot-av">AI助手</div></div>
          <div class="msg-content"><div class="msg-bubble bot"><div class="typing-dots"><span></span><span></span><span></span></div></div></div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="input-area">
        <div class="input-wrap" :class="{ disabled: !assistantConfig.kbId }">
          <textarea
            ref="inputRef"
            v-model="inputText"
            :placeholder="assistantConfig.kbId ? '输入问题，Enter 发送，Shift+Enter 换行' : '请先在助手设置中选择知识库'"
            :disabled="!assistantConfig.kbId || isStreaming"
            rows="1"
            @keydown.enter.exact.prevent="sendMessage"
            @input="autoResize"
          ></textarea>
          <button class="send-btn" :class="{ active: inputText.trim() && assistantConfig.kbId && !isStreaming }"
            @click="sendMessage" :disabled="!inputText.trim() || !assistantConfig.kbId || isStreaming">
            <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20"><path d="M2,21L23,12L2,3V10L17,12L2,14V21Z"/></svg>
          </button>
        </div>
      </div>
    </main>

    <!-- 助手设置面板 -->
    <Transition name="panel">
      <div v-if="showAssistantPanel" class="panel-overlay" @click.self="showAssistantPanel = false">
        <div class="side-panel">
          <div class="panel-header">
            <h3>助手设置</h3>
            <button class="close-btn" @click="showAssistantPanel = false">
              <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20"><path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/></svg>
            </button>
          </div>
          <div class="panel-body">
            <div class="form-field">
              <label>助手名称</label>
              <input v-model="assistantConfig.name" type="text" placeholder="例如：我的知识助手" class="panel-input" />
            </div>
            <div class="form-field">
              <label>选择知识库</label>
              <select v-model="assistantConfig.kbId" class="panel-select" @change="onKbChange">
                <option value="">-- 请选择知识库 --</option>
                <option v-for="kb in kbList" :key="kb.kb_id" :value="kb.kb_id">{{ kb.name }}</option>
              </select>
            </div>
            <div class="form-field">
              <label>回答数量 (top_k)</label>
              <input v-model.number="assistantConfig.topK" type="number" min="1" max="20" class="panel-input" />
            </div>
            <div class="form-field toggle-field">
              <label>启用重排序</label>
              <button class="toggle-btn" :class="{ on: assistantConfig.useRerank }" @click="assistantConfig.useRerank = !assistantConfig.useRerank">
                <span class="toggle-knob"></span>
              </button>
            </div>
            <button class="save-btn" @click="saveAssistantConfig">保存设置</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 参考来源 Tooltip -->
    <div
      v-if="sourceTooltip.visible"
      class="source-tooltip"
      :style="{ top: sourceTooltip.y + 'px', left: sourceTooltip.x + 'px' }"
    >
      <div class="tooltip-header">
        <span class="tooltip-label">检索段落</span>
        <span v-if="sourceTooltip.data.score" class="tooltip-score">相关度 {{ (sourceTooltip.data.score * 100).toFixed(0) }}%</span>
      </div>
      <div class="tooltip-content">{{ sourceTooltip.data.content_preview || '无内容' }}</div>
      <div class="tooltip-meta">
        <span v-if="sourceTooltip.data.page_idx">页码: {{ sourceTooltip.data.page_idx }}</span>
      </div>
    </div>

    <!-- 个人信息面板 -->
    <Transition name="panel">
      <div v-if="showProfilePanel" class="panel-overlay" @click.self="showProfilePanel = false">
        <div class="side-panel">
          <div class="panel-header">
            <h3>个人信息</h3>
            <button class="close-btn" @click="showProfilePanel = false">
              <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20"><path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/></svg>
            </button>
          </div>
          <div class="panel-body">
            <div class="profile-avatar">{{ (userInfo.username || 'U')[0].toUpperCase() }}</div>
            <div class="form-field">
              <label>用户名</label>
              <input v-model="profileForm.username" type="text" class="panel-input" />
            </div>
            <div class="form-field">
              <label>邮箱</label>
              <input v-model="profileForm.email" type="email" class="panel-input" placeholder="选填" />
            </div>
            <div class="form-field">
              <label>新密码</label>
              <input v-model="profileForm.newPassword" type="password" class="panel-input" placeholder="不修改请留空" />
            </div>
            <div v-if="profileMsg" class="profile-msg" :class="profileMsgType">{{ profileMsg }}</div>
            <button class="save-btn" @click="saveProfile">保存修改</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { streamAskWithConv, createConversation, listConversations, deleteConversation } from '../api/qa'
import axios from 'axios'

const router = useRouter()

// ── 用户信息 ──────────────────────────────────────────
const userInfo = reactive(JSON.parse(localStorage.getItem('user_info') || '{}'))
const userToken = () => localStorage.getItem('user_token') || ''

// ── 侧边栏 ────────────────────────────────────────────
const sidebarCollapsed = ref(false)

// ── 助手配置（持久化） ────────────────────────────────
const ASSISTANT_KEY = 'user_assistant_config'
const assistantConfig = reactive({
  name: '智能助手',
  kbId: '',
  kbName: '',
  topK: 5,
  useRerank: true,
  ...JSON.parse(localStorage.getItem(ASSISTANT_KEY) || '{}'),
})

// ── 知识库列表（按部门权限过滤） ─────────────────────
const kbList = ref([])
async function loadKBList() {
  try {
    const res = await axios.get('/api/v1/knowledge-bases', {
      params: { page: 1, size: 100 },
      headers: { Authorization: `Bearer ${userToken()}` },
    })
    const allKBs = res.data?.data?.knowledge_bases || []
    // 读取部门数据，找出当前用户所在部门关联的知识库
    const username = userInfo.username
    const deptRaw = localStorage.getItem('rag_departments')
    const depts = deptRaw ? JSON.parse(deptRaw) : []
    // 找出包含当前用户的部门
    const userDepts = depts.filter(d => (d.memberUsernames || []).includes(username))
    if (userDepts.length === 0) {
      // 不在任何部门：显示全部（或可改为空列表，视业务需求）
      kbList.value = allKBs
    } else {
      // 收集所有部门关联的 kbId
      const allowedKbIds = new Set()
      for (const d of userDepts) {
        for (const id of (d.kbIds || [])) allowedKbIds.add(id)
      }
      kbList.value = allKBs.filter(kb => allowedKbIds.has(kb.kb_id))
    }
  } catch { kbList.value = [] }
}

function onKbChange() {
  const kb = kbList.value.find(k => k.kb_id === assistantConfig.kbId)
  assistantConfig.kbName = kb?.name || ''
}

function saveAssistantConfig() {
  localStorage.setItem(ASSISTANT_KEY, JSON.stringify({
    name: assistantConfig.name,
    kbId: assistantConfig.kbId,
    kbName: assistantConfig.kbName,
    topK: assistantConfig.topK,
    useRerank: assistantConfig.useRerank,
  }))
  showAssistantPanel.value = false
}

// ── 会话管理 ──────────────────────────────────────────
const SESSIONS_KEY = 'user_chat_sessions'
const sessions = ref(JSON.parse(localStorage.getItem(SESSIONS_KEY) || '[]'))
const currentSessionId = ref(sessions.value[0]?.id || null)

const currentMessages = computed(() => {
  const s = sessions.value.find(s => s.id === currentSessionId.value)
  return s?.messages || []
})

function saveSessions() {
  localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions.value))
}

async function newChat() {
  const id = Date.now().toString()
  // conversationId 在第一次发送时由后端创建，此处先置空
  sessions.value.unshift({ id, name: '新对话', messages: [], conversationId: null })
  currentSessionId.value = id
  saveSessions()
  // 新对话自动显示欢迎语（打字机效果，不调用知识库）
  await nextTick()
  showWelcomeMessage()
}

async function showWelcomeMessage() {
  const name = userInfo.username || '同学'
  const welcomeText = `您好，${name}！欢迎使用 PengMind 智能问答。请在左侧「助手设置」中选择知识库，然后输入您的问题，我会基于知识库内容为您解答。`
  // 直接 push 普通对象，通过末尾索引获取 Vue 管理的响应式引用
  const s = sessions.value.find(s => s.id === currentSessionId.value)
  if (!s) return
  s.messages.push({
    role: 'assistant',
    content: '',
    time: Date.now(),
    streaming: true,
    sources: [],
    thinking: '',
    thinkingDone: false,
    thinkOpen: false,
  })
  const welcomeMsg = s.messages[s.messages.length - 1]
  await nextTick()
  await scrollBottom()

  // 逐字打出
  for (const char of welcomeText) {
    welcomeMsg.content += char
    await new Promise(r => setTimeout(r, 30))
  }
  welcomeMsg.streaming = false
  saveSessions()
}

function switchSession(id) {
  currentSessionId.value = id
}

function deleteSession(id) {
  sessions.value = sessions.value.filter(s => s.id !== id)
  if (currentSessionId.value === id) {
    currentSessionId.value = sessions.value[0]?.id || null
  }
  saveSessions()
}

function pushMessage(msg) {
  const s = sessions.value.find(s => s.id === currentSessionId.value)
  if (s) {
    s.messages.push(msg)
    if (s.messages.length === 1 && msg.role === 'user') {
      s.name = msg.content.slice(0, 20) || '新对话'
    }
    saveSessions()
  }
}

// ── 发送消息 ──────────────────────────────────────────
const inputText = ref('')
const isStreaming = ref(false)
const inputRef = ref(null)
const scrollRef = ref(null)
const abortCtrl = ref(null)

const quickQuestions = ['这份文档的主要内容是什么？', '请总结关键要点', '有哪些重要数据？', '请列出主要章节']

function sendQuick(q) { inputText.value = q; sendMessage() }

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || !assistantConfig.kbId || isStreaming.value) return

  if (!currentSessionId.value) newChat()

  pushMessage({ role: 'user', content: text, time: Date.now() })
  inputText.value = ''
  if (inputRef.value) inputRef.value.style.height = 'auto'
  await scrollBottom()

  // 直接 push 普通对象，通过末尾索引获取 Vue 管理的响应式引用
  // 不能用 reactive() 再 pushMessage，否则 Vue 会解包导致变量引用失效
  pushMessage({
    role: 'assistant', content: '', time: Date.now(), streaming: true, sources: [],
    thinking: '',        // 思考链内容（实时累积）
    thinkingDone: false, // 思考链是否结束
    thinkOpen: false,    // 思考链面板是否展开
  })
  const sess0 = sessions.value.find(s => s.id === currentSessionId.value)
  const assistantMsg = sess0.messages[sess0.messages.length - 1]
  isStreaming.value = true
  const ctrl = new AbortController()
  abortCtrl.value = ctrl

  // ── 懒创建 conversation_id（首次发送时向后端申请）──────────────
  const sess = sessions.value.find(s => s.id === currentSessionId.value)
  if (sess && !sess.conversationId && assistantConfig.kbId) {
    try {
      const res = await createConversation({
        userId: userInfo.user_id || userInfo.username || 'user',
        kbId: assistantConfig.kbId,
        title: text.slice(0, 40),
      })
      sess.conversationId = res?.data?.conversation_id || null
      saveSessions()
    } catch (e) {
      console.warn('[UserChat] 创建会话失败，降级为无持久化模式', e)
    }
  }
  const conversationId = sess?.conversationId || null

  try {
    const resp = await streamAskWithConv({
      query: text,
      knowledge_base_id: assistantConfig.kbId,
      conversation_id: conversationId,
      top_k: assistantConfig.topK,
      use_rerank: assistantConfig.useRerank,
      signal: ctrl.signal,
    })
    if (!resp.ok) throw new Error(`服务器错误 (${resp.status})`)

    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buf = '', full = ''
    // 已处理过的 base64 块数量，用于增量解码，避免重复拼接
    let processedThinkChunks = 0

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      const lines = buf.split('\n'); buf = lines.pop() || ''
      // SSE 解析：连续的 data: 行属于同一事件，按规范用 \n 拼接
      let lastWasData = false
      for (const line of lines) {
        const t = line.trim()
        if (!t.startsWith('data:')) { lastWasData = false; continue }
        const raw = t.slice(5)
        const payload = raw.startsWith(' ') ? raw.slice(1) : raw
        if (lastWasData) full += '\n'
        full += payload
        lastWasData = true
      }

      // ── 增量解析思考链标记（\x01base64\x01 格式）──
      const thinkRe = /\x01([A-Za-z0-9+/=]+)\x01/g
      const allMatches = [...full.matchAll(thinkRe)]
      // 只处理新增的块，用 TextDecoder 正确解码 UTF-8
      for (let i = processedThinkChunks; i < allMatches.length; i++) {
        try {
          const bytes = Uint8Array.from(atob(allMatches[i][1]), c => c.charCodeAt(0))
          assistantMsg.thinking += new TextDecoder('utf-8').decode(bytes)
        } catch {}
      }
      processedThinkChunks = allMatches.length

      // 有思考内容时先渲染"思考中"，再标记结束（延迟让用户看到思考中状态）
      // 只有 thinking 非空时才设置 thinkingDone，避免无思考内容时显示空的"思考结束"
      if (full.includes('\x02THINK_END\x02') && !assistantMsg.thinkingDone && assistantMsg.thinking) {
        await nextTick()
        await new Promise(r => setTimeout(r, 300))
        assistantMsg.thinkingDone = true
      }

      // 移除思考链标记，得到干净的正文流
      let strippedFull = full
        .replace(/\x01[A-Za-z0-9+/=]*\x01/g, '')
        .replace(/\x02THINK_END\x02/g, '')

      // ── 解析 RAG_META ────────────────────────────────
      const m = strippedFull.match(/<!--RAG_META\s+([\s\S]*?)\s+RAG_META-->/)
      if (m) {
        try { const meta = JSON.parse(m[1]); assistantMsg.sources = meta.citations || [] } catch {}
        assistantMsg.content = strippedFull.replace(/\n*<!--RAG_META[\s\S]*?RAG_META-->/, '').trimEnd()
      } else {
        assistantMsg.content = strippedFull
      }

      await nextTick(); await scrollBottom()
    }

    // 最终清理
    const strippedFinal = full
      .replace(/\x01[A-Za-z0-9+/=]*\x01/g, '')
      .replace(/\x02THINK_END\x02/g, '')
    const fm = strippedFinal.match(/<!--RAG_META\s+([\s\S]*?)\s+RAG_META-->/)
    if (fm) {
      try { const meta = JSON.parse(fm[1]); assistantMsg.sources = meta.citations || [] } catch {}
      assistantMsg.content = strippedFinal.replace(/\n*<!--RAG_META[\s\S]*?RAG_META-->/, '').trimEnd()
    } else {
      assistantMsg.content = strippedFinal
    }
    if (!assistantMsg.thinkingDone && assistantMsg.thinking) {
      assistantMsg.thinkingDone = true
    }
    assistantMsg.streaming = false
  } catch (e) {
    assistantMsg.streaming = false
    if (e.name !== 'AbortError') assistantMsg.error = e.message || '请求失败'
    else assistantMsg.content += '\n\n*[已中断]*'
  } finally {
    isStreaming.value = false; abortCtrl.value = null
    saveSessions(); await scrollBottom()
  }
}

// ── 思考链折叠切换 ────────────────────────────────────
function toggleThink(msg) {
  msg.thinkOpen = !msg.thinkOpen
}

function autoResize() {
  const el = inputRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 150) + 'px'
}

async function scrollBottom() {
  await nextTick()
  if (scrollRef.value) scrollRef.value.scrollTop = scrollRef.value.scrollHeight
}

function renderText(content) {
  if (!content) return ''
  return content
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
}

function fmtTime(ts) {
  return new Date(ts).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// ── 参考来源 Tooltip ──────────────────────────────────
const sourceTooltip = reactive({ visible: false, x: 0, y: 0, data: {} })

function showSourceTooltip(event, source) {
  const rect = event.target.getBoundingClientRect()
  sourceTooltip.x = rect.left
  sourceTooltip.y = rect.bottom + 8
  sourceTooltip.data = source
  sourceTooltip.visible = true
}

function hideSourceTooltip() {
  sourceTooltip.visible = false
}

// ── 面板 ──────────────────────────────────────────────
const showAssistantPanel = ref(false)
const showProfilePanel = ref(false)

// ── 个人信息 ──────────────────────────────────────────
const profileForm = reactive({
  username: userInfo.username || '',
  email: userInfo.email || '',
  newPassword: '',
})
const profileMsg = ref('')
const profileMsgType = ref('ok')

async function saveProfile() {
  try {
    const payload = { username: profileForm.username, email: profileForm.email }
    if (profileForm.newPassword) payload.password = profileForm.newPassword
    await axios.put('/api/auth/user/info', payload, {
      headers: { Authorization: `Bearer ${userToken()}` },
    })
    Object.assign(userInfo, { username: profileForm.username, email: profileForm.email })
    localStorage.setItem('user_info', JSON.stringify(userInfo))
    profileMsg.value = '保存成功'; profileMsgType.value = 'ok'
    profileForm.newPassword = ''
  } catch (e) {
    profileMsg.value = e.response?.data?.message || '保存失败'; profileMsgType.value = 'err'
  }
}

// ── 退出 ──────────────────────────────────────────────
function handleLogout() {
  localStorage.removeItem('user_token')
  localStorage.removeItem('user_info')
  router.push('/user/login')
}

// ── 初始化 ────────────────────────────────────────────
onMounted(async () => {
  if (!userToken()) { router.push('/user/login'); return }
  await loadKBList()
  if (!currentSessionId.value && sessions.value.length === 0) newChat()
})
</script>

<style scoped>
/* ── 整体布局 ── */
.user-chat-page {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: linear-gradient(135deg, #f0faf5 0%, #e8f8f0 100%);
  font-family: inherit;
}

/* ── 侧边栏 ── */
.sidebar {
  width: 260px;
  flex-shrink: 0;
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(16px);
  border-right: 1px solid rgba(168,230,207,0.3);
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  overflow: hidden;
}
.sidebar.collapsed { width: 72px; }

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 16px;
  border-bottom: 1px solid rgba(168,230,207,0.2);
  flex-shrink: 0;
}
.brand-icon {
  width: 32px; height: 32px;
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
}
.brand-logo-img {
  width: 32px;
  height: 32px;
  object-fit: contain;
  border-radius: 8px;
  pointer-events: none;
  user-select: none;
}
.brand-name { font-size: 16px; font-weight: 700; color: #2d6a4f; flex: 1; white-space: nowrap; }
.collapse-btn {
  background: none; border: none; cursor: pointer;
  color: #74c69d; padding: 4px;
  display: flex; align-items: center;
}
.collapse-btn svg { width: 20px; height: 20px; transition: transform 0.3s; }

.new-chat-btn {
  margin: 12px;
  padding: 10px 14px;
  background: linear-gradient(135deg, #52b788, #2d6a4f);
  border: none; border-radius: 10px;
  color: white; font-size: 14px; font-weight: 600;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 8px;
  transition: all 0.2s;
  flex-shrink: 0;
}
.new-chat-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(82,183,136,0.35); }

.sidebar-nav { flex: 1; overflow-y: auto; padding: 8px; }
.nav-section-title { font-size: 11px; font-weight: 600; color: #74c69d; padding: 8px 8px 4px; text-transform: uppercase; letter-spacing: 0.5px; }

.session-item {
  display: flex; align-items: center; gap: 8px;
  padding: 9px 10px; border-radius: 8px;
  cursor: pointer; color: #52b788;
  transition: background 0.15s;
  font-size: 13px;
}
.session-item:hover { background: rgba(168,230,207,0.15); }
.session-item.active { background: rgba(168,230,207,0.25); color: #2d6a4f; font-weight: 500; }
.session-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.del-btn { background: none; border: none; cursor: pointer; color: #b7e4c7; padding: 2px; opacity: 0; transition: opacity 0.15s; }
.session-item:hover .del-btn { opacity: 1; }
.del-btn:hover { color: #ef4444; }
.no-sessions { font-size: 12px; color: #b7e4c7; padding: 12px 8px; text-align: center; }

.sidebar-footer { padding: 12px; border-top: 1px solid rgba(168,230,207,0.2); display: flex; flex-direction: column; gap: 4px; }
.footer-btn {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; border: none; border-radius: 8px;
  background: none; cursor: pointer;
  font-size: 13px; color: #52b788;
  transition: background 0.15s;
  text-align: left;
}
.footer-btn:hover { background: rgba(168,230,207,0.15); }
.footer-btn.logout { color: #ef4444; }
.footer-btn.logout:hover { background: rgba(239,68,68,0.08); }

.sidebar-footer-icons { padding: 12px 8px; border-top: 1px solid rgba(168,230,207,0.2); display: flex; flex-direction: column; gap: 4px; align-items: center; }
.icon-btn { background: none; border: none; cursor: pointer; color: #52b788; padding: 8px; border-radius: 8px; transition: background 0.15s; }
.icon-btn:hover { background: rgba(168,230,207,0.15); }
.icon-btn.logout { color: #ef4444; }
.icon-btn.logout:hover { background: rgba(239,68,68,0.08); }

/* ── 主聊天区 ── */
.chat-main { flex: 1; display: flex; flex-direction: column; min-width: 0; }

.chat-topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 24px;
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(168,230,207,0.25);
  flex-shrink: 0;
}
.topbar-left { display: flex; align-items: center; gap: 12px; }
.assistant-avatar {
  width: 38px; height: 38px;
  background: linear-gradient(135deg, #a8e6cf, #52b788);
  border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white;
}
.assistant-avatar svg { width: 22px; height: 22px; }
.assistant-name { font-size: 15px; font-weight: 600; color: #1b4332; }
.assistant-kb { font-size: 12px; color: #74c69d; }
.user-badge { font-size: 13px; font-weight: 500; color: #52b788; background: rgba(168,230,207,0.2); padding: 5px 12px; border-radius: 20px; }

/* ── 消息区 ── */
.messages-area { flex: 1; overflow-y: auto; padding: 24px; }

.welcome-screen { text-align: center; padding: 60px 20px; }
.welcome-avatar {
  width: 80px; height: 80px;
  background: linear-gradient(135deg, rgba(168,230,207,0.3), rgba(82,183,136,0.2));
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  margin: 0 auto 20px; color: #52b788;
}
.welcome-screen h2 { font-size: 24px; color: #1b4332; margin-bottom: 8px; }
.welcome-screen p { font-size: 15px; color: #74c69d; margin-bottom: 24px; }
.welcome-screen strong { color: #2d6a4f; }
.no-kb-tip {
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(255,193,7,0.1); border: 1px solid rgba(255,193,7,0.3);
  color: #b7791f; font-size: 13px; padding: 8px 14px; border-radius: 8px; margin-bottom: 20px;
}
.quick-list { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; max-width: 500px; margin: 0 auto; }
.quick-chip {
  padding: 8px 16px; background: rgba(255,255,255,0.9);
  border: 1px solid rgba(168,230,207,0.4); border-radius: 20px;
  font-size: 13px; color: #52b788; cursor: pointer; transition: all 0.2s;
}
.quick-chip:hover { background: rgba(168,230,207,0.2); border-color: #52b788; transform: translateY(-1px); }

.msg-row { display: flex; gap: 12px; margin-bottom: 20px; animation: fadeIn 0.2s ease; }
.msg-row.user { flex-direction: row-reverse; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }

.msg-avatar { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; flex-shrink: 0; }
.user-av { background: linear-gradient(135deg, #52b788, #2d6a4f); color: white; font-size: 14px; }
/* bot 头像：青绿色背景，白色"AI助手"文字，字体缩小以适配四个字 */
.bot-av {
  background: linear-gradient(135deg, #52b788, #2d6a4f);
  color: white;
  font-size: 9px;
  letter-spacing: 0.5px;
  border-radius: 10px;
  line-height: 1.2;
  text-align: center;
  padding: 2px;
}

.msg-content { display: flex; flex-direction: column; max-width: 72%; }
.msg-row.user .msg-content { align-items: flex-end; }

.msg-bubble { padding: 12px 16px; border-radius: 16px; line-height: 1.7; }
.msg-bubble.user { background: linear-gradient(135deg, rgba(168,230,207,0.4), rgba(82,183,136,0.2)); }
.msg-bubble.bot { background: rgba(255,255,255,0.95); box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.msg-text { font-size: 14px; color: #1b4332; word-break: break-word; }
.msg-text :deep(code) { background: rgba(168,230,207,0.2); padding: 2px 6px; border-radius: 4px; font-size: 13px; }
.msg-text :deep(strong) { font-weight: 600; color: #1b4332; }

.typing-cursor { display: inline-block; width: 2px; height: 15px; background: #52b788; vertical-align: text-bottom; animation: blink 0.8s infinite; margin-left: 2px; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }

.typing-dots { display: flex; gap: 5px; padding: 4px 0; }
.typing-dots span { width: 7px; height: 7px; background: #74c69d; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; }
.typing-dots span:nth-child(1){animation-delay:-0.32s}
.typing-dots span:nth-child(2){animation-delay:-0.16s}
@keyframes bounce { 0%,80%,100%{transform:scale(0.6);opacity:0.4} 40%{transform:scale(1);opacity:1} }

.sources-row { margin-top: 8px; }

/* ── 参考来源 hover 弹窗 ── */
.sources-trigger {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(168,230,207,0.15);
  border: 1px solid rgba(168,230,207,0.4);
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  color: #2d6a4f;
  cursor: pointer;
  transition: all 0.2s;
}
.sources-trigger:hover { background: rgba(168,230,207,0.3); border-color: #52b788; }
.sources-trigger svg { flex-shrink: 0; color: #52b788; }

.sources-popup {
  display: none;
  position: absolute;
  bottom: 100%;
  left: 0;
  width: 400px;
  max-height: 340px;
  overflow-y: auto;
  background: white;
  border: 1px solid rgba(168,230,207,0.4);
  border-radius: 12px;
  box-shadow: 0 12px 40px rgba(0,0,0,0.15), 0 4px 12px rgba(0,0,0,0.08);
  padding: 16px;
  z-index: 9999;
  animation: popupIn 0.15s ease;
}
.sources-trigger:hover .sources-popup { display: block; }
@keyframes popupIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }

.popup-title { font-size: 13px; font-weight: 600; color: #1b4332; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid rgba(168,230,207,0.3); }
.popup-chunk { margin-bottom: 12px; padding: 10px 12px; background: rgba(240,250,245,0.6); border: 1px solid rgba(168,230,207,0.2); border-radius: 8px; }
.popup-chunk:last-child { margin-bottom: 0; }
.popup-chunk-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.popup-chunk-idx { font-size: 11px; font-weight: 600; color: #2d6a4f; }
.popup-chunk-score { font-size: 10px; color: #52b788; background: rgba(168,230,207,0.3); padding: 1px 6px; border-radius: 8px; }
.popup-chunk-page { font-size: 10px; color: #74c69d; }
.popup-chunk-text { font-size: 12px; color: #1b4332; line-height: 1.6; word-break: break-word; }
.msg-error { font-size: 12px; color: #ef4444; margin-top: 4px; }
.msg-time { font-size: 11px; color: #b7e4c7; margin-top: 4px; }

/* ── 输入区 ── */
.input-area { padding: 16px 24px 24px; flex-shrink: 0; }
.input-wrap {
  display: flex; align-items: flex-end; gap: 10px;
  background: rgba(255,255,255,0.95);
  border: 2px solid rgba(168,230,207,0.4);
  border-radius: 16px; padding: 10px 14px;
  transition: all 0.25s;
}
.input-wrap:focus-within { border-color: #52b788; box-shadow: 0 0 0 4px rgba(82,183,136,0.1); }
.input-wrap.disabled { opacity: 0.6; }
.input-wrap textarea {
  flex: 1; border: none; background: transparent;
  font-size: 14px; color: #1b4332; resize: none; outline: none;
  line-height: 1.5; max-height: 150px; font-family: inherit;
}
.input-wrap textarea::placeholder { color: #b7e4c7; }
.send-btn {
  width: 38px; height: 38px; border: none;
  background: #e8f8f0; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; color: #b7e4c7; transition: all 0.2s; flex-shrink: 0;
}
.send-btn.active { background: linear-gradient(135deg, #52b788, #2d6a4f); color: white; box-shadow: 0 3px 10px rgba(82,183,136,0.35); }
.send-btn.active:hover { transform: scale(1.06); }
.send-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* ── 面板 ── */
.panel-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.3);
  z-index: 200; display: flex; align-items: center; justify-content: flex-end;
}
.side-panel {
  width: 360px; height: 100vh;
  background: white; display: flex; flex-direction: column;
  box-shadow: -4px 0 24px rgba(0,0,0,0.12);
}
.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 20px 24px; border-bottom: 1px solid rgba(168,230,207,0.3);
}
.panel-header h3 { font-size: 17px; font-weight: 700; color: #1b4332; }
.close-btn { background: none; border: none; cursor: pointer; color: #74c69d; padding: 4px; }
.close-btn:hover { color: #2d6a4f; }
.panel-body { flex: 1; overflow-y: auto; padding: 24px; }

.form-field { margin-bottom: 20px; }
.form-field label { display: block; font-size: 13px; font-weight: 600; color: #2d6a4f; margin-bottom: 7px; }
.panel-input, .panel-select {
  width: 100%; padding: 11px 14px;
  border: 2px solid rgba(168,230,207,0.4); border-radius: 10px;
  font-size: 14px; color: #1b4332; background: rgba(240,250,245,0.6);
  outline: none; transition: border-color 0.2s; box-sizing: border-box;
}
.panel-input:focus, .panel-select:focus { border-color: #52b788; background: white; }

.toggle-field { display: flex; align-items: center; justify-content: space-between; }
.toggle-btn {
  width: 44px; height: 24px; border-radius: 12px;
  background: #e0e0e0; border: none; cursor: pointer;
  position: relative; transition: background 0.25s;
}
.toggle-btn.on { background: #52b788; }
.toggle-knob {
  position: absolute; top: 2px; left: 2px;
  width: 20px; height: 20px; border-radius: 50%;
  background: white; transition: transform 0.25s;
  box-shadow: 0 1px 4px rgba(0,0,0,0.2);
}
.toggle-btn.on .toggle-knob { transform: translateX(20px); }

.save-btn {
  width: 100%; padding: 13px;
  background: linear-gradient(135deg, #52b788, #2d6a4f);
  border: none; border-radius: 10px;
  color: white; font-size: 15px; font-weight: 600;
  cursor: pointer; transition: all 0.2s;
  box-shadow: 0 3px 10px rgba(82,183,136,0.3);
}
.save-btn:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(82,183,136,0.4); }

.profile-avatar {
  width: 72px; height: 72px; border-radius: 50%;
  background: linear-gradient(135deg, #52b788, #2d6a4f);
  color: white; font-size: 28px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 24px;
}
.profile-msg { padding: 10px 14px; border-radius: 8px; font-size: 13px; margin-bottom: 14px; }
.profile-msg.ok { background: rgba(82,183,136,0.1); color: #2d6a4f; }
.profile-msg.err { background: rgba(239,68,68,0.08); color: #ef4444; }

/* ── 思考链 ── */
.think-block {
  margin-bottom: 6px;
  max-width: 100%;
}

.think-toggle {
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(168,230,207,0.12);
  border: 1px solid rgba(168,230,207,0.35);
  border-radius: 20px;
  padding: 5px 12px;
  cursor: pointer;
  font-size: 12px;
  color: #52b788;
  transition: all 0.2s;
  user-select: none;
}
.think-toggle:hover { background: rgba(168,230,207,0.22); border-color: #52b788; }

.think-status { display: flex; align-items: center; gap: 5px; }
.think-status.thinking { color: #74c69d; }
.think-status.done { color: #2d6a4f; }

/* 思考中的三点动画（复用 typing-dots 样式但更小） */
.think-dots { display: flex; gap: 3px; align-items: center; }
.think-dots span {
  width: 5px; height: 5px; background: #74c69d; border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}
.think-dots span:nth-child(1){animation-delay:-0.32s}
.think-dots span:nth-child(2){animation-delay:-0.16s}

.think-chevron {
  color: #74c69d;
  transition: transform 0.2s;
  flex-shrink: 0;
}
.think-chevron.open { transform: rotate(180deg); }

.think-content {
  margin-top: 6px;
  padding: 10px 14px;
  background: rgba(240,250,245,0.6);
  border: 1px solid rgba(168,230,207,0.25);
  border-radius: 10px;
  /* 半透明效果 */
  opacity: 0.75;
  max-height: 260px;
  overflow-y: auto;
  transition: max-height 0.25s ease;
}
.think-content:hover { opacity: 0.92; }

.think-text {
  font-size: 12px;
  color: #52b788;
  line-height: 1.7;
  word-break: break-word;
  font-family: 'Courier New', monospace;
}
.think-text :deep(code) { background: rgba(168,230,207,0.2); padding: 1px 4px; border-radius: 3px; }

/* ── 面板动画 ── */
.panel-enter-active, .panel-leave-active { transition: opacity 0.25s; }
.panel-enter-active .side-panel, .panel-leave-active .side-panel { transition: transform 0.25s ease; }
.panel-enter-from, .panel-leave-to { opacity: 0; }
.panel-enter-from .side-panel, .panel-leave-to .side-panel { transform: translateX(100%); }
</style>
