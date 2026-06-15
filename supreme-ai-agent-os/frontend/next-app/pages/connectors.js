import useSWR from 'swr'
import { get } from '../lib/api'
import { Card, PageHeader, Badge, EmptyState } from '../components/Card'

const MODE_COLOR = {
  api: 'green',
  browser_automation: 'blue',
  manual_session_required: 'yellow',
  unavailable: 'red',
}

const MODE_ICON = {
  api: '🔌',
  browser_automation: '🌐',
  manual_session_required: '👤',
  unavailable: '⛔',
}

export default function ConnectorsPage() {
  const { data: allConnectors } = useSWR('/api/connectors/all', get, { refreshInterval: 30000 })
  const integrations = allConnectors?.integrations || []
  const platforms = allConnectors?.bounty_platforms || []

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <PageHeader
        title="🔌 Connectors & Platforms"
        subtitle="Integration health and bounty platform connector status"
      />

      {/* Bounty Platforms */}
      <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--accent)' }}>Bounty Platforms</h2>
      <div className="space-y-3 mb-8">
        {platforms.length === 0 && <EmptyState icon="🔌" title="Loading connectors…" />}
        {platforms.map(p => (
          <Card key={p.id}>
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-base">{MODE_ICON[p.mode]}</span>
                  <span className="font-semibold text-sm" style={{ color: 'var(--text)' }}>{p.name}</span>
                  <Badge label={p.mode?.replace(/_/g, ' ')} type={MODE_COLOR[p.mode] || 'gray'} />
                  {p.has_credentials
                    ? <Badge label="credentials ✓" type="green" />
                    : <Badge label="no credentials" type="yellow" />
                  }
                  {p.module_present
                    ? <Badge label="module ✓" type="purple" />
                    : <Badge label="module missing" type="red" />
                  }
                </div>
                <p className="text-xs text-gray-500 mb-2">{p.notes}</p>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div>
                    <span className="text-gray-600">Ingest: </span>
                    <span className="text-gray-300">{p.ingest_status?.replace(/_/g, ' ')}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Submission: </span>
                    <span className="text-gray-300">{p.submission_status?.replace(/_/g, ' ')}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Payout: </span>
                    <span className="text-gray-300">{p.payout_tracking?.replace(/_/g, ' ')}</span>
                  </div>
                </div>
              </div>
              <a href={p.url} target="_blank" rel="noopener noreferrer" className="text-xs shrink-0" style={{ color: 'var(--accent)' }}>
                → {p.url?.replace('https://', '')}
              </a>
            </div>
            {p.auth_env && p.auth_env.length > 0 && (
              <div className="mt-2 pt-2 border-t text-xs text-gray-600 flex flex-wrap gap-2" style={{ borderColor: 'var(--border)' }}>
                <span>Required env:</span>
                {p.auth_env.map(k => (
                  <code key={k} className="px-1.5 py-0.5 rounded" style={{ background: 'var(--surface2)', color: '#a78bfa' }}>{k}</code>
                ))}
              </div>
            )}
          </Card>
        ))}
      </div>

      {/* Integrations */}
      <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--accent)' }}>Tool Integrations</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {integrations.map(c => (
          <Card key={c.id}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium text-gray-300">{c.name}</span>
              <Badge label={c.enabled ? 'on' : 'off'} type={c.enabled ? 'green' : 'gray'} />
            </div>
            <p className="text-xs text-gray-600">{c.category}</p>
          </Card>
        ))}
      </div>
    </div>
  )
}
