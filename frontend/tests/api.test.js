import assert from 'node:assert/strict'
import { afterEach, test } from 'node:test'

import { ApiError, apiRequest } from '../src/services/api.js'
import { getAuthenticatedSession, login, logout, register } from '../src/services/authApi.js'
import {
  getInterviewReview,
  getInterviewWorkspace,
  submitInterviewAnswer,
} from '../src/services/interviewApi.js'
import {
  evaluateWorkplaceSimulation,
  getSimulationAttempt,
  saveFrontendSimulationProgress,
} from '../src/services/simulationApi.js'
import { getApiHealth } from '../src/services/systemApi.js'


const originalFetch = globalThis.fetch

afterEach(() => {
  globalThis.fetch = originalFetch
})

test('API requests use relative paths, include credentials, and encode JSON', async () => {
  let capturedPath
  let capturedOptions
  globalThis.fetch = async (path, options) => {
    capturedPath = path
    capturedOptions = options
    return new Response(JSON.stringify({ saved: true }), {
      headers: { 'Content-Type': 'application/json' },
      status: 200,
    })
  }

  const result = await apiRequest('/api/example', {
    body: { step: 1 },
    method: 'POST',
  })

  assert.deepEqual(result, { saved: true })
  assert.equal(capturedPath, '/api/example')
  assert.equal(capturedOptions.credentials, 'include')
  assert.equal(capturedOptions.headers.get('Content-Type'), 'application/json')
  assert.equal(capturedOptions.body, '{"step":1}')
})

test('API errors preserve JSON error details and status codes', async () => {
  globalThis.fetch = async () => new Response(
    JSON.stringify({ error: 'Please sign in.' }),
    {
      headers: { 'Content-Type': 'application/json' },
      status: 401,
    },
  )

  await assert.rejects(
    apiRequest('/api/protected'),
    (error) => error instanceof ApiError
      && error.message === 'Please sign in.'
      && error.status === 401,
  )
})

test('API errors never expose raw Flask HTML responses', async () => {
  const flask404 = '<!doctype html><title>404 Not Found</title><p>The requested URL was not found.</p>'
  globalThis.fetch = async () => new Response(flask404, {
    headers: { 'Content-Type': 'text/html; charset=utf-8' },
    status: 404,
  })

  await assert.rejects(
    apiRequest('/api/example'),
    (error) => error instanceof ApiError
      && error.message === 'CareerGrid received an unexpected server response. Please refresh and try again.'
      && !error.message.includes('404 Not Found')
      && !error.message.includes('<!doctype html>')
      && error.status === 404,
  )
})

test('health service calls the real relative API endpoint', async () => {
  let capturedPath
  globalThis.fetch = async (path) => {
    capturedPath = path
    return new Response(JSON.stringify({ service: 'careergrid', status: 'ok' }), {
      headers: { 'Content-Type': 'application/json' },
      status: 200,
    })
  }

  const result = await getApiHealth()

  assert.equal(capturedPath, '/api/health')
  assert.equal(result.status, 'ok')
})

test('authentication service uses the protected session endpoint', async () => {
  let capturedPath
  globalThis.fetch = async (path) => {
    capturedPath = path
    return new Response(
      JSON.stringify({
        authenticated: true,
        user: { email: 'student@example.com', id: 'user-1', name: 'Student' },
      }),
      {
        headers: { 'Content-Type': 'application/json' },
        status: 200,
      },
    )
  }

  const result = await getAuthenticatedSession()

  assert.equal(capturedPath, '/api/auth/session')
  assert.equal(result.authenticated, true)
  assert.equal(result.user.id, 'user-1')
})

test('authentication actions use relative JSON API endpoints and Flask credentials', async () => {
  const requests = []
  globalThis.fetch = async (path, options) => {
    requests.push({ path, options })
    return new Response(JSON.stringify({ ok: true }), {
      headers: { 'Content-Type': 'application/json' },
      status: 200,
    })
  }

  await login({ email: 'student@example.com', password: 'secret' })
  await register({ fullName: 'Student User', email: 'student@example.com', password: 'secret' })
  await logout()

  assert.deepEqual(requests.map(({ path }) => path), [
    '/api/auth/login',
    '/api/auth/register',
    '/api/auth/logout',
  ])
  assert.ok(requests.every(({ options }) => options.credentials === 'include'))
  assert.deepEqual(JSON.parse(requests[0].options.body), {
    email: 'student@example.com',
    password: 'secret',
  })
  assert.deepEqual(JSON.parse(requests[1].options.body), {
    email: 'student@example.com',
    full_name: 'Student User',
    password: 'secret',
  })
})

test('simulation services encode identifiers and use the backend payload contract', async () => {
  const requests = []
  globalThis.fetch = async (path, options) => {
    requests.push({ path, options })
    return new Response(JSON.stringify({ ok: true }), {
      headers: { 'Content-Type': 'application/json' },
      status: 200,
    })
  }

  await getSimulationAttempt('attempt/with spaces')
  await saveFrontendSimulationProgress('attempt-1', 2, { summary: 'Checked' })

  assert.equal(
    requests[0].path,
    '/api/simulation/attempts/attempt%2Fwith%20spaces',
  )
  assert.equal(
    requests[1].path,
    '/api/simulation/attempts/attempt-1/frontend/progress',
  )
  assert.deepEqual(JSON.parse(requests[1].options.body), {
    response: { summary: 'Checked' },
    step: 2,
  })
})

test('workplace evaluation uses the shared service and existing Flask contract', async () => {
  let capturedPath
  let capturedOptions
  globalThis.fetch = async (path, options) => {
    capturedPath = path
    capturedOptions = options
    return new Response(JSON.stringify({ overall_score: 88 }), {
      headers: { 'Content-Type': 'application/json' },
      status: 200,
    })
  }

  await evaluateWorkplaceSimulation({
    attemptId: 'attempt-1',
    evidence: { changed_files: [{ path: 'server.py', before: 'old', after: 'new' }] },
  })

  assert.equal(capturedPath, '/api/simulation/evaluation')
  assert.deepEqual(JSON.parse(capturedOptions.body), {
    attempt_id: 'attempt-1',
    evidence: { changed_files: [{ path: 'server.py', before: 'old', after: 'new' }] },
  })
})

test('interview service preserves multipart form data', async () => {
  let capturedBody
  globalThis.fetch = async (_path, options) => {
    capturedBody = options.body
    return new Response(JSON.stringify({ saved: true }), {
      headers: { 'Content-Type': 'application/json' },
      status: 200,
    })
  }
  const formData = new FormData()
  formData.set('question_id', '1')

  await submitInterviewAnswer('interview-1', formData)

  assert.equal(capturedBody, formData)
})

test('interview service loads an encoded workspace API path', async () => {
  let capturedPath
  globalThis.fetch = async (path) => {
    capturedPath = path
    return new Response(JSON.stringify({ status: 'in_progress', questions: [] }), {
      headers: { 'Content-Type': 'application/json' },
      status: 200,
    })
  }

  await getInterviewWorkspace('interview/with spaces')

  assert.equal(capturedPath, '/api/interview/interview%2Fwith%20spaces')
})

test('interview service loads an encoded review API path', async () => {
  let capturedPath
  globalThis.fetch = async (path) => {
    capturedPath = path
    return new Response(JSON.stringify({ status: 'completed', question_results: [] }), {
      headers: { 'Content-Type': 'application/json' },
      status: 200,
    })
  }

  await getInterviewReview('interview/with spaces')

  assert.equal(capturedPath, '/api/interview/interview%2Fwith%20spaces/review')
})
