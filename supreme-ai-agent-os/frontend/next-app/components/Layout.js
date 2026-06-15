import Link from 'next/link'
import { useRouter } from 'next/router'
import { useState, useEffect, useCallback } from 'react'
import { get } from '../lib/api'
import useWebSocket from '../lib/useWebSocket'

const NAV = [
  { href: '/',           icon: '⚡', label: 'Overview' },
  { href: '/agents',     icon: '🤖', label: 'Agents' },
  { href: '/tasks',      icon: '📋', label: 'Tasks' },
  { href: '/bounties',   icon: '🎯', label: 'Bounties' },
  { href: '/browser',    icon: '🌐', label: 'Browser' },
  { href: '/terminal',   icon: '💻', label: 'Terminal' },
  { href: '/approvals',  icon: '✅', label: 'Approvals' },
  { href: '/revenue',    icon: '💰', label: 'Revenue' },
  { href: '/payments',   icon: '💳', label: 'Payments' },
  { href: '/logs',       icon: '📊', label: 'Logs' },
  { href: '/connectors', icon: '🔌', label: 'Connectors' },
  { href: '/settings',   icon: '⚙️', label: 'Settings' },
]

const STATUS_COLORS = {
  running: '#60a5fa',
  completed: '#22c55e',
  failed: '#ef4444',
  queued: '#a78bfa',
}

function StatusDot({ ok, pulse }) {
  return (
    <span
      className={`inline-block w-2 h-2 rounded-full shadow-sm ${pulse ? 'animate-pulse' : ''}`}
      style={{ background: ok ? '#22c55e' : '#ef4444' }}
    />
  )
}

export default function Layout({ children }) {
  const router = useRouter()
  const [status, setStatus] = useState(null)
  const [collapsed, setCollapsed] = useState(false)
  const [liveEvents, setLiveEvents] = useState([])
  const [wsConnected, setWsConnected] = useState(false)

  useEffect(() => {
    get('/health').then(setStatus).catch(() => setStatus({ status: 'error' }))
    const t = setInterval(() => {
      get('/health').then(setStatus).catch(() => setStatus({ status: 'error' }))
    }, 15000)
    return () => clearInterval(t)
  }, [])

  useWebSocket(useCallback((msg) => {
    setWsConnected(true)
    if (msg.type === 'task_update') {
      const d = msg.data || {}
      setLiveEvents(prev => [{
        id: d.id,
        status: d.status,
        ts: Date.now(),
      }, ...prev].slice(0, 4))
    }
  }, []))

  const apiOk = status?.status === 'ok'

  return (
    <div className="flex h-screen" style={{ background: 'var(--bg)' }}>
      {/* Sidebar */}
      <aside
        className={`flex flex-col shrink-0 border-r transition-all duration-200 ${collapsed ? 'w-14' : 'w-56'}`}
        style={{ background: '#0d0d1a', borderColor: 'var(--border)' }}
      >
        {/* Logo */}
        <div className="flex items-center gap-2 px-3 py-4 border-b" style={{ borderColor: 'var(--border)' }}>
          <button
            onClick={() => setCollapsed(c => !c)}
            className="glow-dot shrink-0 cursor-pointer border-0 bg-transparent"
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          />
          {!collapsed && (
            <span className="font-bold text-sm tracking-tight" style={{ color: 'var(--accent)' }}>
              Supreme AI OS
            </span>
          )}
        </div>

        {/* Nav items */}
        <nav className="flex-1 py-2 overflow-y-auto">
          {NAV.map(({ href, icon, label }) => {
            const active = router.pathname === href
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-3 px-3 py-2 mx-1 my-0.5 rounded-lg text-sm font-medium transition-colors ${
                  active
                    ? 'bg-[#1e1e3a] text-accent'
                    : 'text-gray-400 hover:bg-[#1a1a2e] hover:text-gray-200'
                }`}
                style={active ? { color: 'var(--accent)' } : {}}
              >
                <span className="text-base shrink-0">{icon}</span>
                {!collapsed && <span>{label}</span>}
              </Link>
            )
          })}
        </nav>

        {/* Live activity feed (only when expanded) */}
        {!collapsed && liveEvents.length > 0 && (
          <div className="px-3 pb-2 border-t" style={{ borderColor: 'var(--border)' }}>
            <p className="text-xs text-gray-600 uppercase tracking-wider mt-2 mb-1">Live Activity</p>
            {liveEvents.map((e, i) => (
              <div key={i} className="flex items-center gap-2 py-0.5">
                <span
                  className="w-1.5 h-1.5 rounded-full shrink-0"
                  style={{ background: STATUS_COLORS[e.status] || '#6b7280' }}
                />
                <span className="text-xs text-gray-500 truncate">
                  Task #{e.id} → <span style={{ color: STATUS_COLORS[e.status] || '#6b7280' }}>{e.status}</span>
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Status footer */}
        <div
          className="p-3 border-t text-xs flex items-center gap-2"
          style={{ borderColor: 'var(--border)', color: 'var(--text-muted)' }}
        >
          <StatusDot ok={apiOk} pulse={apiOk} />
          {!collapsed && (
            <span className="text-gray-500">
              {apiOk ? 'API Online' : 'API Offline'}
              {wsConnected && apiOk && <span className="ml-1 text-green-700">· WS ✓</span>}
            </span>
          )}
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  )
}
