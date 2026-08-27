import { apiRequest } from './api.js'

function getApiHealth() {
  return apiRequest('/api/health')
}

export { getApiHealth }
