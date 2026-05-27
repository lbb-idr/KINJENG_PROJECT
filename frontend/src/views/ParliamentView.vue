<template>
  <div class="parliament-container">
    <NavBar />

    <div class="main-content">
      <div class="header">
        <h1 class="page-title">🧠 Debat Internal</h1>
        <p class="page-desc">Debat multi-agen untuk menentukan skor Likert dari pertanyaan survei.</p>
      </div>

      <!-- Mode Toggle -->
      <div class="mode-toggle">
        <button :class="['mode-btn', { active: mode === 'auto' }]" @click="mode = 'auto'">
          ⚡ Otomatis
        </button>
        <button :class="['mode-btn', { active: mode === 'manual' }]" @click="switchToManual">
          ✏️ Atur Manual
        </button>
      </div>

      <div class="parliament-layout">
        <!-- Left: Controls -->
        <div class="control-panel">
          <!-- Question Input (shared) -->
          <div class="panel-section">
            <h3 class="section-title">❓ Pertanyaan</h3>
            <textarea
              v-model="question"
              class="question-input"
              placeholder="Ketik pertanyaan survei disini..."
              rows="3"
            ></textarea>
          </div>

          <!-- ===== AUTO MODE ===== -->
          <template v-if="mode === 'auto'">
            <div class="panel-section">
              <button
                class="pick-btn"
                :disabled="!question.trim() || busy"
                @click="pickAgents"
              >🎯 Cari 5 Agen Relevan</button>
            </div>

            <Transition name="slide">
              <div v-if="agents.length > 0 && (status === 'selecting' || status === 'ready')" class="panel-section">
                <h3 class="section-title">
                  👥 Konfirmasi Agen
                  <span class="step-counter">{{ confirmedCount < agents.length ? confirmedCount+1 : '✓' }}/{{ agents.length }}</span>
                </h3>
                <div class="step-bar">
                  <div class="step-fill" :style="{ width: (confirmedCount / agents.length * 100) + '%' }"></div>
                </div>

                <div v-if="currentAgent" class="agent-card-compact">
                  <div class="agent-avatar">{{ (currentAgent.name || '?')[0] }}</div>
                  <h4 class="agent-name">{{ currentAgent.name || 'Agent' }}</h4>
                  <div class="agent-meta">
                    <span>{{ currentAgent.age }} th</span>
                    <span>{{ currentAgent.occupation || currentAgent.profession || '?' }}</span>
                    <span>{{ currentAgent.personality || currentAgent.mbti || '?' }}</span>
                  </div>
                  <div class="agent-meta">
                    <span>Opini: {{ currentAgent.opinion_bias || 'Seimbang' }}</span>
                  </div>
                  <div v-if="currentAgent.bio" class="agent-bio">{{ currentAgent.bio }}</div>
                  <button class="confirm-btn" :disabled="busy" @click="confirmCurrent">
                    ✓ Konfirmasi Agen {{ confirmedCount + 1 }}
                  </button>
                </div>

                <div v-if="confirmedCount >= agents.length && agents.length > 0" class="ready-section">
                  <div class="ready-check">✓</div>
                  <p class="ready-text">Semua {{ agents.length }} agen siap!</p>
                  <button class="debate-btn" :disabled="busy" @click="startDebate">⚡ Mulai Debat</button>
                </div>
              </div>
            </Transition>
          </template>

          <!-- ===== MANUAL MODE ===== -->
          <template v-if="mode === 'manual'">
            <div class="panel-section">
              <h3 class="section-title">
                ✏️ Agen {{ manualStep+1 }}/5
                <span class="step-counter">Isi identitas</span>
              </h3>

              <div v-if="manualStep < 5" class="manual-form">
                <div class="form-row">
                  <label>Nama Panggilan</label>
                  <input v-model="manualForm.name" class="param-input" placeholder="Misal: Agen A" />
                </div>
                <div class="form-row">
                  <label>Usia</label>
                  <input v-model.number="manualForm.age" type="number" min="18" max="80" class="param-input" />
                </div>
                <div class="form-row">
                  <label>Kelamin</label>
                  <select v-model="manualForm.gender" class="param-select">
                    <option>Laki-laki</option><option>Perempuan</option>
                  </select>
                </div>
                <div class="form-row">
                  <label>Pendidikan</label>
                  <select v-model="manualForm.education" class="param-select">
                    <option>SD/SMP</option><option>SMA/SMK</option><option>D3</option><option>S1</option><option>S2/S3</option>
                  </select>
                </div>
                <div class="form-row">
                  <label>Pekerjaan</label>
                  <select v-model="manualForm.occupation" class="param-select">
                    <option>Pelajar/Mahasiswa</option><option>PNS</option><option>Karyawan Swasta</option><option>Wirausaha</option><option>Profesional</option><option>Lainnya</option>
                  </select>
                </div>
                <div class="form-row">
                  <label>Kepribadian</label>
                  <select v-model="manualForm.personality" class="param-select">
                    <option>Suka Menganalisis</option><option>Mudah Terbawa Perasaan</option><option>Selalu Bertanya-tanya</option><option>Semangat</option><option>Praktis</option><option>Cuek</option><option>Ideal</option>
                  </select>
                </div>
                <div class="form-row">
                  <label>Opini</label>
                  <select v-model="manualForm.opinion_bias" class="param-select">
                    <option>Hati-hati</option><option>Seimbang</option><option>Terbuka</option><option>Netral</option>
                  </select>
                </div>

                <div class="manual-buttons">
                  <button class="randomize-small" @click="randomizeManualForm">🎲 Acak</button>
                  <button class="next-btn" @click="saveManualAgent">
                    {{ manualStep < 4 ? 'Simpan & Lanjut →' : 'Simpan' }}
                  </button>
                </div>
              </div>

              <div v-if="manualAgents.length >= 5" class="ready-section">
                <div class="ready-check">✓</div>
                <p class="ready-text">Semua 5 agen telah diisi!</p>
                <div class="manual-summary">
                  <div v-for="(a, i) in manualAgents" :key="i" class="summary-chip">
                    <span class="chip-name">{{ a.name || `Agen ${i+1}` }}</span>
                    <span class="chip-detail">{{ a.age }}th • {{ a.occupation }}</span>
                  </div>
                </div>
                <button class="debate-btn" :disabled="busy" @click="runManualDebate">⚡ Mulai Debat</button>
              </div>
            </div>
          </template>

          <div v-if="error" class="error-box">{{ error }}</div>
        </div>

        <!-- Right: Debate Display -->
        <div class="debate-panel">
          <div v-if="loading" class="loading-state">
            <div class="pulse-ring"></div>
            <p v-if="status === 'round1' || status === 'round2'">Mendebatkan...</p>
            <p v-else-if="status === 'chairperson'">Ketua debat menganalisis...</p>
            <p v-else>Menunggu...</p>
          </div>

          <div v-else-if="posts.length > 0" class="debate-content">
            <div class="timeline-feed">
              <div v-for="(post, i) in posts" :key="post.post_id || i" class="post-item">
                <div class="post-marker">
                  <div class="marker-dot" :class="post.round_num === 1 ? 'dot-r1' : 'dot-r2'"></div>
                  <div class="marker-line" v-if="i < posts.length - 1"></div>
                </div>
                <div class="post-card">
                  <div class="card-header">
                    <div class="agent-info">
                      <div class="avatar">{{ (post.agent_name || '?')[0] }}</div>
                      <span class="agent-name">{{ post.agent_name }}</span>
                      <span class="round-badge">Ron {{ post.round_num }}</span>
                    </div>
                  </div>
                  <div class="card-body">
                    <p class="post-content">{{ post.content }}</p>
                  </div>
                </div>
              </div>
            </div>

            <Transition name="result">
              <div v-if="result" class="result-card">
                <div class="result-header">HASIL DEBAT</div>
                <div class="result-score">
                  <span class="score-value">{{ result.likert_score }}/5</span>
                  <span class="score-label">Skor Likert</span>
                </div>
                <div class="result-confidence" v-if="result.confidence">
                  <div class="conf-bar">
                    <div class="conf-fill" :style="{ width: (result.confidence * 100) + '%' }"></div>
                  </div>
                  <span class="conf-text">{{ (result.confidence * 100).toFixed(0) }}% keyakinan</span>
                </div>
                <div class="result-conclusion" v-if="result.chairperson_conclusion">
                  <p class="conclusion-text">{{ result.chairperson_conclusion }}</p>
                </div>
              </div>
            </Transition>
          </div>

          <div v-else class="empty-state">
            <div class="empty-icon">🧠</div>
            <p v-if="mode === 'auto'">
              Ketik pertanyaan, lalu tekan <strong>"Cari 5 Agen Relevan"</strong> untuk memilih peserta debat yang paling sesuai dengan topik.
            </p>
            <p v-else>
              Atau pilih mode <strong>"Atur Manual"</strong> untuk menentukan sendiri identitas setiap agen.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import axios from 'axios'
