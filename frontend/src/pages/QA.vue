<template>
  <div class="qa-page">
    <div class="qa-container">
      <!-- ================================================================ -->
      <!-- 左侧：对话区域 -->
      <!-- ================================================================ -->
      <div class="chat-section">
        <!-- 顶部：知识库选择 + 操作 -->
        <div class="chat-header">
          <h1 class="page-title">
            <span class="title-icon">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20M12,6A4,4 0 0,0 8,10H10A2,2 0 0,1 12,8A2,2 0 0,1 14,10C14,12 11,11.75 11,15H13C13,12.75 16,12.5 16,10A4,4 0 0,0 12,6Z"/></svg>
            </span>
            智能问答
          </h1>

          <div class="header-actions">
            <!-- 知识库选择器 -->
            <div class="kb-selector" ref="kbDropdownRef">
              <button class="kb-selector-btn" @click="showKbDropdown = !showKbDropdown">
                <svg class="kb-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M12,3L1,9L12,15L21,10.09V17H23V9M5,13.18V17.18L12,21L19,17.18V13.18L12,17L5,13.18Z"/></svg>
                <span v-if="!selectedKbId" class="placeholder">{{ kbList.length ? '选择知识库' : '加载中...' }}</span>
                <span v-else class="kb-name">{{ selectedKbName }}</span>
                <svg class="dropdown-arrow" :class="{ open: showKbDropdown }" viewBox="0 0 24 24" fill="currentColor"><path d="M7,10L12,15L17,10H7Z"/></svg>
              </button>
              <div v-if="showKbDropdown" class="kb-dropdown">
                <div
                  v-for="kb in kbList"
                  :key="kb.kb_id"
                  class="kb-option"
                  :class="{ selected: selectedKbId === kb.kb_id }"
                  @click="selectKB(kb)"
                >
                  <div class="kb-option-info">
                    <span class="kb-option-name">{{ kb.name }}</span>
                    <span class="kb-option-meta">{{ kb.doc_count ?? 0 }} 文档</span>
                  </div>
                  <div v-if="selectedKbId === kb.kb_id" class="check-mark">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M21,7L9,19L3.5,13.5L4.91,12.09L9,16.17L19.59,5.59L21,7Z"/></svg>
                  </div>
                </div>
                <div v-if="kbList.length === 0" class="kb-empty">暂无可用知识库</div>
              </div>
            </div>

            <!-- 清空 -->
            <button class="btn btn-ghost" @click="clearChat" :disabled="messages.length === 0">
              <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/></svg>
              清空
            </button>
          </div>
        </div>

        <!-- 对话消息 -->
        <div class="messages-container" ref="scrollRef">
          <!-- 空状态 -->
          <div v-if="messages.length === 0" class="welcome-state">
            <div class="welcome-icon">
              <svg viewBox="0 0 24 24" fill="currentColor" width="40" height="40"><path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20M12,6A4,4 0 0,0 8,10H10A2,2 0 0,1 12,8A2,2 0 0,1 14,10C14,12 11,11.75 11,15H13C13,12.75 16,12.5 16,10A4,4 0 0,0 12,6Z"/></svg>
            </div>
            <h2>有什么可以帮助您的？</h2>
            <p>选择知识库后，基于 RAG 技术从文档中为您检索精准答案</p>
            <div class="quick-questions">
              <button
                v-for="(q, i) in quickQuestions"
                :key="i"
                class="quick-btn"
                @click="askQuick(q)"
              >{{ q }}</button>
            </div>
          </div>

          <!-- 消息列表 -->
          <div
            v-for="(msg, i) in messages"
            :key="i"
            class="message-row"
            :class="msg.role"
          >
            <!-- 头像 -->
            <div class="msg-avatar">
              <div v-if="msg.role === 'user'" class="avatar user-avatar-icon">我</div>
              <div v-else class="avatar bot-avatar-icon">AI助手</div>
            </div>

            <!-- 气泡区域 -->
            <div class="msg-bubble-wrap">
              <!-- 思考链（仅 assistant） -->
              <div v-if="msg.role === 'assistant' && (msg.thinking || msg.thinkingDone)" class="think-block">
                <button class="think-toggle" @click="msg.thinkOpen = !msg.thinkOpen">
                  <span v-if="!msg.thinkingDone" class="think-status thinking">
                    <span class="think-dots-sm"><span></span><span></span><span></span></span>
                    思考中
                  </span>
                  <span v-else class="think-status done">
                    <svg viewBox="0 0 24 24" fill="currentColor" width="13" height="13"><path d="M9,20.42L2.79,14.21L5.62,11.38L9,14.77L18.88,4.88L21.71,7.71L9,20.42Z"/></svg>
                    思考结束
                  </span>
                  <svg class="think-chevron" :class="{ open: msg.thinkOpen }" viewBox="0 0 24 24" fill="currentColor" width="13" height="13"><path d="M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z"/></svg>
                </button>
                <div v-if="msg.thinkOpen" class="think-content">
                  <div class="think-text" v-html="formatContent({ content: msg.thinking })"></div>
                  <div v-if="!msg.thinkingDone" class="typing-cursor"></div>
                </div>
              </div>

              <!-- 气泡 -->
              <div class="msg-bubble" :class="msg.role">
                <!-- 检索阶段（无 thinking 无 content）：三点等待 -->
                <div v-if="msg.streaming && !msg.content && !msg.thinking" class="typing-dots"><span></span><span></span><span></span></div>
                <!-- 思考结束、正式内容还未到达 -->
                <div v-else-if="msg.streaming && !msg.content && msg.thinkingDone" class="typing-dots"><span></span><span></span><span></span></div>
                <!-- 正式内容 -->
                <div v-else class="msg-text" v-html="formatContent(msg)"></div>
                <div v-if="msg.streaming && msg.content" class="typing-cursor"></div>
                <!-- 错误 -->
                <div v-if="msg.error" class="msg-error">{{ msg.error }}</div>
                <!-- 引用来源 -->
                <div v-if="msg.sources && msg.sources.length" class="msg-sources">
                  <div class="sources-title">
                    <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14"><path d="M12,3L1,9L12,15L21,10.09V17H23V9M5,13.18V17.18L12,21L19,17.18V13.18L12,17L5,13.18Z"/></svg>
                    参考来源
                  </div>
                  <div class="sources-list">
                    <div v-for="(src, si) in msg.sources" :key="si" class="source-chip">
                      <span class="source-doc">{{ src.doc_id?.slice(-8) || '--' }}</span>
                      <span v-if="src.score" class="source-score">{{ (src.score * 100).toFixed(0) }}%</span>
                    </div>
                  </div>
                </div>
                <span class="msg-time">{{ formatTime(msg.time) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="input-section">
          <div class="input-wrapper" :class="{ disabled: !selectedKbId }">
            <textarea
              ref="inputRef"
              v-model="inputText"
              class="chat-input"
              :placeholder="selectedKbId ? '输入问题，Enter 发送' : '请先选择知识库'"
              rows="1"
              :disabled="!selectedKbId || isStreaming"
              @keydown.enter.exact.prevent="sendMessage"
              @input="autoResize"
            ></textarea>
            <button
              class="send-btn"
              :class="{ ready: inputText.trim() && selectedKbId && !isStreaming }"
              @click="sendMessage"
              :disabled="!inputText.trim() || !selectedKbId || isStreaming"
            >
              <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20"><path d="M2,21L23,12L2,3V10L17,12L2,14V21Z"/></svg>
            </button>
          </div>
          <div class="input-hint">Enter 发送 · Shift+Enter 换行</div>
        </div>
      </div>

      <!-- ================================================================ -->
      <!-- 右侧：信息面板 -->
      <!-- ================================================================ -->
      <div class="sidebar-section">
        <!-- 当前知识库 -->
        <div class="info-card">
          <h3 class="card-title">
            <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M12,3L1,9L12,15L21,10.09V17H23V9M5,13.18V17.18L12,21L19,17.18V13.18L12,17L5,13.18Z"/></svg>
            {{ selectedKbId ? selectedKbName : '知识库' }}
          </h3>
          <template v-if="selectedKbId">
            <div class="info-row">
              <span>文档数</span>
              <span class="info-val">{{ selectedKbDocCount ?? '--' }}</span>
            </div>
            <div class="info-row">
              <span>分块数</span>
              <span class="info-val">{{ selectedKbChunks ?? '--' }}</span>
            </div>
            <div class="info-row">
              <span>状态</span>
              <span class="info-val ok">正常</span>
            </div>
          </template>
          <template v-else>
            <p class="info-hint">请在上方选择一个知识库开始提问</p>
          </template>
        </div>

        <!-- 对话信息 -->
        <div v-if="messages.length > 0" class="info-card">
          <h3 class="card-title">
            <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M20,2H4C2.9,2 2,2.9 2,4V22L6,18H20C21.1,18 22,17.1 22,16V4C22,2.9 21.1,2 20,2M20,16H5.2L4,17.2V4H20V16Z"/></svg>
            对话信息
          </h3>
          <div class="info-row">
            <span>问答轮次</span>
            <span class="info-val">{{ Math.floor(messages.length / 2) }}</span>
          </div>
          <div class="info-row">
            <span>消息数</span>
            <span class="info-val">{{ messages.length }}</span>
          </div>
          <button class="btn btn-ghost btn-small" @click="clearChat">清空对话记录</button>
        </div>

        <!-- 提示 -->
        <div class="info-card">
          <h3 class="card-title">
            <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M13.5,5.5C14.59,5.5 15.5,4.58 15.5,3.5C15.5,2.38 14.59,1.5 13.5,1.5C12.39,1.5 11.5,2.38 11.5,3.5C11.5,4.58 12.39,5.5 13.5,5.5M9.89,19.38L10.89,15L13,17V23H15V15.5L12.89,13.5L13.5,10.5C14.79,12 16.79,13 19,13V11C17.09,11 15.5,10 14.69,8.58L13.69,7C13.29,6.38 12.69,6 12,6C11.69,6 11.5,6.08 11.19,6.08L6,8.28V13H8V9.58L9.79,8.88L8.19,17L3.29,16L2.89,18L9.89,19.38Z"/></svg>
            使用提示
          </h3>
          <ul class="tips-list">
            <li>提问越具体，答案越精准</li>
            <li>支持询问文档中的具体内容</li>
            <li>回答会自动引用原文出处</li>
            <li>支持多轮对话保持上下文</li>
          </ul>
        </div>

        <!-- 错误日志 -->
        <div v-if="errorLog.length" class="info-card error-card">
          <h3 class="card-title error-title">错误日志</h3>
          <div v-for="(e, i) in errorLog" :key="i" class="error-line">{{ e }}</div>
          <button class="btn btn-ghost btn-small" @click="errorLog = []">清除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<!-- ================================================================== -->
<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { knowledgeApi } from '../api/knowledge'
import { streamAsk } from '../api/qa'

// -----------------------------------------------------------------------
// 知识库
// -----------------------------------------------------------------------

const kbList = ref([])
const selectedKbId = ref('')
const showKbDropdown = ref(false)
const kbDropdownRef = ref(null)

const selectedKbName = computed(() => {
  const kb = kbList.value.find(k => k.kb_id === selectedKbId.value)
  return kb?.name || ''
})
const selectedKbDocCount = computed(() => {
  const kb = kbList.value.find(k => k.kb_id === selectedKbId.value)
  return kb?.doc_count
})
const selectedKbChunks = computed(() => {
  const kb = kbList.value.find(k => k.kb_id === selectedKbId.value)
  return kb?.total_chunks
})

async function loadKBList() {
  try {
    const res = await knowledgeApi.getList({ page: 1, size: 100 })
    kbList.value = res?.data?.knowledge_bases || res?.knowledge_bases || []

    // 恢复上次选择
    const lastKb = localStorage.getItem('qa_last_kb')
    if (lastKb && kbList.value.some(k => k.kb_id === lastKb)) {
      selectedKbId.value = lastKb
    } else if (kbList.value.length > 0) {
      selectedKbId.value = kbList.value[0].kb_id
    }
  } catch (e) {
    console.warn('[QA] 加载知识库列表失败:', e.message)
  }
}

function selectKB(kb) {
  selectedKbId.value = kb.kb_id
  localStorage.setItem('qa_last_kb', kb.kb_id)
  showKbDropdown.value = false
}

// 点击外部关闭下拉
function handleOutsideClick(e) {
  if (kbDropdownRef.value && !kbDropdownRef.value.contains(e.target)) {
    showKbDropdown.value = false
  }
}

// -----------------------------------------------------------------------
// 消息与对话
// -----------------------------------------------------------------------

const STORAGE_KEY = 'rag_qa_messages'

const messages = ref(loadMessages())
const inputText = ref('')
const isStreaming = ref(false)
const currentAssistantMsg = ref(null)   // 流式进行中的消息对象引用
const abortController = ref(null)
const errorLog = ref([])
const inputRef = ref(null)
const scrollRef = ref(null)

const quickQuestions = [
  '这份文档的主要内容是什么？',
  '请总结一下关键要点',
  '有哪些重要的数据或指标？',
  '请列出文档中的主要章节',
]

function loadMessages() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
  } catch { return [] }
}

