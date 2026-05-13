/**
 * 问答检索服务 API — 对接 search_and_ask 后端 (端口 8002)
 *
 * Vite 代理: /api/qa → http://localhost:8002, 路径重写 /api/qa → /api/v1
 *
 * 后端路由前缀: /api/v1/search
 *   POST /search          → 纯检索
 *   POST /ask             → 问答（非流式）
 *   POST /ask/stream      → 问答（SSE 流式）
 *   POST /writechat       → 撰写模式（非流式）
 *   POST /writechat/stream→ 撰写模式（SSE 流式）
 */

import axios from 'axios'

// ---------------------------------------------------------------------------
// axios 实例
// ---------------------------------------------------------------------------

const qaApi = axios.create({
  baseURL: '/api/qa',          // → proxy → http://localhost:8002/api/v1
  timeout: 120000,             // 问答可能较慢，设 2 分钟
  headers: { 'Content-Type': 'application/json' },
})

qaApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

qaApi.interceptors.response.use(
  (res) => res.data,
  (err) => Promise.reject(err),
)

// ---------------------------------------------------------------------------
// 检索（不调 LLM）
// ---------------------------------------------------------------------------

/**
 * 纯检索：返回父块内容，不生成回答
 */
export function searchChunks({ query, knowledge_base_id, top_k = 10, use_rerank = true }) {
  return qaApi.post('/search/search', { query, knowledge_base_id, top_k, use_rerank })
}

// ---------------------------------------------------------------------------
// 非流式问答
// ---------------------------------------------------------------------------

/**
 * 标准问答（非流式）
 * @returns {{ answer, citations, search_results, timestamp }}
 *
 * 注意：历史截断已统一由后端 qa.py 管控，此处不再截断。
 */
export function ask({ query, knowledge_base_id, top_k = 10, use_rerank = true, chat_history = null, answer_mode = 'strict' }) {
  return qaApi.post('/search/ask', {
    query,
    knowledge_base_id,
    top_k,
    use_rerank,
    chat_history: chat_history ?? null,
    answer_mode,
  })
}

// ---------------------------------------------------------------------------
// 流式问答（核心接口）
// ---------------------------------------------------------------------------

/**
 * 流式问答（SSE）— 返回 fetch Response 供 ReadableStream 消费
 *
 * 用法:
 *   const resp = await streamAsk({ query, knowledge_base_id, ... })
 *   const reader = resp.body.getReader()
 *   // 逐块读取 SSE 事件
 *
 * SSE 格式:
 *   data: {token}
 *   ...
 *   data: <!--RAG_META {...} RAG_META-->
 */
export function streamAsk({
  query,
  knowledge_base_id,
  top_k = 10,
  use_rerank = true,
  chat_history = null,
  signal = null,
  answer_mode = 'strict',
}) {
  const token = localStorage.getItem('token') || ''
  return fetch('/api/qa/search/ask/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    // 历史截断统一由后端 qa.py 管控，此处完整透传
    body: JSON.stringify({
      query,
      knowledge_base_id,
      top_k,
      use_rerank,
      chat_history: chat_history ?? null,
      answer_mode,
    }),
    ...(signal ? { signal } : {}),
  })
}


// ---------------------------------------------------------------------------
// 对话持久化管理（conversation_id 模式）
// ---------------------------------------------------------------------------

/**
 * 创建新会话，返回 { conversation_id }
 * @param {string} userId  用户ID，管理员传 "admin"
 * @param {string} kbId    知识库ID
 * @param {string} title   会话标题（可选）
 */
export function createConversation({ userId, kbId, title = '新对话' }) {
  return qaApi.post('/search/conversation/create', {
    user_id: userId,
    kb_id: kbId,
    title,
  })
}

/**
 * 获取用户的会话列表
 */
export function listConversations({ userId, page = 1, size = 50 }) {
  return qaApi.get('/search/conversation/list', {
    params: { user_id: userId, page, size },
  })
}

/**
 * 获取会话详情 + 完整消息列表
 */
export function getConversation(conversationId) {
  return qaApi.get(`/search/conversation/${conversationId}`)
}

/**
 * 删除会话
 */
export function deleteConversation(conversationId) {
  return qaApi.delete(`/search/conversation/${conversationId}`)
}

/**
 * 更新会话标题
 */
export function updateConversationTitle(conversationId, title) {
  return qaApi.put(`/search/conversation/${conversationId}/title`, { title })
}

/**
 * 流式问答（支持 conversation_id 持久化模式）
 * 传入 conversationId 时：后端自动从数据库加载历史并保存消息
 * 不传时：退回 chat_history 兼容模式
 */
export function streamAskWithConv({
  query,
  knowledge_base_id,
  conversation_id = null,
  top_k = 10,
  use_rerank = true,
  chat_history = null,
  signal = null,
  answer_mode = 'strict',
}) {
  const token = localStorage.getItem('token') || ''
  return fetch('/api/qa/search/ask/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      query,
      knowledge_base_id,
      conversation_id,
      top_k,
      use_rerank,
      // 兼容旧模式：不传 conversation_id 时使用 chat_history
      chat_history: conversation_id ? null : (chat_history ?? null),
      answer_mode,
    }),
    ...(signal ? { signal } : {}),
  })
}

// ---------------------------------------------------------------------------
// 辅助
// ---------------------------------------------------------------------------

/** 健康检查 */
export function healthCheck() {
  return qaApi.get('/search/health')
}

export default qaApi
