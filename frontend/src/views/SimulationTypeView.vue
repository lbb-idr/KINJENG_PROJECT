<template>
  <div class="type-selector-container">
    <NavBar />

    <div class="main-content">
      <div class="selector-header">
        <div class="step-indicator">
          <span class="step active">01</span>
          <span class="step-connector"></span>
          <span class="step">{{ $t('simType.upload') }}</span>
          <span class="step-connector"></span>
          <span class="step">{{ $t('simType.engine') }}</span>
          <span class="step-connector"></span>
          <span class="step">{{ $t('simType.simulate') }}</span>
          <span class="step-connector"></span>
          <span class="step">{{ $t('simType.report') }}</span>
        </div>
        <h1 class="selector-title">{{ $t('simType.chooseTitle') }}</h1>
        <p class="selector-desc">{{ $t('simType.chooseDesc') }}</p>
      </div>

      <div class="type-grid">
        <div
          v-for="type in types"
          :key="type.id"
          class="type-card"
          :class="{ selected: selectedType === type.id }"
          @click="selectedType = type.id"
        >
          <div class="card-icon">{{ type.icon }}</div>
          <h3 class="card-title">{{ type.title }}</h3>
          <p class="card-desc">{{ type.desc }}</p>
          <div class="card-tags">
            <span v-for="tag in type.tags" :key="tag" class="card-tag">{{ tag }}</span>
          </div>
          <div v-if="selectedType === type.id" class="card-check">✓</div>
        </div>
      </div>

      <Transition name="fade">
        <div v-if="selectedType" class="params-panel">
          <h3 class="params-title">{{ $t('simType.parameters') }}</h3>
          <div class="params-grid">
            <div class="param-item">
              <label>{{ $t('simType.agentCount') }}</label>
              <select v-model="params.agentCount" class="param-select">
                <option :value="100">100</option>
                <option :value="500">500</option>
                <option :value="1000">1,000</option>
                <option :value="5000">5,000</option>
                <option :value="10000">10,000</option>
              </select>
            </div>
            <div class="param-item">
              <label>{{ $t('simType.simulationRounds') }}</label>
              <select v-model="params.maxRounds" class="param-select">
                <option :value="5">5</option>
                <option :value="10">10</option>
                <option :value="20">20</option>
                <option :value="50">50</option>
              </select>
            </div>
            <div class="param-item">
              <label>{{ $t('simType.platform') }}</label>
              <select v-model="params.platform" class="param-select">
                <option value="twitter">{{ $t('simType.platformTwitter') }}</option>
                <option value="reddit">{{ $t('simType.platformReddit') }}</option>
                <option value="both">{{ $t('simType.platformBoth') }}</option>
              </select>
            </div>
            <div v-if="selectedType === 'academic'" class="param-item">
              <label>{{ $t('simType.likertScale') }}</label>
              <select v-model="params.likertScale" class="param-select">
                <option :value="5">Likert 1-5</option>
                <option :value="7">Likert 1-7</option>
              </select>
            </div>
          </div>

          <div class="stats-bar">
            <div class="stat-item">
              <span class="stat-label">Agen</span>
              <span class="stat-value">{{ stats.totalAgents }}</span>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
              <span class="stat-label">Simulasi</span>
              <span class="stat-value">{{ stats.totalRounds }} ronde</span>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
              <span class="stat-label">Respon</span>
              <span class="stat-value">{{ stats.totalResponses }}</span>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
              <span class="stat-label">Platform</span>
              <span class="stat-value">{{ stats.platforms }}</span>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item mode-item">
              <span class="stat-label">Graph Engine</span>
              <select v-model="graphMode" @change="onGraphModeChange" class="mode-select-sm">
                <option value="local">Local</option>
                <option value="zep">Zep Cloud</option>
              </select>
            </div>
          </div>

          <div class="params-actions">
            <button class="btn-back" @click="$router.push('/')">
              ← {{ $t('simType.back') }}
            </button>
            <button class="btn-continue" @click="confirmType">
              {{ $t('simType.confirmAndContinue') }} →
            </button>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import NavBar from '../components/NavBar.vue'
