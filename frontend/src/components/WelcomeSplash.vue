<template>
  <Transition name="splash-fade">
    <div v-if="show" class="splash-overlay">
      <div class="splash-glow-1" />
      <div class="splash-glow-2" />

      <div class="splash-card">
        <div class="splash-corner-tl" />
        <div class="splash-corner-tr" />
        <div class="splash-corner-bl" />
        <div class="splash-corner-br" />

        <div class="splash-header">
          <div class="splash-icon-wrapper">
            <div class="splash-ping" />
            <div class="splash-icon-box">
              <svg viewBox="0 0 100 100" class="splash-svg" fill="currentColor">
                <rect x="48" y="20" width="4" height="60" rx="2" />
                <circle cx="50" cy="18" r="4" />
                <path d="M50 35 C15 22, 10 32, 50 35 Z" fill-opacity="0.8" />
                <path d="M50 35 C85 22, 90 32, 50 35 Z" fill-opacity="0.8" />
                <path d="M50 45 C20 40, 18 48, 50 45 Z" fill-opacity="0.6" />
                <path d="M50 45 C80 40, 82 48, 50 45 Z" fill-opacity="0.6" />
              </svg>
            </div>
          </div>

          <span class="splash-badge">MULTI-AGENT SOCIAL RESEARCH PLATFORM</span>
          <h1 class="splash-title">KINJENG PROJECT</h1>
          <div class="splash-divider" />
          <p class="splash-desc">
            Ekosistem pemodelan sosiokultural berbasis kognisi agen kecerdasan buatan. Mengombinasikan graph pengetahuan interaktif dengan mesin rujukan sosiologis untuk menyajikan simulasi data sosial se-presisi mungkin.
          </p>
        </div>

        <div class="splash-features">
          <div class="splash-feature">
            <span class="splash-bullet" />
            <div>
              <span class="splash-feature-title">KINJENG Engine V1.0</span>
              <span class="splash-feature-desc">Model simulasi kognitif agen sosiokultural.</span>
            </div>
          </div>
          <div class="splash-feature">
            <span class="splash-bullet" />
            <div>
              <span class="splash-feature-title">Graph Interaksi</span>
              <span class="splash-feature-desc">Visualisasi riil jaringan korelasi komunikasi.</span>
            </div>
          </div>
          <div class="splash-feature">
            <span class="splash-bullet" />
            <div>
              <span class="splash-feature-title">Consensus Debating</span>
              <span class="splash-feature-desc">Diskursus internal tandingan multi-perspektif.</span>
            </div>
          </div>
          <div class="splash-feature">
            <span class="splash-bullet" />
            <div>
              <span class="splash-feature-title">Tabulasi Analitik</span>
              <span class="splash-feature-desc">Statistik distribusi frekuensi & tabulasi silang.</span>
            </div>
          </div>
        </div>

        <button class="splash-btn" @click="dismiss">
          <span>MULAI EKSPLORASI DASBOR</span>
          <span class="splash-btn-arrow">→</span>
        </button>
      </div>
    </div>
  </Transition>

  <!-- Toast -->
  <Transition name="toast-fade">
    <div v-if="toast" class="splash-toast">{{ toast }}</div>
  </Transition>
</template>

<script setup>
import { ref } from 'vue'

const show = ref(!sessionStorage.getItem('kinjeng_splash_dismissed'))
const toast = ref('')

function dismiss() {
  sessionStorage.setItem('kinjeng_splash_dismissed', 'true')
  show.value = false
  toast.value = 'Selamat Datang di Kinjeng Project!'
  setTimeout(() => { toast.value = '' }, 3000)
}
</script>

<style scoped>
.splash-fade-enter-active,
.splash-fade-leave-active {
  transition: opacity 0.3s ease;
}
.splash-fade-enter-from,
.splash-fade-leave-to {
  opacity: 0;
}

.splash-overlay {
  position: fixed;
  inset: 0;
  z-index: 99999;
  background: #070707;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  text-align: center;
  overflow-y: auto;
  user-select: none;
}

.splash-glow-1 {
  position: absolute;
  top: 25%;
  left: 25%;
  width: 300px;
  height: 300px;
  border-radius: 50%;
  background: rgba(255,106,51,0.10);
  filter: blur(120px);
  pointer-events: none;
}
.splash-glow-2 {
  position: absolute;
  bottom: 25%;
  right: 25%;
  width: 300px;
  height: 300px;
  border-radius: 50%;
  background: rgba(255,69,0,0.05);
  filter: blur(120px);
  pointer-events: none;
}

