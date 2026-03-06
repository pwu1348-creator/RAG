/**
 * QA Service API - 问答检索服务 (端口 8002)
 */

import axios from 'axios'

// 创建 qa 专用 axios 实例
const qaApi = axios.create({
  baseURL: '/api/qa',
  timeout: 60000, // 1分钟，问答可能需要较长时间
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
qaApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
qaApi.interceptors.response.use(
  (response) => response.data,
  (error) => Promise.reject(error)
)

/**
 * 单轮问答
 * @param {Object} data
 * @param {string} data.question - 问题
 * @param {string[]} data.knowledgeBaseIds - 知识库ID列表
 * @param {string} data.conversationId - 对话ID（可选）
 * @param {number} data.topK - 检索数量
 */
export function askQuestion(data) {
  return qaApi.post('/qa/ask', data)
}

/**
 * 流式问答
 * @param {Object} data
 * @param {string} data.question - 问题
 * @param {string[]} data.knowledgeBaseIds - 知识库ID列表
 */
export function streamAsk(data) {
  return fetch('/api/qa/qa/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
    },
    body: JSON.stringify(data)
  })
}

/**
 * 创建新对话
 * @param {string} title - 对话标题
 */
export function createConversation(title = '新对话') {
  return qaApi.post('/chat/conversations', null, { params: { title } })
}

/**
 * 获取对话列表
 */
export function getConversationList() {
  return qaApi.get('/chat/conversations')
}

/**
 * 发送消息
 * @param {string} conversationId - 对话ID
 * @param {Object} data
 * @param {string} data.message - 消息内容
 * @param {string[]} data.knowledgeBaseIds - 知识库ID列表
 */
export function sendMessage(conversationId, data) {
  return qaApi.post(`/chat/conversations/${conversationId}/messages`, data)
}

/**
 * 知识库检索
 * @param {Object} data
 * @param {string} data.query - 查询文本
 * @param {string[]} data.knowledgeBaseIds - 知识库ID列表
 * @param {number} data.topK - 返回数量
 */
export function searchKnowledgeBase(data) {
  return qaApi.post('/search/', data)
}

/**
 * 获取知识库列表
 */
export function getKnowledgeBaseList() {
  return qaApi.get('/knowledge-base/')
}

/**
 * 获取知识库状态
 * @param {string} kbId - 知识库ID
 */
export function getKnowledgeBaseStatus(kbId) {
  return qaApi.get(`/knowledge-base/${kbId}/status`)
}

/**
 * 健康检查
 */
export function healthCheck() {
  return qaApi.get('/health')
}

export default qaApi