import { getGraphMode, setGraphMode } from '../api/graph'

const router = useRouter()
const selectedType = ref(null)
const graphMode = ref('local')
const params = reactive({
  agentCount: 500,
  maxRounds: 10,
  platform: 'both',
  likertScale: 5
})

const stats = computed(() => {
  const agents = params.agentCount
  const rounds = params.maxRounds
  const totalResponses = agents * rounds
  let platforms = 1
  if (params.platform === 'both') platforms = 2
  return {
    totalAgents: agents.toLocaleString(),
    totalRounds: rounds,
    totalResponses: totalResponses.toLocaleString(),
    platforms
  }
})

onMounted(async () => {
  try {
    const res = await getGraphMode()
    graphMode.value = res.data?.mode || 'local'
  } catch {
    graphMode.value = 'local'
  }
})

async function onGraphModeChange() {
  try {
    await setGraphMode(graphMode.value)
  } catch {
    graphMode.value = 'local'
  }
}

const types = [
  {
    id: 'academic',
    icon: '🎓',
    title: 'Akademik',
    desc: 'Kuesioner dengan skala Likert, pilihan ganda, dan esai. Hasil statistik deskriptif dan inferensial untuk penelitian akademik.',
    tags: ['Likert', 'Kuesioner', 'Statistik', 'Demografi']
  },
  {
    id: 'political',
    icon: '🗳️',
    title: 'Politik',
    desc: 'Opini publik, preferensi kandidat, isu terkini, dan analisis swing. Cocok untuk riset politik dan sosial.',
    tags: ['Polling', 'Opini Publik', 'Preferensi']
  },
  {
    id: 'market',
    icon: '📊',
    title: 'Riset Pasar',
    desc: 'Analisis perilaku konsumen, persepsi merek, NPS, dan A/B testing untuk kebutuhan riset pasar dan bisnis.',
    tags: ['Konsumen', 'Brand', 'NPS', 'A/B Test']
  },
  {
    id: 'social',
    icon: '🌐',
    title: 'Sosial',
    desc: 'Opini publik bebas, berita viral, dampak kebijakan. Simulasi interaksi sosial multi-agent skala besar.',
    tags: ['Opini', 'Viral', 'Kebijakan', 'Sosial']
  },
  {
    id: 'custom',
    icon: '⚙️',
    title: 'Kustom',
    desc: 'Alur kerja MiroFish bebas. Upload dokumen dan deskripsi kebutuhan, tentukan sendiri skenario simulasi yang diinginkan.',
    tags: ['Bebas', 'Kustom', 'Lengkap']
  }
]

function confirmType() {
  router.push({
    name: 'Home',
    query: { type: selectedType.value, ...params }
  })
}
</script>