function saveMessages() {
  try {
    // 只保留最近 100 条
    const toSave = messages.value.slice(-100)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave))
  } catch { /* ignore */ }
}

function clearChat() {
  messages.value = []
  localStorage.removeItem(STORAGE_KEY)
}

// -----------------------------------------------------------------------
// 发送消息 & 流式接收
// -----------------------------------------------------------------------

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || !selectedKbId.value || isStreaming.value) return

  // 添加用户消息
  const userMsg = { role: 'user', content: text, time: Date.now() }
  messages.value.push(userMsg)
  inputText.value = ''
  if (inputRef.value) inputRef.value.style.height = 'auto'
  saveMessages()
  await scrollBottom()

  // 创建 assistant 占位消息（含思考链字段）
  // 必须用 reactive() 包装，确保属性变更能触发 Vue 响应式更新
  const assistantMsg = reactive({
    role: 'assistant', content: '', time: Date.now(), streaming: true, sources: [],
    thinking: '', thinkingDone: false, thinkOpen: false,
  })
  messages.value.push(assistantMsg)
  currentAssistantMsg.value = assistantMsg

  // 构建聊天历史
  const history = buildHistory()

  // 开始流式
  isStreaming.value = true
  const controller = new AbortController()
  abortController.value = controller

  try {
    const response = await streamAsk({
      query: text,
      knowledge_base_id: selectedKbId.value,
      top_k: 5,
      use_rerank: true,
      chat_history: history,
      signal: controller.signal,
    })

    if (!response.ok) {
      throw new Error(`服务器错误 (${response.status})`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let fullText = ''
    // 已处理过的 base64 块数量，用于增量解码，避免重复拼接
    let processedThinkChunks = 0

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed.startsWith('data: ')) continue
        const payload = trimmed.slice(6)
        fullText += payload
      }

      // ── 增量解析思考链标记（\x01base64\x01 格式）──
      const thinkRe = /\x01([A-Za-z0-9+/=]+)\x01/g
      const allMatches = [...fullText.matchAll(thinkRe)]
      // 只处理新增的块，用 TextDecoder 正确解码 UTF-8
      for (let i = processedThinkChunks; i < allMatches.length; i++) {
        try {
          const bytes = Uint8Array.from(atob(allMatches[i][1]), c => c.charCodeAt(0))
          assistantMsg.thinking += new TextDecoder('utf-8').decode(bytes)
        } catch {}
      }
      processedThinkChunks = allMatches.length

      // 有思考内容时先渲染"思考中"，再标记结束（延迟一帧让用户看到思考中状态）
      if (fullText.includes('\x02THINK_END\x02') && !assistantMsg.thinkingDone) {
        await nextTick()
        await new Promise(r => setTimeout(r, 300))
        assistantMsg.thinkingDone = true
      }

      // ── 去掉思考链标记，得到干净正文 ────────────────
      let stripped = fullText
        .replace(/\x01[A-Za-z0-9+/=]*\x01/g, '')
        .replace(/\x02THINK_END\x02/g, '')

      // ── 解析 RAG_META ────────────────────────────────
      const metaMatch = stripped.match(/<!--RAG_META\s+([\s\S]*?)\s+RAG_META-->/)
      if (metaMatch) {
        try {
          const meta = JSON.parse(metaMatch[1])
          assistantMsg.sources = meta.citations || []
          assistantMsg.searchResults = meta.search_results || []
        } catch { /* parse error */ }
        assistantMsg.content = stripped.replace(/\n*<!--RAG_META[\s\S]*?RAG_META-->/, '').trimEnd()
      } else {
        assistantMsg.content = stripped
      }

      await nextTick()
      await scrollBottom()
    }

    // 最终清理
    let strippedFinal = fullText
      .replace(/\x01[A-Za-z0-9+/=]*\x01/g, '')
      .replace(/\x02THINK_END\x02/g, '')
    const finalMetaMatch = strippedFinal.match(/<!--RAG_META\s+([\s\S]*?)\s+RAG_META-->/)
    if (finalMetaMatch) {
      try {
        const meta = JSON.parse(finalMetaMatch[1])
        assistantMsg.sources = meta.citations || []
        assistantMsg.searchResults = meta.search_results || []
      } catch { /* parse error */ }
      assistantMsg.content = strippedFinal.replace(/\n*<!--RAG_META[\s\S]*?RAG_META-->/, '').trimEnd()
    } else {
      assistantMsg.content = strippedFinal
    }
    if (!assistantMsg.thinkingDone && assistantMsg.thinking) {
      assistantMsg.thinkingDone = true
    }
    assistantMsg.streaming = false
  } catch (e) {
    if (e.name === 'AbortError') {
      assistantMsg.content += '\n\n*[已中断]*'
    } else {
      assistantMsg.error = e.message || '请求失败'
      errorLog.value.unshift(`[${new Date().toLocaleTimeString()}] ${assistantMsg.error}`)
      if (errorLog.value.length > 20) errorLog.value.pop()
    }
    assistantMsg.streaming = false
  } finally {
    isStreaming.value = false
    currentAssistantMsg.value = null
    abortController.value = null
    saveMessages()
    await scrollBottom()
  }
}

