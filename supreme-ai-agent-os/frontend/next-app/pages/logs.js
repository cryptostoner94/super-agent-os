import useSWR from 'swr'
import { get } from '../lib/api'
import { Card, PageHeader, Badge } from '../components/Card'

const KIND_COLOR = {
  task_start: 'blue', task_finish: 'green', agent_run: 'purple',
  inception_run: 'purple', startup: 'green', bounty_plan_created: 'yellow',
  artifact_created: 'blue', error: 'red',
}

export default function LogsPage() {
  const { data: events = [], mutate } = useSWR('/logs?limit=100', get, { refreshInterval: 5000 })

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <PageHeader
        title="📊 Event Logs"
        subtitle="Real-time system events from SQLite memory store"
        action={
          <button onClick={() => mutate()} className="text-xs px-3 py-1.5 rounded-lg" style={{ background: 'var(--surface2)', color: 'var(--accent)' }}>
            ↻ Refresh
          </button>
        }
      />
      <Card>
        <div className="space-y-1 max-h-[70vh] overflow-y-auto pr-1">
          {(!Array.isArray(events) || events.length === 0) && (
            <p className="text-sm text-gray-500 text-center py-8">No events yet. Run some tasks to see activity.</p>
          )}
          {(Array.isArray(events) ? events : []).map((e, i) => (
            <div key={i} className="flex items-start gap-3 p-2.5 rounded-lg hover:bg-white hover:bg-opacity-5 text-xs">
              <Badge label={e.kind} type={KIND_COLOR[e.kind] || 'gray'} />
              <span className="text-gray-600 shrink-0">{e.created ? new Date(e.created * 1000).toLocaleTimeString() : ''}</span>
              <span className="text-gray-400 truncate">
                {typeof e.payload === 'object' ? JSON.stringify(e.payload).slice(0, 120) : String(e.payload || '')}
              </span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
