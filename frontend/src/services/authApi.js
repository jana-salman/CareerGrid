import { apiRequest } from './api.js'

function getAuthenticatedSession() {
  return apiRequest('/api/auth/session')
}

function login({ email, password }) {
  return apiRequest('/api/auth/login', {
    method: 'POST',
    body: { email, password },
  })
}

function register({ fullName, email, password }) {
  return apiRequest('/api/auth/register', {
    method: 'POST',
    body: { email, full_name: fullName, password },
  })
}

function logout() {
  return apiRequest('/api/auth/logout', { method: 'POST' })
}

export { getAuthenticatedSession, login, logout, register }
