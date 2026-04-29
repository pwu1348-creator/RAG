<template>
  <div class="mud-man-wrapper" :style="wrapperStyle">
    <svg
      viewBox="0 0 120 180"
      xmlns="http://www.w3.org/2000/svg"
      class="mud-svg"
      ref="svgRef"
    >
      <!-- 身体阴影 -->
      <ellipse cx="60" cy="174" rx="28" ry="7" fill="rgba(0,0,0,0.15)" />

      <!-- 腿 -->
      <!-- 左腿 -->
      <rect x="38" y="128" width="16" height="36" rx="8" fill="#8B6914" />
      <!-- 右腿 -->
      <rect x="66" y="128" width="16" height="36" rx="8" fill="#8B6914" />
      <!-- 左脚 -->
      <ellipse cx="46" cy="164" rx="13" ry="8" fill="#6B4F10" />
      <!-- 右脚 -->
      <ellipse cx="74" cy="164" rx="13" ry="8" fill="#6B4F10" />

      <!-- 身体 -->
      <rect x="30" y="78" width="60" height="56" rx="18" fill="#A0722A" />
      <!-- 肚子高光 -->
      <ellipse cx="60" cy="98" rx="16" ry="13" fill="rgba(255,220,120,0.25)" />
      <!-- 衣服纹理 -->
      <path d="M42,90 Q60,86 78,90" stroke="rgba(139,105,20,0.4)" stroke-width="2" fill="none" stroke-linecap="round"/>
      <path d="M40,102 Q60,98 80,102" stroke="rgba(139,105,20,0.3)" stroke-width="1.5" fill="none" stroke-linecap="round"/>

      <!-- 左臂 -->
      <g v-if="state !== 'password'">
        <rect
          x="12" y="82" width="18" height="44" rx="9"
          fill="#A0722A"
          :transform="leaning === 'left' ? 'rotate(12,21,82)' : leaning === 'right' ? 'rotate(-8,21,82)' : ''"
        />
        <!-- 左手 -->
        <circle
          :cx="leaning === 'left' ? 18 : leaning === 'right' ? 24 : 21"
          :cy="leaning === 'left' ? 128 : leaning === 'right' ? 124 : 126"
          r="10" fill="#8B6914"
        />
      </g>
      <!-- 左臂捂眼 -->
      <g v-else>
        <rect x="10" y="52" width="18" height="40" rx="9" fill="#A0722A"
          transform="rotate(35,19,72)" />
        <circle cx="24" cy="50" r="11" fill="#8B6914" />
      </g>

      <!-- 右臂 -->
      <g v-if="state !== 'password'">
        <rect
          x="90" y="82" width="18" height="44" rx="9"
          fill="#A0722A"
          :transform="leaning === 'left' ? 'rotate(-8,99,82)' : leaning === 'right' ? 'rotate(12,99,82)' : ''"
        />
        <!-- 右手 -->
        <circle
          :cx="leaning === 'left' ? 96 : leaning === 'right' ? 102 : 99"
          :cy="leaning === 'left' ? 124 : leaning === 'right' ? 128 : 126"
          r="10" fill="#8B6914"
        />
      </g>
      <!-- 右臂捂眼 -->
      <g v-else>
        <rect x="92" y="52" width="18" height="40" rx="9" fill="#A0722A"
          transform="rotate(-35,101,72)" />
        <circle cx="96" cy="50" r="11" fill="#8B6914" />
      </g>

      <!-- 脖子 -->
      <rect x="48" y="66" width="24" height="16" rx="8" fill="#A0722A" />

      <!-- 头部整体（含倾斜） -->
      <g :transform="headTransform">
        <!-- 头部主体 -->
        <circle cx="60" cy="46" r="34" fill="#C49A3C" />
        <!-- 头顶高光 -->
        <ellipse cx="50" cy="26" rx="12" ry="8" fill="rgba(255,230,150,0.3)" transform="rotate(-20,50,26)" />

        <!-- 耳朵 -->
        <circle cx="26" cy="46" r="8" fill="#B8892E" />
        <circle cx="94" cy="46" r="8" fill="#B8892E" />
        <!-- 耳朵内 -->
        <circle cx="26" cy="46" r="4" fill="#A07828" />
        <circle cx="94" cy="46" r="4" fill="#A07828" />

        <!-- 头发/泥巴纹理 -->
        <path d="M32,22 Q46,12 60,14 Q74,12 88,22" stroke="#8B6914" stroke-width="4" fill="none" stroke-linecap="round"/>
        <path d="M36,16 Q40,8 46,12" stroke="#8B6914" stroke-width="3" fill="none" stroke-linecap="round"/>
        <path d="M72,12 Q78,8 84,16" stroke="#8B6914" stroke-width="3" fill="none" stroke-linecap="round"/>
        <!-- 额头泥巴纹 -->
        <path d="M44,20 Q52,16 60,18 Q68,16 76,20" stroke="rgba(139,105,20,0.35)" stroke-width="1.5" fill="none" stroke-linecap="round"/>

        <!-- 眉毛 -->
        <path
          :d="eyebrowPath"
          stroke="#6B4F10"
          stroke-width="3.5"
          fill="none"
          stroke-linecap="round"
          class="eyebrows"
        />

        <!-- 眼睛区域 -->
        <g class="eyes">
          <!-- 左眼白 -->
          <ellipse cx="44" cy="46" rx="10" ry="11" fill="white" />
          <!-- 右眼白 -->
          <ellipse cx="76" cy="46" rx="10" ry="11" fill="white" />

          <!-- 闭眼遮罩（密码状态） -->
          <g v-if="state === 'password'">
            <!-- 左眼上眼皮 -->
            <ellipse cx="44" cy="40" rx="10" ry="8" fill="#C49A3C" />
            <!-- 右眼上眼皮 -->
            <ellipse cx="76" cy="40" rx="10" ry="8" fill="#C49A3C" />
            <!-- 左闭眼线 -->
            <path d="M34,46 Q44,40 54,46" stroke="#6B4F10" stroke-width="3" fill="none" stroke-linecap="round"/>
            <!-- 右闭眼线 -->
            <path d="M66,46 Q76,40 86,46" stroke="#6B4F10" stroke-width="3" fill="none" stroke-linecap="round"/>
            <!-- 睫毛 -->
            <path d="M36,44 L34,40" stroke="#6B4F10" stroke-width="2" stroke-linecap="round"/>
            <path d="M44,42 L44,38" stroke="#6B4F10" stroke-width="2" stroke-linecap="round"/>
            <path d="M52,44 L54,40" stroke="#6B4F10" stroke-width="2" stroke-linecap="round"/>
            <path d="M68,44 L66,40" stroke="#6B4F10" stroke-width="2" stroke-linecap="round"/>
            <path d="M76,42 L76,38" stroke="#6B4F10" stroke-width="2" stroke-linecap="round"/>
            <path d="M84,44 L86,40" stroke="#6B4F10" stroke-width="2" stroke-linecap="round"/>
          </g>

          <!-- 正常/翻白眼状态的眼球 -->
          <g v-if="state !== 'password'">
            <!-- 左眼球 -->
            <circle :cx="leftPupil.x" :cy="leftPupil.y" r="5.5" fill="#3d2b00" class="pupil" />
            <circle :cx="leftPupil.x + 1.5" :cy="leftPupil.y - 1.5" r="1.8" fill="white" />
            <!-- 右眼球 -->
            <circle :cx="rightPupil.x" :cy="rightPupil.y" r="5.5" fill="#3d2b00" class="pupil" />
            <circle :cx="rightPupil.x + 1.5" :cy="rightPupil.y - 1.5" r="1.8" fill="white" />
          </g>
        </g>

        <!-- 嘴巴 -->
        <path :d="mouthPath" stroke="#8B5E1A" stroke-width="2.5" fill="none" stroke-linecap="round" />

        <!-- 腮红 -->
        <ellipse cx="30" cy="56" rx="8" ry="5" fill="rgba(220,100,80,0.2)" />
        <ellipse cx="90" cy="56" rx="8" ry="5" fill="rgba(220,100,80,0.2)" />
      </g>
    </svg>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  // idle | username | password
  state: {
    type: String,
    default: 'idle'
  },
  // 鼠标在页面上的坐标（相对于视口）
  mouseX: {
    type: Number,
    default: 0
  },
  mouseY: {
    type: Number,
    default: 0
  },
  // 泥巴人自身在页面上的中心坐标
  centerX: {
    type: Number,
    default: 0
  },
  centerY: {
    type: Number,
    default: 0
  },
  // 'left' | 'right' | '' — 身体倾斜方向
  leaning: {
    type: String,
    default: ''
  }
})

