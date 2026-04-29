<template>
  <!--
    泥巴人 v3 — 4个角色（参考 React 版本移植到 Vue）
    props:
      isTypingUsername  — 正在输入账号（角色互视）
      isTypingPassword  — 正在输入密码（角色躲避）
      showPassword      — 密码可见（紫色偷看）
      mouseX / mouseY   — 鼠标坐标
  -->
  <div class="chars-wrap" ref="wrapRef">
    <!-- 紫色高矩形（最后面） -->
    <div
      class="char purple-char"
      ref="purpleRef"
      :style="purpleStyle"
    >
      <div class="eyes" :style="purpleEyesStyle">
        <div class="eyeball" :class="{ blink: purpleBlink }">
          <div class="pupil" :style="{ transform: `translate(${purpleEyePos.x}px,${purpleEyePos.y}px)` }"></div>
        </div>
        <div class="eyeball" :class="{ blink: purpleBlink }">
          <div class="pupil" :style="{ transform: `translate(${purpleEyePos.x}px,${purpleEyePos.y}px)` }"></div>
        </div>
      </div>
    </div>

    <!-- 黑色中矩形 -->
    <div
      class="char black-char"
      ref="blackRef"
      :style="blackStyle"
    >
      <div class="eyes" :style="blackEyesStyle">
        <div class="eyeball sm" :class="{ blink: blackBlink }">
          <div class="pupil sm" :style="{ transform: `translate(${blackEyePos.x}px,${blackEyePos.y}px)` }"></div>
        </div>
        <div class="eyeball sm" :class="{ blink: blackBlink }">
          <div class="pupil sm" :style="{ transform: `translate(${blackEyePos.x}px,${blackEyePos.y}px)` }"></div>
        </div>
      </div>
    </div>

    <!-- 橙色半圆（前左） -->
    <div
      class="char orange-char"
      ref="orangeRef"
      :style="orangeStyle"
    >
      <div class="eyes no-white" :style="orangeEyesStyle">
        <div class="pupil-only" :style="{ transform: `translate(${orangeEyePos.x}px,${orangeEyePos.y}px)` }"></div>
        <div class="pupil-only" :style="{ transform: `translate(${orangeEyePos.x}px,${orangeEyePos.y}px)` }"></div>
      </div>
    </div>

    <!-- 黄色圆顶矩形（前右） -->
    <div
      class="char yellow-char"
      ref="yellowRef"
      :style="yellowStyle"
    >
      <div class="eyes no-white" :style="yellowEyesStyle">
        <div class="pupil-only" :style="{ transform: `translate(${yellowEyePos.x}px,${yellowEyePos.y}px)` }"></div>
        <div class="pupil-only" :style="{ transform: `translate(${yellowEyePos.x}px,${yellowEyePos.y}px)` }"></div>
      </div>
      <!-- 嘴巴 -->
      <div class="mouth" :style="yellowMouthStyle"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  isTypingUsername: { type: Boolean, default: false },
  isTypingPassword: { type: Boolean, default: false },
  showPassword: { type: Boolean, default: false },
  mouseX: { type: Number, default: 0 },
  mouseY: { type: Number, default: 0 },
  hasPassword: { type: Boolean, default: false }
})

const wrapRef = ref(null)
const purpleRef = ref(null)
const blackRef = ref(null)
const orangeRef = ref(null)
const yellowRef = ref(null)

// 眨眼状态
const purpleBlink = ref(false)
const blackBlink = ref(false)

// 偷看状态
const isPeeking = ref(false)

// 随机眨眼
function scheduleBlink(blinkRef) {
  const delay = Math.random() * 4000 + 3000
  return setTimeout(() => {
    blinkRef.value = true
    setTimeout(() => {
      blinkRef.value = false
      scheduleBlink(blinkRef)
    }, 150)
  }, delay)
}

let purpleBlinkTimer = null
let blackBlinkTimer = null
let peekTimer = null

onMounted(() => {
  purpleBlinkTimer = scheduleBlink(purpleBlink)
  blackBlinkTimer = scheduleBlink(blackBlink)
})

onUnmounted(() => {
  clearTimeout(purpleBlinkTimer)
  clearTimeout(blackBlinkTimer)
  clearTimeout(peekTimer)
})