<style scoped>
.type-selector-container {
  min-height: 100vh;
  background: var(--bg-primary, #FFFFFF);
  font-family: var(--font-sans);
  color: var(--text-primary, #000);
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px;
}

.selector-header {
  margin-bottom: 40px;
}

.step-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 30px;
  font-family: var(--font-mono);
  font-size: 0.8rem;
}

.step {
  color: var(--text-secondary, #999);
  padding: 4px 8px;
  border: 1px solid var(--border-color, #E5E5E5);
  font-weight: 500;
}

.step.active {
  color: var(--accent-primary, #FF4500);
  border-color: var(--accent-primary, #FF4500);
  background: rgba(255, 69, 0, 0.05);
}

.step-connector {
  width: 20px;
  height: 1px;
  background: var(--border-color, #E5E5E5);
}

.selector-title {
  font-size: 2.5rem;
  font-weight: 600;
  margin: 0 0 10px 0;
}

.selector-desc {
  color: var(--text-secondary, #666);
  font-size: 1.05rem;
  line-height: 1.6;
}

.type-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.type-card {
  border: 1px solid var(--border-color, #E5E5E5);
  padding: 25px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  background: var(--bg-card, #FFF);
}

.type-card:hover {
  border-color: var(--accent-primary, #FF4500);
  transform: translateY(-2px);
  box-shadow: var(--shadow, 0 2px 8px rgba(0,0,0,0.08));
}

.type-card.selected {
  border: 2px solid var(--accent-primary, #FF4500);
  background: var(--bg-selected, rgba(255, 69, 0, 0.03));
}

.card-icon {
  font-size: 2rem;
  margin-bottom: 12px;
}

.card-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.card-desc {
  font-size: 0.85rem;
  color: var(--text-secondary, #666);
  line-height: 1.5;
  margin-bottom: 12px;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.card-tag {
  font-size: 0.7rem;
  padding: 2px 8px;
  background: var(--bg-secondary, #F5F5F5);
  border: 1px solid var(--border-color, #E5E5E5);
  font-family: var(--font-mono);
  color: var(--text-secondary, #666);
}

.card-check {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 24px;
  height: 24px;
  background: var(--accent-primary, #FF4500);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 700;
}

.params-panel {
  border: 1px solid var(--border-color, #E5E5E5);
  padding: 30px;
  background: var(--bg-card, #FFF);
}

.params-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 20px 0;
}

.params-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.param-item label {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-secondary, #666);
  font-family: var(--font-mono);
}

.param-select {
  padding: 10px;
  border: 1px solid var(--border-color, #DDD);
  background: var(--bg-primary, #FFF);
  font-family: var(--font-mono);
  font-size: 0.9rem;
  color: var(--text-primary, #000);
  cursor: pointer;
}

.param-select:focus {
  outline: none;
  border-color: var(--accent-primary, #FF4500);
}

.params-actions {
  display: flex;
  gap: 15px;
  justify-content: flex-end;
}

.btn-back {
  padding: 12px 24px;
  background: transparent;
  border: 1px solid var(--border-color, #DDD);
  color: var(--text-primary, #000);
  cursor: pointer;
  font-family: var(--font-mono);
  font-size: 0.9rem;
  transition: all 0.2s;
}

.btn-back:hover {
  border-color: var(--text-primary, #000);
}

.btn-continue {
  padding: 12px 24px;
  background: var(--black, #000);
  color: var(--white, #FFF);
  border: none;
  cursor: pointer;
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: 0.9rem;
  transition: all 0.3s;
}

.btn-continue:hover {
  background: var(--accent-primary, #FF4500);
}

.stats-bar {
  display: flex;
  align-items: center;
  gap: 0;
  margin: 20px 0;
  padding: 12px 0;
  border-top: 1px solid var(--border-color, #E5E5E5);
  border-bottom: 1px solid var(--border-color, #E5E5E5);
}

.stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 0;
}

.stat-label {
  font-size: 0.7rem;
  color: var(--text-secondary, #666);
  font-family: var(--font-mono);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.stat-value {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-primary, #000);
  font-family: var(--font-mono);
}

.stat-divider {
  width: 1px;
  height: 32px;
  background: var(--border-color, #E5E5E5);
}

.mode-item {
  flex: 1.3;
}

.mode-select-sm {
  padding: 4px 8px;
  border: 1px solid var(--border-color, #DDD);
  background: var(--bg-primary, #FFF);
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--text-primary, #000);
  cursor: pointer;
  outline: none;
}

.mode-select-sm:focus {
  border-color: var(--accent-primary, #FF4500);
}

.mode-select-sm option {
  background: var(--bg-card, #FFF);
  color: var(--text-primary, #000);
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .main-content {
    padding: 20px;
  }
  .selector-title {
    font-size: 1.8rem;
  }
  .selector-desc {
    font-size: 0.9rem;
  }
  .step-indicator {
    flex-wrap: wrap;
    gap: 8px;
    font-size: 0.7rem;
  }
  .step-connector {
    width: 12px;
  }
  .type-grid {
    grid-template-columns: 1fr;
  }
  .params-grid {
    grid-template-columns: 1fr;
  }
  .params-panel {
    padding: 20px;
  }
  .stats-bar {
    flex-wrap: wrap;
    gap: 8px;
  }
  .stat-item {
    flex: 1 1 45%;
  }
  .params-actions {
    flex-direction: column;
  }
  .params-actions button {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .selector-title {
    font-size: 1.4rem;
  }
  .stat-item {
    flex: 1 1 100%;
  }
}
</style>
