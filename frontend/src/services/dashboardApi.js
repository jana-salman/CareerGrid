import { apiRequest, encodeApiPathSegment } from './api.js'

let activeDashboardUserId = null
let cachedDashboard = null
let dashboardCacheGeneration = 0
let pendingDashboardRequest = null

function clearDashboardCache() {
  dashboardCacheGeneration += 1
  activeDashboardUserId = null
  cachedDashboard = null
}

function setDashboardSession(userId) {
  const normalizedUserId = typeof userId === 'string' ? userId.trim() : ''

  if (!normalizedUserId) {
    clearDashboardCache()
    return
  }

  if (activeDashboardUserId && activeDashboardUserId !== normalizedUserId) {
    dashboardCacheGeneration += 1
    cachedDashboard = null
  }

  activeDashboardUserId = normalizedUserId
}

function getCachedDashboard() {
  if (
    !cachedDashboard
    || !activeDashboardUserId
    || cachedDashboard.user_id !== activeDashboardUserId
  ) {
    return null
  }

  return cachedDashboard
}

function requestDashboard() {
  // Development Strict Mode remounts effects. Share only the active request;
  // later visits still obtain fresh, server-authoritative Dashboard data.
  if (!pendingDashboardRequest) {
    const requestGeneration = dashboardCacheGeneration
    pendingDashboardRequest = apiRequest('/api/dashboard')
      .then((dashboard) => {
        if (requestGeneration !== dashboardCacheGeneration) {
          return dashboard
        }
        setDashboardSession(dashboard.user_id)
        cachedDashboard = dashboard
        return dashboard
      })
      .catch((error) => {
        if (error.status === 401) {
          clearDashboardCache()
        }
        throw error
      })
      .finally(() => {
        pendingDashboardRequest = null
      })
  }

  return pendingDashboardRequest
}

function getDashboard() {
  return requestDashboard()
}

function prefetchDashboard() {
  const cached = getCachedDashboard()
  return cached ? Promise.resolve(cached) : requestDashboard()
}

function refreshDashboard() {
  return requestDashboard()
}

function getWorkplaceReport(attemptId) {
  return apiRequest(
    `/api/simulation/attempts/${encodeApiPathSegment(attemptId)}/report`,
  )
}

export {
  clearDashboardCache,
  getCachedDashboard,
  getDashboard,
  getWorkplaceReport,
  prefetchDashboard,
  refreshDashboard,
  setDashboardSession,
}
