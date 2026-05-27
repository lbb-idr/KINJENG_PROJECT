<template>
  <div class="results-container">
    <header class="step-header">
      <div class="header-left">
        <div class="brand" @click="router.push('/')">KINJENG</div>
      </div>
      <div class="header-center">
        <div class="workflow-step">
          <span class="step-num">Langkah 5/5</span>
          <span class="step-name">Hasil Survei</span>
        </div>
      </div>
      <div class="header-right">
        <NavBar />
      </div>
    </header>

    <!-- Simulasi History Bar -->
    <div v-if="simHistory" class="sim-history-bar">
      <div class="sim-hist-item">
        <span class="hist-label">Agen</span>
        <span class="hist-value">{{ simHistory.agentCount || '-' }}</span>
      </div>
      <div class="sim-hist-divider"></div>
      <div class="sim-hist-item">
        <span class="hist-label">Ronde</span>
        <span class="hist-value">{{ simHistory.roundsCompleted || '-' }}</span>
      </div>
      <div class="sim-hist-divider"></div>
      <div class="sim-hist-item">
        <span class="hist-label">Respon</span>
        <span class="hist-value">{{ simHistory.totalResponses || '-' }}</span>
      </div>
      <div class="sim-hist-divider"></div>
      <div class="sim-hist-item">
        <span class="hist-label">Platform</span>
        <span class="hist-value">{{ simHistory.platform || '-' }}</span>
      </div>
      <div class="sim-hist-divider"></div>
      <div class="sim-hist-item">
        <span class="hist-label">Status</span>
        <span class="hist-value" :class="simHistory.statusClass">{{ simHistory.statusText }}</span>
      </div>
    </div>

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
        <button v-if="selectedProject" class="btn-delete-project" @click="deleteProjectData(selectedProject)" title="Hapus data project ini">✕</button>
        <button class="refresh-btn" @click="refreshProjects">↻</button>
      </div>

      <div v-if="loading" class="loading-state">⏳ Memuat data...</div>
      <div v-if="runningSurvey" class="running-survey-state">
        <div class="running-spinner"></div>
        <p class="running-text">⏳ Mengenerate dan menjalankan survei...</p>
        <p class="running-sub">Ini mungkin memakan waktu beberapa saat</p>
      </div>
      <div v-if="error && !runningSurvey" class="error-box">{{ error }}</div>
      <div v-if="showRunButton" class="run-survey-box">
        <p>Hasil survei belum tersedia untuk project ini.</p>
        <p class="run-survey-hint">Survei akan menggunakan data simulasi yang sudah selesai untuk menghasilkan kuesioner dan menjalankannya ke agen.</p>
        <button class="run-survey-btn" @click="runSurveyForProject">
          🚀 Jalankan Survei Sekarang
        </button>
      </div>

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

        <!-- Report Summary dari Step 4 -->
        <div v-if="reportSummary || reportSections.length" class="section report-summary-section">
          <h2 class="section-title">📄 Ringkasan Laporan Simulasi</h2>
          <p v-if="reportSummary" class="report-summary-text">{{ reportSummary }}</p>
          <ul v-if="reportSections.length" class="report-section-list">
            <li v-for="(sec, i) in reportSections" :key="i">{{ sec }}</li>
          </ul>
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

        <!-- Customize Questions (sebelum PDF) -->
        <div class="section customize-section">
          <h2 class="section-title">✏️ Kustomisasi Pertanyaan</h2>
          <p>Ubah, tambah, atau hapus pertanyaan survei. Setelah selesai, jalankan ulang survei untuk melihat hasil terbaru.</p>
          <div v-if="surveyConfig" class="editor-inline">
            <SurveyQuestionEditor ref="editorRef" :survey="surveyConfig" @update:survey="onSurveyUpdate" />
            <div class="editor-actions">
              <button class="btn-regenerate" @click="regenerateSurvey">🔄 Generate Ulang</button>
              <button class="btn-run-custom" @click="runSurveyWithCustomQuestions" :disabled="runningSurvey">
                {{ runningSurvey ? '⏳ Menjalankan...' : '🚀 Jalankan Ulang Survei' }}
              </button>
            </div>
          </div>
          <div v-else class="no-editor-placeholder">
            <p>Klik tombol di bawah untuk memuat pertanyaan survei dan melakukan kustomisasi.</p>
            <button class="btn-load-questions" @click="loadQuestionsForEditing">📋 Muat Pertanyaan</button>
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
import SurveyQuestionEditor from '../components/SurveyQuestionEditor.vue'

