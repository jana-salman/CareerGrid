import { apiRequest, encodeApiPathSegment } from './api.js'

function getDashboard() {
  return apiRequest('/api/dashboard')
}

function getWorkplaceReport(attemptId) {
  return apiRequest(
    `/api/simulation/attempts/${encodeApiPathSegment(attemptId)}/report`,
  )
}

export { getDashboard, getWorkplaceReport }