// 密码可见时偷看
watch(() => [props.hasPassword, props.showPassword], ([hasPwd, showPwd]) => {
  clearTimeout(peekTimer)
  if (hasPwd && showPwd) {
    const schedulePeek = () => {
      peekTimer = setTimeout(() => {
        isPeeking.value = true
        setTimeout(() => {
          isPeeking.value = false
          schedulePeek()
        }, 800)
      }, Math.random() * 3000 + 2000)
    }
    schedulePeek()
  } else {
    isPeeking.value = false
  }
})

// 计算某个元素相对鼠标的偏移（用于身体倾斜和眼球跟踪）
function calcPos(el) {
  if (!el) return { faceX: 0, faceY: 0, bodySkew: 0 }
  const rect = el.getBoundingClientRect()
  const cx = rect.left + rect.width / 2
  const cy = rect.top + rect.height / 3
  const dx = props.mouseX - cx
  const dy = props.mouseY - cy
  const faceX = Math.max(-15, Math.min(15, dx / 20))
  const faceY = Math.max(-10, Math.min(10, dy / 30))
  const bodySkew = Math.max(-6, Math.min(6, -dx / 120))
  return { faceX, faceY, bodySkew }
}

// 眼球位置（限制在眼白范围内）
function clampEye(dx, dy, max = 5) {
  const dist = Math.sqrt(dx * dx + dy * dy)
  if (dist === 0) return { x: 0, y: 0 }
  const scale = Math.min(dist, max) / dist
  return { x: dx * scale, y: dy * scale }
}

function eyePosFromMouse(el, maxDist = 5) {
  if (!el) return { x: 0, y: 0 }
  const rect = el.getBoundingClientRect()
  const cx = rect.left + rect.width / 2
  const cy = rect.top + rect.height / 2
  return clampEye(props.mouseX - cx, props.mouseY - cy, maxDist)
}

// ── 紫色角色 ──────────────────────────────────────────
const purpleStyle = computed(() => {
  const pos = calcPos(purpleRef.value)
  const isPasswordMode = props.hasPassword && !props.showPassword
  const isTypingPwd = props.isTypingPassword
  let skew = pos.bodySkew
  let tx = 0
  let height = 400

  if (isTypingPwd || isPasswordMode) {
    height = 440
    skew = pos.bodySkew - 12
    tx = 40
  }
  if (props.hasPassword && props.showPassword) {
    skew = 0
    tx = 0
  }

  return {
    transform: `skewX(${skew}deg) translateX(${tx}px)`,
    height: height + 'px'
  }
})

const purpleEyesStyle = computed(() => {
  const pos = calcPos(purpleRef.value)
  const isPasswordMode = props.hasPassword && !props.showPassword
  const isPwdVisible = props.hasPassword && props.showPassword

  if (isPwdVisible) return { left: '20px', top: '35px' }
  if (props.isTypingUsername) return { left: '55px', top: '65px' }
  return { left: (45 + pos.faceX) + 'px', top: (40 + pos.faceY) + 'px' }
})

const purpleEyePos = computed(() => {
  const isPwdVisible = props.hasPassword && props.showPassword
  if (isPwdVisible) return isPeeking.value ? { x: 4, y: 5 } : { x: -4, y: -4 }
  if (props.isTypingUsername) return { x: 3, y: 4 }
  return eyePosFromMouse(purpleRef.value, 5)
})

// ── 黑色角色 ──────────────────────────────────────────
const blackStyle = computed(() => {
  const pos = calcPos(blackRef.value)
  const isPwdVisible = props.hasPassword && props.showPassword
  let skew = pos.bodySkew

  if (isPwdVisible) skew = 0
  else if (props.isTypingUsername) skew = pos.bodySkew * 1.5 + 10
  else if (props.isTypingPassword || (props.hasPassword && !props.showPassword)) skew = pos.bodySkew * 1.5

  return { transform: `skewX(${skew}deg)` }
})

const blackEyesStyle = computed(() => {
  const pos = calcPos(blackRef.value)
  const isPwdVisible = props.hasPassword && props.showPassword

  if (isPwdVisible) return { left: '10px', top: '28px' }
  if (props.isTypingUsername) return { left: '32px', top: '12px' }
  return { left: (26 + pos.faceX) + 'px', top: (32 + pos.faceY) + 'px' }
})

const blackEyePos = computed(() => {
  const isPwdVisible = props.hasPassword && props.showPassword
  if (isPwdVisible) return { x: -4, y: -4 }
  if (props.isTypingUsername) return { x: 0, y: -4 }
  return eyePosFromMouse(blackRef.value, 4)
})

