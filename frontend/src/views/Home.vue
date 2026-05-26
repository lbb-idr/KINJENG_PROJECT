<template>
  <div class="home-container">
    <NavBar />

    <div class="main-content">
      <!-- Hero / Instruksi Awal -->
      <section class="hero-section">
        <div class="hero-badge">MIROFISH v0.1</div>
        <h1 class="hero-title">Selamat Datang di MiroFish</h1>
        <p class="hero-desc">
          Platform simulasi multi-agent untuk riset akademik, polling politik,
          riset pasar, dan simulasi sosial. Ikuti langkah-langkah di bawah ini
          untuk memulai.
        </p>
      </section>

      <!-- Panduan Langkah -->
      <section class="guide-steps">
        <div class="guide-step" :class="{ active: !simulationType }">
          <div class="step-number">1</div>
          <div class="step-body">
            <h3 class="step-title">Pilih Jenis Simulasi</h3>
            <p class="step-desc">
              Tentukan jenis simulasi yang sesuai dengan kebutuhan riset Anda.
              Tersedia pilihan: Akademik, Politik, Market, Sosial, atau Kustom.
            </p>
            <button class="step-btn" @click="$router.push('/choose-simulation')">
              {{ simulationType ? 'Ubah Jenis Simulasi' : 'Pilih Sekarang' }}
              <span class="btn-arrow">→</span>
            </button>
            <span v-if="simulationType" class="step-done">✓ {{ typeLabels[simulationType] || simulationType }}</span>
          </div>
        </div>

        <div class="guide-step" :class="{ active: simulationType && !canSubmit, muted: !simulationType }">
          <div class="step-number">2</div>
          <div class="step-body">
            <h3 class="step-title">Upload Dokumen</h3>
            <p class="step-desc">
              Unggah dokumen pendukung seperti PDF, Markdown, atau file teks
              yang berisi data atau referensi untuk simulasi.
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
            <div class="step-hint">Format: PDF, MD, TXT</div>
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
              :placeholder="'Contoh: Saya ingin mensimulasikan opini publik tentang kebijakan pendidikan terbaru di Indonesia...'"
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
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import NavBar from '../components/NavBar.vue'
import HistoryDatabase from '../components/HistoryDatabase.vue'
import pendingStore, { setSimulationType, setPendingUpload } from '../store/pendingUpload.js'

const router = useRouter()
const route = useRoute()
const formData = ref({ simulationRequirement: '' })
const files = ref([])
const loading = ref(false)
const isDragOver = ref(false)
const fileInput = ref(null)
const simulationType = ref(pendingStore.simulationType)

const typeLabels = {
  academic: 'Akademik',
  political: 'Politik',
  market: 'Market',
  social: 'Sosial',
  custom: 'Kustom'
}

const canSubmit = computed(() =>
  simulationType.value && formData.value.simulationRequirement.trim() !== '' && files.value.length > 0
)

watch(() => route.query, (query) => {
  if (query.type) {
    setSimulationType(query.type, {
      agentCount: Number(query.agentCount) || 500,
      maxRounds: Number(query.maxRounds) || 10,
      platform: query.platform || 'both',
      likertScale: Number(query.likertScale) || 5
    })
    simulationType.value = query.type
  }
}, { immediate: true })

const triggerFileInput = () => { fileInput.value?.click() }
const handleFileSelect = (e) => { addFiles(Array.from(e.target.files)) }
const addFiles = (newFiles) => {
  files.value.push(...newFiles.filter(f => ['pdf', 'md', 'txt'].includes(f.name.split('.').pop().toLowerCase())))
}
const removeFile = (index) => { files.value.splice(index, 1) }

const startSimulation = () => {
  if (!canSubmit.value || loading.value) return
  loading.value = true
  setPendingUpload(files.value, formData.value.simulationRequirement)
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

/* Feature Section */
.feature-section {
  margin-bottom: 40px;
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
