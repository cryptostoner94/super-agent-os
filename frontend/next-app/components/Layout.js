import Link from 'next/link'
import { useRouter } from 'next/router'
import { useState, useEffect, useCallback } from 'react'
import { get } from '../lib/api'
import useWebSocket from '../lib/useWebSocket'
import { useTheme } from '../lib/theme'

const NAV = [
  { href: '/',           icon: '⚡', label: 'Overview' },
  { href: '/agents',     icon: '🤖', label: 'Agents' },
  { href: '/war-map',    icon: '🗺️', label: 'War Map' },
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
  { href: '/war-map',  icon: '🗺️', label: 'War Map' },
  { href: '/bounties', icon: '🎯', label: 'Bounties' },
]

function StatusDot({ ok, pulse }) {
  return (
    <span
      className={`inline-block w-2 h-2 rounded-full ${pulse ? 'animate-pulse' : ''}`}
      style={{ background: ok ? '#22c55e' : '#ef4444' }}
    />
  )
}

function ThemeToggle({ small }) {
  const { theme, toggleTheme } = useTheme()
  return (
    <button
      onClick={toggleTheme}
      aria-label="Toggle theme"
      style={{
        background: 'none',
        border: 'none',
        cursor: 'pointer',
        fontSize: small ? '16px' : '18px',
        lineHeight: 1,
        padding: '4px',
        minHeight: 'unset',
        minWidth: 'unset',
      }}
      title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {theme === 'dark' ? '☀️' : '🌙'}
    </button>
  )
}

