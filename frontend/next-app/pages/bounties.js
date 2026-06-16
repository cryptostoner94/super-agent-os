import { useState } from 'react'
import useSWR from 'swr'
import { get, post } from '../lib/api'
import { Card, PageHeader, Badge, EmptyState } from '../components/Card'

const EFFORT_COLOR = { low: 'green', medium: 'yellow', high: 'red' }
const TYPE_COLOR = { bug_bounty: 'red', bounty: 'purple', hackathon: 'blue', grant: 'green', freelance: 'yellow' }

export default function BountiesPage() {
  const { data: rewards } = useSWR('/rewards', get, { refreshInterval: 30000 })
  const { data: platforms } = useSWR('/bounty-platforms', get, { refreshInterval: 30000 })
  const [filter, setFilter] = useState('all')
  const [planProgram, setPlanProgram] = useState('')
  const [planScope, setPlanScope] = useState('')
  const [plan, setPlan] = useState(null)
  const [loading, setLoading] = useState(false)

  const opportunities = rewards?.opportunities || []
  const filtered = filter === 'all' ? opportunities : opportunities.filter(o => o.type === filter)

  async function createPlan(e) {
    e.preventDefault()
    if (!planProgram.trim()) return
    setLoading(true)
    try {
      const r = await post('/bounty/plan', { program: planProgram, scope: planScope })
      setPlan(r)
    } catch (err) {
      setPlan({ error: err.message })
    } finally {
      setLoading(false)
    }
  }

  const platformList = platforms?.platforms || []

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <PageHeader title="🎯 Bounties & Opportunities" subtitle={`${opportunities.length} active opportunities`} />

      {/* Platform status */}
      {platformList.length > 0 && (
        <Card className="mb-6">
          <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--text)' }}>Platform Connectors</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
            {platformList.map(p => (
              <div key={p.id} className="p-3 rounded-xl border text-center" style={{ background: 'var(--surface2)', borderColor: 'var(--border)' }}>
                <p className="text-xs font-semibold text-gray-300 mb-1">{p.name}</p>
                <Badge label={p.mode?.replace('_', ' ')} type={p.has_credentials ? 'green' : 'yellow'} />
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* OWASP Bounty Planner */}
      <Card className="mb-6">
        <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--text)' }}>🗂 Create Bounty Hunt Plan (OWASP Checklist)</h2>
        <form onSubmit={createPlan} className="flex gap-2 mb-3">
          <input
            value={planProgram}
            onChange={e => setPlanProgram(e.target.value)}
            placeholder="Program name (e.g. Acme Corp on Bugcrowd)"
            className="flex-1 rounded-lg px-3 py-2 text-sm border"
            style={{ background: 'var(--surface2)', borderColor: 'var(--border)', color: 'var(--text)' }}
          />
          <input
            value={planScope}
            onChange={e => setPlanScope(e.target.value)}
            placeholder="Scope (e.g. *.example.com)"
            className="w-48 rounded-lg px-3 py-2 text-sm border"
            style={{ background: 'var(--surface2)', borderColor: 'var(--border)', color: 'var(--text)' }}
          />
          <button
            type="submit"
            disabled={loading || !planProgram.trim()}
            className="px-4 py-2 rounded-lg text-sm font-semibold disabled:opacity-50 shrink-0"
            style={{ background: 'var(--accent-dark)', color: '#fff' }}
          >
            {loading ? '…' : '+ Plan'}
          </button>
        </form>
        {plan && !plan.error && (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-1.5 mt-3">
            {plan.checks?.map(c => (
              <div key={c.id} className="flex items-center gap-2 p-2 rounded-lg text-xs" style={{ background: 'var(--surface2)' }}>
                <span>{c.status === 'pending' ? '⬜' : '✅'}</span>
                <span className="text-gray-400">{c.name}</span>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Opportunities list */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>Live Opportunities</h2>
          <div className="flex gap-1">
            {['all', 'bug_bounty', 'bounty', 'hackathon', 'grant', 'freelance'].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${filter === f ? 'text-white' : 'text-gray-500 hover:text-gray-300'}`}
                style={filter === f ? { background: 'var(--accent-dark)' } : {}}
              >
                {f.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>
        {filtered.length === 0 ? (
          <EmptyState icon="🎯" title="No opportunities found" />
        ) : (
          <div className="space-y-2">
            {filtered.map((r, i) => (
              <div key={i} className="flex items-start justify-between gap-3 p-4 rounded-xl border" style={{ background: 'var(--surface2)', borderColor: 'var(--border)' }}>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge label={r.type?.replace('_', ' ')} type={TYPE_COLOR[r.type] || 'gray'} />
                    <Badge label={r.effort} type={EFFORT_COLOR[r.effort] || 'gray'} />
                  </div>
                  <p className="text-sm font-medium text-gray-200">{r.title}</p>
                  <p className="text-xs text-gray-500 mt-1">{r.description}</p>
                </div>
                <div className="shrink-0 text-right">
                  <p className="text-sm font-bold" style={{ color: '#22c55e' }}>{r.payout}</p>
                  <a href={r.url?.startsWith('https://') ? r.url : '#'} target="_blank" rel="noopener noreferrer" className="text-xs mt-1 block" style={{ color: 'var(--accent)' }}>→ View</a>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
