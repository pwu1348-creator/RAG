<template>
  <div class="falling-leaves">
    <div
      v-for="leaf in leaves"
      :key="leaf.id"
      class="leaf"
      :style="getLeafStyle(leaf)"
    >
      <svg viewBox="0 0 24 24" fill="currentColor">
        <path d="M17,8C8,10 5.9,16.17 3.82,21.34L5.71,22L6.66,19.7C7.14,19.87 7.64,20 8,20C19,20 22,3 22,3C21,5 14,5.25 9,6.25C4,7.25 2,11.5 2,13.5C2,15.5 3.75,17.25 3.75,17.25C7,8 17,8 17,8Z"/>
      </svg>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  count: {
    type: Number,
    default: 15
  },
  interval: {
    type: Number,
    default: 2000
  }
})

const leaves = ref([])
let leafId = 0
let intervalId = null

// 叶子颜色配置 - 清新自然色系
const leafColors = [
  '#a8e6cf', // 浅绿
  '#7fcdcd', // 青绿
  '#88d8b0', // 薄荷绿
  '#98d8c8', // 青 cyan
  '#b4e7ce', // 淡青绿
  '#c8e6c9', // 浅翠绿
  '#dcedc8', // 嫩芽绿
]

const createLeaf = () => {
  const id = leafId++
  const leaf = {
    id,
    left: Math.random() * 100,
    delay: Math.random() * 2,
    duration: 12 + Math.random() * 8,
    size: 16 + Math.random() * 20,
    color: leafColors[Math.floor(Math.random() * leafColors.length)],
    rotation: Math.random() * 360,
    swayAmount: 30 + Math.random() * 50,
  }
  
  leaves.value.push(leaf)
  
  // 动画结束后移除叶子
  setTimeout(() => {
    leaves.value = leaves.value.filter(l => l.id !== id)
  }, leaf.duration * 1000)
}

const getLeafStyle = (leaf) => {
  return {
    left: `${leaf.left}%`,
    width: `${leaf.size}px`,
    height: `${leaf.size}px`,
    color: leaf.color,
    animationDuration: `${leaf.duration}s`,
    animationDelay: `${leaf.delay}s`,
    '--rotation': `${leaf.rotation}deg`,
    '--sway-amount': `${leaf.swayAmount}px`,
  }
}

onMounted(() => {
  // 初始创建一些叶子
  for (let i = 0; i < props.count; i++) {
    setTimeout(createLeaf, i * 300)
  }
  
  // 持续创建新叶子
  intervalId = setInterval(createLeaf, props.interval)
})

onUnmounted(() => {
  if (intervalId) {
    clearInterval(intervalId)
  }
})
</script>

<style scoped>
.falling-leaves {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.leaf {
  position: absolute;
  top: -60px;
  opacity: 0.7;
  animation-name: fall, sway;
  animation-timing-function: linear, ease-in-out;
  animation-iteration-count: 1, infinite;
  filter: drop-shadow(1px 1px 2px rgba(0, 0, 0, 0.1));
}

.leaf svg {
  width: 100%;
  height: 100%;
}

@keyframes fall {
  0% {
    transform: translateY(0) rotate(var(--rotation, 0deg));
    opacity: 0;
  }
  10% {
    opacity: 0.5;
  }
  100% {
    transform: translateY(calc(100vh + 60px)) rotate(calc(var(--rotation, 0deg) + 360deg));
    opacity: 0.5;
  }
}

@keyframes sway {
  0%, 100% {
    margin-left: 0;
  }
  25% {
    margin-left: var(--sway-amount, 30px);
  }
  75% {
    margin-left: calc(var(--sway-amount, 30px) * -1);
  }
}
</style>
