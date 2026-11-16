import { apiRequest, encodeApiPathSegment } from './api.js'

const careerPath = (careerId) => `/api/careers/${encodeApiPathSegment(careerId)}`

function getCareers() {
  return apiRequest('/api/careers')
}

function getPositions(careerId) {
  return apiRequest(`${careerPath(careerId)}/positions`)
}

function getCompanies(careerId, positionId, country = '') {
  const query = country ? `?country=${encodeURIComponent(country)}` : ''
  return apiRequest(
    `${careerPath(careerId)}/positions/${encodeApiPathSegment(positionId)}/companies${query}`,
  )
}

export { getCareers, getCompanies, getPositions }