import NavBar from '../components/NavBar.vue'

const API = import.meta.env.VITE_API_BASE_URL ? import.meta.env.VITE_API_BASE_URL + '/api' : (import.meta.env.PROD ? '/api' : 'http://localhost:5001/api')

const question = ref('Seberapa setuju Anda bahwa perubahan iklim adalah ancaman serius yang memerlukan tindakan segera?')
const mode = ref('auto')

// Auto mode
const agents = ref([])
const confirmedCount = ref(0)
const sessionId = ref('')
const status = ref('idle')
const posts = ref([])
const result = ref(null)
const loading = ref(false)
const busy = ref(false)
const error = ref('')

// Manual mode
const manualStep = ref(0)
const manualForm = ref(createEmptyForm())
const manualAgents = ref([])

const currentAgent = computed(() => {
  if (confirmedCount.value < agents.value.length) {
    return agents.value[confirmedCount.value]
  }
  return null
})

function createEmptyForm() {
  return {
    name: '',
    age: 28,
    gender: 'Laki-laki',
    education: 'S1',
    occupation: 'Karyawan Swasta',
    personality: 'Praktis',
    opinion_bias: 'Seimbang'
  }
}

function randomizeManualForm() {
  const ages = Array.from({length: 43}, (_, i) => i + 18)
  const genders = ['Laki-laki', 'Perempuan']
  const educations = ['SD/SMP', 'SMA/SMK', 'D3', 'S1', 'S2/S3']
  const occupations = ['Pelajar/Mahasiswa', 'PNS', 'Karyawan Swasta', 'Wirausaha', 'Profesional', 'Lainnya']
  const personalities = ['Suka Menganalisis', 'Mudah Terbawa Perasaan', 'Selalu Bertanya-tanya', 'Semangat', 'Praktis', 'Cuek', 'Ideal']
  const biases = ['Hati-hati', 'Seimbang', 'Terbuka', 'Netral']

  manualForm.value = {
    name: `Agen ${manualStep.value + 1}`,
    age: ages[Math.floor(Math.random() * ages.length)],
    gender: genders[Math.floor(Math.random() * genders.length)],
    education: educations[Math.floor(Math.random() * educations.length)],
    occupation: occupations[Math.floor(Math.random() * occupations.length)],
    personality: personalities[Math.floor(Math.random() * personalities.length)],
    opinion_bias: biases[Math.floor(Math.random() * biases.length)]
  }
}

