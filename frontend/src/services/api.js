class ApiError extends Error {
  constructor(message, { status = 0, data = null, cause = null } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
    this.cause = cause
  }
}

function isJsonRequestBody(body) {
  if (body === null || body === undefined) {
    return false
  }

  return Array.isArray(body) || Object.getPrototypeOf(body) === Object.prototype
}

async function parseResponseBody(response) {
  if (response.status === 204) {
    return null
  }

  const text = await response.text()
  if (!text) {
    return null
  }

  const contentType = response.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    try {
      return JSON.parse(text)
    } catch {
      return text
    }
  }

  return text
}

function errorMessage(response, data) {
  if (data && typeof data === 'object') {
    if (typeof data.error === 'string' && data.error) {
      return data.error
    }
    if (typeof data.message === 'string' && data.message) {
      return data.message
    }
  }

  if (typeof data === 'string') {
    return 'CareerGrid received an unexpected server response. Please refresh and try again.'
  }

  return response.statusText || `Request failed with status ${response.status}.`
}

async function apiRequest(path, options = {}) {
  if (typeof path !== 'string' || !path.startsWith('/api/')) {
    throw new TypeError('API requests must use a relative /api/ path.')
  }

  const headers = new Headers(options.headers)
  let body = options.body

  if (isJsonRequestBody(body)) {
    if (!headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json')
    }
    body = JSON.stringify(body)
  }

  let response
  try {
    response = await fetch(path, {
      ...options,
      body,
      credentials: 'include',
      headers,
    })
  } catch (cause) {
    throw new ApiError('Unable to reach CareerGrid.', { cause })
  }

  const data = await parseResponseBody(response)
  if (!response.ok) {
    throw new ApiError(errorMessage(response, data), {
      status: response.status,
      data,
    })
  }

  return data
}

function encodeApiPathSegment(value) {
  return encodeURIComponent(String(value))
}

export { ApiError, apiRequest, encodeApiPathSegment }
