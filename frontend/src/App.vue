<template>
  <WelcomeSplash />
  <router-view />
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useTheme } from './composables/useTheme'
import WelcomeSplash from './components/WelcomeSplash.vue'

const API = import.meta.env.VITE_API_BASE_URL ? import.meta.env.VITE_API_BASE_URL + '/api' : (import.meta.env.PROD ? '/api' : 'http://localhost:5001/api')
const { theme } = useTheme()

onMounted(() => {
  document.documentElement.setAttribute('data-theme', theme.value)
  window.addEventListener('beforeunload', shutdownServer)
})

onUnmounted(() => {
  window.removeEventListener('beforeunload', shutdownServer)
})

function shutdownServer() {
  navigator.sendBeacon(`${API}/system/disconnect`, '')
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root,
[data-theme="light"] {
  --bg-primary: #FFFFFF;
  --bg-secondary: #F5F5F5;
  --bg-card: #FFFFFF;
  --bg-selected: rgba(255, 69, 0, 0.03);
  --text-primary: #000000;
  --text-secondary: #666666;
  --text-tertiary: #999999;
  --border-color: #E5E5E5;
  --shadow: 0 2px 8px rgba(0,0,0,0.08);
  --black: #000000;
  --white: #FFFFFF;
  --accent-primary: #FF4500;
  --accent-secondary: #FF6A33;
  --navbar-bg: #000000;
  --navbar-text: #FFFFFF;
  --success: #2a9d2a;
  --warning: #cc8800;
  --danger: #cc3333;
}

[data-theme="dark"] {
  --bg-primary: #111111;
  --bg-secondary: #1A1A1A;
  --bg-card: #1E1E1E;
  --bg-selected: rgba(255, 69, 0, 0.08);
  --text-primary: #EEEEEE;
  --text-secondary: #999999;
  --text-tertiary: #777777;
  --border-color: #333333;
  --shadow: 0 2px 8px rgba(0,0,0,0.4);
  --black: #1A1A1A;
  --white: #EEEEEE;
  --accent-primary: #FF6A33;
  --accent-secondary: #FF4500;
  --navbar-bg: #1A1A1A;
  --navbar-text: #EEEEEE;
  --success: #4CAF50;
  --warning: #FFA000;
  --danger: #EF5350;
}

#app {
  font-family: 'JetBrains Mono', 'Space Grotesk', 'Noto Sans SC', monospace;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--text-primary);
  background-color: var(--bg-primary);
  transition: color 0.3s ease, background-color 0.3s ease;
}

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--bg-secondary); }
::-webkit-scrollbar-thumb { background: var(--text-tertiary); }
::-webkit-scrollbar-thumb:hover { background: var(--text-secondary); }

button { font-family: inherit; cursor: pointer; }
a { color: inherit; }

/* ===== Global Responsive Utilities ===== */

/* Mobile: stack dual-panel layouts vertically */
@media (max-width: 768px) {
  .content-area {
    flex-direction: column !important;
  }
  .content-area > .panel-wrapper {
    width: 100% !important;
    height: 50% !important;
    opacity: 1 !important;
    transform: none !important;
    border-right: none !important;
    border-bottom: 1px solid var(--border-color);
  }
}

/* Mobile: adjust header spacing */
@media (max-width: 768px) {
  .app-header {
    padding: 0 12px !important;
    gap: 8px;
  }
  .header-center {
    position: static !important;
    transform: none !important;
  }
  .app-header .brand {
    font-size: 14px !important;
  }
  .step-divider {
    display: none !important;
  }
  .workflow-step .step-name {
    display: none !important;
  }
  .step-num {
    font-size: 11px !important;
  }
  .view-switcher .switch-btn {
    padding: 4px 8px !important;
    font-size: 10px !important;
  }
  .header-right {
    gap: 8px !important;
  }
}

/* Very small screens */
@media (max-width: 480px) {
  .app-header .brand {
    display: none !important;
  }
  .view-switcher .switch-btn {
    font-size: 9px !important;
    padding: 3px 6px !important;
  }
}

/* ===== End Global Responsive Utilities ===== */
</style>
