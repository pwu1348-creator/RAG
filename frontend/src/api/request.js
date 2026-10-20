import axios from 'axios'
import { useUserStore } from '../stores'

// 创建 axios 实例
const request = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    console.log('Request:', config.method, config.url)
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
      console.log('Added token to request')
    }
    // FormData 需要让 axios 自动设置 Content-Type（含 boundary），否则后端无法解析
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    const { data } = response
    if (data.code !== 200) {
      // 处理业务错误
      return Promise.reject(new Error(data.message || '请求失败'))
    }
    return data
  },
  (error) => {
    const { response, config } = error
    
    if (response && response.data) {
      const backendMessage = response.data.message || response.data.msg || ''
      // 登录接口的 401 不做跳转，让页面自行处理错误提示
      const isLoginRequest = config && config.url && config.url.includes('/login')
      switch (response.status) {
        case 401:
          if (isLoginRequest) {
            return Promise.reject(new Error(backendMessage || '账号或密码错误'))
          }
          const userStore = useUserStore()
          userStore.logout()
          window.location.href = '/login'
          break
        case 403:
          return Promise.reject(new Error(backendMessage || '没有权限访问该资源'))
        case 404:
          return Promise.reject(new Error(backendMessage || '请求的资源不存在'))
        case 500:
          return Promise.reject(new Error(backendMessage || '服务器内部错误'))
        default:
          return Promise.reject(new Error(backendMessage || `请求失败: ${response.status}`))
      }
    } else if (error.request) {
      return Promise.reject(new Error('网络错误，请检查网络连接'))
    } else {
      return Promise.reject(new Error(error.message || '请求失败'))
    }
  }
)

export default request
