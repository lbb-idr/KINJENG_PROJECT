<template>
  <div class="results-container">
    <NavBar />

    <div class="main-content">
      <div class="header">
        <h1 class="page-title">📊 Hasil Survei</h1>
        <p class="page-desc">Statistik deskriptif, distribusi frekuensi, dan unduh PDF laporan akademik.</p>
      </div>

      <!-- Project Selector -->
      <div class="project-bar">
        <select v-model="selectedProject" class="project-select" @change="loadResults">
          <option value="">-- Pilih Project --</option>
          <option v-for="p in projects" :key="p" :value="p">{{ p }}</option>
        </select>
        <button class="refresh-btn" @click="refreshProjects">↻</button>
      </div>

      <div v-if="loading" class="loading-state">⏳ Memuat data...</div>
      <div v-if="error" class="error-box">{{ error }}</div>

      <!-- Stats Dashboard -->
      <template v-if="stats">
        <div class="summary-card" v-if="stats.summary">
          <p class="summary-text">{{ stats.summary.text }}</p>
        </div>

        <!-- Metric Cards -->
        <div class="metrics-row">
          <div class="metric-card">
            <div class="metric-value">{{ stats.total_respondents }}</div>
            <div class="metric-label">Responden</div>
          </div>
          <div class="metric-card">
            <div class="metric-value">{{ stats.total_questions }}</div>
            <div class="metric-label">Pertanyaan</div>
          </div>
          <div class="metric-card" v-if="stats.cronbach_alpha !== null && stats.cronbach_alpha !== undefined">
            <div class="metric-value" :class="alphaClass">{{ stats.cronbach_alpha.toFixed(3) }}</div>
            <div class="metric-label">Cronbach's α</div>
          </div>
          <div class="metric-card" v-if="stats.summary">
            <div class="metric-value">{{ stats.summary.overall_mean.toFixed(2) }}/{{ stats.likert_scale }}</div>
            <div class="metric-label">Mean Rata-rata</div>
          </div>
        </div>

        <!-- Descriptive Stats Table -->
        <div class="section">
          <h2 class="section-title">📋 Statistik Deskriptif</h2>
          <div class="table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th>#</th><th>Pertanyaan</th><th>N</th><th>Mean</th><th>SD</th><th>Min</th><th>Max</th><th>Rel. Mean</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(desc, qid, i) in stats.descriptives" :key="qid">
                  <td>{{ i + 1 }}</td>
                  <td class="q-text">{{ desc.question_text || qid }}</td>
                  <td>{{ desc.n }}</td>
                  <td>{{ desc.mean }}</td>
                  <td>{{ desc.std_dev }}</td>
                  <td>{{ desc.min }}</td>
                  <td>{{ desc.max }}</td>
                  <td>{{ desc.relative_mean }}%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Frequency Distributions -->
        <div class="section">
          <h2 class="section-title">📊 Distribusi Frekuensi</h2>
          <div v-for="(freq, qid) in stats.frequencies" :key="qid" class="freq-card">
            <h3 class="freq-title">{{ qid }}: {{ freq.question_text }}</h3>
            <div class="bar-chart" v-if="freq.type === 'likert'">
              <div v-for="(val, score) in freq.distribution" :key="score" class="bar-item">
                <div class="bar-label">{{ score }}</div>
                <div class="bar-track">
                  <div class="bar-fill" :style="{ width: val.percentage + '%' }"></div>
                </div>
                <div class="bar-value">{{ val.count }}</div>
                <div class="bar-pct">{{ val.percentage }}%</div>
              </div>
            </div>
            <div v-else-if="freq.type === 'mcq'" class="mcq-table-wrap">
              <table class="data-table mcq-table">
                <thead><tr><th>Pilihan</th><th>Frekuensi</th><th>%</th></tr></thead>
                <tbody>
                  <tr v-for="(val, opt) in freq.distribution" :key="opt">
                    <td>{{ opt }}</td><td>{{ val.count }}</td><td>{{ val.percentage }}%</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else-if="freq.type === 'open'" class="open-responses">
              <p class="open-count">{{ freq.total_responses }} respons terbuka</p>
              <div v-for="resp in (freq.responses || []).slice(0, 5)" :key="resp" class="open-item">
                “{{ resp }}”
              </div>
            </div>
          </div>
        </div>

        <!-- Cross-tabs -->
        <div class="section" v-if="stats.cross_tabs && stats.cross_tabs.length">
          <h2 class="section-title">🔗 Tabulasi Silang</h2>
          <div v-for="ct in stats.cross_tabs" :key="ct.field" class="cross-tab">
            <h3 class="freq-title">Berdasarkan {{ ct.field }}</h3>
            <div class="table-wrap">
              <table class="data-table">
                <thead><tr><th>Kelompok</th><th>N</th><th>Mean</th><th>Std</th></tr></thead>
                <tbody>
                  <tr v-for="g in ct.groups" :key="g.group">
                    <td>{{ g.group }}</td><td>{{ g.n }}</td><td>{{ g.mean }}</td><td>{{ g.std }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- PDF Download -->
        <div class="section pdf-section">
          <h2 class="section-title">📄 Laporan PDF</h2>
          <p>Generate laporan format PDF yang siap untuk publikasi akademik.</p>
          <div class="pdf-actions">
            <button class="pdf-btn" @click="generatePDF" :disabled="generating">
              {{ generating ? '⏳ Mengenerate...' : '📄 Generate PDF' }}
            </button>
            <a v-if="pdfReady" :href="pdfUrl" class="download-link" download>⬇ Download PDF</a>
          </div>
          <div v-if="pdfError" class="error-box">{{ pdfError }}</div>
        </div>
      </template>

      <div v-else-if="!loading && selectedProject" class="empty-state">
        <p>Tidak ada data. Jalankan survei dulu.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import NavBar from '../components/NavBar.vue'

const route = useRoute()
const router = useRouter()
const API = 'http://localhost:5001/api'

const selectedProject = ref('')
const projects = ref([])
const stats = ref(null)
const loading = ref(false)
const error = ref('')
const generating = ref(false)
const pdfReady = ref(false)
const pdfError = ref('')

const pdfUrl = computed(() => `${API}/survey/report/${selectedProject.value}`)

const alphaClass = computed(() => {
  if (!stats.value?.cronbach_alpha) return ''
  const a = stats.value.cronbach_alpha
  if (a >= 0.7) return 'alpha-good'
  if (a >= 0.5) return 'alpha-mid'
  return 'alpha-bad'
})

onMounted(async () => {
  await refreshProjects()
  // Auto-select project dari query param
  const projectFromQuery = route.query.project
  if (projectFromQuery && projects.value.includes(projectFromQuery)) {
    selectedProject.value = projectFromQuery
    loadResults()
  } else if (projectFromQuery) {
    // Project belum di-load, tunggu dan coba lagi
    selectedProject.value = projectFromQuery
    const unwatch = watch(projects, (vals) => {
      if (vals.includes(projectFromQuery)) {
        loadResults()
        unwatch()
      }
    })
  }
})

async function refreshProjects() {
  try {
    const { data } = await axios.get(`${API}/survey/results`)
    if (data.success) projects.value = data.data.projects || []
  } catch (e) {
    error.value = 'Gagal memuat daftar project'
  }
}

async function loadResults() {
  if (!selectedProject.value) return
  loading.value = true
  error.value = ''
  stats.value = null
  pdfReady.value = false
  try {
    const { data } = await axios.get(`${API}/survey/results/${selectedProject.value}/statistics`)
    if (data.success) stats.value = data.data
    else error.value = data.error
  } catch (e) {
    error.value = e.response?.data?.error || e.message
  } finally {
    loading.value = false
  }
}

async function generatePDF() {
  if (!selectedProject.value) return
  generating.value = true
  pdfError.value = ''
  pdfReady.value = false
  try {
    const { data } = await axios.post(`${API}/survey/report/generate/${selectedProject.value}`)
    if (data.success) pdfReady.value = true
    else pdfError.value = data.error
  } catch (e) {
    pdfError.value = e.response?.data?.error || e.message
  } finally {
    generating.value = false
  }
}
</script>

<style scoped>
.results-container { min-height: 100vh; background: var(--bg-primary); color: var(--text-primary); font-family: var(--font-sans); }
.main-content { max-width: 1200px; margin: 0 auto; padding: 30px 40px; }
.header { margin-bottom: 24px; }
.page-title { font-size: 2rem; font-weight: 600; margin: 0 0 8px; }
.page-desc { color: var(--text-secondary); font-size: 0.95rem; }

.project-bar { display: flex; gap: 10px; margin-bottom: 24px; }
.project-select { flex: 1; padding: 12px; border: 1px solid var(--border-color); background: var(--bg-card); font-family: var(--font-mono); color: var(--text-primary); }
.project-select:focus { outline: none; border-color: var(--accent-primary); }
.refresh-btn { padding: 8px 16px; border: 1px solid var(--border-color); background: var(--bg-card); cursor: pointer; color: var(--text-primary); }

.loading-state { text-align: center; padding: 40px; color: var(--text-secondary); }
.error-box { padding: 12px; background: var(--bg-secondary); border: 1px solid var(--danger); color: var(--danger); font-size: 0.85rem; margin-bottom: 16px; }

.summary-card { border: 2px solid var(--black); padding: 20px; margin-bottom: 20px; background: var(--bg-card); }
.summary-text { font-size: 0.95rem; line-height: 1.6; }

.metrics-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin-bottom: 24px; }
.metric-card { border: 1px solid var(--border-color); padding: 20px; text-align: center; background: var(--bg-card); }
.metric-value { font-size: 1.8rem; font-weight: 700; font-family: var(--font-mono); }
.metric-label { font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px; font-family: var(--font-mono); }
.alpha-good { color: var(--success); }
.alpha-mid { color: var(--warning); }
.alpha-bad { color: var(--danger); }

