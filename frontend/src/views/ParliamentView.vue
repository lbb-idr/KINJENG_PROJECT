<template>
  <div class="parliament-container">
    <NavBar />

    <div class="main-content">
      <div class="header">
        <div class="step-indicator">
          <span class="step active">{{ $t('simType.simulate') }}</span>
          <span class="step-connector"></span>
          <span class="step">{{ $t('simType.report') }}</span>
        </div>
        <h1 class="page-title">🧠 Debat Internal</h1>
        <p class="page-desc">Simulasi suara-suara berbeda dalam diri agen sebelum memutuskan jawaban survei.</p>
      </div>

      <div class="parliament-layout">
        <!-- Left: Agent Config + Question Input -->
        <div class="control-panel">
          <div class="panel-section">
            <h3 class="section-title">👤 Agen</h3>
            <button class="randomize-btn" @click="randomizeAgent">🎲 Acak Profil</button>
            <div class="agent-form">
              <div class="form-row">
                <label>Usia</label>
                <input v-model.number="agent.age" type="number" min="18" max="80" class="param-input" />
              </div>
              <div class="form-row">
                <label>Kelamin</label>
                <select v-model="agent.gender" class="param-select">
                  <option>Laki-laki</option>
                  <option>Perempuan</option>
                </select>
              </div>
              <div class="form-row">
                <label>Pendidikan</label>
                <select v-model="agent.education" class="param-select">
                  <option>SD/SMP</option><option>SMA/SMK</option><option>D3</option><option>S1</option><option>S2/S3</option>
                </select>
              </div>
              <div class="form-row">
                <label>Pekerjaan</label>
                <select v-model="agent.occupation" class="param-select">
                  <option>Pelajar/Mahasiswa</option><option>PNS</option><option>Karyawan Swasta</option><option>Wirausaha</option><option>Profesional</option><option>Lainnya</option>
                </select>
              </div>
              <div class="form-row">
                <label>Kepribadian</label>
                <select v-model="agent.personality" class="param-select">
                  <option>Suka Menganalisis</option><option>Mudah Terbawa Perasaan</option><option>Selalu Bertanya-tanya</option><option>Semangat</option><option>Praktis</option><option>Cuek</option><option>Ideal</option>
                </select>
              </div>
              <div class="form-row">
                <label>Pengetahuan</label>
                <select v-model="agent.knowledge_level" class="param-select">
                  <option>Rendah</option><option>Sedang</option><option>Tinggi</option><option>Ahli</option>
                </select>
              </div>
              <div class="form-row">
                <label>Opini</label>
                <select v-model="agent.opinion_bias" class="param-select">
                  <option>Hati-hati</option><option>Seimbang</option><option>Terbuka</option><option>Netral</option>
                </select>
              </div>
            </div>
          </div>

          <div class="panel-section">
            <h3 class="section-title">❓ Pertanyaan</h3>
            <textarea
              v-model="question"
              class="question-input"
              placeholder="Ketik pertanyaan survei disini..."
              rows="3"
            ></textarea>
            <div class="question-controls">
              <label class="checkbox-row">
                <input type="checkbox" v-model="useLlm" />
                Gunakan LLM (lambat tapi realistis)
              </label>
              <button
                class="debate-btn"
                :disabled="!question || debating"
                @click="runDebate"
              >
                {{ debating ? '⏳ Mempertimbangkan...' : '⚡ Mulai Diskusi' }}
              </button>
            </div>
          </div>

          <div v-if="error" class="error-box">{{ error }}</div>
        </div>

        <!-- Right: Debate Results -->
        <div class="debate-panel">
          <!-- Perspectives -->
          <div v-if="debateResult" class="debate-results">
            <div class="perspectives-grid">
              <div
                v-for="(pData, pKey) in debateResult.perspectives"
                :key="pKey"
                class="perspective-card"
                :class="{ dominant: pKey === debateResult.dominant_perspective }"
              >
                <div class="perspective-header">
                  <span class="perspective-name">{{ pData.name }}</span>
                  <span v-if="pKey === debateResult.dominant_perspective" class="dominant-badge">DOMINAN</span>
                </div>
                <p class="perspective-text">{{ pData.response }}</p>
              </div>
            </div>

            <!-- Result -->
            <div class="result-card">
              <div class="result-score">
                <span class="score-label">Skor Likert</span>
                <span class="score-value">{{ debateResult.final_likert_score }}/5</span>
              </div>
              <div class="result-details">
                <div class="detail-row">
                  <span class="detail-label">Keyakinan</span>
                  <div class="confidence-bar">
                    <div class="confidence-fill" :style="{ width: (debateResult.confidence * 100) + '%' }"></div>
                  </div>
                  <span class="detail-value">{{ (debateResult.confidence * 100).toFixed(0) }}%</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Sintesis</span>
                  <span class="detail-value">{{ debateResult.chairperson_synthesis }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Penalaran</span>
                  <span class="detail-value">{{ debateResult.reasoning }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Empty state -->
          <div v-else class="empty-state">
            <div class="empty-icon">🧠</div>
            <p>Atur profil agen dan ketik pertanyaan, lalu tekan "Mulai Debat" untuk melihat bagaimana agen mempertimbangkan dari berbagai sisi.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from 'axios'
import NavBar from '../components/NavBar.vue'

const API = 'http://localhost:5001/api'

const agent = reactive({
  age: 28,
  gender: 'Laki-laki',
  education: 'S1',
  occupation: 'Karyawan Swasta',
  personality: 'Praktis',
  trait: 'Logis dan rasional',
  knowledge_level: 'Sedang',
  opinion_bias: 'Seimbang',
  social_influence: 'Mandiri'
})

const question = ref('Seberapa setuju Anda bahwa perubahan iklim adalah ancaman serius yang memerlukan tindakan segera?')
const useLlm = ref(false)
const debating = ref(false)
const debateResult = ref(null)
const error = ref('')

function randomizeAgent() {
  const ages = Array.from({length: 43}, (_, i) => i + 18)
  const genders = ['Laki-laki', 'Perempuan']
  const educations = ['SD/SMP', 'SMA/SMK', 'D3', 'S1', 'S2/S3']
  const occupations = ['Pelajar/Mahasiswa', 'PNS', 'Karyawan Swasta', 'Wirausaha', 'Profesional', 'Lainnya']
  const personalities = ['Suka Menganalisis', 'Mudah Terbawa Perasaan', 'Selalu Bertanya-tanya', 'Semangat', 'Praktis', 'Cuek', 'Ideal']
  const traits = ['Teliti', 'Cepat', 'Ragu-ragu', 'Tegas', 'Mudah dipengaruhi', 'Kritis', 'Empatik', 'Logis', 'Kreatif', 'Praktis']
  const kls = ['Rendah', 'Sedang', 'Tinggi', 'Ahli']
  const biases = ['Hati-hati', 'Seimbang', 'Terbuka', 'Netral']
  const infls = ['Mandiri', 'Terpengaruh teman', 'Terpengaruh media', 'Terpengaruh tokoh publik']

  agent.age = ages[Math.floor(Math.random() * ages.length)]
  agent.gender = genders[Math.floor(Math.random() * genders.length)]
  agent.education = educations[Math.floor(Math.random() * educations.length)]
  agent.occupation = occupations[Math.floor(Math.random() * occupations.length)]
  agent.personality = personalities[Math.floor(Math.random() * personalities.length)]
  agent.trait = traits[Math.floor(Math.random() * traits.length)]
  agent.knowledge_level = kls[Math.floor(Math.random() * kls.length)]
  agent.opinion_bias = biases[Math.floor(Math.random() * biases.length)]
  agent.social_influence = infls[Math.floor(Math.random() * infls.length)]
}

async function runDebate() {
  if (!question.value.trim()) return
  debating.value = true
  error.value = ''
  debateResult.value = null

  try {
    const { data } = await axios.post(`${API}/cognitive/parliament/debate`, {
      question: question.value,
      persona: { ...agent },
      likert_scale: 5,
      use_llm: useLlm.value
    })
    if (data.success) {
      debateResult.value = data.data
    } else {
      error.value = data.error || 'Debate failed'
    }
  } catch (e) {
    error.value = e.response?.data?.error || e.message
  } finally {
    debating.value = false
  }
}
</script>

<style scoped>
.parliament-container {
  min-height: 100vh;
  background: var(--bg-primary, #FFF);
  font-family: var(--font-sans);
  color: var(--text-primary, #000);
}

.main-content { max-width: 1400px; margin: 0 auto; padding: 30px 40px; }

.header { margin-bottom: 30px; }
.step-indicator { display: flex; align-items: center; gap: 10px; margin-bottom: 20px; font-family: var(--font-mono); font-size: 0.8rem; }
.step { color: var(--text-secondary); padding: 4px 8px; border: 1px solid var(--border-color); }
.step.active { color: var(--accent-primary); border-color: var(--accent-primary); background: rgba(255,69,0,0.05); }
.step-connector { width: 20px; height: 1px; background: var(--border-color); }
.page-title { font-size: 2rem; font-weight: 600; margin: 0 0 8px; }
.page-desc { color: var(--text-secondary); font-size: 0.95rem; }

.parliament-layout { display: grid; grid-template-columns: 380px 1fr; gap: 30px; }

.control-panel { display: flex; flex-direction: column; gap: 20px; }
.panel-section { border: 1px solid var(--border-color); padding: 20px; background: var(--bg-card); }
.section-title { font-size: 1rem; font-weight: 600; margin: 0 0 14px 0; }

.randomize-btn { width: 100%; padding: 8px; margin-bottom: 14px; background: var(--bg-secondary); border: 1px dashed var(--border-color); cursor: pointer; font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-primary); }
.randomize-btn:hover { border-color: var(--accent-primary); }

.agent-form { display: flex; flex-direction: column; gap: 10px; }
.form-row { display: flex; flex-direction: column; gap: 4px; }
.form-row label { font-size: 0.75rem; font-weight: 500; color: var(--text-secondary); font-family: var(--font-mono); }
.param-input, .param-select { padding: 8px; border: 1px solid var(--border-color); background: var(--bg-primary); font-family: var(--font-mono); font-size: 0.85rem; color: var(--text-primary); }
.param-input:focus, .param-select:focus { outline: none; border-color: var(--accent-primary); }

.question-input { width: 100%; padding: 12px; border: 1px solid var(--border-color); background: var(--bg-primary); font-family: var(--font-mono); font-size: 0.85rem; resize: vertical; color: var(--text-primary); }
.question-input:focus { outline: none; border-color: var(--accent-primary); }

.question-controls { margin-top: 12px; display: flex; flex-direction: column; gap: 10px; }
.checkbox-row { display: flex; align-items: center; gap: 8px; font-size: 0.8rem; font-family: var(--font-mono); color: var(--text-secondary); cursor: pointer; }
.debate-btn { width: 100%; padding: 14px; background: var(--black); color: var(--white); border: none; font-family: var(--font-mono); font-weight: 700; font-size: 0.9rem; cursor: pointer; transition: all 0.3s; }
.debate-btn:hover:not(:disabled) { background: var(--accent-primary); }
.debate-btn:disabled { background: var(--border-color); color: var(--text-tertiary); cursor: not-allowed; }

.error-box { padding: 12px; background: var(--bg-secondary); border: 1px solid var(--danger); color: var(--danger); font-size: 0.85rem; }

.debate-panel { min-height: 400px; }
.debate-results { display: flex; flex-direction: column; gap: 20px; }

.perspectives-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.perspective-card { border: 1px solid var(--border-color); padding: 16px; background: var(--bg-card); transition: all 0.3s; }
.perspective-card.dominant { border-color: var(--accent-primary); background: rgba(255,69,0,0.03); }
.perspective-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.perspective-name { font-weight: 600; font-size: 0.9rem; }
.dominant-badge { font-size: 0.65rem; padding: 2px 6px; background: var(--accent-primary); color: white; font-family: var(--font-mono); }
.perspective-text { font-size: 0.85rem; line-height: 1.5; color: var(--text-secondary); }

.result-card { border: 2px solid var(--black); padding: 24px; background: var(--bg-card); }
.result-score { display: flex; align-items: baseline; gap: 12px; margin-bottom: 20px; }
.score-label { font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-secondary); }
.score-value { font-size: 2.5rem; font-weight: 700; }

.result-details { display: flex; flex-direction: column; gap: 12px; }
.detail-row { display: flex; align-items: center; gap: 10px; font-size: 0.85rem; }
.detail-label { font-family: var(--font-mono); color: var(--text-secondary); min-width: 70px; }
.detail-value { color: var(--text-primary); }
.confidence-bar { flex: 1; height: 8px; background: var(--bg-secondary); border-radius: 4px; overflow: hidden; }
.confidence-fill { height: 100%; background: var(--accent-primary); transition: width 0.5s; }

.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 400px; border: 1px dashed var(--border-color); text-align: center; padding: 40px; color: var(--text-secondary); }
.empty-icon { font-size: 4rem; margin-bottom: 20px; }
.empty-state p { max-width: 400px; line-height: 1.6; }

@media (max-width: 900px) {
  .parliament-layout { grid-template-columns: 1fr; }
  .perspectives-grid { grid-template-columns: 1fr; }
}
</style>
