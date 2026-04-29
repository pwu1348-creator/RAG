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
 *   POST /index/kb/{id}   → 重索知识库
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
 */
export function ask({ query, knowledge_base_id, top_k = 10, use_rerank = true, chat_history = null }) {
  return qaApi.post('/search/ask', {
    query,
    knowledge_base_id,
    top_k,
    use_rerank,
    chat_history: chat_history?.slice(-10) ?? null,
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
      top_k,
      use_rerank,
      chat_history: chat_history?.slice(-10) ?? null,
    }),
    ...(signal ? { signal } : {}),
  })
}

// ---------------------------------------------------------------------------
// 撰写模式
// ---------------------------------------------------------------------------

/** 撰写模式（非流式） */
export function writeChat({ query, knowledge_base_id, top_k = 10, use_rerank = true }) {
  return qaApi.post('/search/writechat', { query, knowledge_base_id, top_k, use_rerank })
}

/** 撰写模式（流式） */
export function streamWriteChat({
  query,
  knowledge_base_id,
  top_k = 10,
  use_rerank = true,
}) {
  const token = localStorage.getItem('token') || ''
  return fetch('/api/qa/search/writechat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ query, knowledge_base_id, top_k, use_rerank }),
  })
}

// ---------------------------------------------------------------------------
// 索引管理
// ---------------------------------------------------------------------------

/** 重索整个知识库 */
export function reindexKB(kbId) {
  return qaApi.post(`/search/index/kb/${kbId}`)
}

/** 重索单个文档 */
export function reindexDoc(kbId, docId) {
  return qaApi.post(`/search/index/doc/${kbId}/${docId}`)
}

// ---------------------------------------------------------------------------
// 辅助
// ---------------------------------------------------------------------------

/** 健康检查 */
export function healthCheck() {
  return qaApi.get('/search/health')
}

export default qaApi