.section { margin-bottom: 30px; }
.section-title { font-size: 1.2rem; font-weight: 600; margin: 0 0 14px 0; padding-bottom: 8px; border-bottom: 2px solid var(--black); }

.table-wrap { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-family: var(--font-mono); font-size: 0.8rem; }
.data-table th { background: var(--black); color: var(--white); padding: 10px 8px; text-align: center; font-weight: 600; }
.data-table td { padding: 8px; text-align: center; border-bottom: 1px solid var(--border-color); }
.data-table tr:nth-child(even) td { background: var(--bg-secondary); }
.q-text { text-align: left; max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.freq-card { border: 1px solid var(--border-color); padding: 16px; margin-bottom: 14px; background: var(--bg-card); }
.freq-title { font-size: 0.9rem; font-weight: 600; margin: 0 0 12px; }
.bar-chart { display: flex; flex-direction: column; gap: 6px; }
.bar-item { display: flex; align-items: center; gap: 10px; font-family: var(--font-mono); font-size: 0.8rem; }
.bar-label { min-width: 24px; font-weight: 600; text-align: center; }
.bar-track { flex: 1; height: 20px; background: var(--bg-secondary); border-radius: 2px; overflow: hidden; }
.bar-fill { height: 100%; background: var(--accent-primary); transition: width 0.5s; border-radius: 2px; }
.bar-value { min-width: 30px; text-align: center; font-weight: 600; }
.bar-pct { min-width: 40px; text-align: right; color: var(--text-secondary); }
.mcq-table-wrap { overflow-x: auto; }
.mcq-table { min-width: 300px; }
.open-responses { }
.open-count { font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 8px; }
.open-item { padding: 8px 12px; margin-bottom: 6px; background: var(--bg-secondary); font-style: italic; font-size: 0.85rem; border-left: 3px solid var(--accent-primary); }

.cross-tab { margin-bottom: 16px; }

.pdf-section { }
.pdf-actions { display: flex; gap: 14px; align-items: center; margin-top: 12px; }
.pdf-btn { padding: 14px 28px; background: var(--black); color: var(--white); border: none; font-family: var(--font-mono); font-weight: 700; cursor: pointer; transition: all 0.3s; }
.pdf-btn:hover:not(:disabled) { background: var(--accent-primary); }
.pdf-btn:disabled { background: var(--border-color); color: var(--text-tertiary); cursor: not-allowed; }
.download-link { padding: 14px 28px; background: var(--accent-primary); color: white; text-decoration: none; font-family: var(--font-mono); font-weight: 700; }

.empty-state { text-align: center; padding: 60px; color: var(--text-secondary); border: 1px dashed var(--border-color); }
</style>
