import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { userApi } from '../api/user'
import { hashPassword } from '../utils/crypto'

export const useUserStore = defineStore('user', () => {
  // State
  const userInfo = ref(null)
  const token = ref(localStorage.getItem('token') || '')
  const error = ref('')
  const isLoggedIn = computed(() => !!token.value && !!userInfo.value)

  // Actions
  const setUserInfo = (data) => {
    userInfo.value = data
  }

  const setToken = (newToken) => {
    token.value = newToken
    if (newToken) {
      localStorage.setItem('token', newToken)
    } else {
      localStorage.removeItem('token')
    }
  }

  const login = async (credentials) => {
    error.value = ''
    try {
      // 前端密码加密：SHA-256 哈希后再传输
      const encryptedPassword = await hashPassword(credentials.password)
      const encryptedCredentials = {
        username: credentials.username,
        password: encryptedPassword
      }
      console.log('Login request (password encrypted)')
      const response = await userApi.login(encryptedCredentials)
      console.log('Login response:', response)
      if (response.code === 200 && response.data && response.data.success) {
        console.log('Login success, setting token:', response.data.token)
        setToken(response.data.token)
        setUserInfo(response.data.admin || response.data.user)
        return { success: true }
      } else {
        error.value = response.message || response.data?.message || '登录失败'
        return { success: false, error: error.value }
      }
    } catch (err) {
      console.error('Login error:', err)
      error.value = err.message || '网络错误'
      return { success: false, error: error.value }
    }
  }

  const logout = () => {
    userInfo.value = null
    setToken('')
    localStorage.removeItem('admin_info')
  }

  const fetchUserInfo = async () => {
    if (token.value) {
      try {
        const response = await userApi.getUserInfo()
        if (response.data) {
          setUserInfo(response.data)
        }
      } catch (err) {
        console.error('Failed to fetch user info:', err)
      }
    }
  }

  return {
    userInfo,
    token,
    error,
    isLoggedIn,
    setUserInfo,
    setToken,
    login,
    logout,
    fetchUserInfo
  }
})
