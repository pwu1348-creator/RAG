import { reactive } from 'vue'

const state = reactive({
  toasts: []
})

let id = 0

function showToast(message, type = 'success', duration = 3000) {
  const toast = { id: ++id, message, type }
  state.toasts.push(toast)
  setTimeout(() => {
    const idx = state.toasts.findIndex(t => t.id === toast.id)
    if (idx !== -1) state.toasts.splice(idx, 1)
  }, duration)
}

export function useToast() {
  return { toasts: state.toasts, showToast }
}
