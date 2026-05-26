import { ref, watchEffect } from 'vue'

const theme = ref(localStorage.getItem('theme') || 'light')

export function useTheme() {
  function applyTheme(t) {
    document.documentElement.setAttribute('data-theme', t)
    localStorage.setItem('theme', t)
  }

  watchEffect(() => {
    applyTheme(theme.value)
  })

  function setTheme(t) {
    theme.value = t
  }

  return { theme, setTheme }
}

export default theme