const svgRef = ref(null)

// 头部变换
const headTransform = computed(() => {
  if (props.state === 'username') return 'translate(0, -2)'
  if (props.state === 'password') return 'translate(0, 0)'
  return ''
})

// 眼球跟随鼠标（仅 idle 状态）
const pupilOffset = computed(() => {
  if (props.state !== 'idle' || !props.centerX) return { dx: 0, dy: 0 }
  const dx = props.mouseX - props.centerX
  const dy = props.mouseY - props.centerY
  const dist = Math.sqrt(dx * dx + dy * dy)
  const maxMove = 4
  if (dist === 0) return { dx: 0, dy: 0 }
  const scale = Math.min(dist / 120, 1) * maxMove
  return {
    dx: (dx / dist) * scale,
    dy: (dy / dist) * scale
  }
})

const leftPupil = computed(() => {
  if (props.state === 'username') return { x: 44, y: 38 }  // 上翻
  const { dx, dy } = pupilOffset.value
  return { x: 44 + dx, y: 46 + dy }
})

const rightPupil = computed(() => {
  if (props.state === 'username') return { x: 76, y: 38 }  // 上翻
  const { dx, dy } = pupilOffset.value
  return { x: 76 + dx, y: 46 + dy }
})

// 眉毛
const eyebrowPath = computed(() => {
  if (props.state === 'username') {
    return 'M34,30 Q44,24 54,30 M66,30 Q76,24 86,30'
  }
  if (props.state === 'password') {
    return 'M34,34 Q44,32 54,34 M66,34 Q76,32 86,34'
  }
  return 'M34,34 Q44,30 54,34 M66,34 Q76,30 86,34'
})

