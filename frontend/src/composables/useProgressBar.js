import { ref, onUnmounted } from 'vue'

export function useProgressBar() {
  const progress = ref(0)
  const statusText = ref('')
  const isActive = ref(false)
  let timer = null
  let currentStep = 0

  const steps = [
    { at: 0, text: 'Memulai...' },
    { at: 15, text: 'Memproses data...' },
    { at: 30, text: 'Menyiapkan simulasi...' },
    { at: 50, text: 'Menjalankan simulasi...' },
    { at: 70, text: 'Menganalisis hasil...' },
    { at: 85, text: 'Menyelesaikan...' },
    { at: 95, text: 'Hampir selesai...' },
  ]

  function start(duration = 60000) {
    isActive.value = true
    progress.value = 0
    currentStep = 0
    statusText.value = steps[0].text
    const incrementPerMs = 95 / duration
    const startTime = Date.now()

    timer = setInterval(() => {
      const elapsed = Date.now() - startTime
      progress.value = Math.min(95, elapsed * incrementPerMs)
      
      while (currentStep < steps.length - 1 && progress.value >= steps[currentStep + 1].at) {
        currentStep++
        statusText.value = steps[currentStep].text
      }

      if (progress.value >= 95) {
        clearInterval(timer)
      }
    }, 200)
  }

  function complete() {
    clearInterval(timer)
    progress.value = 100
    statusText.value = 'Selesai'
    setTimeout(() => {
      isActive.value = false
    }, 500)
  }

  function fail(message = 'Gagal') {
    clearInterval(timer)
    statusText.value = message
    setTimeout(() => {
      isActive.value = false
    }, 3000)
  }

  function reset() {
    clearInterval(timer)
    progress.value = 0
    statusText.value = ''
    isActive.value = false
  }

  onUnmounted(() => clearInterval(timer))

  return { progress, statusText, isActive, start, complete, fail, reset }
}