// ── 橙色角色 ──────────────────────────────────────────
const orangeStyle = computed(() => {
  const pos = calcPos(orangeRef.value)
  const isPwdVisible = props.hasPassword && props.showPassword
  return { transform: `skewX(${isPwdVisible ? 0 : pos.bodySkew}deg)` }
})

const orangeEyesStyle = computed(() => {
  const pos = calcPos(orangeRef.value)
  const isPwdVisible = props.hasPassword && props.showPassword
  if (isPwdVisible) return { left: '50px', top: '85px' }
  return { left: (82 + pos.faceX) + 'px', top: (90 + pos.faceY) + 'px' }
})

const orangeEyePos = computed(() => {
  const isPwdVisible = props.hasPassword && props.showPassword
  if (isPwdVisible) return { x: -5, y: -4 }
  return eyePosFromMouse(orangeRef.value, 5)
})

// ── 黄色角色 ──────────────────────────────────────────
const yellowStyle = computed(() => {
  const pos = calcPos(yellowRef.value)
  const isPwdVisible = props.hasPassword && props.showPassword
  return { transform: `skewX(${isPwdVisible ? 0 : pos.bodySkew}deg)` }
})

const yellowEyesStyle = computed(() => {
  const pos = calcPos(yellowRef.value)
  const isPwdVisible = props.hasPassword && props.showPassword
  if (isPwdVisible) return { left: '20px', top: '35px' }
  return { left: (52 + pos.faceX) + 'px', top: (40 + pos.faceY) + 'px' }
})

const yellowEyePos = computed(() => {
  const isPwdVisible = props.hasPassword && props.showPassword
  if (isPwdVisible) return { x: -5, y: -4 }
  return eyePosFromMouse(yellowRef.value, 5)
})

const yellowMouthStyle = computed(() => {
  const pos = calcPos(yellowRef.value)
  const isPwdVisible = props.hasPassword && props.showPassword
  if (isPwdVisible) return { left: '10px', top: '88px' }
  return { left: (40 + pos.faceX) + 'px', top: (88 + pos.faceY) + 'px' }
})
</script>

<style scoped>
.chars-wrap {
  position: relative;
  width: 550px;
  height: 400px;
  flex-shrink: 0;
}

/* ── 角色基础 ── */
.char {
  position: absolute;
  bottom: 0;
  transition: transform 0.7s ease-in-out, height 0.7s ease-in-out;
  transform-origin: bottom center;
}

/* 紫色高矩形 */
.purple-char {
  left: 70px;
  width: 180px;
  height: 400px;
  background: #6C3FF5;
  border-radius: 10px 10px 0 0;
  z-index: 1;
}

/* 黑色中矩形 */
.black-char {
  left: 240px;
  width: 120px;
  height: 310px;
  background: #2D2D2D;
  border-radius: 8px 8px 0 0;
  z-index: 2;
}

/* 橙色半圆 */
.orange-char {
  left: 0;
  width: 240px;
  height: 200px;
  background: #FF9B6B;
  border-radius: 120px 120px 0 0;
  z-index: 3;
}

/* 黄色圆顶矩形 */
.yellow-char {
  left: 310px;
  width: 140px;
  height: 230px;
  background: #E8D754;
  border-radius: 70px 70px 0 0;
  z-index: 4;
}

/* ── 眼睛 ── */
.eyes {
  position: absolute;
  display: flex;
  gap: 28px;
  transition: left 0.7s ease-in-out, top 0.7s ease-in-out;
}

.eyes.no-white {
  gap: 24px;
}

.eyeball {
  width: 18px;
  height: 18px;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  transition: height 0.15s ease;
  flex-shrink: 0;
}

.eyeball.sm {
  width: 16px;
  height: 16px;
}

.eyeball.blink {
  height: 2px !important;
}

.pupil {
  width: 8px;
  height: 8px;
  background: #2D2D2D;
  border-radius: 50%;
  transition: transform 0.1s ease-out;
  flex-shrink: 0;
}

.pupil.sm {
  width: 6px;
  height: 6px;
}

/* 无眼白的瞳孔 */
.pupil-only {
  width: 12px;
  height: 12px;
  background: #2D2D2D;
  border-radius: 50%;
  transition: transform 0.1s ease-out;
  flex-shrink: 0;
}

/* 嘴巴 */
.mouth {
  position: absolute;
  width: 80px;
  height: 4px;
  background: #2D2D2D;
  border-radius: 999px;
  transition: left 0.2s ease-out, top 0.2s ease-out;
}
</style>
