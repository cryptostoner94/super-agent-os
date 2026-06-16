import { useState, useCallback } from 'react'
import Link from 'next/link'
import useSWR from 'swr'
import { get, post } from '../lib/api'
import { Badge } from '../components/Card'
import useWebSocket from '../lib/useWebSocket'
import { useTheme } from '../lib/theme'

const REFRESH = 8000

const STATUS_COLOR = { queued: 'purple', running: 'blue', completed: 'green', failed: 'red' }

function timeAgo(ts) {
  const s = Math.floor((Date.now() - ts) / 1000)
  if (s < 60) return `${s}s ago`
  if (s < 3600) return `${Math.floor(s / 60)}m ago`
  return `${Math.floor(s / 3600)}h ago`
}

const QUICK_ACTIONS = [
  { href: '/bounties',   icon: '🎯', label: 'Bounties' },
  { href: '/revenue',    icon: '💰', label: 'Revenue' },
  { href: '/agents',     icon: '🤖', label: 'Agents' },
  { href: '/tasks',      icon: '📋', label: 'Tasks' },
  { href: '/war-map',    icon: '🗺️', label: 'War Map' },
  { href: '/connectors', icon: '🔌', label: 'Connect' },
  { href: '/payments',   icon: '💳', label: 'Payments' },
  { href: '/settings',   icon: '⚙️', label: 'Settings' },
]

const AGENT_ICONS = {
  executive: '🧠', planner: '📋', researcher: '🔍', builder: '🔨',
  bounty_hunter: '🎯', reward_scout: '💰', browser: '🌐',
  monitor: '📡', memory_agent: '🧩', telegram_agent: '📱', executor: '⚙️',
}

