import request from './request'

/**
 * 管理员认证 API
 */
export const adminAuthApi = {
  // 管理员登录
  login(data) {
    return request.post('/auth/admin/login', data)
  },

  // 管理员注册
  register(data) {
    return request.post('/auth/admin/register', data)
  },

  // 登出
  logout() {
    return request.post('/auth/logout')
  }
}

/**
 * 管理员管理 API
 */
export const adminApi = {
  // 获取仪表盘统计
  getDashboard() {
    return request.get('/admin/dashboard')
  },

  // 获取存储的统计数据
  getStatistics() {
    return request.get('/admin/statistics')
  },

  // 同步统计数据
  syncStatistics() {
    return request.post('/admin/statistics/sync')
  },

  // 获取用户列表
  getUserList(params) {
    return request.get('/admin/users', { params })
  },

  // 创建用户
  createUser(data) {
    return request.post('/admin/users', data)
  },

  // 获取用户详情
  getUserDetail(id) {
    return request.get(`/admin/users/${id}`)
  },

  // 更新用户
  updateUser(id, data) {
    return request.put(`/admin/users/${id}`, data)
  },

  // 重置用户密码
  resetUserPassword(id, newPassword) {
    return request.post(`/admin/users/${id}/password`, { new_password: newPassword })
  },

  // 锁定用户
  lockUser(id) {
    return request.post(`/admin/users/${id}/lock`)
  },

  // 解锁用户
  unlockUser(id) {
    return request.post(`/admin/users/${id}/unlock`)
  },

  // 删除用户
  deleteUser(id) {
    return request.delete(`/admin/users/${id}`)
  },

  // 上传用户头像
  uploadAvatar(userId, file) {
    const formData = new FormData()
    formData.append('file', file)
    return request.post(`/admin/users/${userId}/avatar`, formData)
  },

  // 获取管理员列表
  getAdminList(params) {
    return request.get('/admin/admins', { params })
  },

  // 创建管理员
  createAdmin(data) {
    return request.post('/admin/admins', data)
  },

  // 获取管理员详情
  getAdminDetail(id) {
    return request.get(`/admin/admins/${id}`)
  },

  // 更新管理员
  updateAdmin(id, data) {
    return request.put(`/admin/admins/${id}`, data)
  },

  // 删除管理员
  deleteAdmin(id) {
    return request.delete(`/admin/admins/${id}`)
  }
}

/**
 * 知识库管理 API
 */
export const knowledgeBaseApi = {
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

  // 删除知识库
  delete(id) {
    return request.delete(`/knowledge-bases/${id}`)
  },

  // 获取知识库用户列表
  getUsers(kbId, params) {
    return request.get(`/knowledge-bases/${kbId}/users`, { params })
  },

  // 添加用户到知识库
  addUser(kbId, data) {
    return request.post(`/knowledge-bases/${kbId}/users`, data)
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
  }
}

/**
 * 系统设置 API
 */
export const settingsApi = {
  // 获取所有设置
  getAll() {
    return request.get('/settings')
  },

  // 获取分类设置
  getByCategory(category) {
    return request.get(`/settings/${category}`)
  },

  // 获取具体设置
  getSetting(category, key) {
    return request.get(`/settings/${category}/${key}`)
  },

  // 更新设置
  updateSetting(category, key, data) {
    return request.put(`/settings/${category}/${key}`, data)
  },

  // 批量更新设置
  updateBatch(settings) {
    return request.put('/settings/batch', { settings })
  },

  // 获取系统信息
  getSystemInfo() {
    return request.get('/settings/system-info')
  },

  // 获取 API 配置列表
  getApiConfigs(params) {
    return request.get('/settings/api-configs', { params })
  },

  // 创建 API 配置
  createApiConfig(data) {
    return request.post('/settings/api-configs', data)
  },

  // 获取 API 配置详情
  getApiConfig(id, includeKey = false) {
    return request.get(`/settings/api-configs/${id}`, { params: { include_key: includeKey } })
  },

  // 更新 API 配置
  updateApiConfig(id, data) {
    return request.put(`/settings/api-configs/${id}`, data)
  },

  // 删除 API 配置
  deleteApiConfig(id) {
    return request.delete(`/settings/api-configs/${id}`)
  },

  // 设为默认 API 配置
  setDefaultApiConfig(id) {
    return request.post(`/settings/api-configs/${id}/default`)
  },

  // 获取检索设置
  getRetrievalSettings(kbId) {
    return request.get('/settings/retrieval', { params: { kb_id: kbId } })
  },

  // 更新检索设置
  updateRetrievalSettings(data) {
    return request.put('/settings/retrieval', data)
  }
}
