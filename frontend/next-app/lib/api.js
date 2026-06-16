// Use /api prefix so nginx strips it and proxies to the backend.
// This works from any device — no hardcoded host/port needed.
const BASE = '/api'

export async function apiFetch(path, opts = {}) {
  const url = BASE + path
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...opts.headers },
    ...opts,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || err.error || 'Request failed')
  }
  return res.json()
}

export const get = (path) => apiFetch(path)
export const post = (path, body) => apiFetch(path, { method: 'POST', body: JSON.stringify(body) })