function buildHistory() {
  // 从当前会话中提取最近 6 轮问答作为上下文
  const history = []
  for (const msg of messages.value) {
    if (msg.streaming || msg.error) continue
    if (msg.role === 'user') {
      history.push({ role: 'user', content: msg.content })
    } else if (msg.role === 'assistant') {
      history.push({ role: 'assistant', content: msg.content })
    }
  }
  // 不包含最后一条（正在生成的）
  if (history.length && history[history.length - 1].role === 'assistant') {
    history.pop()
  }
  return history.slice(-12)
}

function askQuick(question) {
  inputText.value = question
  sendMessage()
}

// 中断流式
function cancelStream() {
  if (abortController.value) {
    abortController.value.abort()
  }
}

// -----------------------------------------------------------------------
// 格式化
// -----------------------------------------------------------------------

function formatContent(msg) {
  if (!msg.content) return ''
  let t = msg.content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  // Markdown: **bold**
  t = t.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  // Markdown: `code`
  t = t.replace(/`(.+?)`/g, '<code>$1</code>')
  // 换行
  t = t.replace(/\n/g, '<br>')
  return t
}

function formatTime(ts) {
  const d = new Date(ts)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// -----------------------------------------------------------------------
// 滚动 & 尺寸
// -----------------------------------------------------------------------

async function scrollBottom() {
  await nextTick()
  if (scrollRef.value) {
    scrollRef.value.scrollTop = scrollRef.value.scrollHeight
  }
}

function autoResize() {
  const el = inputRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 150) + 'px'
}

