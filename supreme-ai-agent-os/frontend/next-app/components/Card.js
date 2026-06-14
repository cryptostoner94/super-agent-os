export function Card({ children, className = '', onClick }) {
  return (
    <div
      onClick={onClick}
      className={`rounded-2xl border p-5 transition-colors ${onClick ? 'cursor-pointer hover:border-purple-700' : ''} ${className}`}
      style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
    >
      {children}
    </div>
  )
}

export function MetricCard({ icon, label, value, sub, color = 'var(--accent)' }) {
  return (
    <Card>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider font-medium">{label}</p>
          <p className="text-3xl font-bold mt-1" style={{ color }}>{value ?? '—'}</p>
          {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
        </div>
        <span className="text-2xl opacity-60">{icon}</span>
      </div>
    </Card>
  )
}

export function PageHeader({ title, subtitle, action }) {
  return (
    <div className="flex items-start justify-between mb-6">
      <div>
        <h1 className="text-xl font-bold" style={{ color: 'var(--text)' }}>{title}</h1>
        {subtitle && <p className="text-sm text-gray-500 mt-0.5">{subtitle}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  )
}

export function Badge({ label, type = 'gray' }) {
  const map = {
    green: 'badge-green', yellow: 'badge-yellow', red: 'badge-red',
    blue: 'badge-blue', purple: 'badge-purple', gray: 'badge-gray',
    ok: 'badge-green', error: 'badge-red', warn: 'badge-yellow',
    pending: 'badge-yellow', completed: 'badge-green', failed: 'badge-red',
    running: 'badge-blue', queued: 'badge-purple',
  }
  return <span className={`badge ${map[type] || 'badge-gray'}`}>{label}</span>
}

export function Skeleton({ h = 'h-4', w = 'w-full', className = '' }) {
  return <div className={`skeleton ${h} ${w} ${className}`} />
}

export function EmptyState({ icon = '📭', title, subtitle }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <span className="text-5xl mb-4 opacity-40">{icon}</span>
      <h3 className="text-base font-semibold text-gray-400">{title}</h3>
      {subtitle && <p className="text-sm text-gray-600 mt-1">{subtitle}</p>}
    </div>
  )
}