const route = useRoute()
const router = useRouter()
const API = import.meta.env.VITE_API_BASE_URL ? import.meta.env.VITE_API_BASE_URL + '/api' : (import.meta.env.PROD ? '/api' : 'http://localhost:5001/api')

const selectedProject = ref('')
const projects = ref([])
const stats = ref(null)
const loading = ref(false)
const error = ref('')
const generating = ref(false)
const pdfReady = ref(false)
const pdfError = ref('')
const runningSurvey = ref(false)
const showRunButton = ref(false)
const surveyConfig = ref(null)
const editorRef = ref(null)

// Simulation history data
const simHistory = ref(null)
let simId = null

// Report summary dari Step 4
const reportSummary = ref(null)
const reportSections = ref([])

const pdfUrl = computed(() => `${API}/survey/report/${selectedProject.value}`)

const alphaClass = computed(() => {
  if (!stats.value?.cronbach_alpha) return ''
  const a = stats.value.cronbach_alpha
  if (a >= 0.7) return 'alpha-good'
  if (a >= 0.5) return 'alpha-mid'
  return 'alpha-bad'
})

async function loadSimHistory(simId) {
  try {
    const { data: simData } = await axios.get(`${API}/simulation/${simId}`)
    if (!simData.success) return
    const sim = simData.data
    const { data: configData } = await axios.get(`${API}/simulation/${simId}/config`)
    const config = configData.success ? configData.data : {}
    const maxRounds = config?.time_config ? Math.round(
      (config.time_config.total_simulation_hours || 0) * 60 /
      Math.max(config.time_config.minutes_per_round || 60, 1)
    ) : 0
    const enableTwitter = sim.enable_twitter
    const enableReddit = sim.enable_reddit
    const platform = enableTwitter && enableReddit ? 'Twitter + Reddit'
      : enableTwitter ? 'Twitter' : 'Reddit'
    simHistory.value = {
      agentCount: sim.profiles_count || sim.entities_count || 0,
      roundsCompleted: `${sim.current_round || 0}/${maxRounds}`,
      totalResponses: (sim.profiles_count || 0) * (sim.current_round || 0),
      platform,
      statusText: sim.status === 'completed' ? 'Selesai' : 'Processing',
      statusClass: sim.status === 'completed' ? 'status-completed' : 'status-processing'
    }
  } catch (e) {
    console.warn('Gagal load sim history:', e.message)
  }
}

onMounted(async () => {
  await refreshProjects()
  // Auto-select project dari query param
  const projectFromQuery = route.query.project
  const reportId = route.query.reportId
  if (reportId) {
    try {
      const { data: reportData } = await axios.get(`${API}/report/${reportId}`)
      if (reportData.success && reportData.data?.simulation_id) {
        // Simpan outline summary dari Step 4 report
        const outline = reportData.data.outline
        if (outline) {
          reportSummary.value = outline.summary || ''
          reportSections.value = (outline.sections || []).map(s => s.title || s)
        }
        simId = reportData.data.simulation_id
        await loadSimHistory(simId)
        const { data: simData } = await axios.get(`${API}/simulation/${simId}`)
        if (simData.success && simData.data?.project_id) {
          const pid = simData.data.project_id
          selectedProject.value = pid
          loadResults()
        }
      }
    } catch (e) {
      console.warn('Gagal load dari reportId:', e.message)
    }
  } else if (projectFromQuery) {
    selectedProject.value = projectFromQuery
    loadResults()
    // Cari simulation ID dari project ini buat sim history
    try {
      const { data: listData } = await axios.get(`${API}/simulation/list`, { params: { project_id: projectFromQuery } })
      if (listData.success && listData.data?.length > 0) {
        simId = listData.data[listData.data.length - 1].simulation_id
        await loadSimHistory(simId)
      }
    } catch (e) {
      console.warn('Gagal load sim list:', e.message)
    }
  }
})

