<template>
  <div class="language-switcher" ref="switcherRef">
    <button class="switcher-trigger" @click="toggleDropdown">
      {{ currentLabel }}
      <span class="caret">{{ open ? '▲' : '▼' }}</span>
    </button>
    <ul v-if="open" class="switcher-dropdown">
      <li
        v-for="loc in availableLocales"
        :key="loc.key"
        class="switcher-option"
        :class="{ active: loc.key === locale }"
        @click="switchLocale(loc.key)"
      >
        {{ loc.label }}
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { availableLocales } from '../i18n/index.js'

const { locale } = useI18n({ useScope: 'global' })
const open = ref(false)
const switcherRef = ref(null)

const currentLabel = computed(() => {
  const found = availableLocales.find(l => l.key === locale.value)
  return found ? found.label : locale.value
})

const toggleDropdown = () => { open.value = !open.value }
const switchLocale = (key) => {
  locale.value = key
  localStorage.setItem('locale', key)
  document.documentElement.lang = key
  open.value = false
}
const onClickOutside = (e) => {
  if (switcherRef.value && !switcherRef.value.contains(e.target)) open.value = false
}

onMounted(() => {
  document.addEventListener('click', onClickOutside)
  document.documentElement.lang = locale.value
})
onUnmounted(() => document.removeEventListener('click', onClickOutside))
</script>

<style scoped>
.language-switcher { position: relative; display: inline-block; font-family: var(--font-mono); }
.switcher-trigger {
  background: transparent;
  color: var(--navbar-text, #FFF);
  border: 1px solid rgba(255,255,255,0.2);
  padding: 4px 10px;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: border-color 0.2s;
}
.switcher-trigger:hover { border-color: var(--accent-primary, #FF4500); }
.caret { font-size: 0.5rem; }
.switcher-dropdown {
  position: absolute;
  top: 100%; right: 0;
  margin-top: 4px;
  background: var(--bg-card, #1E1E1E);
  border: 1px solid var(--border-color, #333);
  list-style: none;
  padding: 4px 0;
  min-width: 100%;
  z-index: 1000;
  box-shadow: var(--shadow);
}
.switcher-option {
  padding: 6px 12px;
  font-size: 0.75rem;
  color: var(--text-primary, #EEE);
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s;
}
.switcher-option:hover { background: var(--bg-secondary, #1A1A1A); }
.switcher-option.active { color: var(--accent-primary, #FF6A33); }
</style>
