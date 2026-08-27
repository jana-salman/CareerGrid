import { apiRequest, encodeApiPathSegment } from './api.js'

function attemptPath(attemptId) {
  return `/api/simulation/attempts/${encodeApiPathSegment(attemptId)}`
}

function getSimulationAttempt(attemptId) {
  return apiRequest(attemptPath(attemptId))
}

function getFrontendSimulationProgress(attemptId) {
  return apiRequest(`${attemptPath(attemptId)}/frontend/progress`)
}

function saveFrontendSimulationProgress(attemptId, step, response) {
  return apiRequest(`${attemptPath(attemptId)}/frontend/progress`, {
    method: 'POST',
    body: { response, step },
  })
}

function restartFrontendSimulation(attemptId) {
  return apiRequest(`${attemptPath(attemptId)}/frontend/restart`, {
    method: 'POST',
  })
}

function requestAdvisorGuidance({ advisorContext, attemptId } = {}) {
  return apiRequest('/api/simulation/advisor/reply', {
    method: 'POST',
    body: {
      advisor_context: advisorContext,
      ...(attemptId ? { attempt_id: attemptId } : {}),
    },
  })
}

function evaluateWorkplaceSimulation({ evidence, attemptId } = {}) {
  return apiRequest('/api/simulation/evaluation', {
    method: 'POST',
    body: {
      evidence,
      ...(attemptId ? { attempt_id: attemptId } : {}),
    },
  })
}

export {
  evaluateWorkplaceSimulation,
  getFrontendSimulationProgress,
  getSimulationAttempt,
  requestAdvisorGuidance,
  restartFrontendSimulation,
  saveFrontendSimulationProgress,
}
