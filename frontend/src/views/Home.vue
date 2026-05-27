<template>
  <div class="home-container">
    <!-- Welcome Overlay -->
    <Transition name="welcome-fade">
      <div v-if="showWelcome" class="welcome-overlay" @click="startWelcomeClick">
        <div class="welcome-center">
          <img :src="logoImg" alt="KINJENG" class="welcome-logo" :class="{ 'logo-flying': isLogoFlying, 'logo-expand': isLogoExpanding }" @click.stop="handleLogoClick" />
          <h1 class="welcome-title">KINJENG<span class="welcome-accent">_PROJECT</span></h1>
          <p class="welcome-subtitle">Multi-Agent Social Simulation Platform</p>
          <button class="welcome-btn" @click.stop="startWelcomeClick">
            🚀 Mulai
          </button>
          <p class="welcome-hint">Klik logo atau tombol Mulai untuk memulai</p>
        </div>
      </div>
    </Transition>

    <NavBar />

    <div class="main-content">
      <!-- Hero / Instruksi Awal -->
      <section class="hero-section">
        <div class="hero-badge">KINJENG_PROJECT v0.1</div>
        <h1 class="hero-title">Selamat Datang di KINJENG_PROJECT</h1>
        <p class="hero-desc">
          Platform simulasi multi-agent untuk riset akademik, polling politik,
          riset pasar, dan simulasi sosial. Ikuti langkah-langkah di bawah ini
          untuk memulai.
        </p>
      </section>

      <!-- Panduan Langkah -->
      <section class="guide-steps">
        <div class="guide-step step-type" :class="{ active: !simulationType }">
          <div class="step-number">1</div>
          <div class="step-body">
            <h3 class="step-title">Pilih Jenis Simulasi</h3>
            <p class="step-desc" v-if="!simulationType">
              Pilih jenis simulasi yang sesuai dengan kebutuhan riset Anda.
            </p>

            <div v-if="!simulationType" class="type-select-inline">
              <p class="step-desc">
                Pilih tipe simulasi dan atur parameter, atau upload dokumen untuk simulasi kustom.
              </p>
              <button class="step-btn" @click="goToChooseSimulation">
                🎯 Pilih Jenis Simulasi <span class="btn-arrow">→</span>
              </button>
            </div>
            <div v-else class="type-selected-inline">
              <span class="step-done">✓ {{ typeLabels[simulationType] || simulationType }}</span>
              <span class="step-summary">{{ params.agentCount.toLocaleString() }} agen · {{ params.maxRounds }} ronde · {{ params.platform === 'both' ? '2 platform' : params.platform }}</span>
              <button class="step-btn-small" @click="goToChooseSimulation">Ganti</button>
            </div>
          </div>
        </div>

        <div class="guide-step" :class="{ active: simulationType && !canSubmit, muted: !simulationType }">
          <div class="step-number">2</div>
          <div class="step-body">
            <h3 class="step-title">Upload Dokumen</h3>
            <p class="step-desc">
              Unggah dokumen pendukung sesuai jenis simulasi yang dipilih.
            </p>
            <div class="step-files">
              <div
                class="mini-upload"
                :class="{ 'has-files': files.length > 0 }"
                @click="triggerFileInput"
              >
                <input ref="fileInput" type="file" multiple accept=".pdf,.md,.txt" @change="handleFileSelect" style="display: none" />
                <span v-if="files.length === 0">+ Klik untuk upload file</span>
                <span v-else>{{ files.length }} file terpilih</span>
              </div>
              <div v-if="files.length > 0" class="file-chips">
                <span v-for="(f, i) in files" :key="i" class="file-chip">
                  {{ f.name }} <button @click.stop="removeFile(i)">×</button>
                </span>
              </div>
            </div>
            <div class="step-hint">{{ uploadHintText }}</div>
          </div>
        </div>

        <div class="guide-step" :class="{ active: simulationType && canSubmit && !loading, muted: !simulationType }">
          <div class="step-number">3</div>
          <div class="step-body">
            <h3 class="step-title">Deskripsi Kebutuhan</h3>
            <p class="step-desc">
              Jelaskan kebutuhan simulasi Anda dalam bahasa alami. Semakin
              detail deskripsi Anda, semakin akurat hasil simulasi.
            </p>
            <textarea
              v-model="formData.simulationRequirement"
              class="step-textarea"
              :placeholder="descPlaceholderText"
              rows="3"
            ></textarea>
          </div>
        </div>

        <div class="guide-step" :class="{ active: simulationType && canSubmit }">
          <div class="step-number final">4</div>
          <div class="step-body">
            <h3 class="step-title">Jalankan Simulasi</h3>
            <p class="step-desc">
              Setelah semua langkah terpenuhi, klik tombol di bawah untuk
              memulai proses simulasi.
            </p>
            <button
              class="step-btn start-btn"
              @click="startSimulation"
              :disabled="!canSubmit || loading"
            >
              <span v-if="!loading">🚀 Jalankan Simulasi</span>
              <span v-else>⏳ Memproses...</span>
              <span class="btn-arrow">→</span>
            </button>
            <div v-if="!simulationType" class="step-hint warn">
              Selesaikan Langkah 1 (Pilih Jenis Simulasi) terlebih dahulu
            </div>
            <div v-else-if="!canSubmit" class="step-hint">
              Upload file dan tulis deskripsi kebutuhan untuk mengaktifkan tombol
            </div>
          </div>
        </div>
      </section>

      <!-- Fitur Tambahan -->
      <section class="feature-section">
        <h2 class="section-title">Fitur Lainnya</h2>
        <div class="feature-cards">
          <div class="feature-card" @click="$router.push('/parliament')">
            <div class="card-icon-wrap">
              <span class="card-icon">🧠</span>
            </div>
            <h3 class="card-title">Debat Internal</h3>
            <p class="card-desc">
              Simulasi perdebatan multi-perspektif dalam diri agen sebelum
              menentukan jawaban survei.
            </p>
            <div class="card-tags">
              <span class="tag">Logika</span>
              <span class="tag">Emosi</span>
              <span class="tag">Sosial</span>
            </div>
          </div>

          <div class="feature-card" @click="$router.push('/survey-results')">
            <div class="card-icon-wrap">
              <span class="card-icon">📊</span>
            </div>
            <h3 class="card-title">Hasil Survei</h3>
            <p class="card-desc">
              Lihat statistik deskriptif, distribusi frekuensi, tabulasi
              silang, dan unduh PDF laporan akademik.
            </p>
            <div class="card-tags">
              <span class="tag">Statistik</span>
              <span class="tag">PDF</span>
            </div>
          </div>
        </div>
      </section>

      <HistoryDatabase />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import NavBar from '../components/NavBar.vue'
