import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  // State
  const sidebarCollapsed = ref(false)
  const theme = ref(localStorage.getItem('theme') || 'light')
  const loading = ref(false)
  const notifications = ref([])

  // Actions
  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  const setTheme = (newTheme) => {
    theme.value = newTheme
    localStorage.setItem('theme', newTheme)
    document.documentElement.setAttribute('data-theme', newTheme)
  }

  const setLoading = (status) => {
    loading.value = status
  }

  const addNotification = (notification) => {
    const id = Date.now()
    notifications.value.push({
      id,
      type: 'info',
      duration: 3000,
      ...notification
    })
    
    if (notification.duration !== 0) {
      setTimeout(() => {
        removeNotification(id)
      }, notification.duration || 3000)
    }
    
    return id
  }

  const removeNotification = (id) => {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index > -1) {
      notifications.value.splice(index, 1)
    }
  }

  const success = (message) => {
    return addNotification({ type: 'success', message })
  }

  const error = (message) => {
    return addNotification({ type: 'error', message })
  }

  const warning = (message) => {
    return addNotification({ type: 'warning', message })
  }

  const info = (message) => {
    return addNotification({ type: 'info', message })
  }

  return {
    sidebarCollapsed,
    theme,
    loading,
    notifications,
    toggleSidebar,
    setTheme,
    setLoading,
    addNotification,
    removeNotification,
    success,
    error,
    warning,
    info
  }
})
