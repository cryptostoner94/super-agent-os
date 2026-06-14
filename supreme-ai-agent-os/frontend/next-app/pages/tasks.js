import { useState } from 'react'
import useSWR from 'swr'
import { get, post } from '../lib/api'
import { Card, PageHeader, Badge, EmptyState } from '../components/Card'

const STATUS_COLOR = { queued: 'purple', running: 'blue', completed: 'green', failed: 'red' }
const AGENTS = ['executive', 'planner', 'researcher', 'builder', 'bounty_hunter', 'reward_scout']

export default function TasksPage() {
  const { data: tasks = [], mutate } = useSWR('/tasks?limit=50', get, { refreshInterval: 5000 })
  const [prompt, setPrompt] = useState('')
  const [agentId, setAgentId] = useState('executive')
  const [loading, setLoading] = useState(false)

  async function createTask(e) {
    e.preventDefault()
    if (!prompt.trim()) return
    setLoading(true)
    try {
      await post('/tasks', { prompt, agent_id: agentId })
      setPrompt('')
      await mutate()
    } catch (_err) {
      // task creation failure shown in task list; not fatal
    } finally {
      setLoading(false)
    }
  }

  const tList = Array.isArray(tasks) ? tasks : []
  const counts = tList.reduce((a, t) => { a[t.status] = (a[t.status] || 0) + 1; return a }, {})

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <PageHeader title="📋 Tasks" subtitle={`${tList.length} total · ${counts.running || 0} running`} />

      <div className="grid grid-cols-4 gap-3 mb-6">
        {['queued', 'running', 'completed', 'failed'].map(s => (
          <Card key={s}>
            <p className="text-xs text-gray-500 uppercase tracking-wider">{s}</p>
            <p className="text-2xl font-bold mt-1" style={{ color: s === 'completed' ? '#22c55e' : s === 'failed' ? '#ef4444' : 'var(--accent)' }}>
              {counts[s] || 0}
            </p>
          </Card>
        ))}
      </div>

      <Card className="mb-6">
        <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--text)' }}>Create Task</h2>
        <form onSubmit={createTask} className="flex gap-2">
          <select
            value={agentId}
            onChange={e => setAgentId(e.target.value)}
            className="rounded-lg px-3 py-2 text-sm border shrink-0"
            style={{ background: 'var(--surface2)', borderColor: 'var(--border)', color: 'var(--text)' }}
          >
            {AGENTS.map(a => <option key={a} value={a}>{a}</option>)}
          </select>
          <input
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            placeholder="Task description…"
            className="flex-1 rounded-lg px-3 py-2 text-sm border"
            style={{ background: 'var(--surface2)', borderColor: 'var(--border)', color: 'var(--text)' }}
          />
          <button
            type="submit"
            disabled={loading || !prompt.trim()}
            className="px-4 py-2 rounded-lg text-sm font-semibold disabled:opacity-50 shrink-0"
            style={{ background: 'var(--accent-dark)', color: '#fff' }}
          >
            {loading ? '…' : 'Create'}
          </button>
        </form>
      </Card>

      <Card>
        <h2 className="text-sm font-semibold mb-4" style={{ color: 'var(--text)' }}>Task Queue</h2>
        {tList.length === 0 ? (
          <EmptyState icon="📋" title="No tasks yet" subtitle="Create a task above to get started." />
        ) : (
          <div className="space-y-2">
            {tList.map(t => (
              <div key={t.id} className="flex items-start gap-3 p-3 rounded-xl border" style={{ background: 'var(--surface2)', borderColor: 'var(--border)' }}>
                <Badge label={t.status} type={STATUS_COLOR[t.status] || 'gray'} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-300 truncate">{t.prompt?.slice(0, 100)}</p>
                  <p className="text-xs text-gray-600 mt-0.5">
                    {t.agent_id} · {t.id} · {t.started ? `${Math.round((t.finished || Date.now() / 1000) - t.started)}s` : 'queued'}
                  </p>
                </div>
                {t.result?.error && (
                  <span className="text-xs text-red-400 shrink-0 max-w-32 truncate">{t.result.error}</span>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
