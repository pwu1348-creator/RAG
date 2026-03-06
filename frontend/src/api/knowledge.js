import request from './request'

/**
 * 知识库管理 API
 */
export const knowledgeApi = {
  // ==================== 知识库管理 ====================
  
  // 获取知识库列表
  getList(params) {
    return request.get('/knowledge-bases', { params })
  },

  // 创建知识库
  create(data) {
    return request.post('/knowledge-bases', data)
  },

  // 获取知识库详情
  getDetail(id) {
    return request.get(`/knowledge-bases/${id}`)
  },

  // 更新知识库
  update(id, data) {
    return request.put(`/knowledge-bases/${id}`, data)
  },

  // 删除知识库（仅删除元数据）
  delete(id) {
    return request.delete(`/knowledge-bases/${id}`)
  },

  // 删除知识库集合（删除整个ChromaDB集合，危险操作）
  deleteCollection(id) {
    return request.delete(`/knowledge-bases/${id}/collection`)
  },

  // ==================== 知识库用户管理 ====================
  
  // 获取知识库用户列表
  getUsers(kbId, params) {
    return request.get(`/knowledge-bases/${kbId}/users`, { params })
  },

  // 添加用户到知识库
  addUser(kbId, userId, role = 'viewer') {
    return request.post(`/knowledge-bases/${kbId}/users`, { user_id: userId, role })
  },

  // 更新用户角色
  updateUserRole(kbId, userId, role) {
    return request.put(`/knowledge-bases/${kbId}/users/${userId}`, { role })
  },

  // 移除用户
  removeUser(kbId, userId) {
    return request.delete(`/knowledge-bases/${kbId}/users/${userId}`)
  },

  // 获取用户的知识库
  getUserKnowledgeBases(userId, params) {
    return request.get(`/knowledge-bases/users/${userId}/kbs`, { params })
  },

  // ==================== 知识库文档管理 ====================
  
  // 获取知识库中的文档列表
  getDocuments(kbId, params) {
    return request.get(`/knowledge-bases/${kbId}/documents`, { params })
  },

  // 获取文档详情（包含所有片段）
  getDocumentDetail(kbId, docId) {
    return request.get(`/knowledge-bases/${kbId}/documents/${docId}`)
  },

  // 删除知识库中的文档（从ChromaDB中删除）
  deleteDocument(kbId, docId) {
    return request.delete(`/knowledge-bases/${kbId}/documents/${docId}`)
  },

  // 上传文件到知识库（待解析状态）
  uploadDocument(kbId, file) {
    const formData = new FormData()
    formData.append('file', file)
    return request.post(`/knowledge-bases/${kbId}/documents`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 解析知识库中的文档
  parseDocument(kbId, docId) {
    return request.post(`/knowledge-bases/${kbId}/documents/${docId}/parse`)
  },

  // 批量解析知识库中的文档
  parseDocuments(kbId, docIds) {
    return request.post(`/knowledge-bases/${kbId}/documents/parse`, { doc_ids: docIds })
  },

  // ==================== 知识库文件关联 ====================
  
  // 获取未关联到知识库的文件列表
  getUnlinkedFiles(params) {
    return request.get('/knowledge-bases/files/unlinked', { params })
  },

  // 关联文件到知识库
  associateFile(kbId, docId) {
    return request.post(`/knowledge-bases/${kbId}/files/${docId}`)
  },

  // 从知识库移除文件（取消关联）
  removeFile(kbId, docId) {
    return request.delete(`/knowledge-bases/${kbId}/files/${docId}`)
  }
}

export default knowledgeApi
