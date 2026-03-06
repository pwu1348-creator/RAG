import request from './request'

export const userApi = {
  // 管理员登录
  login(data) {
    return request.post('/auth/admin/login', data)
  },

  // 用户注册
  register(data) {
    return request.post('/auth/register', data)
  },

  // 获取当前用户信息
  getUserInfo() {
    return request.get('/user/info')
  },

  // 更新用户信息
  updateUserInfo(data) {
    return request.put('/user/info', data)
  },

  // 获取用户列表
  getUserList(params) {
    return request.get('/users', { params })
  },

  // 创建用户
  createUser(data) {
    return request.post('/users', data)
  },

  // 更新用户
  updateUser(id, data) {
    return request.put(`/users/${id}`, data)
  },

  // 删除用户
  deleteUser(id) {
    return request.delete(`/users/${id}`)
  },

  // 修改密码
  changePassword(data) {
    return request.post('/user/change-password', data)
  }
}