// -----------------------------------------------------------------------
// 生命周期
// -----------------------------------------------------------------------

// -----------------------------------------------------------------------
// 欢迎消息（打字机效果，纯前端，不调用知识库）
// -----------------------------------------------------------------------

async function showWelcomeMessage() {
  const welcomeText = '您好，欢迎使用 PengMind 智能问答！请在上方选择知识库，然后输入您的问题，我会基于知识库内容为您解答。'
  const welcomeMsg = reactive({
    role: 'assistant',
    content: '',
    time: Date.now(),
    streaming: true,
    sources: [],
    thinking: '',
    thinkingDone: false,
    thinkOpen: false,
  })
  messages.value.push(welcomeMsg)
  await nextTick()
  await scrollBottom()

  // 逐字打出
  for (const char of welcomeText) {
    welcomeMsg.content += char
    await new Promise(r => setTimeout(r, 30))
  }
  welcomeMsg.streaming = false
  saveMessages()
}

onMounted(() => {
  loadKBList()
  document.addEventListener('click', handleOutsideClick)
  // 仅在没有历史消息时显示欢迎语
  if (messages.value.length === 0) {
    showWelcomeMessage()
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleOutsideClick)
  cancelStream()
})
</script>

<!-- ================================================================== -->
<style scoped>
.qa-page {
  height: 100vh;
  overflow: hidden;
}