export default function Overview() {
  const { theme, toggleTheme } = useTheme()
  const { data: health } = useSWR('/health', get, { refreshInterval: REFRESH })
  const { data: tasks } = useSWR('/tasks', get, { refreshInterval: REFRESH })
  const { data: agents = [] } = useSWR('/agents', get, { refreshInterval: 30000 })
  const { data: rewards } = useSWR('/rewards', get, { refreshInterval: 60000 })

  const [prompt, setPrompt] = useState('')
  const [agentId, setAgentId] = useState('executive')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [liveEvents, setLiveEvents] = useState([])

  useWebSocket(useCallback((msg) => {
    if (msg.type === 'task_update') {
      const d = msg.data || {}
      setLiveEvents(prev => [{
        id: d.id, status: d.status, prompt: d.prompt || '', ts: Date.now()
      }, ...prev].slice(0, 6))
    }
  }, []))

  const taskList = Array.isArray(tasks) ? tasks : []
  const running = taskList.filter(t => t.status === 'running').length
  const completed = taskList.filter(t => t.status === 'completed').length
  const visibleAgents = Array.isArray(agents) ? agents.filter(a => a.visible !== false) : []
  const opps = rewards?.opportunities || []
  const apiOk = health?.status === 'ok'

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

  const recentTasks = taskList.slice(0, 5)
  const activityFeed = liveEvents.length > 0 ? liveEvents : recentTasks.map(t => ({
    id: t.id, status: t.status, prompt: t.prompt || '', ts: (t.created || 0) * 1000
  }))

  return (
    <div style={{ background: 'var(--bg)', minHeight: '100%' }}>

      {/* ── Hero Header ── */}
      <div
        className="gradient-hero relative overflow-hidden"
        style={{ padding: '28px 24px 20px' }}
      >
        <div
          style={{
            position: 'absolute', top: '-40px', right: '-40px',
            width: '200px', height: '200px', borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(167,139,250,0.12) 0%, transparent 70%)',
            pointerEvents: 'none',
          }}
        />
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div style={{ position: 'relative', flexShrink: 0 }}>
              <div
                style={{
                  width: '52px', height: '52px', borderRadius: '16px',
                  background: 'linear-gradient(135deg, #7c3aed, #a78bfa)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '26px', boxShadow: '0 0 0 3px rgba(167,139,250,0.2)',
                }}
              >
                🤖
              </div>
              {apiOk && (
                <span
                  className="animate-pulse"
                  style={{
                    position: 'absolute', bottom: '-2px', right: '-2px',
                    width: '14px', height: '14px', borderRadius: '50%',
                    background: '#22c55e', border: '2px solid var(--bg)',
                    boxShadow: '0 0 6px #22c55e',
                  }}
                />
              )}
            </div>
            <div>
              <h1 style={{ color: 'var(--text)', fontSize: '22px', fontWeight: 800, letterSpacing: '-0.3px' }}>
                Super Agent OS
              </h1>
              <p style={{ color: 'var(--muted)', fontSize: '12px', marginTop: '2px' }}>
                Autonomous AI Operations Platform
              </p>
              <div className="flex items-center gap-2 mt-2">
                <span
                  style={{
                    display: 'inline-flex', alignItems: 'center', gap: '5px',
                    padding: '3px 10px', borderRadius: '99px', fontSize: '11px', fontWeight: 600,
                    background: apiOk ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)',
                    color: apiOk ? '#22c55e' : '#ef4444',
                    border: `1px solid ${apiOk ? '#166534' : '#991b1b'}`,
                  }}
                >
                  <span className={apiOk ? 'animate-pulse' : ''} style={{ fontSize: '8px' }}>●</span>
                  {apiOk ? 'Systems Online' : 'Offline'}
                </span>
              </div>
            </div>
          </div>
          <button
            onClick={toggleTheme}
            style={{
              background: 'var(--surface2)', border: '1px solid var(--border)',
              borderRadius: '10px', padding: '8px 10px', fontSize: '18px',
              cursor: 'pointer', lineHeight: 1,
            }}
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
        </div>
      </div>

      <div style={{ padding: '0 16px 100px' }}>

        {/* ── Pipeline Strip ── */}
        <div
          className="flex gap-3 overflow-x-auto"
          style={{ margin: '16px 0', paddingBottom: '4px', scrollbarWidth: 'none' }}
        >
          {[
            { icon: '🤖', label: 'Agents', value: visibleAgents.length || '—', href: '/agents', color: '#a78bfa' },
            { icon: '⚡', label: 'Running', value: running, href: '/tasks', color: '#60a5fa' },
            { icon: '✅', label: 'Done', value: completed, href: '/tasks', color: '#22c55e' },
            { icon: '🎯', label: 'Bounties', value: opps.filter(o => o.type === 'bug_bounty').length || '—', href: '/bounties', color: '#ef4444' },
            { icon: '💼', label: 'Opps', value: opps.length || '—', href: '/revenue', color: '#f59e0b' },
          ].map(({ icon, label, value, href, color }) => (
            <Link
              key={href + label}
              href={href}
              style={{
                flexShrink: 0, display: 'flex', flexDirection: 'column', alignItems: 'center',
                gap: '4px', padding: '12px 16px', borderRadius: '16px', minWidth: '80px',
                background: 'var(--surface)', border: '1px solid var(--border)', textDecoration: 'none',
              }}
            >
              <span style={{ fontSize: '20px' }}>{icon}</span>
              <span style={{ fontSize: '20px', fontWeight: 700, color, lineHeight: 1 }}>{value}</span>
              <span style={{ fontSize: '10px', color: 'var(--muted)', fontWeight: 500 }}>{label}</span>
            </Link>
          ))}
        </div>

        {/* ── Command Center ── */}
        <div
          style={{
            background: 'var(--surface)', border: '1px solid var(--border)',
            borderRadius: '20px', padding: '20px', marginBottom: '16px',
          }}
          className="shadow-glow"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 style={{ color: 'var(--text)', fontSize: '15px', fontWeight: 700 }}>⚡ Command Center</h2>
            <Link href="/tasks" style={{ fontSize: '12px', color: 'var(--accent)', textDecoration: 'none' }}>
              All Tasks →
            </Link>
          </div>

          {/* Agent pills */}
          <div className="flex gap-2 overflow-x-auto mb-4" style={{ scrollbarWidth: 'none', paddingBottom: '2px' }}>
            {(visibleAgents.length > 0
              ? visibleAgents
              : [
                  { id: 'executive', name: 'Executive', icon: '🧠' },
                  { id: 'researcher', name: 'Research', icon: '🔍' },
                  { id: 'bounty_hunter', name: 'Bounty', icon: '🎯' },
                  { id: 'reward_scout', name: 'Revenue', icon: '💰' },
                  { id: 'browser', name: 'Browser', icon: '🌐' },
                ]
            ).slice(0, 7).map(a => (
              <button
                key={a.id}
                onClick={() => setAgentId(a.id)}
                style={{
                  flexShrink: 0, display: 'inline-flex', alignItems: 'center', gap: '6px',
                  padding: '6px 14px', borderRadius: '99px', fontSize: '12px', fontWeight: 600,
                  background: agentId === a.id ? 'var(--accent-dark)' : 'var(--surface2)',
                  color: agentId === a.id ? '#fff' : 'var(--muted)',
                  border: `1px solid ${agentId === a.id ? 'var(--accent)' : 'var(--border)'}`,
                  cursor: 'pointer', transition: 'all 0.15s',
                }}
              >
                <span style={{ fontSize: '14px' }}>{a.icon || AGENT_ICONS[a.id] || '🤖'}</span>
                {a.name}
              </button>
            ))}
          </div>

          {/* Terminal-style prompt */}
          <form onSubmit={runTask}>
            <div
              style={{
                background: 'var(--surface2)', borderRadius: '12px',
                border: '1px solid var(--border)', overflow: 'hidden',
              }}
            >
              <div
                style={{
                  padding: '8px 14px', display: 'flex', alignItems: 'center', gap: '8px',
                  borderBottom: '1px solid var(--border)',
                }}
              >
                <span style={{ color: 'var(--accent)', fontSize: '12px', fontFamily: 'monospace', fontWeight: 700 }}>
                  {AGENT_ICONS[agentId] || '🤖'} {agentId}
                </span>
                <span style={{ color: 'var(--muted)', fontSize: '11px' }}>›</span>
              </div>
              <textarea
                value={prompt}
                onChange={e => setPrompt(e.target.value)}
                rows={3}
                placeholder="Describe your mission…  (Ctrl+Enter to launch)"
                onKeyDown={e => {
                  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) runTask(e)
                }}
                style={{
                  width: '100%', padding: '12px 14px', background: 'transparent',
                  color: 'var(--text)', border: 'none', outline: 'none', resize: 'none',
                  fontFamily: 'monospace', fontSize: '13px', lineHeight: '1.5',
                }}
              />
            </div>
            <button
              type="submit"
              disabled={loading || !prompt.trim()}
              style={{
                width: '100%', marginTop: '10px', padding: '12px',
                borderRadius: '12px', fontSize: '14px', fontWeight: 700,
                background: loading || !prompt.trim()
                  ? 'var(--surface2)'
                  : 'linear-gradient(135deg, #7c3aed, #a78bfa)',
                color: loading || !prompt.trim() ? 'var(--muted)' : '#fff',
                border: 'none', cursor: loading || !prompt.trim() ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s', letterSpacing: '0.02em',
              }}
            >
              {loading ? '⏳ Agent Working…' : '▶ Launch Agent'}
            </button>
          </form>

          {result && (
            <div
              style={{
                marginTop: '14px', padding: '14px', borderRadius: '12px',
                background: result.error ? 'rgba(239,68,68,0.05)' : 'var(--surface2)',
                border: `1px solid ${result.error ? '#991b1b' : 'var(--border)'}`,
              }}
            >
              {result.error ? (
                <p style={{ color: '#ef4444', fontSize: '13px' }}>Error: {result.error}</p>
              ) : (
                <div>
                  <div className="flex gap-2 flex-wrap mb-3">
                    {result.intent && <Badge label={result.intent} type="blue" />}
                    {result.agent && <Badge label={result.agent} type="purple" />}
                    {result.soul_score != null && (
                      <Badge
                        label={`soul ${(result.soul_score * 100).toFixed(0)}%`}
                        type={result.soul_passed ? 'green' : 'yellow'}
                      />
                    )}
                  </div>
                  <p style={{ color: 'var(--text)', fontSize: '13px', lineHeight: '1.6', whiteSpace: 'pre-wrap' }}>
                    {(result.answer || JSON.stringify(result, null, 2)).slice(0, 1000)}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* ── Agent Status Mini Map ── */}
        <div
          style={{
            background: 'var(--surface)', border: '1px solid var(--border)',
            borderRadius: '20px', padding: '16px 20px', marginBottom: '16px',
          }}
        >
          <div className="flex items-center justify-between mb-3">
            <h2 style={{ color: 'var(--text)', fontSize: '14px', fontWeight: 700 }}>🗺️ Agent Status</h2>
            <Link href="/war-map" style={{ fontSize: '12px', color: 'var(--accent)', textDecoration: 'none' }}>
              Full War Map →
            </Link>
          </div>
          <div className="flex gap-3 overflow-x-auto" style={{ scrollbarWidth: 'none' }}>
            {(visibleAgents.length > 0
              ? visibleAgents
              : Object.entries(AGENT_ICONS).map(([id, icon]) => ({ id, icon, name: id }))
            ).slice(0, 8).map(a => {
              const isRunning = taskList.some(t => t.agent_id === a.id && t.status === 'running')
              return (
                <div
                  key={a.id}
                  style={{ flexShrink: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px', minWidth: '60px' }}
                >
                  <div
                    style={{
                      width: '40px', height: '40px', borderRadius: '12px', fontSize: '20px',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      background: isRunning ? 'rgba(96,165,250,0.15)' : 'var(--surface2)',
                      border: `1px solid ${isRunning ? '#1d4ed8' : 'var(--border)'}`,
                      boxShadow: isRunning ? '0 0 8px rgba(96,165,250,0.3)' : 'none',
                    }}
                    className={isRunning ? 'animate-pulse-slow' : ''}
                  >
                    {a.icon || AGENT_ICONS[a.id] || '🤖'}
                  </div>
                  <span style={{ fontSize: '9px', color: 'var(--muted)', textAlign: 'center', lineHeight: 1.2 }}>
                    {(a.name || a.id).slice(0, 8)}
                  </span>
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: isRunning ? '#60a5fa' : '#22c55e' }} />
                </div>
              )
            })}
          </div>
        </div>

        {/* ── Quick Actions ── */}
        <div className="flex gap-2 overflow-x-auto mb-4" style={{ scrollbarWidth: 'none', paddingBottom: '2px' }}>
          {QUICK_ACTIONS.map(({ href, icon, label }) => (
            <Link
              key={href}
              href={href}
              style={{
                flexShrink: 0, display: 'flex', flexDirection: 'column', alignItems: 'center',
                gap: '6px', padding: '12px 14px', borderRadius: '14px', minWidth: '72px',
                background: 'var(--surface)', border: '1px solid var(--border)', textDecoration: 'none',
              }}
            >
              <span style={{ fontSize: '22px' }}>{icon}</span>
              <span style={{ fontSize: '10px', color: 'var(--muted)', fontWeight: 600 }}>{label}</span>
            </Link>
          ))}
        </div>

        {/* ── Live Activity Feed ── */}
        <div
          style={{
            background: 'var(--surface)', border: '1px solid var(--border)',
            borderRadius: '20px', padding: '16px 20px',
          }}
        >
          <div className="flex items-center justify-between mb-3">
            <h2 style={{ color: 'var(--text)', fontSize: '14px', fontWeight: 700 }}>📡 Live Activity</h2>
            <Link href="/tasks" style={{ fontSize: '12px', color: 'var(--accent)', textDecoration: 'none' }}>
              View all →
            </Link>
          </div>
          {activityFeed.length === 0 ? (
            <p style={{ color: 'var(--muted)', fontSize: '13px', textAlign: 'center', padding: '20px 0' }}>
              No activity yet. Launch an agent above.
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {activityFeed.map((ev, i) => (
                <div
                  key={ev.id || i}
                  style={{
                    display: 'flex', alignItems: 'center', gap: '10px',
                    padding: '10px 12px', borderRadius: '12px',
                    background: 'var(--surface2)', border: '1px solid var(--border)',
                  }}
                >
                  <span
                    style={{
                      width: '8px', height: '8px', borderRadius: '50%', flexShrink: 0,
                      background: ev.status === 'completed' ? '#22c55e'
                        : ev.status === 'running' ? '#60a5fa'
                        : ev.status === 'failed' ? '#ef4444' : '#a78bfa',
                      boxShadow: ev.status === 'running' ? '0 0 6px #60a5fa' : 'none',
                    }}
                    className={ev.status === 'running' ? 'animate-pulse' : ''}
                  />
                  <span
                    style={{
                      flex: 1, fontSize: '12px', color: 'var(--text)',
                      overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    }}
                  >
                    {ev.prompt?.slice(0, 60) || `Task #${ev.id}`}
                  </span>
                  <div style={{ flexShrink: 0, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '2px' }}>
                    <Badge label={ev.status} type={STATUS_COLOR[ev.status] || 'gray'} />
                    {ev.ts > 0 && (
                      <span style={{ fontSize: '10px', color: 'var(--muted)' }}>{timeAgo(ev.ts)}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  )
}
