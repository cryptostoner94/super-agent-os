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
          <h3 className="font-semibold mb-3" style={{ color: AGENT_COLORS[selected.id] || '#a78bfa' }}>
            {selected.icon} {selected.name}
          </h3>
          <p className="text-sm text-gray-400 mb-4">{selected.role}</p>
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
              {loading ? '…' : '▶ Run'}
            </button>
          </div>
          {result && (
            <div className="mt-4 p-4 rounded-xl border text-sm" style={{ background: 'var(--surface2)', borderColor: 'var(--border)' }}>
              {result.error
                ? <p className="text-red-400">{result.error}</p>
                : <p className="text-gray-300 whitespace-pre-wrap">{(result.answer || '').slice(0, 1000)}</p>
              }
            </div>
          )}
        </Card>
      )}
    </div>
  )
}