.qa-container {
  display: flex;
  height: 100%;
}

/* ---------- 左侧聊天 ---------- */
.chat-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgba(255,255,255,0.55);
  backdrop-filter: blur(10px);
  min-width: 0;
}

/* --- 头部 --- */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 28px;
  border-bottom: 1px solid rgba(168,230,207,0.3);
  flex-shrink: 0;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--gray-800);
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  width: 28px;
  height: 28px;
  color: var(--primary-dark);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* --- KB 选择器 --- */
.kb-selector { position: relative; }

.kb-selector-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: rgba(255,255,255,0.9);
  border: 1px solid rgba(168,230,207,0.5);
  border-radius: var(--radius-full);
  cursor: pointer;
  font-size: 13px;
  color: var(--gray-700);
  transition: all var(--transition);
  min-width: 150px;
}

.kb-selector-btn:hover {
  border-color: var(--primary);
  background: white;
  box-shadow: var(--shadow-sm);
}

.kb-selector-btn .placeholder { color: var(--gray-400); }
.kb-selector-btn .kb-name { font-weight: 500; color: var(--gray-800); }

.kb-icon { width: 16px; height: 16px; color: var(--primary-dark); flex-shrink: 0; }

.dropdown-arrow {
  width: 14px; height: 14px; color: var(--gray-400);
  transition: transform 0.2s;
}
.dropdown-arrow.open { transform: rotate(180deg); }

