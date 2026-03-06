<template>
  <div class="layout">
    <FallingLeaves />
    <Sidebar />
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import Sidebar from './Sidebar.vue'
import FallingLeaves from './FallingLeaves.vue'
</script>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  margin-left: 260px;
  padding: 0;
  min-height: 100vh;
  position: relative;
  z-index: 1;
}

/* 页面切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateX(10px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}

/* 响应式 */
@media (max-width: 768px) {
  .main-content {
    margin-left: 0;
    padding-top: 60px;
  }
}
</style>
