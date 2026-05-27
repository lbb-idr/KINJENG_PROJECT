import { reactive } from 'vue'

const state = reactive({
  files: [],
  simulationRequirement: '',
  isPending: false,
  simulationType: null,
  surveyParams: {
    agentCount: 500,
    maxRounds: 10,
    platform: 'both',
    likertScale: 5
  },
  customScenario: {
    title: '',
    context: '',
    agentRules: ''
  }
})

export function setPendingUpload(files, requirement) {
  state.files = files
  state.simulationRequirement = requirement
  state.isPending = true
}

export function getPendingUpload() {
  return {
    files: state.files,
    simulationRequirement: state.simulationRequirement,
    isPending: state.isPending,
    simulationType: state.simulationType,
    surveyParams: { ...state.surveyParams },
    customScenario: { ...state.customScenario }
  }
}

export function clearPendingUpload() {
  state.files = []
  state.simulationRequirement = ''
  state.isPending = false
  // Jangan reset simulationType dan surveyParams — masih dipakai Step 2-5
}

export function clearAll() {
  state.files = []
  state.simulationRequirement = ''
  state.isPending = false
  state.simulationType = null
  state.surveyParams = { agentCount: 500, maxRounds: 10, platform: 'both', likertScale: 5 }
  state.customScenario = { title: '', context: '', agentRules: '' }
}

export function setSimulationType(type, params) {
  state.simulationType = type
  if (params) {
    state.surveyParams = { ...state.surveyParams, ...params }
  }
}

export function setCustomScenario(scenario) {
  if (scenario) {
    state.customScenario = { ...state.customScenario, ...scenario }
  }
}

export default state