function saveManualAgent() {
  const name = manualForm.value.name.trim() || `Agen ${manualStep.value + 1}`
  const f = manualForm.value
  manualAgents.value.push({
    user_id: `manual_${manualStep.value + 1}`,
    name: name,
    username: `manual_agent_${manualStep.value + 1}`,
    age: f.age,
    gender: f.gender,
    education: f.education,
    occupation: f.occupation,
    profession: f.occupation,
    personality: f.personality,
    mbti: f.personality,
    opinion_bias: f.opinion_bias,
    bio: `Usia ${f.age}, ${f.occupation}, ${f.personality}`
  })

  if (manualStep.value < 4) {
    manualStep.value++
    manualForm.value = createEmptyForm()
  } else {
    manualStep.value = 5
  }
}

function switchToManual() {
  mode.value = 'manual'
  resetAll()
}

function resetAll() {
  agents.value = []
  confirmedCount.value = 0
  sessionId.value = ''
  posts.value = []
  result.value = null
  status.value = 'idle'
  loading.value = false
  error.value = ''
}

// ── Auto mode ──

async function pickAgents() {
  if (!question.value.trim()) return
  busy.value = true
  error.value = ''
  resetAll()

  try {
    const { data } = await axios.post(`${API}/survey/debate/start`, {
      question_text: question.value,
      agent_count: 5,
      likert_scale: 5
    })
    if (data.success) {
      sessionId.value = data.data.session_id
      agents.value = data.data.agents || []
      confirmedCount.value = 0
      status.value = data.data.status || 'selecting'
    } else {
      error.value = data.error || 'Gagal mengambil agen'
    }
  } catch (e) {
    error.value = e.response?.data?.error || e.message
  } finally {
    busy.value = false
  }
}

