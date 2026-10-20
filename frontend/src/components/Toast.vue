<template>
  <div class="toast-container">
    <transition-group name="toast">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        :class="['toast-item', toast.type]"
      >
        <svg v-if="toast.type === 'success'" class="toast-icon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12,2C17.52,2 22,6.48 22,12C22,17.52 17.52,22 12,22C6.48,22 2,17.52 2,12C2,6.48 6.48,2 12,2M11,16.5L18,9.5L16.59,8.09L11,13.67L7.91,10.59L6.5,12L11,16.5Z"/>
        </svg>
        <svg v-else-if="toast.type === 'error'" class="toast-icon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12,2C17.53,2 22,6.47 22,12C22,17.53 17.53,22 12,22C6.47,22 2,17.53 2,12C2,6.47 6.47,2 12,2M15.59,7L12,10.59L8.41,7L7,8.41L10.59,12L7,15.59L8.41,17L12,13.41L15.59,17L17,15.59L13.41,12L17,8.41L15.59,7Z"/>
        </svg>
        <svg v-else-if="toast.type === 'warning'" class="toast-icon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M13,14H11V10H13M13,18H11V16H13M1,21H23L12,2L1,21Z"/>
        </svg>
        <svg v-else class="toast-icon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M13,9H11V7H13M13,17H11V11H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z"/>
        </svg>
        <span class="toast-msg">{{ toast.message }}</span>
        <!-- 进度条 -->
        <div class="toast-progress" :class="toast.type">
          <div class="toast-progress-bar" :style="{ animationDuration: '3s' }"></div>
        </div>
      </div>
    </transition-group>
  </div>
</template>

<script setup>
import { useToast } from '@/utils/toast'
const { toasts } = useToast()
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 99999;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  pointer-events: none;
}

.toast-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 24px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.08);
  backdrop-filter: blur(12px);
  pointer-events: auto;
  position: relative;
  overflow: hidden;
}

.toast-item.success {
  background: rgba(240, 253, 244, 0.97);
  color: #166534;
  border: 1px solid #bbf7d0;
}

.toast-item.error {
  background: rgba(254, 242, 242, 0.97);
  color: #991b1b;
  border: 1px solid #fecaca;
}

.toast-item.warning {
  background: rgba(255, 251, 235, 0.97);
  color: #92400e;
  border: 1px solid #fde68a;
}

.toast-item.info {
  background: rgba(239, 246, 255, 0.97);
  color: #1e40af;
  border: 1px solid #bfdbfe;
}

.toast-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.toast-msg {
  white-space: nowrap;
}

/* 底部进度条 */
.toast-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: transparent;
  overflow: hidden;
  border-radius: 0 0 12px 12px;
}

.toast-progress-bar {
  height: 100%;
  width: 100%;
  transform-origin: left;
  animation: progressShrink 3s linear forwards;
}

.toast-progress.success .toast-progress-bar {
  background: linear-gradient(90deg, #22c55e, #16a34a);
}

.toast-progress.error .toast-progress-bar {
  background: linear-gradient(90deg, #ef4444, #dc2626);
}

.toast-progress.warning .toast-progress-bar {
  background: linear-gradient(90deg, #f59e0b, #d97706);
}

.toast-progress.info .toast-progress-bar {
  background: linear-gradient(90deg, #3b82f6, #2563eb);
}

@keyframes progressShrink {
  from { transform: scaleX(1); }
  to { transform: scaleX(0); }
}

/* 入场动画：从上方滑入 + 缩放 */
.toast-enter-active {
  transition: all 0.4s cubic-bezier(0.21, 1.02, 0.73, 1);
}

/* 离场动画：向上淡出 */
.toast-leave-active {
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.toast-enter-from {
  opacity: 0;
  transform: translateY(-20px) scale(0.9);
}

.toast-leave-to {
  opacity: 0;
  transform: translateY(-18px) scale(0.92);
}

/* 列表移动动画 */
.toast-move {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
</style>
