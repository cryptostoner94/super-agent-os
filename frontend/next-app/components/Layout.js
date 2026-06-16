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

const BOTTOM_NAV = [
  { href: '/',         icon: '⚡', label: 'Home' },
  { href: '/agents',   icon: '🤖', label: 'Agents' },
  { href: '/tasks',    icon: '📋', label: 'Tasks' },
  { href: '/bounties', icon: '🎯', label: 'Bounties' },
]

const STATUS_COLORS = {
  running: '#60a5fa', completed: '#22c55e', failed: '#ef4444', queued: '#a78bfa',
}

function StatusDot({ ok, pulse }) {
  return (
    <span
      className={`inline-block w-2 h-2 rounded-full ${pulse ? 'animate-pulse' : ''}`}
      style={{ background: ok ? '#22c55e' : '#ef4444' }}
    />
  )
}

export default function Layout({ children }) {
  const router = useRouter()
  const [status, setStatus] = useState(null)
  const [collapsed, setCollapsed] = useState(false)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [liveEvents, setLiveEvents] = useState([])
  const [wsConnected, setWsConnected] = useState(false)

  useEffect(() => {
    get('/health').then(setStatus).catch(() => setStatus({ status: 'error' }))
    const t = setInterval(() => {
      get('/health').then(setStatus).catch(() => setStatus({ status: 'error' }))
    }, 15000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    if (drawerOpen) setDrawerOpen(false)
  }, [router.pathname]) // eslint-disable-line react-hooks/exhaustive-deps

  useWebSocket(useCallback((msg) => {
    setWsConnected(true)
    if (msg.type === 'task_update') {
      const d = msg.data || {}
      setLiveEvents(prev => [{ id: d.id, status: d.status, ts: Date.now() }, ...prev].slice(0, 4))
    }
  }, []))

  const apiOk = status?.status === 'ok'

  const SidebarContent = ({ compact }) => (
    <>
      <nav className="flex-1 py-2 overflow-y-auto">
        {NAV.map(({ href, icon, label }) => {
          const active = router.pathname === href
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 mx-1 my-0.5 rounded-xl text-sm font-medium transition-colors ${
                active ? 'bg-[#1e1e3a]' : 'text-gray-400 hover:bg-[#1a1a2e] hover:text-gray-200'
              }`}
              style={active ? { color: 'var(--accent)' } : {}}
            >
              <span className="text-lg shrink-0 leading-none">{icon}</span>
              {!compact && <span>{label}</span>}
            </Link>
          )
        })}
      </nav>

      {!compact && liveEvents.length > 0 && (
        <div className="px-3 pb-2 border-t" style={{ borderColor: 'var(--border)' }}>
          <p className="text-xs text-gray-600 uppercase tracking-wider mt-2 mb-1">Live Activity</p>
          {liveEvents.map((e, i) => (
            <div key={i} className="flex items-center gap-2 py-0.5">
              <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: STATUS_COLORS[e.status] || '#6b7280' }} />
              <span className="text-xs text-gray-500 truncate">
                Task #{e.id} → <span style={{ color: STATUS_COLORS[e.status] || '#6b7280' }}>{e.status}</span>
              </span>
            </div>
          ))}
        </div>
      )}

      <div className="p-3 border-t text-xs flex items-center gap-2" style={{ borderColor: 'var(--border)' }}>
        <StatusDot ok={apiOk} pulse={apiOk} />
        {!compact && (
          <span className="text-gray-500">
            {apiOk ? 'API Online' : 'API Offline'}
            {wsConnected && apiOk && <span className="ml-1 text-green-700">· WS ✓</span>}
          </span>
        )}
      </div>
    </>
  )

  return (
    <div className="flex" style={{ background: 'var(--bg)', height: '100dvh' }}>

      {/* ── Desktop sidebar (hidden on mobile) ── */}
      <aside
        className={`hidden md:flex flex-col shrink-0 border-r transition-all duration-200 ${collapsed ? 'w-14' : 'w-56'}`}
        style={{ background: '#0d0d1a', borderColor: 'var(--border)' }}
      >
        <div className="flex items-center gap-2 px-3 py-4 border-b" style={{ borderColor: 'var(--border)' }}>
          <button
            onClick={() => setCollapsed(c => !c)}
            className="glow-dot shrink-0 cursor-pointer border-0 bg-transparent"
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          />
          {!collapsed && (
            <span className="font-bold text-sm tracking-tight" style={{ color: 'var(--accent)' }}>
              Super Agent OS
            </span>
          )}
        </div>
        <SidebarContent compact={collapsed} />
      </aside>

      {/* ── Mobile drawer overlay ── */}
      {drawerOpen && (
        <div
          className="md:hidden fixed inset-0 z-50 flex"
          style={{ background: 'rgba(0,0,0,0.7)' }}
          onClick={() => setDrawerOpen(false)}
          onKeyDown={(e) => { if (e.key === 'Escape') setDrawerOpen(false) }}
          role="presentation"
        >
          <div
            className="flex flex-col w-64 h-full border-r"
            style={{ background: '#0d0d1a', borderColor: 'var(--border)' }}
            onClick={e => e.stopPropagation()}
            onKeyDown={e => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="Navigation menu"
          >
            <div className="flex items-center justify-between px-4 py-4 border-b" style={{ borderColor: 'var(--border)' }}>
              <span className="font-bold text-sm" style={{ color: 'var(--accent)' }}>Super Agent OS</span>
              <button
                onClick={() => setDrawerOpen(false)}
                className="text-gray-500 hover:text-gray-200 text-xl w-8 h-8 flex items-center justify-center"
                aria-label="Close menu"
              >
                ✕
              </button>
            </div>
            <SidebarContent compact={false} />
          </div>
        </div>
      )}

      {/* ── Main area ── */}
      <div className="flex-1 flex flex-col min-h-0 min-w-0">

        {/* Mobile top bar */}
        <header
          className="md:hidden flex items-center justify-between px-4 border-b shrink-0"
          style={{ background: '#0d0d1a', borderColor: 'var(--border)', height: '52px' }}
        >
          <button
            onClick={() => setDrawerOpen(true)}
            className="flex items-center justify-center w-9 h-9 rounded-lg text-gray-400 hover:text-gray-200 text-xl"
            aria-label="Open menu"
            style={{ background: 'var(--surface2)' }}
          >
            ☰
          </button>
          <span className="font-bold text-sm" style={{ color: 'var(--accent)' }}>Super Agent OS</span>
          <div className="flex items-center gap-2">
            <StatusDot ok={apiOk} pulse={apiOk} />
            <span className="text-xs text-gray-500">{apiOk ? 'Live' : 'Off'}</span>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto" style={{ paddingBottom: 'calc(env(safe-area-inset-bottom) + 72px)' }}>
          <div className="md:pb-0" style={{ minHeight: '100%' }}>
            {children}
          </div>
        </main>

        {/* ── Mobile bottom nav ── */}
        <nav
          className="md:hidden fixed bottom-0 left-0 right-0 border-t flex"
          style={{
            background: '#0d0d1a',
            borderColor: 'var(--border)',
            paddingBottom: 'env(safe-area-inset-bottom)',
            zIndex: 40,
          }}
        >
          {BOTTOM_NAV.map(({ href, icon, label }) => {
            const active = router.pathname === href
            return (
              <Link
                key={href}
                href={href}
                className="flex-1 flex flex-col items-center justify-center gap-0.5 py-2.5 transition-colors"
                style={{ color: active ? 'var(--accent)' : '#6b7280' }}
              >
                <span className="text-xl leading-none">{icon}</span>
                <span className="text-[10px] font-medium">{label}</span>
              </Link>
            )
          })}
          <button
            onClick={() => setDrawerOpen(true)}
            className="flex-1 flex flex-col items-center justify-center gap-0.5 py-2.5 transition-colors"
            style={{ color: drawerOpen ? 'var(--accent)' : '#6b7280' }}
          >
            <span className="text-xl leading-none">☰</span>
            <span className="text-[10px] font-medium">More</span>
          </button>
        </nav>
      </div>
    </div>
  )
}