.kb-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 260px;
  max-height: 300px;
  overflow-y: auto;
  background: white;
  border: 1px solid rgba(168,230,207,0.4);
  border-radius: var(--radius);
  box-shadow: var(--shadow-lg);
  z-index: 1000;
  animation: fadeIn 0.15s ease;
}

.kb-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  cursor: pointer;
  transition: background 0.15s;
}

.kb-option:hover { background: rgba(168,230,207,0.12); }
.kb-option.selected { background: rgba(168,230,207,0.2); }

.kb-option-info { display: flex; flex-direction: column; gap: 2px; }
.kb-option-name { font-size: 14px; color: var(--gray-800); font-weight: 500; }
.kb-option-meta { font-size: 11px; color: var(--gray-500); }

.check-mark { width: 18px; height: 18px; color: var(--primary-dark); }
.kb-empty { padding: 20px; text-align: center; color: var(--gray-400); font-size: 13px; }

/* --- 消息区 --- */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 28px;
}

/* 欢迎状态 */
.welcome-state {
  text-align: center;
  padding: 60px 20px;
}

.welcome-icon {
  width: 72px; height: 72px;
  background: linear-gradient(135deg, rgba(168,230,207,0.3), rgba(136,216,176,0.3));
  border-radius: var(--radius-full);
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 20px;
  color: var(--primary-dark);
}

.welcome-state h2 { font-size: 22px; color: var(--gray-800); margin-bottom: 8px; }
.welcome-state p { font-size: 14px; color: var(--gray-500); margin-bottom: 28px; }

