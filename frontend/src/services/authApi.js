import { apiRequest } from './api.js'

function getAuthenticatedSession() {
  return apiRequest('/api/auth/session')
}

export { getAuthenticatedSession }
