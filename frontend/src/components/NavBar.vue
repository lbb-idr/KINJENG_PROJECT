<template>
  <nav class="navbar">
    <div class="nav-brand" @click="$router.push('/')">KINJENG_PROJECT</div>
    <button class="hamburger" :class="{ open: menuOpen }" @click="menuOpen = !menuOpen" aria-label="Menu">
      <span></span><span></span><span></span>
    </button>
    <div class="nav-links" :class="{ open: menuOpen }">
      <ThemeToggle />
      <LanguageSwitcher />
      <button
        v-for="link in links"
        :key="link.to"
        class="nav-link-btn"
        :class="{ active: $route.path === link.to }"
        @click="menuOpen = false; $router.push(link.to)"
      >
        {{ link.icon }} {{ link.label }}
      </button>
      <a href="https://github.com/lbb-idr/KINJENG_PROJECT" target="_blank" class="github-link" @click="menuOpen = false">
        {{ $t('nav.visitGithub') }} <span class="arrow">↗</span>
      </a>
    </div>
  </nav>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import ThemeToggle from './ThemeToggle.vue'
import LanguageSwitcher from './LanguageSwitcher.vue'

const route = useRoute()
const menuOpen = ref(false)

const links = computed(() => [
  { to: '/', icon: '🏠', label: 'Beranda' },
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

/* Hamburger */
.hamburger {
  display: none;
  flex-direction: column;
  gap: 4px;
  background: none;
  border: none;
  padding: 8px;
  cursor: pointer;
  z-index: 110;
}
.hamburger span {
  display: block;
  width: 22px;
  height: 2px;
  background: var(--navbar-text, #FFF);
  transition: all 0.3s;
}
.hamburger.open span:nth-child(1) { transform: translateY(6px) rotate(45deg); }
.hamburger.open span:nth-child(2) { opacity: 0; }
.hamburger.open span:nth-child(3) { transform: translateY(-6px) rotate(-45deg); }

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

/* Mobile Nav */
@media (max-width: 768px) {
  .navbar {
    padding: 0 16px;
  }
  .hamburger {
    display: flex;
  }
  .nav-links {
    display: none;
    position: fixed;
    top: 60px;
    left: 0;
    right: 0;
    bottom: 0;
    background: var(--navbar-bg, #000);
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    gap: 12px;
    padding: 32px 20px;
    z-index: 100;
    overflow-y: auto;
  }
  .nav-links.open {
    display: flex;
  }
  .nav-link-btn {
    width: 100%;
    max-width: 320px;
    padding: 14px 16px;
    font-size: 0.9rem;
    text-align: center;
  }
  .github-link {
    width: 100%;
    max-width: 320px;
    text-align: center;
    padding: 14px 16px;
    font-size: 0.9rem;
    border: 1px solid rgba(255,255,255,0.15);
    opacity: 1;
  }
}
</style>