import HistoryDatabase from '../components/HistoryDatabase.vue'
import pendingStore, { setSimulationType, setPendingUpload, setCustomScenario } from '../store/pendingUpload.js'

const router = useRouter()
const route = useRoute()
const formData = ref({ simulationRequirement: '' })
const files = ref([])
const loading = ref(false)
const fileInput = ref(null)
const simulationType = ref(pendingStore.simulationType)
const customScenario = reactive({ ...pendingStore.customScenario })

const params = reactive({
  agentCount: 500,
  maxRounds: 10,
  platform: 'both',
  likertScale: 5
})

const typeLabels = {
  academic: 'Akademik',
  political: 'Politik',
  market: 'Riset Pasar',
  social: 'Sosial',
  custom: 'Kustom'
}

const canSubmit = computed(() =>
  simulationType.value && formData.value.simulationRequirement.trim() !== '' && files.value.length > 0
)

const uploadHintText = computed(() => {
  const hints = {
    academic: 'Upload paper penelitian, jurnal, skripsi, tesis, atau artikel ilmiah',
    political: 'Upload berita, artikel opini, dokumen kebijakan, pidato, press release',
    market: 'Upload proposal produk, business plan, laporan pasar, analisis kompetitor',
    social: 'Upload campuran berita, data sosial, opini publik, artikel',
    custom: 'Upload dokumen sesuai skenario yang Anda tulis di atas'
  }
  return hints[simulationType.value] || 'Format: PDF, MD, TXT'
})

