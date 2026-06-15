import useSWR from 'swr'
import { get, post } from '../lib/api'
import { Card, MetricCard, PageHeader, Badge, EmptyState } from '../components/Card'
import { useState } from 'react'

const AGENT_COLORS = {
  executive: '#a78bfa', planner: '#60a5fa', researcher: '#34d399',
  builder: '#f59e0b', browser: '#06b6d4', bounty_hunter: '#ef4444',
  reward_scout: '#f97316', memory_agent: '#8b5cf6', monitor: '#22c55e',
  telegram_agent: '#2563eb', executor: '#64748b',
}

export default function AgentsPage() {
  const { data: agents = [] } = useSWR('/agents', get, { refreshInterval: 10000 })
  const { data: perf = {} } = useSWR('/agents/performance', () => get('/agents/performance').catch(() => ({})), { refreshInterval: 10000 })
  const [selected, setSelected] = useState(null)
  const [prompt, setPrompt] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  async function runAgent() {
    if (!selected || !prompt.trim()) return
    setLoading(true)
    setResult(null)
    try {
      const r = await post('/agent/run', { prompt, agent_id: selected.id })
      setResult(r)
    } catch (e) {
      setResult({ error: e.message })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <PageHeader title="🤖 Agents" subtitle={`${agents.length} agents registered`} />

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 mb-6">
        {agents.filter(a => a.visible !== false).map(a => (
          <Card
            key={a.id}
            onClick={() => setSelected(selected?.id === a.id ? null : a)}
            className={`cursor-pointer text-center transition-all ${selected?.id === a.id ? 'ring-1' : ''}`}
            style={selected?.id === a.id ? { ringColor: AGENT_COLORS[a.id] } : {}}
          >
            <div className="text-3xl mb-2">{a.icon}</div>
            <p className="text-sm font-semibold" style={{ color: AGENT_COLORS[a.id] || '#a78bfa' }}>{a.name}</p>
            <p className="text-xs text-gray-500 mt-1 line-clamp-2">{a.role}</p>
          </Card>
        ))}
      </div>

      {selected && (
        <Card className="mb-6">
          <div className="flex items-start justify-between mb-3">
            <div>
              <h3 className="font-semibold" style={{ color: AGENT_COLORS[selected.id] || '#a78bfa' }}>
                {selected.icon} {selected.name}
              </h3>
              <p className="text-sm text-gray-400 mt-1">{selected.role}</p>
            </div>
            {perf[selected.id] && (
              <div className="flex gap-4 text-right">
                <div>
                  <p className="text-xs text-gray-600">Runs</p>
                  <p className="text-sm font-bold" style={{ color: 'var(--accent)' }}>{perf[selected.id].runs}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600">Avg Score</p>
                  <p className="text-sm font-bold" style={{ color: perf[selected.id].avg_score > 0.7 ? '#22c55e' : '#f59e0b' }}>
                    {(perf[selected.id].avg_score * 100).toFixed(0)}%
                  </p>
                </div>
              </div>
            )}
          </div>
          <div className="flex gap-2">
            <input
              className="flex-1 rounded-lg px-3 py-2 text-sm border"
              style={{ background: 'var(--surface2)', borderColor: 'var(--border)', color: 'var(--text)' }}
              placeholder={`Ask ${selected.name} something…`}
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && runAgent()}
            />
            <button
              onClick={runAgent}
              disabled={loading || !prompt.trim()}
              className="px-4 py-2 rounded-lg text-sm font-semibold disabled:opacity-50"
              style={{ background: 'var(--accent-dark)', color: '#fff' }}
            >
              {loading ? '⏳' : '▶ Run'}
            </button>
          </div>
          {result && (
            <div className="mt-4 p-4 rounded-xl border text-sm" style={{ background: 'var(--surface2)', borderColor: 'var(--border)' }}>
              {result.error ? (
                <p className="text-red-400">{result.error}</p>
              ) : (
                <div>
                  <div className="flex gap-2 flex-wrap mb-2">
                    {result.intent && <Badge label={result.intent} type="blue" />}
                    {result.provider && <Badge label={result.provider} type="gray" />}
                    {result.soul_passed != null && (
                      <Badge label={`soul ${result.soul_passed ? '✓' : '✗'} ${result.soul_score != null ? (result.soul_score * 100).toFixed(0) + '%' : ''}`} type={result.soul_passed ? 'green' : 'red'} />
                    )}
                  </div>
                  <p className="text-gray-300 whitespace-pre-wrap leading-relaxed">{(result.answer || '').slice(0, 1200)}</p>
                </div>
              )}
            </div>
          )}
        </Card>
      )}

      {/* Performance table */}
      {Object.keys(perf).length > 0 && (
        <Card>
          <h2 className="text-sm font-semibold mb-4" style={{ color: 'var(--text)' }}>Agent Performance</h2>
          <div className="space-y-2">
            {Object.entries(perf).sort((a, b) => b[1].runs - a[1].runs).map(([id, p]) => (
              <div key={id} className="flex items-center gap-3">
                <span className="text-xs text-gray-400 w-28 truncate capitalize">{id.replace(/_/g, ' ')}</span>
                <div className="flex-1 h-1.5 rounded-full bg-gray-800 overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${Math.min(100, p.avg_score * 100)}%`,
                      background: p.avg_score > 0.7 ? '#22c55e' : p.avg_score > 0.4 ? '#f59e0b' : '#ef4444'
                    }}
                  />
                </div>
                <span className="text-xs font-bold w-10 text-right" style={{ color: 'var(--accent)' }}>{p.runs}x</span>
                <span className="text-xs w-10 text-right" style={{ color: p.avg_score > 0.7 ? '#22c55e' : '#f59e0b' }}>
                  {(p.avg_score * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}
