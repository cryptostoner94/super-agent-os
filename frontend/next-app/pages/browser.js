import { useState } from 'react'
import useSWR from 'swr'
import { get, post } from '../lib/api'
import { Card, PageHeader, Badge } from '../components/Card'

export default function BrowserPage() {
  const { data: status } = useSWR('/browser/status', get, { refreshInterval: 15000 })
  const [url, setUrl] = useState('')
  const [action, setAction] = useState('fetch')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [screenshot, setScreenshot] = useState(null)

  async function runBrowser(e) {
    e.preventDefault()
    if (!url.trim()) return
    setLoading(true)
    setResult(null)
    setScreenshot(null)
    try {
      let r
      if (action === 'screenshot') {
        r = await post('/browser/screenshot', { url, full_page: false })
        if (r.screenshot_base64) setScreenshot(r.screenshot_base64)
      } else if (action === 'extract') {
        r = await post('/browser/extract', { url })
      } else if (action === 'summarize') {
        r = await post('/browser/summarize', { url })
      } else {
        r = await post('/browser/fetch', { url })
      }
      setResult(r)
    } catch (err) {
      setResult({ error: err.message })
    } finally {
      setLoading(false)
    }
  }

  const engineOk = status != null && (status.available || status.mode !== 'unavailable')

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <PageHeader title="🌐 Browser Sessions" subtitle="Real browser automation via Playwright" />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <Card>
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Engine</p>
          <p className="text-base font-bold" style={{ color: 'var(--accent)' }}>{status?.engine || status?.mode || '…'}</p>
        </Card>
        <Card>
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Status</p>
          <Badge label={engineOk ? 'Available' : 'Unavailable'} type={engineOk ? 'green' : 'red'} />
        </Card>
        <Card>
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Capabilities</p>
          <p className="text-xs text-gray-400">{status?.capabilities?.join(', ') || 'click, screenshot, extract, form fill'}</p>
        </Card>
      </div>

      {!engineOk && (
        <div className="mb-4 p-4 rounded-xl border border-yellow-800 bg-yellow-900 bg-opacity-20">
          <p className="text-yellow-400 text-sm font-medium">⚠ Browser engine not available in this environment</p>
          <p className="text-yellow-600 text-xs mt-1">
            Run locally with Playwright installed: <code className="bg-black bg-opacity-30 px-1 rounded">pip install playwright && playwright install chromium</code>
          </p>
        </div>
      )}

      <Card className="mb-6">
        <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--text)' }}>Browser Task</h2>
        <form onSubmit={runBrowser} className="space-y-3">
          <div className="flex gap-2">
            {['fetch', 'extract', 'screenshot', 'summarize'].map(a => (
              <button
                key={a}
                type="button"
                onClick={() => setAction(a)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${action === a ? 'text-white' : 'text-gray-500'}`}
                style={action === a ? { background: 'var(--accent-dark)' } : { background: 'var(--surface2)' }}
              >
                {a}
              </button>
            ))}
          </div>
          <div className="flex gap-2">
            <input
              value={url}
              onChange={e => setUrl(e.target.value)}
              placeholder="https://example.com"
              className="flex-1 rounded-lg px-3 py-2 text-sm border"
              style={{ background: 'var(--surface2)', borderColor: 'var(--border)', color: 'var(--text)' }}
            />
            <button
              type="submit"
              disabled={loading || !url.trim()}
              className="px-4 py-2 rounded-lg text-sm font-semibold disabled:opacity-50 shrink-0"
              style={{ background: 'var(--accent-dark)', color: '#fff' }}
            >
              {loading ? '⏳' : '▶ Go'}
            </button>
          </div>
        </form>
      </Card>

      {screenshot && (
        <Card className="mb-6">
          <h3 className="text-sm font-medium mb-3 text-gray-300">Screenshot</h3>
          <img src={`data:image/png;base64,${screenshot}`} alt="Screenshot" className="rounded-lg max-w-full border" style={{ borderColor: 'var(--border)' }} />
        </Card>
      )}

      {result && (
        <Card>
          <h3 className="text-sm font-medium mb-3 text-gray-300">Result</h3>
          {result.error ? (
            <p className="text-red-400 text-sm">{result.error}</p>
          ) : (
            <pre className="text-xs text-gray-400 whitespace-pre-wrap overflow-auto max-h-96">
              {typeof result === 'string' ? result : JSON.stringify(result, null, 2)}
            </pre>
          )}
        </Card>
      )}
    </div>
  )
}
