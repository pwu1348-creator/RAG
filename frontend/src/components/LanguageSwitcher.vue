<template>
  <div class="language-switcher">
    <button 
      class="lang-btn" 
      :class="{ active: currentLocale === 'zh' }"
      @click="switchLanguage('zh')"
    >
      中文
    </button>
    <span class="divider">|</span>
    <button 
      class="lang-btn" 
      :class="{ active: currentLocale === 'en' }"
      @click="switchLanguage('en')"
    >
      EN
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { locale } = useI18n()

const currentLocale = computed(() => locale.value)

const switchLanguage = (lang) => {
  locale.value = lang
  localStorage.setItem('locale', lang)
}
</script>

<style scoped>
.language-switcher {
  display: flex;
  align-items: center;
  gap: 8px;
}

.lang-btn {
  padding: 4px 8px;
  border: none;
  background: transparent;
  color: #666;
  cursor: pointer;
  font-size: 14px;
  border-radius: 4px;
  transition: all 0.3s;
}

.lang-btn:hover {
  color: #333;
  background: #f0f0f0;
}

.lang-btn.active {
  color: #1890ff;
  font-weight: 500;
}

.divider {
  color: #ddd;
}
</style>
