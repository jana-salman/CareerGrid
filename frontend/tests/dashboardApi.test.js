import assert from 'node:assert/strict'
import { afterEach, test } from 'node:test'

import {
  clearDashboardCache,
  getCachedDashboard,
  getDashboard,
  prefetchDashboard,
  refreshDashboard,
  setDashboardSession,
} from '../src/services/dashboardApi.js'


const originalFetch = globalThis.fetch

afterEach(() => {
  clearDashboardCache()
  globalThis.fetch = originalFetch
})

test('concurrent Dashboard loads share one in-flight API request', async () => {
  let releaseRequest
  let requestCount = 0
  const requestGate = new Promise((resolve) => {
    releaseRequest = resolve
  })

  globalThis.fetch = async () => {
    requestCount += 1
    await requestGate
    return new Response(JSON.stringify({ attempts: [], user_id: 'student-1' }), {
      headers: { 'Content-Type': 'application/json' },
      status: 200,
    })
  }

  const firstLoad = getDashboard()
  const strictModeRemountLoad = getDashboard()

  assert.strictEqual(firstLoad, strictModeRemountLoad)
  assert.equal(requestCount, 1)

  releaseRequest()
  await Promise.all([firstLoad, strictModeRemountLoad])
})

test('Dashboard data is fetched again after the in-flight request settles', async () => {
  let requestCount = 0
  globalThis.fetch = async () => {
    requestCount += 1
    return new Response(JSON.stringify({ attempts: [], user_id: 'student-1' }), {
      headers: { 'Content-Type': 'application/json' },
      status: 200,
    })
  }

  await getDashboard()
  await getDashboard()

  assert.equal(requestCount, 2)
})

test('a prefetched Dashboard renders from memory while a fresh request runs', async () => {
  let responseVersion = 1
  globalThis.fetch = async () => new Response(
    JSON.stringify({
      attempts: [],
      simulation_count: responseVersion,
      user_id: 'student-1',
    }),
    {
      headers: { 'Content-Type': 'application/json' },
      status: 200,
    },
  )

  setDashboardSession('student-1')
  await prefetchDashboard()

  const renderStarted = performance.now()
  const immediateDashboard = getCachedDashboard()
  const cacheReadMilliseconds = performance.now() - renderStarted

  assert.equal(immediateDashboard.simulation_count, 1)
  assert.ok(cacheReadMilliseconds < 5)

  responseVersion = 2
  const refreshedDashboard = await refreshDashboard()
  assert.equal(refreshedDashboard.simulation_count, 2)
  assert.equal(getCachedDashboard().simulation_count, 2)
})

test('Dashboard cache is isolated by session identity and cleared on logout', async () => {
  globalThis.fetch = async () => new Response(
    JSON.stringify({ attempts: [], user_id: 'student-1' }),
    {
      headers: { 'Content-Type': 'application/json' },
      status: 200,
    },
  )

  setDashboardSession('student-1')
  await prefetchDashboard()
  assert.equal(getCachedDashboard().user_id, 'student-1')

  setDashboardSession('student-2')
  assert.equal(getCachedDashboard(), null)

  clearDashboardCache()
  assert.equal(getCachedDashboard(), null)
})

test('an expired Flask session clears previously cached Dashboard data', async () => {
  globalThis.fetch = async () => new Response(
    JSON.stringify({ attempts: [], user_id: 'student-1' }),
    {
      headers: { 'Content-Type': 'application/json' },
      status: 200,
    },
  )

  setDashboardSession('student-1')
  await prefetchDashboard()
  assert.notEqual(getCachedDashboard(), null)

  globalThis.fetch = async () => new Response(
    JSON.stringify({ error: 'Authentication required.' }),
    {
      headers: { 'Content-Type': 'application/json' },
      status: 401,
    },
  )

  await assert.rejects(refreshDashboard(), { status: 401 })
  assert.equal(getCachedDashboard(), null)
})
