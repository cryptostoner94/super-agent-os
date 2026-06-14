import { useState } from 'react'
import { post } from '../lib/api'
import { Card, PageHeader } from '../components/Card'

export default function TerminalPage() {
  const [cmd, setCmd] = useState('')
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)

  async function runCmd(e) {
    e.preventDefault()
    if (!cmd.trim()) return
    const c = cmd.trim()
    setCmd('')
    setLoading(true)
    try {
      const r = await post('/system/exec', { command: c, timeout: 10 })
      setHistory(h => [{ cmd: c, result: r, ts: new Date().toISOString() }, ...h])
    } catch (err) {
      setHistory(h => [{ cmd: c, result: { error: err.message }, ts: new Date().toISOString() }, ...h])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <PageHeader title="💻 Terminal Jobs" subtitle="Sandboxed command execution — allowlisted commands only" />

      <Card className="mb-4">
        <div className="mb-3 p-3 rounded-lg text-xs border" style={{ background: 'var(--surface2)', borderColor: 'var(--border)' }}>
          <span className="text-yellow-400 font-medium">⚠ Security note:</span>
          <span className="text-gray-400 ml-2">Only allowlisted commands execute. Arbitrary shell access is disabled.</span>
        </div>
        <form onSubmit={runCmd} className="flex gap-2">
          <span className="text-green-400 font-mono py-2 text-sm shrink-0">$</span>
          <input
            value={cmd}
            onChange={e => setCmd(e.target.value)}
            placeholder="ls / pwd / date / whoami / uname / echo …"
            className="flex-1 rounded-lg px-3 py-2 text-sm border font-mono"
            style={{ background: '#000', borderColor: 'var(--border)', color: '#22c55e' }}
          />
          <button
            type="submit"
            disabled={loading || !cmd.trim()}
            className="px-4 py-2 rounded-lg text-sm font-semibold disabled:opacity-50 shrink-0"
            style={{ background: 'var(--accent-dark)', color: '#fff' }}
          >
            {loading ? '…' : 'Run'}
          </button>
        </form>
      </Card>

      {history.length > 0 && (
        <Card>
          <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--text)' }}>Job History</h2>
          <div className="space-y-3 font-mono text-xs">
            {history.map((h, i) => (
              <div key={i} className="p-3 rounded-lg" style={{ background: '#000' }}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-green-400">$ {h.cmd}</span>
                  <span className="text-gray-600">{h.ts}</span>
                </div>
                {h.result.error ? (
                  <p className="text-red-400">{h.result.error}</p>
                ) : (
                  <>
                    {h.result.stdout && <p className="text-gray-300 whitespace-pre">{h.result.stdout}</p>}
                    {h.result.stderr && <p className="text-yellow-400 whitespace-pre">{h.result.stderr}</p>}
                    <p className="text-gray-600 mt-1">exit {h.result.returncode ?? h.result.exit_code ?? 0}</p>
                  </>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}
