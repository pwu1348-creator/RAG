import request from './request'

/**
 * 文件解析 API
 */
export const parserApi = {
  // 上传文件
  upload(file, knowledgeBaseId = null, options = {}) {
    const formData = new FormData()
    formData.append('file', file)
    if (knowledgeBaseId) {
      formData.append('knowledge_base_id', knowledgeBaseId)
    }
    formData.append('options', JSON.stringify(options))

    return request.post('/parser/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 获取任务状态
  getTaskStatus(taskId) {
    return request.get(`/parser/task/${taskId}`)
  },

  // 删除任务
  deleteTask(taskId) {
    return request.delete(`/parser/task/${taskId}`)
  },

  // 获取任务列表
  getTaskList(params = {}) {
    return request.get('/parser/tasks', { params })
  },

  // 获取文档列表
  getDocumentList(params = {}) {
    return request.get('/parser/documents', { params })
  },

  // 获取文档详情
  getDocumentDetail(docId) {
    return request.get(`/parser/document/${docId}`)
  },

  // 删除文档
  deleteDocument(docId) {
    return request.delete(`/parser/document/${docId}`)
  },

  // 获取支持格式
  getSupportedFormats() {
    return request.get('/parser/supported-formats')
  }
}

export default parserApi
