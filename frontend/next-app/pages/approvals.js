import { Card, PageHeader, Badge, EmptyState } from '../components/Card'
import useSWR from 'swr'
import { get } from '../lib/api'

export default function ApprovalsPage() {
  const { data: tasks = [] } = useSWR('/tasks?limit=100', get, { refreshInterval: 5000 })
  const tList = Array.isArray(tasks) ? tasks : []
  const highRisk = tList.filter(t => t.prompt?.toLowerCase().includes('delete') || t.prompt?.toLowerCase().includes('transfer') || t.prompt?.toLowerCase().includes('payment'))

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <PageHeader title="✅ Approvals" subtitle="High-risk task approval queue" />
      <div className="mb-4 p-4 rounded-xl border border-yellow-800" style={{ background: 'rgba(251,191,36,0.05)' }}>
        <p className="text-yellow-400 text-sm font-medium">⚠ Approval Gate Active</p>
        <p className="text-yellow-700 text-xs mt-1">
          Tasks matching risk criteria (delete, transfer, payment, dangerous commands) require manual approval before execution.
          Threshold: ${process.env.NEXT_PUBLIC_WARDEN_THRESHOLD || '100'} credit equivalent.
        </p>
      </div>
      <Card>
        <h2 className="text-sm font-semibold mb-4" style={{ color: 'var(--text)' }}>Pending Approvals</h2>
        {highRisk.length === 0 ? (
          <EmptyState icon="✅" title="No pending approvals" subtitle="All tasks are within auto-approved risk thresholds." />
        ) : (
          <div className="space-y-2">
            {highRisk.map(t => (
              <div key={t.id} className="flex items-center gap-3 p-3 rounded-xl border" style={{ background: 'var(--surface2)', borderColor: 'var(--border)' }}>
                <Badge label="review" type="yellow" />
                <p className="text-sm text-gray-300 flex-1">{t.prompt?.slice(0, 100)}</p>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