.quick-questions {
  display: flex; flex-wrap: wrap; justify-content: center; gap: 10px;
  max-width: 520px; margin: 0 auto;
}

.quick-btn {
  padding: 9px 18px;
  background: rgba(255,255,255,0.9);
  border: 1px solid rgba(168,230,207,0.4);
  border-radius: var(--radius-full);
  font-size: 13px; color: var(--gray-600);
  cursor: pointer;
  transition: all var(--transition);
}

.quick-btn:hover {
  background: var(--primary-light);
  border-color: var(--primary);
  color: var(--primary-dark);
  transform: translateY(-1px);
}

/* 消息行 */
.message-row {
  display: flex;
  gap: 14px;
  margin-bottom: 22px;
  animation: fadeIn 0.25s ease;
}

.message-row.user { flex-direction: row-reverse; }

.msg-avatar { flex-shrink: 0; }

.avatar {
  width: 38px; height: 38px;
  border-radius: var(--radius-full);
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 600;
}

.user-avatar-icon {
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: white;
}

.bot-avatar-icon {
  background: linear-gradient(135deg, #52b788, #2d6a4f);
  color: white;
  font-size: 9px;
  letter-spacing: 0.5px;
  border-radius: 10px;
  line-height: 1.2;
  text-align: center;
  padding: 2px;
}

/* 气泡包裹层（含思考链 + 气泡） */
.msg-bubble-wrap {
  display: flex;
  flex-direction: column;
  max-width: 72%;
}
.message-row.user .msg-bubble-wrap { align-items: flex-end; }

.msg-bubble {
  width: 100%;
  padding: 14px 18px;
  border-radius: var(--radius-lg);
  background: rgba(255,255,255,0.95);
  box-shadow: var(--shadow-sm);
  line-height: 1.7;
}

.message-row.user .msg-bubble {
  background: linear-gradient(135deg, var(--primary-light), rgba(136,216,176,0.3));
}

.msg-text {
  font-size: 14px;
  color: var(--gray-800);
  word-break: break-word;
}

.msg-text :deep(code) {
  background: rgba(127,205,205,0.15);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}

.msg-text :deep(strong) {
  font-weight: 600;
  color: var(--gray-900);
}

.msg-error {
  color: var(--error);
  font-size: 13px;
  margin-top: 4px;
}

.msg-time {
  display: block;
  font-size: 11px;
  color: var(--gray-400);
  margin-top: 8px;
}

/* 打字光标 */
.typing-cursor {
  display: inline-block;
  width: 2px; height: 16px;
  background: var(--primary-dark);
  vertical-align: text-bottom;
  animation: blink 0.8s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* 思考中 */
.typing-dots { display: flex; gap: 5px; padding: 6px 0; }
.typing-dots span {
  width: 7px; height: 7px;
  background: var(--primary);
  border-radius: 50%;
  animation: typingBounce 1.4s infinite ease-in-out both;
}
.typing-dots span:nth-child(1) { animation-delay: -0.32s; }
.typing-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typingBounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* 来源引用 */
.msg-sources {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid rgba(168,230,207,0.3);
}

.sources-title {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; font-weight: 600;
  color: var(--primary-dark);
  margin-bottom: 8px;
}

.sources-list { display: flex; flex-wrap: wrap; gap: 8px; }

.source-chip {
  display: flex; align-items: center; gap: 6px;
  padding: 5px 10px;
  background: rgba(168,230,207,0.18);
  border-radius: var(--radius-sm);
  font-size: 11px;
}

.source-doc { color: var(--gray-600); font-family: monospace; }
.source-score { color: var(--primary-dark); font-weight: 600; }

/* --- 输入区 --- */
.input-section {
  padding: 16px 28px 28px;
  border-top: 1px solid rgba(168,230,207,0.3);
  flex-shrink: 0;
}

.input-wrapper {
  display: flex; align-items: flex-end; gap: 10px;
  background: rgba(255,255,255,0.95);
  border: 2px solid rgba(168,230,207,0.4);
  border-radius: var(--radius-xl);
  padding: 10px 16px;
  transition: all var(--transition);
}

.input-wrapper:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 4px rgba(168,230,207,0.2);
}

.input-wrapper.disabled {
  opacity: 0.6;
}

.chat-input {
  flex: 1;
  border: none; background: transparent;
  font-size: 14px; color: var(--gray-800);
  resize: none; outline: none;
  line-height: 1.5;
  max-height: 150px;
  font-family: inherit;
}

.chat-input::placeholder { color: var(--gray-400); }
.chat-input:disabled { cursor: not-allowed; }

.send-btn {
  width: 38px; height: 38px;
  border: none;
  background: var(--gray-200);
  border-radius: var(--radius-full);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  color: var(--gray-400);
  transition: all var(--transition);
  flex-shrink: 0;
}

.send-btn.ready {
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: white;
  box-shadow: var(--shadow);
}

.send-btn.ready:hover { transform: scale(1.06); box-shadow: var(--shadow-lg); }
.send-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.input-hint {
  text-align: center;
  margin-top: 6px;
  font-size: 11px;
  color: var(--gray-400);
}

/* ---------- 右侧面板 ---------- */
.sidebar-section {
  width: 300px;
  background: rgba(255,255,255,0.7);
  backdrop-filter: blur(10px);
  border-left: 1px solid rgba(168,230,207,0.3);
  padding: 22px;
  overflow-y: auto;
  flex-shrink: 0;
}

.info-card {
  background: rgba(255,255,255,0.85);
  border-radius: var(--radius);
  padding: 18px;
  margin-bottom: 16px;
  box-shadow: var(--shadow-sm);
  border: 1px solid rgba(168,230,207,0.25);
}

.card-title {
  font-size: 14px; font-weight: 600;
  color: var(--gray-800);
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 14px;
}

.card-title svg { color: var(--primary-dark); }

.info-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--gray-100);
  font-size: 13px;
  color: var(--gray-500);
}