async function confirmCurrent() {
  if (busy.value || !sessionId.value) return
  busy.value = true
  try {
    const { data } = await axios.post(`${API}/survey/debate/${sessionId.value}/confirm`)
    if (data.success) {
      confirmedCount.value = data.data.confirmed_count
      status.value = data.data.status
    } else {
      error.value = data.error || 'Gagal konfirmasi'
    }
  } catch (e) {
    error.value = e.response?.data?.error || e.message
  } finally {
    busy.value = false
  }
}

async function startDebate() {
  if (!sessionId.value) return
  loading.value = true
  error.value = ''
  status.value = 'round1'

  try {
    const { data } = await axios.post(`${API}/survey/debate/${sessionId.value}/run`)
    if (data.success) {
      const d = data.data
      status.value = d.status
      posts.value = d.posts || []
      if (d.likert_score !== null) {
        result.value = {
          likert_score: d.likert_score,
          confidence: d.confidence,
          chairperson_conclusion: d.chairperson_conclusion
        }
      }
    } else {
      error.value = data.error || 'Debate gagal'
    }
  } catch (e) {
    error.value = e.response?.data?.error || e.message
  } finally {
    loading.value = false
  }
}

// ── Manual mode ──

async function runManualDebate() {
  if (manualAgents.value.length < 5) return
  loading.value = true
  error.value = ''
  posts.value = []
  result.value = null

  try {
    // Step 1: create session with manual agents
    const { data: startData } = await axios.post(`${API}/survey/debate/start`, {
      question_text: question.value,
      agents: manualAgents.value,
      likert_scale: 5
    })
    if (!startData.success) {
      error.value = startData.error || 'Gagal buat sesi'
      loading.value = false
      return
    }

    const sid = startData.data.session_id
    sessionId.value = sid
    status.value = 'round1'

    // Step 2: run debate (auto-confirms since status=selecting)
    const { data: runData } = await axios.post(`${API}/survey/debate/${sid}/run`)
    if (runData.success) {
      const d = runData.data
      status.value = d.status
      posts.value = d.posts || []
      if (d.likert_score !== null) {
        result.value = {
          likert_score: d.likert_score,
          confidence: d.confidence,
          chairperson_conclusion: d.chairperson_conclusion
        }
      }
    } else {
      error.value = runData.error || 'Debate gagal'
    }
  } catch (e) {
    error.value = e.response?.data?.error || e.message
  } finally {
    loading.value = false
  }
}

onUnmounted(() => {})
</script>