export default function Layout({ children }) {
  const router = useRouter()
  const [status, setStatus] = useState(null)
  const [collapsed, setCollapsed] = useState(false)
  const [sheetOpen, setSheetOpen] = useState(false)
  const [wsConnected, setWsConnected] = useState(false)

  useEffect(() => {
    get('/health').then(setStatus).catch(() => setStatus({ status: 'error' }))
    const t = setInterval(() => {
      get('/health').then(setStatus).catch(() => setStatus({ status: 'error' }))
    }, 15000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => { setSheetOpen(false) }, [router.pathname])

  useEffect(() => {
    if (!sheetOpen) return
    const onKey = (e) => { if (e.key === 'Escape') setSheetOpen(false) }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [sheetOpen])

  useWebSocket(useCallback((msg) => {
    setWsConnected(true)
  }, []))

  const apiOk = status?.status === 'ok'

  return (
    <div className="flex" style={{ background: 'var(--bg)', height: '100dvh' }}>

      {/* ── Desktop sidebar ── */}
      <aside
        className="hidden md:flex flex-col shrink-0 border-r transition-all duration-200"
        style={{
          background: 'var(--surface)',
          borderColor: 'var(--border)',
          width: collapsed ? '64px' : '220px',
        }}
      >
        {/* Header */}
        <div
          className="flex items-center border-b shrink-0"
          style={{
            borderColor: 'var(--border)',
            height: '56px',
            padding: collapsed ? '0' : '0 12px',
            justifyContent: collapsed ? 'center' : 'space-between',
          }}
        >
          <button
            onClick={() => setCollapsed(c => !c)}
            className="flex flex-col items-center justify-center gap-[5px] w-9 h-9 rounded-lg transition-colors"
            style={{ border: 'none', background: 'none', cursor: 'pointer', flexShrink: 0 }}
            aria-label={collapsed ? 'Expand menu' : 'Collapse menu'}
          >
            <span className="block w-5 h-[2px] rounded-full" style={{ background: 'var(--accent)' }} />
            <span className="block w-5 h-[2px] rounded-full" style={{ background: 'var(--accent)' }} />
            <span className="block w-5 h-[2px] rounded-full" style={{ background: 'var(--accent)' }} />
          </button>
          {!collapsed && (
            <span className="font-bold text-sm tracking-tight ml-2" style={{ color: 'var(--accent)' }}>
              Super Agent OS
            </span>
          )}
        </div>

        {/* Nav items */}
        <nav className="flex-1 overflow-y-auto py-2">
          {NAV.map(({ href, icon, label }) => {
            const active = router.pathname === href
            return (
              <Link
                key={href}
                href={href}
                title={collapsed ? label : undefined}
                className="flex items-center mx-1 my-0.5 rounded-xl transition-colors"
                style={{
                  gap: collapsed ? 0 : '10px',
                  padding: collapsed ? '10px 0' : '10px 12px',
                  justifyContent: collapsed ? 'center' : 'flex-start',
                  background: active ? 'var(--surface2)' : 'transparent',
                  color: active ? 'var(--accent)' : 'var(--muted)',
                }}
              >
                <span style={{ fontSize: collapsed ? '22px' : '18px', lineHeight: 1, flexShrink: 0 }}>
                  {icon}
                </span>
                {!collapsed && (
                  <span className="text-sm font-medium">{label}</span>
                )}
              </Link>
            )
          })}
        </nav>

        {/* Status + theme footer */}
        <div
          className="border-t shrink-0 flex items-center"
          style={{
            borderColor: 'var(--border)',
            padding: collapsed ? '12px 0' : '10px 14px',
            justifyContent: collapsed ? 'center' : 'space-between',
            gap: '8px',
          }}
        >
          <div className="flex items-center gap-2">
            <StatusDot ok={apiOk} pulse={apiOk} />
            {!collapsed && (
              <span className="text-xs" style={{ color: 'var(--muted)' }}>
                {apiOk ? 'Online' : 'Offline'}
                {wsConnected && apiOk && <span className="ml-1" style={{ color: 'var(--success)' }}>· WS</span>}
              </span>
            )}
          </div>
          {!collapsed && <ThemeToggle small />}
        </div>
      </aside>

      {/* ── Main area ── */}
      <div className="flex-1 flex flex-col min-h-0 min-w-0">
        <main
          className="flex-1 overflow-y-auto"
          style={{ paddingBottom: 'calc(env(safe-area-inset-bottom) + 64px)' }}
        >
          {children}
        </main>

        {/* ── Mobile bottom nav ── */}
        <nav
          className="md:hidden fixed bottom-0 left-0 right-0 flex border-t"
          style={{
            background: 'var(--surface)',
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
                style={{ color: active ? 'var(--accent)' : 'var(--muted)' }}
              >
                <span className="text-[22px] leading-none">{icon}</span>
                <span className="text-[9px] font-medium tracking-wide">{label}</span>
              </Link>
            )
          })}
          <button
            onClick={() => setSheetOpen(true)}
            className="flex-1 flex flex-col items-center justify-center gap-0.5"
            style={{ color: sheetOpen ? 'var(--accent)' : 'var(--muted)', background: 'none', border: 'none' }}
            aria-label="More navigation"
          >
            <span className="text-[22px] leading-none">⋯</span>
            <span className="text-[9px] font-medium tracking-wide">More</span>
          </button>
        </nav>
      </div>

      {/* ── Mobile bottom sheet ── */}
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
              background: 'var(--surface)',
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
            <div className="flex justify-center pt-3 pb-1">
              <div className="w-10 h-1 rounded-full" style={{ background: 'var(--border)' }} />
            </div>
            <div className="flex items-center justify-between px-5 py-2 mb-1">
              <span className="font-bold text-sm" style={{ color: 'var(--accent)' }}>Super Agent OS</span>
              <div className="flex items-center gap-3">
                <ThemeToggle small />
                <div className="flex items-center gap-2">
                  <StatusDot ok={apiOk} pulse={apiOk} />
                  <span className="text-xs" style={{ color: 'var(--muted)' }}>
                    {apiOk ? 'Online' : 'Offline'}
                  </span>
                </div>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2 px-4 pb-3">
              {NAV.map(({ href, icon, label }) => {
                const active = router.pathname === href
                return (
                  <Link
                    key={href}
                    href={href}
                    className="flex flex-col items-center gap-1.5 py-3 px-2 rounded-2xl"
                    style={{
                      background: active ? 'var(--accent-dark)' : 'var(--surface2)',
                      color: active ? '#fff' : 'var(--muted)',
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
