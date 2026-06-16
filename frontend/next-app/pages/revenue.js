import useSWR from 'swr'
import { get } from '../lib/api'
import { Card, MetricCard, PageHeader, Badge } from '../components/Card'

export default function RevenuePage() {
  const { data: rewards } = useSWR('/rewards', get, { refreshInterval: 60000 })
  const opps = rewards?.opportunities || []

  const byType = opps.reduce((a, o) => {
    a[o.type] = (a[o.type] || 0) + 1
    return a
  }, {})

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <PageHeader title="💰 Revenue & Analytics" subtitle="Opportunity tracking and revenue pipeline" />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <MetricCard icon="🎯" label="Bug Bounties" value={byType.bug_bounty || 0} color="#ef4444" />
        <MetricCard icon="🏆" label="Hackathons" value={byType.hackathon || 0} color="#60a5fa" />
        <MetricCard icon="💼" label="Freelance" value={byType.freelance || 0} color="#f59e0b" />
        <MetricCard icon="🎁" label="Grants" value={byType.grant || 0} color="#22c55e" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <h2 className="text-sm font-semibold mb-4" style={{ color: 'var(--text)' }}>Revenue Potential (Estimated)</h2>
          <div className="space-y-3">
            {opps.slice(0, 5).map((o, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="flex-1">
                  <p className="text-xs text-gray-300">{o.title}</p>
                  <div className="mt-1 h-1.5 rounded-full bg-gray-800 overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${Math.min(100, (i + 1) * 20)}%`,
                        background: 'linear-gradient(90deg, #7c3aed, #a78bfa)'
                      }}
                    />
                  </div>
                </div>
                <p className="text-xs font-bold shrink-0" style={{ color: '#22c55e' }}>{o.payout}</p>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <h2 className="text-sm font-semibold mb-4" style={{ color: 'var(--text)' }}>Pipeline by Category</h2>
          <div className="space-y-3">
            {Object.entries(byType).map(([type, count]) => (
              <div key={type} className="flex items-center gap-3">
                <span className="text-xs text-gray-400 w-24 capitalize">{type.replace('_', ' ')}</span>
                <div className="flex-1 h-2 rounded-full bg-gray-800 overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${(count / opps.length) * 100}%`,
                      background: '#7c3aed'
                    }}
                  />
                </div>
                <span className="text-xs font-bold" style={{ color: 'var(--accent)' }}>{count}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card className="mt-6">
        <h2 className="text-sm font-semibold mb-4" style={{ color: 'var(--text)' }}>All Opportunities Ranked by Payout</h2>
        <div className="space-y-2">
          {opps.map((o, i) => (
            <div key={i} className="flex items-center justify-between gap-4 p-3 rounded-xl border" style={{ background: 'var(--surface2)', borderColor: 'var(--border)' }}>
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <span className="text-xs text-gray-600 w-4 shrink-0">{i + 1}</span>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-gray-200 truncate">{o.title}</p>
                  <div className="flex gap-1 mt-0.5">
                    <Badge label={o.type?.replace('_', ' ')} type="purple" />
                    <Badge label={o.effort} type={o.effort === 'low' ? 'green' : o.effort === 'medium' ? 'yellow' : 'red'} />
                  </div>
                </div>
              </div>
              <p className="text-sm font-bold shrink-0" style={{ color: '#22c55e' }}>{o.payout}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