const descPlaceholderText = computed(() => {
  const placeholders = {
    academic: 'Contoh: Saya ingin mensimulasikan opini publik akademik tentang kebijakan pendidikan terbaru di Indonesia berdasarkan paper yang saya upload...',
    political: 'Contoh: Saya ingin mensimulasikan respons publik terhadap kebijakan baru berdasarkan berita yang saya upload...',
    market: 'Contoh: Saya ingin menganalisis persepsi pasar terhadap produk baru berdasarkan proposal dan data yang saya upload...',
    social: 'Contoh: Saya ingin mensimulasikan opini publik campuran tentang isu sosial terkini dari berbagai sumber...',
    custom: 'Jelaskan skenario simulasi yang Anda inginkan secara detail...'
  }
  return placeholders[simulationType.value] || 'Jelaskan kebutuhan simulasi Anda...'
})

function goToChooseSimulation() {
  router.push({ name: 'SimulationType' })
}

// Welcome Screen
import logoImg from '../assets/logo/KINJENG_Project_logo_compressed.jpeg'
const showWelcome = ref(true)
const isLogoFlying = ref(false)
const isLogoExpanding = ref(false)
const welcomeClickable = ref(true)

function handleLogoClick() {
  if (!welcomeClickable.value) return
  isLogoFlying.value = true
  welcomeClickable.value = false
  setTimeout(() => {
    isLogoFlying.value = false
    welcomeClickable.value = true
  }, 1200)
}

function startWelcomeClick() {
  if (!welcomeClickable.value) return
  welcomeClickable.value = false
  isLogoExpanding.value = true
  setTimeout(() => {
    showWelcome.value = false
    isLogoExpanding.value = false
    welcomeClickable.value = true
  }, 800)
}

watch(() => route.query, (query) => {
  if (query.skipWelcome === 'true') {
    showWelcome.value = false
  }
  if (query.type) {
    simulationType.value = query.type
    params.agentCount = Number(query.agentCount) || 500
    params.maxRounds = Number(query.maxRounds) || 10
    params.platform = query.platform || 'both'
    params.likertScale = Number(query.likertScale) || 5
    setSimulationType(query.type, { ...params })
    if (query.type === 'custom') {
      customScenario.title = query.scenarioTitle || ''
      customScenario.context = query.scenarioContext || ''
      customScenario.agentRules = query.scenarioRules || ''
      setCustomScenario({ ...customScenario })
    }
  }
}, { immediate: true })

const triggerFileInput = () => { fileInput.value?.click() }
const handleFileSelect = (e) => { addFiles(Array.from(e.target.files)) }
const addFiles = (newFiles) => {
  files.value.push(...newFiles.filter(f => ['pdf', 'md', 'txt'].includes(f.name.split('.').pop().toLowerCase())))
}
const removeFile = (index) => { files.value.splice(index, 1) }

const startSimulation = async () => {
  if (!canSubmit.value || loading.value) return
  loading.value = true
  if (simulationType.value === 'custom') {
    setCustomScenario({ ...customScenario })
  }
  setPendingUpload(files.value, formData.value.simulationRequirement)
  await nextTick()
  router.push({ name: 'Process', params: { projectId: 'new' } })
}
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: var(--font-sans);
}

.main-content {
  max-width: 1000px;
  margin: 0 auto;
  padding: 40px;
}

/* Hero */
.hero-section {
  margin-bottom: 40px;
  padding-bottom: 32px;
  border-bottom: 2px solid var(--border-color);
}