<style scoped>
.parliament-container {
  min-height: 100vh;
  background: var(--bg-primary, #FFF);
  font-family: var(--font-sans);
  color: var(--text-primary, #000);
}

.main-content { max-width: 1400px; margin: 0 auto; padding: 30px 40px; }

.header { margin-bottom: 24px; }
.page-title { font-size: 2rem; font-weight: 600; margin: 0 0 8px; }
.page-desc { color: var(--text-secondary); font-size: 0.95rem; }

/* Mode Toggle */
.mode-toggle { display: flex; gap: 8px; margin-bottom: 24px; }
.mode-btn {
  padding: 8px 20px; border: 1px solid var(--border-color);
  background: var(--bg-primary); cursor: pointer;
  font-family: var(--font-mono); font-size: 0.8rem;
  color: var(--text-secondary); transition: all 0.2s;
}
.mode-btn.active { background: var(--black); color: var(--white); border-color: var(--black); }
.mode-btn:hover:not(.active) { border-color: var(--black); }

.parliament-layout { display: grid; grid-template-columns: 380px 1fr; gap: 30px; }

.control-panel { display: flex; flex-direction: column; gap: 16px; }
.panel-section { border: 1px solid var(--border-color); padding: 20px; background: var(--bg-card); }
.section-title { font-size: 1rem; font-weight: 600; margin: 0 0 14px 0; display: flex; align-items: center; gap: 8px; }
.step-counter { font-size: 0.8rem; color: var(--text-secondary); font-family: var(--font-mono); margin-left: auto; }

.question-input { width: 100%; padding: 12px; border: 1px solid var(--border-color); background: var(--bg-primary); font-family: var(--font-mono); font-size: 0.85rem; resize: vertical; color: var(--text-primary); box-sizing: border-box; }
.question-input:focus { outline: none; border-color: var(--accent-primary); }

.pick-btn { width: 100%; padding: 12px; background: var(--black); color: var(--white); border: none; font-family: var(--font-mono); font-weight: 700; font-size: 0.85rem; cursor: pointer; transition: all 0.3s; }
.pick-btn:hover:not(:disabled) { background: var(--accent-primary); }
.pick-btn:disabled { background: var(--border-color); color: var(--text-tertiary); cursor: not-allowed; }

/* Step bar */
.step-bar { height: 5px; background: var(--bg-secondary); border-radius: 3px; overflow: hidden; margin-bottom: 16px; }
.step-fill { height: 100%; background: var(--black); border-radius: 3px; transition: width 0.4s ease; }

/* Agent card compact */
.agent-card-compact { text-align: center; }
.agent-avatar { width: 48px; height: 48px; border-radius: 50%; background: var(--black); color: var(--white); display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: 800; margin: 0 auto 8px; }
.agent-name { font-size: 1rem; font-weight: 700; margin: 0 0 8px; color: var(--text-primary); }
.agent-meta { display: flex; flex-wrap: wrap; justify-content: center; gap: 6px; margin-bottom: 6px; font-size: 0.75rem; font-family: var(--font-mono); color: var(--text-secondary); }
.agent-meta span { padding: 2px 8px; background: var(--bg-secondary); border-radius: 4px; }
.agent-bio { font-size: 0.75rem; color: var(--text-secondary); font-style: italic; margin-bottom: 12px; }

.confirm-btn { width: 100%; padding: 10px; border: none; background: var(--black); color: var(--white); font-family: var(--font-mono); font-weight: 600; font-size: 0.8rem; cursor: pointer; transition: background 0.2s; margin-top: 8px; }
.confirm-btn:hover { background: var(--accent-primary); }
.confirm-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.ready-section { text-align: center; padding: 12px 0; }
.ready-check { width: 40px; height: 40px; border-radius: 50%; background: #D1FAE5; color: #065F46; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: 800; margin: 0 auto 8px; }
.ready-text { font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 12px; }

.debate-btn { width: 100%; padding: 14px; background: var(--black); color: var(--white); border: none; font-family: var(--font-mono); font-weight: 700; font-size: 0.9rem; cursor: pointer; transition: all 0.3s; }
.debate-btn:hover:not(:disabled) { background: var(--accent-primary); }
.debate-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* Manual Form */
.manual-form { display: flex; flex-direction: column; gap: 10px; }
.form-row { display: flex; flex-direction: column; gap: 3px; }
.form-row label { font-size: 0.7rem; font-weight: 500; color: var(--text-secondary); font-family: var(--font-mono); }
.param-input, .param-select { padding: 8px; border: 1px solid var(--border-color); background: var(--bg-primary); font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-primary); }
.param-input:focus, .param-select:focus { outline: none; border-color: var(--accent-primary); }

.manual-buttons { display: flex; gap: 8px; margin-top: 8px; }
.randomize-small { flex: 1; padding: 8px; border: 1px dashed var(--border-color); background: var(--bg-secondary); cursor: pointer; font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-secondary); }
.randomize-small:hover { border-color: var(--accent-primary); }
.next-btn { flex: 2; padding: 8px; border: none; background: var(--black); color: var(--white); font-family: var(--font-mono); font-weight: 600; font-size: 0.8rem; cursor: pointer; }
.next-btn:hover { background: var(--accent-primary); }

.manual-summary { display: flex; flex-direction: column; gap: 6px; margin-bottom: 16px; }
.summary-chip { display: flex; justify-content: space-between; padding: 6px 12px; background: var(--bg-secondary); border-radius: 6px; font-size: 0.75rem; }
.chip-name { font-weight: 600; color: var(--text-primary); }
.chip-detail { color: var(--text-secondary); font-family: var(--font-mono); }

.error-box { padding: 12px; background: var(--bg-secondary); border: 1px solid var(--danger); color: var(--danger); font-size: 0.85rem; }

/* Right Panel */
.debate-panel { min-height: 400px; }

.loading-state { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 400px; gap: 16px; color: var(--text-secondary); font-size: 0.9rem; }
.pulse-ring { width: 40px; height: 40px; border: 3px solid var(--border-color); border-top-color: var(--black); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.timeline-feed { position: relative; }
.post-item { display: flex; gap: 14px; margin-bottom: 18px; }
.post-marker { display: flex; flex-direction: column; align-items: center; width: 18px; flex-shrink: 0; }
.marker-dot { width: 10px; height: 10px; border-radius: 50%; border: 2px solid var(--border-color); background: var(--white); z-index: 1; flex-shrink: 0; }
.marker-dot.dot-r1 { border-color: #3B82F6; background: #DBEAFE; }
.marker-dot.dot-r2 { border-color: #8B5CF6; background: #EDE9FE; }
.marker-line { width: 1px; flex: 1; background: var(--border-color); margin: 3px 0; }
.post-card { flex: 1; border: 1px solid var(--border-color); border-radius: 8px; padding: 12px 14px; background: var(--bg-card); }
.card-header { margin-bottom: 6px; }
.agent-info { display: flex; align-items: center; gap: 8px; }
.avatar { width: 24px; height: 24px; border-radius: 50%; background: var(--black); color: var(--white); display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; flex-shrink: 0; }
.agent-name { font-size: 0.8rem; font-weight: 600; }
.round-badge { font-size: 0.65rem; padding: 1px 6px; border-radius: 4px; background: var(--bg-secondary); color: var(--text-secondary); font-weight: 500; margin-left: auto; }
.post-content { font-size: 0.85rem; line-height: 1.6; color: var(--text-secondary); margin: 0; white-space: pre-wrap; }

.result-card { margin-top: 24px; border: 2px solid var(--black); padding: 20px; background: var(--bg-card); }
.result-header { font-size: 0.7rem; font-weight: 700; letter-spacing: 1px; color: var(--text-secondary); margin-bottom: 14px; }
.result-score { display: flex; align-items: baseline; gap: 8px; margin-bottom: 14px; }
.score-value { font-size: 2rem; font-weight: 800; font-family: var(--font-mono); }
.score-label { font-size: 0.8rem; color: var(--text-secondary); }
.result-confidence { margin-bottom: 14px; }
.conf-bar { height: 5px; background: var(--bg-secondary); border-radius: 3px; overflow: hidden; margin-bottom: 3px; }
.conf-fill { height: 100%; background: var(--black); border-radius: 3px; transition: width 0.5s; }
.conf-text { font-size: 0.7rem; color: var(--text-secondary); }
.result-conclusion { border-top: 1px solid var(--border-color); padding-top: 10px; }
.conclusion-text { font-size: 0.85rem; line-height: 1.5; color: var(--text-primary); margin: 0; white-space: pre-wrap; }

.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 400px; border: 1px dashed var(--border-color); text-align: center; padding: 40px; color: var(--text-secondary); }
.empty-icon { font-size: 4rem; margin-bottom: 20px; }
.empty-state p { max-width: 420px; line-height: 1.6; }

.slide-enter-active { transition: all 0.3s ease; }
.slide-enter-from { opacity: 0; transform: translateY(-10px); }
.result-enter-active { transition: all 0.5s ease; }
.result-enter-from { opacity: 0; transform: translateY(20px); }

@media (max-width: 900px) {
  .parliament-layout { grid-template-columns: 1fr; }
  .main-content { padding: 20px; }
}
</style>
