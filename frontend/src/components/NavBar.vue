<template>
  <nav class="navbar">
    <div class="nav-brand" @click="$router.push('/')">MIROFISH</div>
    <div class="nav-links">
      <ThemeToggle />
      <LanguageSwitcher />
      <button
        v-for="link in links"
        :key="link.to"
        class="nav-link-btn"
        :class="{ active: $route.path === link.to }"
        @click="$router.push(link.to)"
      >
        {{ link.icon }} {{ link.label }}
      </button>
      <a href="https://github.com/666ghj/MiroFish" target="_blank" class="github-link">
        {{ $t('nav.visitGithub') }} <span class="arrow">↗</span>
      </a>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import ThemeToggle from './ThemeToggle.vue'
import LanguageSwitcher from './LanguageSwitcher.vue'

const route = useRoute()

const links = computed(() => [
  { to: '/', icon: '🏠', label: 'Beranda' },
  { to: '/choose-simulation', icon: '🎯', label: 'Simulasi' },
  { to: '/parliament', icon: '🧠', label: 'Debat Internal' },
  { to: '/survey-results', icon: '📊', label: 'Hasil Survei' }
])
</script>

<style scoped>
.navbar {
  height: 60px;
  background: var(--navbar-bg, #000000);
  color: var(--navbar-text, #FFFFFF);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-brand {
  font-family: var(--font-mono);
  font-weight: 800;
  letter-spacing: 1px;
  font-size: 1.2rem;
  cursor: pointer;
  user-select: none;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-link-btn {
  background: none;
  border: 1px solid rgba(255,255,255,0.2);
  color: var(--navbar-text);
  padding: 6px 12px;
  cursor: pointer;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  transition: all 0.2s;
}

.nav-link-btn:hover {
  border-color: var(--accent-primary, #FF4500);
  opacity: 0.9;
}

.nav-link-btn.active {
  border-color: var(--accent-primary, #FF4500);
  background: rgba(255, 69, 0, 0.15);
}

.github-link {
  color: var(--navbar-text);
  text-decoration: none;
  font-family: var(--font-mono);
  font-size: 0.8rem;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.github-link:hover {
  opacity: 1;
}

.arrow {
  font-family: sans-serif;
}
</style>