.hero-badge {
  display: inline-block;
  font-family: var(--font-mono);
  font-size: 0.7rem;
  padding: 4px 10px;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  margin-bottom: 16px;
  letter-spacing: 1px;
}

.hero-title {
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 12px 0;
  line-height: 1.2;
}

.hero-desc {
  font-size: 0.95rem;
  color: var(--text-secondary);
  line-height: 1.7;
  max-width: 700px;
}

/* Guide Steps */
.guide-steps {
  display: flex;
  flex-direction: column;
  gap: 0;
  margin-bottom: 48px;
  border: 1px solid var(--border-color);
}

.guide-step {
  display: flex;
  gap: 20px;
  padding: 24px 28px;
  border-bottom: 1px solid var(--border-color);
  transition: all 0.3s;
}

.guide-step:last-child {
  border-bottom: none;
}

.guide-step.muted {
  opacity: 0.4;
}

.guide-step.active {
  background: var(--bg-selected);
  border-left: 3px solid var(--accent-primary);
}

.step-number {
  width: 36px;
  height: 36px;
  min-width: 36px;
  border: 2px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.guide-step.active .step-number {
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}

.step-number.final {
  border-color: var(--success);
  color: var(--success);
}

.step-body {
  flex: 1;
}

.step-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 6px 0;
}

.step-desc {
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 12px;
}

.step-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: var(--black);
  color: var(--white);
  border: none;
  font-family: var(--font-mono);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.step-btn:hover:not(:disabled) {
  background: var(--accent-primary);
}

.step-btn:disabled {
  background: var(--border-color);
  color: var(--text-tertiary);
  cursor: not-allowed;
}

.step-btn.start-btn {
  padding: 14px 28px;
  font-size: 0.9rem;
  font-weight: 700;
  letter-spacing: 1px;
}

.btn-arrow {
  font-size: 1rem;
}

.step-done {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-left: 12px;
  font-size: 0.8rem;
  color: var(--success);
  font-family: var(--font-mono);
  font-weight: 600;
}

.step-files {
  margin-bottom: 6px;
}

.mini-upload {
  display: inline-block;
  padding: 8px 16px;
  border: 1px dashed var(--border-color);
  cursor: pointer;
  font-family: var(--font-mono);
  font-size: 0.8rem;
  color: var(--text-secondary);
  transition: all 0.3s;
  background: var(--bg-secondary);
}

.mini-upload:hover {
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}

.mini-upload.has-files {
  border-style: solid;
  color: var(--success);
}

.file-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.file-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  font-family: var(--font-mono);
  font-size: 0.75rem;
}

.file-chip button {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-tertiary);
  font-size: 1rem;
  line-height: 1;
}

.file-chip button:hover {
  color: var(--danger);
}

.step-textarea {
  width: 100%;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  padding: 12px 16px;
  font-family: var(--font-mono);
  font-size: 0.85rem;
  line-height: 1.6;
  resize: vertical;
  outline: none;
  color: var(--text-primary);
  min-height: 80px;
}

.step-textarea:focus {
  border-color: var(--accent-primary);
}

.step-hint {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  font-family: var(--font-mono);
  margin-top: 8px;
}

.step-hint.warn {
  color: var(--warning);
}

/* Inline Type Select (simplified) */
.type-select-inline {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 12px 0;
  flex-wrap: wrap;
}
.type-select-inline .step-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: var(--black);
  color: var(--white);
  border: none;
  font-family: var(--font-mono);
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}
.type-select-inline .step-btn:hover {
  background: var(--accent-primary);
}
.type-select-inline .step-desc {
  font-size: 0.82rem;
  color: var(--text-secondary);
  margin: 0;
  flex: 1;
  min-width: 200px;
}
.type-selected-inline {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 12px 0;
  flex-wrap: wrap;
}
.type-selected-inline .step-done {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--success);
  font-family: var(--font-mono);
}
.type-selected-inline .step-summary {
  font-size: 0.78rem;
  color: var(--text-secondary);
  font-family: var(--font-mono);
}
.step-btn-small {
  padding: 4px 12px;
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: 0.72rem;
  cursor: pointer;
  transition: all 0.2s;
}
.step-btn-small:hover {
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}

