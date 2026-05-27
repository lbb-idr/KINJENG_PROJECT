import service from './index'

/**
 * Start a multi-agent debate for one survey question.
 */
export const startDebate = (data) => {
  return service.post('/api/survey/debate/start', data)
}

/**
 * Run all debate rounds for a session (synchronous).
 */
export const runDebate = (sessionId) => {
  return service.post(`/api/survey/debate/${sessionId}/run`)
}

/**
 * Confirm the next unconfirmed agent for a debate session.
 */
export const confirmDebateAgent = (sessionId) => {
  return service.post(`/api/survey/debate/${sessionId}/confirm`)
}

/**
 * Get current debate session state (polling).
 */
export const getDebateSession = (sessionId) => {
  return service.get(`/api/survey/debate/${sessionId}`)
}

/**
 * Run debates for ALL questions in a survey.
 */
export const runAllDebates = (data) => {
  return service.post('/api/survey/debate/run-all', data)
}
