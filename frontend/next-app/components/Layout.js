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
  const [sheetOpen, setSheetOpen] = useState(false)
  const [liveEvents, setLiveEvents] = useState([])
  const [wsConnected, setWsConnected] = useState(false)

  useEffect(() => {
    get('/health').then(setStatus).catch(() => setStatus({ status: 'error' }))
    const t = setInterval(() => {
      get('/health').then(setStatus).catch(() => setStatus({ status: 'error' }))
    }, 15000)
    return () => clearInterval(t)
  }, [])

  // Close sheet on navigation
  useEffect(() => {
    setSheetOpen(false)
  }, [router.pathname])

  // Close sheet on back button / browser back
  useEffect(() => {
    if (!sheetOpen) return
    const onKey = (e) => { if (e.key === 'Escape') setSheetOpen(false) }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [sheetOpen])

  useWebSocket(useCallback((msg) => {
    setWsConnected(true)
    if (msg.type === 'task_update') {
      const d = msg.data || {}
      setLiveEvents(prev => [{ id: d.id, status: d.status, ts: Date.now() }, ...prev].slice(0, 4))
    }
  }, []))

  const apiOk = status?.status === 'ok'

  const DesktopSidebar = () => (
    <aside
      className={`hidden md:flex flex-col shrink-0 border-r transition-all duration-200 ${collapsed ? 'w-14' : 'w-56'}`}
      style={{ background: '#0d0d1a', borderColor: 'var(--border)' }}
    >
      <div className="flex items-center gap-2 px-3 py-4 border-b" style={{ borderColor: 'var(--border)' }}>
        <button
          onClick={() => setCollapsed(c => !c)}
          className="glow-dot shrink-0 cursor-pointer border-0 bg-transparent"
          title={collapsed ? 'Expand' : 'Collapse'}
        />
        {!collapsed && (
          <span className="font-bold text-sm tracking-tight" style={{ color: 'var(--accent)' }}>
            Super Agent OS
          </span>
        )}
      </div>
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
              {!collapsed && <span>{label}</span>}
            </Link>
          )
        })}
      </nav>
      {!collapsed && liveEvents.length > 0 && (
        <div className="px-3 pb-2 border-t" style={{ borderColor: 'var(--border)' }}>
          <p className="text-xs text-gray-600 uppercase tracking-wider mt-2 mb-1">Live</p>
          {liveEvents.map((e, i) => (
            <div key={i} className="flex items-center gap-2 py-0.5">
              <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: STATUS_COLORS[e.status] || '#6b7280' }} />
              <span className="text-xs text-gray-500 truncate">
                #{e.id} <span style={{ color: STATUS_COLORS[e.status] || '#6b7280' }}>{e.status}</span>
              </span>
            </div>
          ))}
        </div>
      )}
      <div className="p-3 border-t text-xs flex items-center gap-2" style={{ borderColor: 'var(--border)' }}>
        <StatusDot ok={apiOk} pulse={apiOk} />
        {!collapsed && (
          <span className="text-gray-500">
            {apiOk ? 'API Online' : 'API Offline'}
            {wsConnected && apiOk && <span className="ml-1 text-green-700">· WS ✓</span>}
          </span>
        )}
      </div>
    </aside>
  )

  return (
    <div className="flex" style={{ background: 'var(--bg)', height: '100dvh' }}>
      <DesktopSidebar />

      {/* ── Main area ── */}
      <div className="flex-1 flex flex-col min-h-0 min-w-0">
        {/* Page content — full height on mobile, bottom-padded for nav bar */}
        <main
          className="flex-1 overflow-y-auto"
          style={{ paddingBottom: 'calc(env(safe-area-inset-bottom) + 64px)' }}
        >
          {children}
        </main>

        {/* ── Mobile bottom nav (5 tabs, no top bar) ── */}
        <nav
          className="md:hidden fixed bottom-0 left-0 right-0 flex border-t"
          style={{
            background: '#0d0d1a',
            borderColor: 'var(--border)',
            paddingBottom: 'env(safe-area-inset-bottom)',
            zIndex: 40,
            height: '56px',
          }}
        >
          {BOTTOM_NAV.map(({ href, icon, label }) => {
            const active = router.pathname === href
            return (
              <Link
                key={href}
                href={href}
                className="flex-1 flex flex-col items-center justify-center gap-0.5"
                style={{ color: active ? 'var(--accent)' : '#6b7280' }}
              >
                <span className="text-[22px] leading-none">{icon}</span>
                <span className="text-[9px] font-medium tracking-wide">{label}</span>
              </Link>
            )
          })}
          {/* More tab */}
          <button
            onClick={() => setSheetOpen(true)}
            className="flex-1 flex flex-col items-center justify-center gap-0.5"
            style={{ color: sheetOpen ? 'var(--accent)' : '#6b7280', background: 'none', border: 'none' }}
            aria-label="More navigation"
          >
            <span className="text-[22px] leading-none">⋯</span>
            <span className="text-[9px] font-medium tracking-wide">More</span>
          </button>
        </nav>
      </div>

      {/* ── Bottom sheet (slides up from bottom) ── */}
      {sheetOpen && (
        <div
          className="md:hidden fixed inset-0 z-50 flex flex-col justify-end"
          style={{ background: 'rgba(0,0,0,0.6)' }}
          onClick={() => setSheetOpen(false)}
          role="presentation"
        >
          <div
            className="rounded-t-3xl border-t"
            style={{
              background: '#0d0d1a',
              borderColor: 'var(--border)',
              paddingBottom: 'calc(env(safe-area-inset-bottom) + 8px)',
              maxHeight: '80vh',
              overflowY: 'auto',
            }}
            onClick={e => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="Navigation"
          >
            {/* Handle bar */}
            <div className="flex justify-center pt-3 pb-1">
              <div className="w-10 h-1 rounded-full bg-gray-700" />
            </div>

            {/* Status row */}
            <div className="flex items-center justify-between px-5 py-2 mb-1">
              <span className="font-bold text-sm" style={{ color: 'var(--accent)' }}>Super Agent OS</span>
              <div className="flex items-center gap-2">
                <StatusDot ok={apiOk} pulse={apiOk} />
                <span className="text-xs text-gray-500">
                  {apiOk ? 'Online' : 'Offline'}
                  {wsConnected && apiOk && <span className="ml-1 text-green-700">· WS</span>}
                </span>
              </div>
            </div>

            {/* Nav grid — 3 columns */}
            <div className="grid grid-cols-3 gap-1 px-3 pb-2">
              {NAV.map(({ href, icon, label }) => {
                const active = router.pathname === href
                return (
                  <Link
                    key={href}
                    href={href}
                    className="flex flex-col items-center gap-1 py-3 px-2 rounded-2xl transition-colors"
                    style={{
                      background: active ? 'var(--accent-dark)' : 'var(--surface2)',
                      color: active ? '#fff' : '#9ca3af',
                    }}
                  >
                    <span className="text-2xl leading-none">{icon}</span>
                    <span className="text-[11px] font-medium text-center leading-tight">{label}</span>
                  </Link>
                )
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
