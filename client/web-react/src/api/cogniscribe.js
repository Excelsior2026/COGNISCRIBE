const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080'
const API_KEY = import.meta.env.VITE_API_KEY || ''
const DEFAULT_POLL_INTERVAL_MS = 1500
const DEFAULT_POLL_TIMEOUT_MS = 10 * 60 * 1000

function buildHeaders(extraHeaders = {}) {
  const headers = { ...extraHeaders }
  if (API_KEY) {
    headers['X-API-Key'] = API_KEY
  }
  return headers
}

function formatValidationDetails(details) {
  const lines = details.map((item) => {
    const location = Array.isArray(item.loc) ? item.loc.join('.') : 'request'
    const message = item.msg || 'Invalid request'
    return `- ${location}: ${message}`
  })

  return `Validation error:\n${lines.join('\n')}`
}

async function parseErrorMessage(response) {
  let payload = null
  try {
    payload = await response.json()
  } catch (err) {
    return `HTTP error! status: ${response.status}`
  }

  if (!payload) {
    return `HTTP error! status: ${response.status}`
  }

  if (payload.message) {
    return payload.message
  }

  if (payload.detail) {
    if (Array.isArray(payload.detail)) {
      return formatValidationDetails(payload.detail)
    }
    if (typeof payload.detail === 'string') {
      return payload.detail
    }
    if (payload.detail.message) {
      return payload.detail.message
    }
  }

  if (payload.error) {
    return payload.error
  }

  return `HTTP error! status: ${response.status}`
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: buildHeaders(options.headers || {}),
  })

  if (!response.ok) {
    const message = await parseErrorMessage(response)
    throw new Error(message)
  }

  return await response.json()
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

async function pollTask(taskId, options = {}) {
  const intervalMs = options.intervalMs || DEFAULT_POLL_INTERVAL_MS
  const timeoutMs = options.timeoutMs || DEFAULT_POLL_TIMEOUT_MS
  const startedAt = Date.now()

  while (true) {
    const status = await fetchJson(`${API_BASE_URL}/api/pipeline/${taskId}`)

    if (status.status === 'completed' && status.result) {
      return status.result
    }

    if (status.status === 'failed') {
      const message = status.error || 'Processing failed'
      throw new Error(message)
    }

    if (status.status === 'cancelled') {
      throw new Error('Processing cancelled')
    }

    if (Date.now() - startedAt > timeoutMs) {
      throw new Error('Processing timed out. Please try again.')
    }

    await sleep(intervalMs)
  }
}

export async function uploadAudio(file, ratio = 0.15, subject = '', options = {}) {
  const formData = new FormData()
  formData.append('file', file)

  const params = new URLSearchParams()
  params.append('ratio', ratio.toString())
  if (subject) {
    params.append('subject', subject)
  }

  const asyncMode = options.asyncMode !== undefined ? options.asyncMode : true
  params.append('async_mode', asyncMode ? 'true' : 'false')

  const response = await fetchJson(`${API_BASE_URL}/api/pipeline?${params}`, {
    method: 'POST',
    body: formData,
  })

  if (response.task_id && response.status === 'processing') {
    if (options.poll === false) {
      return response
    }

    return await pollTask(response.task_id, {
      intervalMs: options.pollIntervalMs,
      timeoutMs: options.pollTimeoutMs,
    })
  }

  return response
}

export async function healthCheck() {
  return await fetchJson(`${API_BASE_URL}/api/health`)
}