async function deleteProjectData(pid) {
  const ok = window.confirm(`Hapus semua data survei untuk ${pid}? PDF dan hasil survei akan dihapus.`)
  if (!ok) return
  try {
    await axios.delete(`${API}/survey/report/${pid}`)
    await axios.delete(`${API}/survey/results/${pid}`)
    const idx = projects.value.indexOf(pid)
    if (idx !== -1) projects.value.splice(idx, 1)
    if (selectedProject.value === pid) {
      selectedProject.value = ''
      stats.value = null
      pdfReady.value = false
    }
  } catch (e) {
    console.warn('Gagal hapus data project:', e)
  }
}

async function refreshProjects() {
  try {
    const { data } = await axios.get(`${API}/survey/results`)
    if (data.success) projects.value = data.data.projects || []
  } catch (e) {
    error.value = 'Gagal memuat daftar project'
  }
}

function selectProject(pid) {
  selectedProject.value = pid
  loadResults()
}

async function loadResults() {
  if (!selectedProject.value) return
  loading.value = true
  error.value = ''
  stats.value = null
  pdfReady.value = false
  showRunButton.value = false
  try {
    const { data } = await axios.get(`${API}/survey/results/${selectedProject.value}/statistics`)
    if (data.success) stats.value = data.data
    else error.value = data.error
  } catch (e) {
    const status = e.response?.status
    if (status === 404) {
      error.value = ''
      if (simId) {
        await autoRunSurvey()
      } else {
        showRunButton.value = true
      }
    } else {
      error.value = e.response?.data?.error || e.message
    }
  } finally {
    loading.value = false
  }
}

async function autoRunSurvey() {
  if (!selectedProject.value || !simId) return
  runningSurvey.value = true
  error.value = ''
  showRunButton.value = false
  surveyConfig.value = null
  try {
    // 1. Ambil simulation state untuk dapat sim_type
    const { data: simState } = await axios.get(`${API}/simulation/${simId}`)
    const simType = simState.success ? (simState.data?.sim_type || 'academic') : 'academic'

    // 2. Ambil simulation config untuk dapat requirement
    const { data: configData } = await axios.get(`${API}/simulation/${simId}/config`)
    const requirement = configData.success
      ? (configData.data?.simulation_requirement || configData.data?.requirement || '')
      : ''
    if (!requirement) throw new Error('Simulasi tidak memiliki deskripsi kebutuhan')

    // 3. Generate survey dari requirement
    const { data: genData } = await axios.post(`${API}/survey/generate`, {
      requirement,
      sim_type: simType
    })
    if (!genData.success) throw new Error(genData.error || 'Gagal generate survey')
    const generatedSurvey = genData.data

    // 4. Run survey
    const { data: runData } = await axios.post(`${API}/survey/run`, {
      project_id: selectedProject.value,
      survey: generatedSurvey,
      agent_count: 50,
      use_llm: false,
      save_results: true
    })
    if (!runData.success) throw new Error(runData.error || 'Gagal run survey')

    // Simpan survey config untuk editor
    surveyConfig.value = generatedSurvey

    // 5. Load hasil
    await loadResults()
  } catch (e) {
    error.value = e.message || 'Gagal menjalankan survei'
  } finally {
    runningSurvey.value = false
  }
}

function onSurveyUpdate(updated) {
  surveyConfig.value = updated
}

async function loadQuestionsForEditing() {
  if (!selectedProject.value || !simId) return
  error.value = ''
  try {
    const { data: simState } = await axios.get(`${API}/simulation/${simId}`)
    const simType = simState.success ? (simState.data?.sim_type || 'academic') : 'academic'
    const { data: configData } = await axios.get(`${API}/simulation/${simId}/config`)
    const requirement = configData.success
      ? (configData.data?.simulation_requirement || configData.data?.requirement || '')
      : ''
    if (!requirement) throw new Error('Simulasi tidak memiliki deskripsi kebutuhan')
    const { data: genData } = await axios.post(`${API}/survey/generate`, {
      requirement,
      sim_type: simType
    })
    if (!genData.success) throw new Error(genData.error || 'Gagal generate survey')
    surveyConfig.value = genData.data
  } catch (e) {
    error.value = e.message || 'Gagal memuat pertanyaan'
  }
}