.section-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 16px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--black);
}

.feature-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.feature-card {
  border: 1px solid var(--border-color);
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s;
  background: var(--bg-card);
}

.feature-card:hover {
  border-color: var(--accent-primary);
  transform: translateY(-2px);
  box-shadow: var(--shadow);
}

.card-icon-wrap {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 14px;
  background: var(--bg-secondary);
  font-size: 1.2rem;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 6px 0;
}

.card-desc {
  font-size: 0.82rem;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 12px;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  font-size: 0.68rem;
  padding: 2px 8px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  font-family: var(--font-mono);
  color: var(--text-secondary);
}

/* Welcome Overlay */
.welcome-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: var(--bg-primary, #000);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.welcome-center {
  text-align: center;
  animation: welcomeFadeIn 1s ease-out;
}
@keyframes welcomeFadeIn {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}
.welcome-logo {
  width: 160px;
  height: auto;
  margin-bottom: 24px;
  cursor: pointer;
  transition: all 0.3s;
  border-radius: 12px;
  animation: logoFloat 4s ease-in-out infinite;
}
@keyframes logoFloat {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  25% { transform: translateY(-12px) rotate(-2deg); }
  50% { transform: translateY(-6px) rotate(1deg); }
  75% { transform: translateY(-18px) rotate(-1deg); }
}
.welcome-logo.logo-flying {
  animation: logoFlyOut 1.2s ease-in-out forwards;
}
@keyframes logoFlyOut {
  0% { transform: translate(0, 0) scale(1) rotate(0deg); }
  30% { transform: translate(100px, -150px) scale(1.3) rotate(15deg); }
  60% { transform: translate(-80px, 100px) scale(0.8) rotate(-20deg); }
  100% { transform: translate(0, 0) scale(1) rotate(0deg); }
}
.welcome-logo.logo-expand {
  animation: logoExpand 0.8s ease-in-out forwards;
}
@keyframes logoExpand {
  0% { transform: scale(1); opacity: 1; }
  100% { transform: scale(50); opacity: 0.3; }
}
.welcome-title {
  font-size: 2.5rem;
  font-weight: 800;
  font-family: var(--font-mono);
  margin: 0 0 8px;
  letter-spacing: 2px;
}
.welcome-accent {
  color: var(--accent-primary, #FF4500);
}
.welcome-subtitle {
  font-size: 0.9rem;
  color: var(--text-secondary, #888);
  margin: 0 0 32px;
  font-family: var(--font-mono);
}
.welcome-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 14px 36px;
  background: var(--accent-primary, #FF4500);
  color: #fff;
  border: none;
  font-family: var(--font-mono);
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s;
  letter-spacing: 1px;
}
.welcome-btn:hover {
  background: var(--black, #000);
  transform: translateY(-2px);
}
.welcome-hint {
  font-size: 0.7rem;
  color: var(--text-tertiary, #555);
  margin-top: 20px;
  font-family: var(--font-mono);
}
.welcome-fade-enter-active,
.welcome-fade-leave-active {
  transition: opacity 0.5s ease;
}
.welcome-fade-enter-from,
.welcome-fade-leave-to {
  opacity: 0;
}
@media (min-width: 1200px) {
  .welcome-logo { width: 220px; }
  .welcome-title { font-size: 3rem; }
}
@media (max-width: 480px) {
  .welcome-logo { width: 120px; }
  .welcome-title { font-size: 1.6rem; }
  .welcome-subtitle { font-size: 0.75rem; }
  .welcome-btn { padding: 12px 24px; font-size: 0.85rem; }
}

@media (max-width: 700px) {
  .feature-cards {
    grid-template-columns: 1fr;
  }
  .main-content {
    padding: 20px;
  }
  .guide-step {
    flex-direction: column;
    gap: 12px;
  }
}
</style>
