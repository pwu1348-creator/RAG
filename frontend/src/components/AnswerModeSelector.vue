<template>
  <div class="answer-mode-selector">
    <label class="mode-label">回答风格</label>
    <div class="mode-buttons">
      <button
        class="mode-btn"
        :class="{ active: modelValue === 'strict' }"
        @click="$emit('update:modelValue', 'strict')"
      >
        <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20M9,13V19H7V13H9M15,15V19H13V15H15M11,11V19H13V11H11Z"/></svg>
        严谨
      </button>
      <button
        class="mode-btn"
        :class="{ active: modelValue === 'loose' }"
        @click="$emit('update:modelValue', 'loose')"
      >
        <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M20,2H4C2.9,2 2,2.9 2,4V22L6,18H20C21.1,18 22,17.1 22,16V4C22,2.9 21.1,2 20,2M20,16H5.2L4,17.2V4H20V16Z"/></svg>
        宽松
      </button>
    </div>
    <p class="mode-desc">{{ description }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: 'strict',
    validator: (v) => ['strict', 'loose'].includes(v),
  },
})

defineEmits(['update:modelValue'])

const description = computed(() => {
  if (props.modelValue === 'strict') {
    return '严格按照文档原文作答，适用于知识库、规章、法规等场景。'
  }
  return '可基于文档合理引申补充，适用于闲聊、改写、扩写、娱乐等场景。'
})
</script>

<style scoped>
.answer-mode-selector {
  margin-bottom: 20px;
}

.mode-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #2d6a4f;
  margin-bottom: 8px;
}

.mode-buttons {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.mode-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 14px;
  border: 2px solid rgba(168, 230, 207, 0.4);
  border-radius: 10px;
  background: rgba(240, 250, 245, 0.6);
  font-size: 14px;
  font-weight: 500;
  color: #52b788;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-btn:hover {
  border-color: #52b788;
  background: rgba(168, 230, 207, 0.15);
}

.mode-btn.active {
  border-color: #2d6a4f;
  background: linear-gradient(135deg, rgba(168, 230, 207, 0.3), rgba(82, 183, 136, 0.15));
  color: #1b4332;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(82, 183, 136, 0.2);
}

.mode-btn svg {
  flex-shrink: 0;
}

.mode-desc {
  font-size: 12px;
  color: #74c69d;
  line-height: 1.5;
  margin: 0;
}
</style>
