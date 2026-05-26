<template>
  <div class="main-view">
    <!-- Header -->
    <header class="app-header">
      <div class="header-left">
        <div class="brand" @click="router.push('/')">MIROFISH</div>
      </div>
      
      <div class="header-center">
        <div class="view-switcher">
          <button 
            v-for="mode in ['graph', 'split', 'workbench']" 
            :key="mode"
            class="switch-btn"
            :class="{ active: viewMode === mode }"
            @click="viewMode = mode"
          >
            {{ { graph: $t('main.layoutGraph'), split: $t('main.layoutSplit'), workbench: $t('main.layoutWorkbench') }[mode] }}
          </button>
        </div>
      </div>

      <div class="header-right">
        <LanguageSwitcher />
        <div class="step-divider"></div>
        <div class="workflow-step">
          <span class="step-num">Langkah 4/5</span>
          <span class="step-name">{{ $tm('main.stepNames')[3] }}</span>
        </div>
        <div class="step-divider"></div>
        <span class="status-indicator" :class="statusClass">
          <span class="dot"></span>
          {{ statusText }}
        </span>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="content-area">
      <!-- Left Panel: Graph -->
      <div class="panel-wrapper left" :style="leftPanelStyle">
        <GraphPanel 
          :graphData="graphData"
          :loading="graphLoading"
          :currentPhase="4"
          :isSimulating="false"
          @refresh="refreshGraph"
          @toggle-maximize="toggleMaximize('graph')"
        />
      </div>

      <!-- Right Panel: Step4 报告生成 -->
      <div class="panel-wrapper right" :style="rightPanelStyle">
        <Step4Report
          v-if="!showRetry"
          :reportId="currentReportId"
          :simulationId="simulationId"
          :systemLogs="systemLogs"
          @add-log="addLog"
          @update-status="updateStatus"
        />
        <!-- Retry state: laporan gagal dimuat -->
        <div v-else class="retry-container">
          <div class="retry-card">
            <div class="retry-icon">!</div>
            <h3 class="retry-title">Laporan Gagal Dimuat</h3>
            <p class="retry-desc">Laporan sebelumnya gagal diproses. Klik tombol di bawah untuk mencoba lagi.</p>
            <button 
              class="retry-btn" 
              :disabled="retrying" 
              @click="retryReportGeneration"
            >
              {{ retrying ? 'Memproses...' : 'Generate Ulang Laporan' }}
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import GraphPanel from '../components/GraphPanel.vue'
import Step4Report from '../components/Step4Report.vue'
import { getProject, getGraphData } from '../api/graph'
import { getSimulation } from '../api/simulation'
import { getReport, generateReport } from '../api/report'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

// Props
const props = defineProps({
  reportId: String
})

// Layout State - 默认切换到工作台视角
const viewMode = ref('workbench')

// Data State
const currentReportId = ref(route.params.reportId)
const simulationId = ref(null)
const projectData = ref(null)
const graphData = ref(null)
const graphLoading = ref(false)
const systemLogs = ref([])
const currentStatus = ref('processing') // processing | completed | error

// Report retry state
const showRetry = ref(false)
const retrying = ref(false)

// Session persistence
const STORAGE_KEY = 'mirofish_report'
function saveSession() {
  if (!currentReportId.value) return
  try {
    const data = {
      reportId: currentReportId.value,
      simulationId: simulationId.value,
      status: currentStatus.value,
      logs: systemLogs.value.slice(-30),
      savedAt: Date.now()
    }
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  } catch (e) {}
}
function restoreSession() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return false
    const saved = JSON.parse(raw)
    if (saved.reportId !== currentReportId.value) return false
    if (Date.now() - saved.savedAt > 30 * 60 * 1000) {
      sessionStorage.removeItem(STORAGE_KEY)
      return false
    }
    currentReportId.value = saved.reportId
    simulationId.value = saved.simulationId || null
    currentStatus.value = saved.status || 'processing'
    if (saved.logs) systemLogs.value = saved.logs
    return true
  } catch (e) { return false }
}
watch([currentStatus, systemLogs], saveSession, { deep: true })

// --- Computed Layout Styles ---
const leftPanelStyle = computed(() => {
  if (viewMode.value === 'graph') return { width: '100%', opacity: 1, transform: 'translateX(0)' }
  if (viewMode.value === 'workbench') return { width: '0%', opacity: 0, transform: 'translateX(-20px)' }
  return { width: '50%', opacity: 1, transform: 'translateX(0)' }
})

const rightPanelStyle = computed(() => {
  if (viewMode.value === 'workbench') return { width: '100%', opacity: 1, transform: 'translateX(0)' }
  if (viewMode.value === 'graph') return { width: '0%', opacity: 0, transform: 'translateX(20px)' }
  return { width: '50%', opacity: 1, transform: 'translateX(0)' }
})

// --- Status Computed ---
const statusClass = computed(() => {
  return currentStatus.value
})

const statusText = computed(() => {
  if (currentStatus.value === 'error') return 'Gagal'
  if (currentStatus.value === 'completed') return 'Selesai'
  return 'Menghasilkan'
})

// --- Helpers ---
const addLog = (msg) => {
  const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + new Date().getMilliseconds().toString().padStart(3, '0')
  systemLogs.value.push({ time, msg })
  if (systemLogs.value.length > 200) {
    systemLogs.value.shift()
  }
}

const updateStatus = (status) => {
  currentStatus.value = status
}

