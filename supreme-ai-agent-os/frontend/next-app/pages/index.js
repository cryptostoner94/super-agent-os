import { useState, useEffect } from 'react'
import useSWR from 'swr'
import { get, post } from '../lib/api'
import { Card, MetricCard, PageHeader, Badge, Skeleton } from '../components/Card'

const REFRESH = 10000

export default function Overview() {
  const { data: health } = useSWR('/health', get, { refreshInterval: REFRESH })
  const { data: status } = useSWR('/api/status', get, { refreshInterval: REFRESH })
  const { data: tasks } = useSWR('/tasks', get, { refreshInterval: REFRESH })
  const { data: agents } = useSWR('/agents', get, { refreshInterval: REFRESH })
  const { data: rewards } = useSWR('/rewards', get, { refreshInterval: REFRESH })

  const [prompt, setPrompt] = useState('')
  const [agentId, setAgentId] = useState('executive')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const taskList = Array.isArray(tasks) ? tasks : []
  const running = taskList.filter(t => t.status === 'running').length
  const completed = taskList.filter(t => t.status === 'completed').length

  async function runTask(e) {
    e.preventDefault()
    if (!prompt.trim()) return
    setLoading(true)
    setResult(null)
    try {
      const r = await post('/inception/run', { prompt, agent_id: agentId })
      setResult(r)
    } catch (err) {
      setResult({ error: err.message })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <PageHeader
        title="⚡ Supreme AI Agent OS"
        subtitle={`v2.0 · ${health?.status === 'ok' ? '🟢 Online' : '🔴 Offline'} · Identity ${health?.identity || '…'}`}
      />

      {/* Metrics row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <MetricCard icon="🤖" label="Agents" value={Array.isArray(agents) ? agents.length : '—'} />
        <MetricCard icon="📋" label="Tasks Total" value={status?.tasks_total ?? '—'} />
        <MetricCard icon="⚡" label="Running" value={running} color="#22c55e" />
        <MetricCard icon="✅" label="Completed" value={completed} color="#a78bfa" />
      </div>

      {/* Soul + Heartbeat */}
      {health && health.soul && (
        <Card className="mb-6">
          <div className="flex flex-wrap gap-6">
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Soul Quality</p>
              <div className="flex items-center gap-2">
                <div className="h-2 rounded-full bg-purple-900 overflow-hidden" style={{ width: 120 }}>
                  <div className="h-full bg-accent rounded-full" style={{ width: `${(health.soul.rolling_quality ?? 0) * 100}%`, background: 'var(--accent)' }} />
                </div>
                <span className="text-sm font-bold" style={{ color: 'var(--accent)' }}>
                  {((health.soul.rolling_quality ?? 0) * 100).toFixed(0)}%
                </span>
              </div>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Cycle</p>
              <p className="text-xl font-bold text-gray-300">{health.soul.cycle ?? 0}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Memory DB</p>
              <p className="text-sm font-medium" style={{ color: 'var(--accent)' }}>{status?.memory?.db_path || 'SQLite Active'}</p>
            </div>
            {health.heartbeat && (
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Uptime</p>
                <p className="text-sm text-gray-300">{Math.floor(health.heartbeat.uptime_s)}s</p>
              </div>
            )}
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Task Runner */}
        <Card>
          <h2 className="text-base font-semibold mb-4" style={{ color: 'var(--text)' }}>🚀 Run Agent Task</h2>
          <form onSubmit={runTask} className="space-y-3">
            <div>
              <label className="text-xs text-gray-500 uppercase tracking-wider block mb-1">Agent</label>
              <select
                value={agentId}
                onChange={e => setAgentId(e.target.value)}
                className="w-full rounded-lg px-3 py-2 text-sm border"
                style={{ background: 'var(--surface2)', borderColor: 'var(--border)', color: 'var(--text)' }}
              >
                {(Array.isArray(agents) ? agents : []).filter(a => a.visible).map(a => (
                  <option key={a.id} value={a.id}>{a.icon} {a.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 uppercase tracking-wider block mb-1">Prompt</label>
              <textarea
                value={prompt}
                onChange={e => setPrompt(e.target.value)}
                rows={4}
                placeholder="e.g. Research open-source bug bounty opportunities and create a plan…"
                className="w-full rounded-lg px-3 py-2 text-sm border resize-none"
                style={{ background: 'var(--surface2)', borderColor: 'var(--border)', color: 'var(--text)' }}
              />
            </div>
            <button
              type="submit"
              disabled={loading || !prompt.trim()}
              className="w-full py-2 rounded-lg text-sm font-semibold transition-opacity disabled:opacity-50"
              style={{ background: 'var(--accent-dark)', color: '#fff' }}
            >
              {loading ? '⏳ Running…' : '▶ Execute'}
            </button>
          </form>

          {result && (
            <div className="mt-4 rounded-xl p-4 border text-sm" style={{ background: 'var(--surface2)', borderColor: 'var(--border)' }}>
              {result.error ? (
                <p className="text-red-400">Error: {result.error}</p>
              ) : (
                <div className="space-y-2">
                  <div className="flex gap-2 flex-wrap">
                    {result.intent && <Badge label={result.intent} type="blue" />}
                    {result.agent && <Badge label={result.agent} type="purple" />}
                    {result.soul_score != null && (
                      <Badge label={`soul: ${(result.soul_score * 100).toFixed(0)}%`} type={result.soul_passed ? 'green' : 'red'} />
                    )}
                  </div>
                  <p className="text-gray-300 whitespace-pre-wrap leading-relaxed">{result.answer || JSON.stringify(result, null, 2)}</p>
                </div>
              )}
            </div>
          )}
        </Card>

        {/* Opportunities */}
        <Card>
          <h2 className="text-base font-semibold mb-4" style={{ color: 'var(--text)' }}>💎 Top Opportunities</h2>
          <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
            {rewards?.opportunities?.slice(0, 8).map((r, i) => (
              <div
                key={i}
                className="flex items-start justify-between gap-3 p-3 rounded-xl border"
                style={{ background: 'var(--surface2)', borderColor: 'var(--border)' }}
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-200 truncate">{r.title}</p>
                  <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">{r.description}</p>
                </div>
                <div className="shrink-0 text-right">
                  <p className="text-xs font-bold" style={{ color: 'var(--success)' }}>{r.payout}</p>
                  <Badge label={r.type} type="purple" />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Recent Tasks */}
      <Card className="mt-6">
        <h2 className="text-base font-semibold mb-4" style={{ color: 'var(--text)' }}>📋 Recent Tasks</h2>
        {taskList.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-8">No tasks yet. Run one above.</p>
        ) : (
          <div className="space-y-2">
            {taskList.slice(0, 5).map(t => (
              <div key={t.id} className="flex items-center gap-3 p-3 rounded-xl border" style={{ background: 'var(--surface2)', borderColor: 'var(--border)' }}>
                <Badge label={t.status} type={t.status} />
                <span className="text-sm text-gray-300 flex-1 truncate">{t.prompt?.slice(0, 80)}</span>
                <span className="text-xs text-gray-600">{t.agent_id}</span>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