// 嘴巴
const mouthPath = computed(() => {
  if (props.state === 'username') return 'M48,62 Q60,58 72,62'
  if (props.state === 'password') return 'M50,62 Q60,62 70,62'
  return 'M48,62 Q60,68 72,62'
})

// 整体包裹层样式（身体倾斜）
const wrapperStyle = computed(() => {
  if (props.leaning === 'left') {
    return { transform: 'rotate(-12deg) translateX(-8px)', transformOrigin: 'bottom center' }
  }
  if (props.leaning === 'right') {
    return { transform: 'rotate(12deg) translateX(8px)', transformOrigin: 'bottom center' }
  }
  return { transform: 'rotate(0deg)', transformOrigin: 'bottom center' }
})
</script>

<style scoped>
.mud-man-wrapper {
  display: inline-block;
  transition: transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.mud-svg {
  width: 140px;
  height: 210px;
  overflow: visible;
  filter: drop-shadow(3px 6px 10px rgba(0,0,0,0.25));
  animation: idleBreath 3s ease-in-out infinite;
}

.state-password .mud-svg {
  animation: coverEyes 0.4s ease-out forwards;
}

@keyframes idleBreath {
  0%, 100% { transform: translateY(0) scaleY(1); }
  50% { transform: translateY(-6px) scaleY(1.01); }
}

@keyframes coverEyes {
  0% { transform: translateY(0); }
  40% { transform: translateY(-5px); }
  100% { transform: translateY(0); }
}

.pupil {
  transition: cx 0.15s ease-out, cy 0.15s ease-out;
}

.eyebrows {
  transition: d 0.3s ease;
}
</style>