const retryReportGeneration = async () => {
  if (!simulationId.value || retrying.value) return
  retrying.value = true
  showRetry.value = false
  addLog('Memulai ulang generate laporan...')
  try {
    const res = await generateReport({
      simulation_id: simulationId.value,
      force_regenerate: true
    })
    if (res.success && res.data) {
      currentReportId.value = res.data.report_id
      showRetry.value = false
      currentStatus.value = 'processing'
      addLog('Generate laporan dimulai ulang')
      // reload data after short delay
      setTimeout(() => loadReportData(), 2000)
    } else {
      addLog('Gagal memulai ulang laporan: ' + (res.error || ''))
      showRetry.value = true
    }
  } catch (err) {
    addLog('Error saat retry laporan: ' + err.message)
    showRetry.value = true
  } finally {
    retrying.value = false
  }
}

// --- Layout Methods ---
const toggleMaximize = (target) => {
  if (viewMode.value === target) {
    viewMode.value = 'split'
  } else {
    viewMode.value = target
  }
}

// --- Data Logic ---
const loadReportData = async () => {
  try {
    addLog(t('log.loadReportData', { id: currentReportId.value }))

    // 获取 report 信息以获取 simulation_id
    const reportRes = await getReport(currentReportId.value)
    if (reportRes.success && reportRes.data) {
      const reportData = reportRes.data
      simulationId.value = reportData.simulation_id
      showRetry.value = false

      if (simulationId.value) {
        // 获取 simulation 信息
        const simRes = await getSimulation(simulationId.value)
        if (simRes.success && simRes.data) {
          const simData = simRes.data

          // 获取 project 信息
          if (simData.project_id) {
            const projRes = await getProject(simData.project_id)
            if (projRes.success && projRes.data) {
              projectData.value = projRes.data
              addLog(t('log.projectLoadSuccess', { id: projRes.data.project_id }))

              // 获取 graph 数据
              if (projRes.data.graph_id) {
                await loadGraph(projRes.data.graph_id)
              }
            }
          }
        }
      }
    } else {
      addLog(t('log.getReportInfoFailed', { error: reportRes.error || t('common.unknownError') }))
      // Report gagal dimuat — tampilkan tombol retry klo ada simulation_id
      if (simulationId.value) {
        showRetry.value = true
        currentStatus.value = 'error'
      }
    }
  } catch (err) {
    addLog(t('log.loadException', { error: err.message }))
    // Ada exception — retry juga dimungkinkan klo simulation_id ada
    if (simulationId.value) {
      showRetry.value = true
      currentStatus.value = 'error'
    }
  }
}

const loadGraph = async (graphId) => {
  graphLoading.value = true
  
  try {
    const res = await getGraphData(graphId)
    if (res.success) {
      graphData.value = res.data
      addLog(t('log.graphDataLoadSuccess'))
    }
  } catch (err) {
    addLog(t('log.graphLoadFailed', { error: err.message }))
  } finally {
    graphLoading.value = false
  }
}

const refreshGraph = () => {
  if (projectData.value?.graph_id) {
    loadGraph(projectData.value.graph_id)
  }
}

// Watch route params
watch(() => route.params.reportId, (newId) => {
  if (newId && newId !== currentReportId.value) {
    currentReportId.value = newId
    loadReportData()
  }
})

onMounted(() => {
  if (!restoreSession()) {
    addLog(t('log.reportViewInit'))
    loadReportData()
  } else {
    addLog('Session report dipulihkan')
    // Tetap fetch data terbaru (simulationId, project, graph)
    loadReportData()
  }
})
</script>

<style scoped>
.main-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #FFF;
  overflow: hidden;
  font-family: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
}

/* Header */
.app-header {
  height: 60px;
  border-bottom: 1px solid #EAEAEA;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #FFF;
  z-index: 100;
  position: relative;
}

.header-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.brand {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  font-size: 18px;
  letter-spacing: 1px;
  cursor: pointer;
}

.view-switcher {
  display: flex;
  background: #F5F5F5;
  padding: 4px;
  border-radius: 6px;
  gap: 4px;
}

.switch-btn {
  border: none;
  background: transparent;
  padding: 6px 16px;
  font-size: 12px;
  font-weight: 600;
  color: #666;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.switch-btn.active {
  background: #FFF;
  color: #000;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.workflow-step {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.step-num {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  color: #999;
}

.step-name {
  font-weight: 700;
  color: #000;
}

.step-divider {
  width: 1px;
  height: 14px;
  background-color: #E0E0E0;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #CCC;
}

.status-indicator.processing .dot { background: #FF9800; animation: pulse 1s infinite; }
.status-indicator.completed .dot { background: #4CAF50; }
.status-indicator.error .dot { background: #F44336; }

@keyframes pulse { 50% { opacity: 0.5; } }

/* Content */
.content-area {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
}

.panel-wrapper {
  height: 100%;
  overflow: hidden;
  transition: width 0.4s cubic-bezier(0.25, 0.8, 0.25, 1), opacity 0.3s ease, transform 0.3s ease;
  will-change: width, opacity, transform;
}

.panel-wrapper.left {
  border-right: 1px solid #EAEAEA;
}

/* Retry container */
.retry-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 40px;
}
.retry-card {
  text-align: center;
  max-width: 400px;
}
.retry-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #FEF2F2;
  color: #DC2626;
  font-size: 28px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  font-family: 'JetBrains Mono', monospace;
}
.retry-title {
  font-size: 18px;
  font-weight: 600;
  color: #1F2937;
  margin: 0 0 8px;
}
.retry-desc {
  font-size: 14px;
  color: #6B7280;
  margin: 0 0 24px;
  line-height: 1.5;
}
.retry-btn {
  padding: 10px 28px;
  border: none;
  border-radius: 8px;
  background: #2563EB;
  color: #FFF;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}
.retry-btn:hover:not(:disabled) {
  background: #1D4ED8;
}
.retry-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