async function runSurveyWithCustomQuestions() {
  if (!selectedProject.value || !surveyConfig.value) return
  runningSurvey.value = true
  error.value = ''
  try {
    const { data: runData } = await axios.post(`${API}/survey/run`, {
      project_id: selectedProject.value,
      survey: surveyConfig.value,
      agent_count: 50,
      use_llm: false,
      save_results: true
    })
    if (!runData.success) throw new Error(runData.error || 'Gagal run survey')
    await loadResults()
  } catch (e) {
    error.value = e.message || 'Gagal menjalankan survei'
  } finally {
    runningSurvey.value = false
  }
}

async function regenerateSurvey() {
  surveyConfig.value = null
  await autoRunSurvey()
}

async function runSurveyForProject() {
  if (!simId && selectedProject.value) {
    // Cari simulation ID dari project
    try {
      const { data: listData } = await axios.get(`${API}/simulation/list`, { params: { project_id: selectedProject.value } })
      if (listData.success && listData.data?.length > 0) {
        simId = listData.data[listData.data.length - 1].simulation_id
      }
    } catch (e) {
      error.value = 'Gagal menemukan simulasi untuk project ini'
      return
    }
  }
  await autoRunSurvey()
}

async function generatePDF() {
  if (!selectedProject.value) return
  generating.value = true
  pdfError.value = ''
  pdfReady.value = false
  try {
    const payload = {}
    // Kirim report summary dari Step 4 kalau ada
    if (reportSummary.value || reportSections.value.length) {
      payload.report_data = {
        title: 'Ringkasan Laporan Simulasi',
        summary: reportSummary.value || '',
        sections: reportSections.value.map(s => ({ title: s }))
      }
    }
    const { data } = await axios.post(`${API}/survey/report/generate/${selectedProject.value}`, payload)
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

.step-header {
  height: 60px;
  border-bottom: 1px solid var(--border-color, #EAEAEA);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: var(--bg-card, #FFF);
  z-index: 100;
  position: relative;
}
.step-header .header-left { display: flex; align-items: center; gap: 16px; }
.step-header .header-center { position: absolute; left: 50%; transform: translateX(-50%); }
.step-header .header-right { display: flex; align-items: center; gap: 12px; }
.step-header .brand {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  font-size: 18px;
  letter-spacing: 1px;
  cursor: pointer;
}
.workflow-step { display: flex; align-items: center; gap: 8px; }
.step-num { font-family: 'JetBrains Mono', monospace; font-size: 13px; color: var(--text-secondary, #6B7280); }
.step-name { font-size: 14px; font-weight: 500; color: var(--text-primary, #1F2937); }

.sim-history-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  padding: 14px 24px;
  background: var(--bg-secondary, #F9FAFB);
  border-bottom: 1px solid var(--border-color, #EAEAEA);
}
.sim-hist-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 28px;
}
.hist-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: var(--text-secondary, #6B7280); font-family: 'JetBrains Mono', monospace; }
.hist-value { font-size: 16px; font-weight: 600; color: var(--text-primary, #1F2937); font-family: 'JetBrains Mono', monospace; margin-top: 4px; }
.sim-hist-divider { width: 1px; height: 36px; background: var(--border-color, #EAEAEA); }
.status-completed { color: var(--success, #059669); }
.status-processing { color: var(--warning, #D97706); }

.main-content { max-width: 1200px; margin: 0 auto; padding: 30px 40px; }
.header { margin-bottom: 24px; }
.page-title { font-size: 2rem; font-weight: 600; margin: 0 0 8px; }
.page-desc { color: var(--text-secondary); font-size: 0.95rem; }

.project-bar { display: flex; gap: 10px; margin-bottom: 24px; align-items: center; }
.project-select { flex: 1; padding: 12px; border: 1px solid var(--border-color); background: var(--bg-card); font-family: var(--font-mono); color: var(--text-primary); }
.project-select:focus { outline: none; border-color: var(--accent-primary); }
.btn-delete-project { padding: 8px 12px; border: 1px solid var(--border-color); background: var(--bg-card); cursor: pointer; color: #9CA3AF; font-size: 0.9rem; transition: all 0.2s; }
.btn-delete-project:hover { color: #EF4444; border-color: #EF4444; }
.refresh-btn { padding: 8px 16px; border: 1px solid var(--border-color); background: var(--bg-card); cursor: pointer; color: var(--text-primary); }

.loading-state { text-align: center; padding: 40px; color: var(--text-secondary); }
.error-box { padding: 12px; background: var(--bg-secondary); border: 1px solid var(--danger); color: var(--danger); font-size: 0.85rem; margin-bottom: 16px; }

.summary-card { border: 2px solid var(--black); padding: 20px; margin-bottom: 20px; background: var(--bg-card); }

.report-summary-section { border-left: 4px solid var(--accent-primary); padding-left: 16px; margin-bottom: 24px; }
.report-summary-text { font-size: 0.95rem; line-height: 1.6; color: var(--text-primary); margin-bottom: 12px; }
.report-section-list { list-style: none; padding: 0; margin: 0; display: flex; flex-wrap: wrap; gap: 8px; }
.report-section-list li { display: inline-block; padding: 4px 12px; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 4px; font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-secondary); }
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

.running-survey-state { text-align: center; padding: 60px 20px; }
.running-spinner { width: 40px; height: 40px; border: 3px solid var(--border-color); border-top-color: var(--accent-primary); border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 16px; }
@keyframes spin { to { transform: rotate(360deg); } }
.running-text { font-size: 1.1rem; font-weight: 500; color: var(--text-primary); }
.running-sub { font-size: 0.85rem; color: var(--text-secondary); margin-top: 6px; }

.run-survey-box { text-align: center; padding: 40px 20px; border: 2px dashed var(--accent-primary); margin: 20px 0; background: var(--bg-card); }
.run-survey-hint { font-size: 0.85rem; color: var(--text-secondary); margin: 8px 0 20px; }
.run-survey-btn { padding: 14px 32px; background: var(--accent-primary); color: white; border: none; font-family: var(--font-mono); font-weight: 700; font-size: 1rem; cursor: pointer; transition: all 0.3s; }
.run-survey-btn:hover { background: var(--black); }

.customize-section { margin-bottom: 30px; }
.customize-section .section-title { font-size: 1.2rem; font-weight: 600; margin: 0 0 6px; padding-bottom: 8px; border-bottom: 2px solid var(--black); }
.customize-section > p { font-size: 0.9rem; color: var(--text-secondary, #6B7280); margin: 0 0 16px; }
.editor-inline { border: 2px solid var(--accent-primary, #3B82F6); border-radius: 8px; padding: 20px; background: var(--bg-card, #FFF); }
.no-editor-placeholder { text-align: center; padding: 40px 20px; border: 2px dashed var(--border-color, #D1D5DB); border-radius: 8px; background: var(--bg-secondary, #F9FAFB); }
.no-editor-placeholder p { font-size: 0.9rem; color: var(--text-secondary, #6B7280); margin-bottom: 16px; }
.btn-load-questions { padding: 12px 28px; border: 1px solid var(--accent-primary, #3B82F6); background: var(--bg-card, #FFF); color: var(--accent-primary, #3B82F6); font-family: var(--font-mono, monospace); font-weight: 700; cursor: pointer; border-radius: 4px; transition: all 0.2s; }
.btn-load-questions:hover { background: var(--accent-primary, #3B82F6); color: white; }
.editor-wrapper { margin: 20px 0; }
.editor-actions { display: flex; gap: 12px; justify-content: flex-end; margin-top: 16px; }
.btn-regenerate { padding: 12px 24px; border: 1px solid var(--border-color, #D1D5DB); background: var(--bg-card, #FFF); color: var(--text-primary, #1F2937); font-family: var(--font-mono, monospace); font-weight: 600; cursor: pointer; border-radius: 4px; transition: all 0.2s; }
.btn-regenerate:hover { border-color: var(--accent-primary, #3B82F6); }
.btn-run-custom { padding: 12px 28px; background: var(--accent-primary, #3B82F6); color: white; border: none; font-family: var(--font-mono, monospace); font-weight: 700; cursor: pointer; border-radius: 4px; transition: all 0.2s; }
.btn-run-custom:hover:not(:disabled) { background: var(--black, #111); }
.btn-run-custom:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
