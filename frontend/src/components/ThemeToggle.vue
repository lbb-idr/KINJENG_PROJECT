<template>
  <button class="theme-toggle" @click="toggleTheme" :title="('main.toggleTheme')">
    <span v-if="isDark">☀️</span>
    <span v-else>🌙</span>
  </button>
</template>

<script setup>
import { computed } from 'vue'
import { useTheme } from '../composables/useTheme'

const { theme, setTheme } = useTheme()
const isDark = computed(() => theme.value === 'dark')

function toggleTheme() {
  setTheme(isDark.value ? 'light' : 'dark')
}
</script>

<style scoped>
.theme-toggle {
  background: none;
  border: 1px solid var(--navbar-text, rgba(255,255,255,0.3));
  color: var(--navbar-text, white);
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.2s;
}

.theme-toggle:hover {
  border-color: var(--navbar-text, white);
  background: rgba(255,255,255,0.1);
}
</style>
