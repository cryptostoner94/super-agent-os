import { useState, useCallback } from 'react'
import useSWR from 'swr'
import { get, post } from '../lib/api'
import { Card, PageHeader, Badge, EmptyState } from '../components/Card'
import useWebSocket from '../lib/useWebSocket'

const STATUS_COLOR = { queued: 'purple', running: 'blue', completed: 'green', failed: 'red', cancelled: 'gray' }
// Agents are now fetched from the backend registry via useSWR

function TaskModal({ task, onClose }) {
  if (!task) return null
  const result = task.result || {}
  const answer = result.answer || result.text || result.error || ''
  const elapsed = task.finished && task.started
    ? `${((task.finished - task.started)).toFixed(1)}s`
    : task.started ? 'running…' : 'queued'

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.7)' }}
      onClick={onClose}
    >
      <div
        className="w-full max-w-3xl rounded-2xl border overflow-hidden"
        style={{ background: 'var(--surface)', borderColor: 'var(--border)', maxHeight: '85vh' }}
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-start justify-between p-5 border-b" style={{ borderColor: 'var(--border)' }}>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <Badge label={task.status} type={STATUS_COLOR[task.status] || 'gray'} />
              <Badge label={task.agent_id} type="purple" />
              {result.intent && <Badge label={result.intent} type="blue" />}
              {result.soul_passed != null && (
                <Badge
                  label={`soul ${result.soul_passed ? '✓' : '✗'} ${result.soul_score != null ? (result.soul_score * 100).toFixed(0) + '%' : ''}`}
                  type={result.soul_passed ? 'green' : 'red'}
                />
              )}
              {result.provider && <Badge label={result.provider} type="gray" />}
            </div>
            <p className="text-sm font-medium text-gray-200 mt-1">{task.prompt}</p>
            <p className="text-xs text-gray-500 mt-1">
              Task #{task.id} · {elapsed}
              {task.created ? ` · ${new Date(task.created * 1000).toLocaleString()}` : ''}
            </p>
          </div>
          <button onClick={onClose} className="ml-4 text-gray-500 hover:text-gray-200 text-lg shrink-0">✕</button>
        </div>
        <div className="p-5 overflow-y-auto" style={{ maxHeight: 'calc(85vh - 120px)' }}>
          {task.status === 'running' && (
            <div className="flex items-center gap-3 mb-4 p-3 rounded-xl border border-blue-800" style={{ background: 'rgba(96,165,250,0.05)' }}>
              <span className="animate-pulse-slow text-blue-400 text-lg">⏳</span>
              <p className="text-blue-400 text-sm">Agent is working… results will appear when complete.</p>
            </div>
          )}
          {answer && (
            <div className="rounded-xl p-4 border text-sm" style={{ background: 'var(--surface2)', borderColor: 'var(--border)' }}>
              {result.error
                ? <p className="text-red-400 whitespace-pre-wrap">{answer}</p>
                : <p className="text-gray-200 whitespace-pre-wrap leading-relaxed">{answer}</p>
              }
            </div>
          )}
          {result.results && result.results.length > 0 && (
            <div className="mt-4">
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Subtask Results</h3>
              <div className="space-y-2">
                {result.results.map((r, i) => (
                  <div key={i} className="p-3 rounded-xl border text-xs" style={{ background: 'var(--surface2)', borderColor: 'var(--border)' }}>
                    <div className="flex items-center gap-2 mb-1">
                      <Badge label={r.agent || 'agent'} type="purple" />
                      {r.provider && <Badge label={r.provider} type="gray" />}
                    </div>
                    <p className="text-gray-400 whitespace-pre-wrap">{(r.output || r.error || '').slice(0, 600)}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
          {!answer && task.status === 'queued' && (
            <EmptyState icon="⏳" title="Task queued" subtitle="Waiting for an agent to pick it up." />
          )}
        </div>
      </div>
    </div>
  )
}

export default function TasksPage() {
  const { data: tasks = [], mutate } = useSWR('/tasks?limit=100', get, { refreshInterval: 5000 })
  const { data: agents = [] } = useSWR('/agents', get)
  const [prompt, setPrompt] = useState('')
  const [agentId, setAgentId] = useState('executive')
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState(null)
  const [filter, setFilter] = useState('all')

  useWebSocket(useCallback((msg) => {
    if (msg.type === 'task_update') {
      mutate()
      if (selected && msg.data?.id === selected.id) {
        get(`/tasks/${selected.id}`).then(setSelected).catch(() => {})
      }
    }
  }, [mutate, selected]))

  async function createTask(e) {
    e.preventDefault()
    if (!prompt.trim()) return
    setLoading(true)
    try {
      const task = await post('/tasks', { prompt, agent_id: agentId })
      setPrompt('')
      await mutate()
      setSelected(task)
    } catch (err) {
      alert('Failed to create task: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  async function openTask(t) {
    try {
      const fresh = await get(`/tasks/${t.id}`)
      setSelected(fresh)
    } catch (_) {
      setSelected(t)
    }
  }

  const tList = Array.isArray(tasks) ? tasks : []
  const filtered = filter === 'all' ? tList : tList.filter(t => t.status === filter)
  const counts = tList.reduce((a, t) => { a[t.status] = (a[t.status] || 0) + 1; return a }, {})

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <PageHeader title="📋 Tasks" subtitle={`${tList.length} total · ${counts.running || 0} running`} />

      <div className="grid grid-cols-4 gap-3 mb-6">
        {['queued', 'running', 'completed', 'failed'].map(s => (
          <Card key={s} onClick={() => setFilter(filter === s ? 'all' : s)} className={`cursor-pointer ${filter === s ? 'ring-1 ring-purple-600' : ''}`}>
            <p className="text-xs text-gray-500 uppercase tracking-wider">{s}</p>
            <p className="text-2xl font-bold mt-1" style={{
              color: s === 'completed' ? '#22c55e' : s === 'failed' ? '#ef4444' : s === 'running' ? '#60a5fa' : 'var(--accent)'
            }}>
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
            {agents.filter(a => a.visible !== false).map(a => (
              <option key={a.id} value={a.id}>{a.icon} {a.name}</option>
            ))}
          </select>
          <input
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            placeholder="Task description… (e.g. Research top 5 bug bounty platforms)"
            className="flex-1 rounded-lg px-3 py-2 text-sm border"
            style={{ background: 'var(--surface2)', borderColor: 'var(--border)', color: 'var(--text)' }}
          />
          <button
            type="submit"
            disabled={loading || !prompt.trim()}
            className="px-4 py-2 rounded-lg text-sm font-semibold disabled:opacity-50 shrink-0"
            style={{ background: 'var(--accent-dark)', color: '#fff' }}
          >
            {loading ? '⏳' : '▶ Create'}
          </button>
        </form>
      </Card>

      <Card>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
            Task Queue {filter !== 'all' && <span className="text-gray-500 font-normal">— {filter}</span>}
          </h2>
          <div className="flex gap-1">
            {['all', 'running', 'completed', 'failed'].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${filter === f ? 'text-white' : 'text-gray-500 hover:text-gray-300'}`}
                style={filter === f ? { background: 'var(--accent-dark)' } : {}}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
        {filtered.length === 0 ? (
          <EmptyState icon="📋" title="No tasks" subtitle={filter === 'all' ? 'Create a task above to get started.' : `No ${filter} tasks.`} />
        ) : (
          <div className="space-y-2">
            {filtered.map(t => {
              const elapsed = t.finished && t.started
                ? `${((t.finished - t.started)).toFixed(1)}s`
                : t.started ? 'running…' : 'queued'
              return (
                <div
                  key={t.id}
                  onClick={() => openTask(t)}
                  className="flex items-start gap-3 p-3 rounded-xl border cursor-pointer hover:border-purple-700 transition-colors"
                  style={{ background: 'var(--surface2)', borderColor: 'var(--border)' }}
                >
                  <Badge label={t.status} type={STATUS_COLOR[t.status] || 'gray'} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-300 truncate">{t.prompt?.slice(0, 120)}</p>
                    <p className="text-xs text-gray-600 mt-0.5">{t.agent_id} · #{t.id} · {elapsed}</p>
                  </div>
                  {t.result?.soul_score != null && (
                    <span className="text-xs shrink-0" style={{ color: t.result.soul_passed ? '#22c55e' : '#ef4444' }}>
                      {(t.result.soul_score * 100).toFixed(0)}%
                    </span>
                  )}
                  <span className="text-gray-600 text-xs shrink-0">→</span>
                </div>
              )
            })}
          </div>
        )}
      </Card>

      {selected && <TaskModal task={selected} onClose={() => setSelected(null)} />}
    </div>
  )
}