.splash-card {
  max-width: 650px;
  width: 100%;
  background: #141414;
  border: 1px solid #2a2a2a;
  padding: 2.5rem;
  position: relative;
  box-shadow: 0 0 50px rgba(255,106,51,0.05);
}

.splash-corner-tl,
.splash-corner-tr,
.splash-corner-bl,
.splash-corner-br {
  position: absolute;
  width: 16px;
  height: 16px;
  border-color: #FF6A33;
}
.splash-corner-tl { top: -1px; left: -1px; border-top: 2px solid; border-left: 2px solid; }
.splash-corner-tr { top: -1px; right: -1px; border-top: 2px solid; border-right: 2px solid; }
.splash-corner-bl { bottom: -1px; left: -1px; border-bottom: 2px solid; border-left: 2px solid; }
.splash-corner-br { bottom: -1px; right: -1px; border-bottom: 2px solid; border-right: 2px solid; }

.splash-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 1.25rem;
}

.splash-icon-wrapper {
  position: relative;
  margin-bottom: 0.875rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.splash-ping {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: rgba(255,106,51,0.05);
  animation: splash-ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;
}

@keyframes splash-ping {
  75%, 100% { transform: scale(1.8); opacity: 0; }
}

.splash-icon-box {
  width: 64px;
  height: 64px;
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.3);
}

.splash-svg {
  width: 40px;
  height: 40px;
  color: #FF6A33;
}

.splash-badge {
  font-family: 'Courier New', monospace;
  font-size: 9px;
  letter-spacing: 0.25em;
  color: #FF6A33;
  font-weight: 700;
  text-transform: uppercase;
}

.splash-title {
  font-family: 'Courier New', monospace;
  font-size: 2rem;
  font-weight: 900;
  letter-spacing: 0.1em;
  color: #ffffff;
  margin-top: 0.5rem;
  line-height: 1.2;
}

@media (min-width: 768px) {
  .splash-title { font-size: 2.5rem; }
}

.splash-divider {
  height: 1px;
  width: 96px;
  background: #2a2a2a;
  margin: 0.75rem 0;
}

.splash-desc {
  font-size: 0.78rem;
  color: #888;
  max-width: 480px;
  line-height: 1.6;
}

.splash-features {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.75rem;
  text-align: left;
  border-top: 1px solid #2a2a2a;
  border-bottom: 1px solid #2a2a2a;
  padding: 1rem 0;
  margin: 1.25rem 0;
  font-family: 'Courier New', monospace;
  font-size: 0.78rem;
}

@media (min-width: 640px) {
  .splash-features { grid-template-columns: 1fr 1fr; }
}

.splash-feature {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
}

.splash-bullet {
  color: #FF6A33;
  margin-top: 0.125rem;
  flex-shrink: 0;
}
.splash-bullet::before { content: '■'; }

.splash-feature-title {
  color: #ffffff;
  font-weight: 700;
  display: block;
}

.splash-feature-desc {
  color: #555;
  font-size: 0.68rem;
}

.splash-btn {
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-family: 'Courier New', monospace;
  font-weight: 700;
  font-size: 0.78rem;
  padding: 12px 24px;
  border: 1px solid #FF6A33;
  background: #FF6A33;
  color: #ffffff;
  cursor: pointer;
  transition: all 0.15s;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.splash-btn:hover {
  background: #FF6A33;
  opacity: 0.9;
}

.splash-btn-arrow {
  transition: transform 0.2s;
}

.splash-btn:hover .splash-btn-arrow {
  transform: translateX(4px);
}

.splash-toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 99999;
  background: #070707;
  border: 1px solid #FF6A33;
  color: #fff;
  padding: 12px 24px;
  font-family: 'Courier New', monospace;
  font-size: 0.82rem;
  box-shadow: 0 0 20px rgba(255,106,51,0.1);
  pointer-events: none;
}
.toast-fade-enter-active { transition: all 0.4s ease; }
.toast-fade-leave-active { transition: all 0.3s ease; }
.toast-fade-enter-from { opacity: 0; transform: translateX(-50%) translateY(10px); }
.toast-fade-leave-to { opacity: 0; transform: translateX(-50%) translateY(-10px); }
</style>
