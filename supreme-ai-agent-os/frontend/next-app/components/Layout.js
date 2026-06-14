import Link from 'next/link'
import { useRouter } from 'next/router'
import { useState, useEffect } from 'react'
import { get } from '../lib/api'

const NAV = [
  { href: '/',           icon: '⚡', label: 'Overview' },
  { href: '/agents',     icon: '🤖', label: 'Agents' },
  { href: '/tasks',      icon: '📋', label: 'Tasks' },
  { href: '/bounties',   icon: '🎯', label: 'Bounties' },
  { href: '/browser',    icon: '🌐', label: 'Browser Sessions' },
  { href: '/terminal',   icon: '💻', label: 'Terminal Jobs' },
  { href: '/approvals',  icon: '✅', label: 'Approvals' },
  { href: '/revenue',    icon: '💰', label: 'Revenue' },
  { href: '/payments',   icon: '💳', label: 'Payments' },
  { href: '/logs',       icon: '📊', label: 'Logs' },
  { href: '/connectors', icon: '🔌', label: 'Connectors' },
  { href: '/settings',   icon: '⚙️', label: 'Settings' },
]

function StatusDot({ ok }) {
  return (
    <span className={`inline-block w-2 h-2 rounded-full ${ok ? 'bg-success' : 'bg-danger'} shadow-sm`} />
  )
}

export default function Layout({ children }) {
  const router = useRouter()
  const [status, setStatus] = useState(null)
  const [collapsed, setCollapsed] = useState(false)

  useEffect(() => {
    get('/health').then(setStatus).catch(() => setStatus({ status: 'error' }))
    const t = setInterval(() => {
      get('/health').then(setStatus).catch(() => setStatus({ status: 'error' }))
    }, 15000)
    return () => clearInterval(t)
  }, [])

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

        {/* Status footer */}
        {!collapsed && (
          <div className="p-3 border-t text-xs text-gray-500 flex items-center gap-2" style={{ borderColor: 'var(--border)' }}>
            <StatusDot ok={status?.status === 'ok'} />
            <span>{status?.status === 'ok' ? 'API Online' : 'API Offline'}</span>
          </div>
        )}
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  )
}