.info-row:last-child { border-bottom: none; }

.info-val { font-weight: 600; color: var(--gray-800); }
.info-val.ok { color: var(--success); }

.info-hint { font-size: 13px; color: var(--gray-400); line-height: 1.6; }

.btn-small { width: 100%; padding: 8px 12px; font-size: 12px; margin-top: 10px; }

.tips-list { list-style: none; padding: 0; }
.tips-list li {
  font-size: 12px; color: var(--gray-600);
  padding: 6px 0 6px 16px;
  position: relative;
}
.tips-list li::before {
  content: '•'; position: absolute; left: 0;
  color: var(--primary);
  font-weight: bold;
}

/* 错误卡片 */
.error-card { border-color: rgba(229,115,115,0.3); }
.error-title { color: var(--error) !important; }
.error-line {
  font-size: 11px; color: var(--error);
  padding: 4px 0;
  border-bottom: 1px solid rgba(229,115,115,0.1);
  word-break: break-all;
}

/* ---------- 思考链 ---------- */
.think-block {
  margin-bottom: 6px;
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

.think-dots-sm { display: flex; gap: 3px; align-items: center; }
.think-dots-sm span {
  width: 5px; height: 5px; background: #74c69d; border-radius: 50%;
  animation: typingBounce 1.4s infinite ease-in-out both;
}
.think-dots-sm span:nth-child(1) { animation-delay: -0.32s; }
.think-dots-sm span:nth-child(2) { animation-delay: -0.16s; }

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
  opacity: 0.75;
  max-height: 260px;
  overflow-y: auto;
}
.think-content:hover { opacity: 0.92; }

.think-text {
  font-size: 12px;
  color: #52b788;
  line-height: 1.7;
  word-break: break-word;
  font-family: 'Courier New', monospace;
}

/* ---------- 响应式 ---------- */
@media (max-width: 1024px) {
  .sidebar-section { display: none; }
}

@media (max-width: 768px) {
  .chat-header { padding: 14px 16px; }
  .messages-container { padding: 16px; }
  .msg-bubble { max-width: 88%; }
  .input-section { padding: 12px 16px 20px; }
}
</style>
