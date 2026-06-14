import { useState, useEffect } from 'react'
import useSWR from 'swr'
import { get, post } from '../lib/api'
import { Card, PageHeader, Badge } from '../components/Card'

export default function SettingsPage() {
  const { data: settings, mutate } = useSWR('/settings', get)
  const { data: startup } = useSWR('/startup', get, { refreshInterval: 30000 })
  const [local, setLocal] = useState({})
  const [saved, setSaved] = useState(false)

  useEffect(() => { if (settings) setLocal(settings) }, [settings])

  async function save() {
    try {
      await post('/settings', local)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
      mutate()
    } catch (_err) {
      // save failure is non-fatal; user can retry
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <PageHeader title="⚙️ Settings" subtitle="System configuration and diagnostics" />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <h2 className="text-sm font-semibold mb-4" style={{ color: 'var(--text)' }}>Configuration</h2>
          {Object.entries(local).map(([k, v]) => (
            <div key={k} className="mb-3">
              <label className="text-xs text-gray-500 uppercase tracking-wider block mb-1">{k.replace(/_/g, ' ')}</label>
              {typeof v === 'boolean' ? (
                <button
                  onClick={() => setLocal(p => ({ ...p, [k]: !p[k] }))}
                  className={`px-3 py-1 rounded-lg text-xs font-medium ${v ? 'bg-green-900 text-green-400' : 'bg-gray-800 text-gray-400'}`}
                >
                  {v ? 'Enabled' : 'Disabled'}
                </button>
              ) : (
                <input
                  value={v == null ? '' : String(v)}
                  onChange={e => {
                    const val = e.target.value
                    setLocal(p => ({ ...p, [k]: isNaN(Number(val)) ? val : Number(val) }))
                  }}
                  className="w-full rounded-lg px-3 py-1.5 text-sm border"
                  style={{ background: 'var(--surface2)', borderColor: 'var(--border)', color: 'var(--text)' }}
                />
              )}
            </div>
          ))}
          <button
            onClick={save}
            className="mt-3 px-4 py-2 rounded-lg text-sm font-semibold"
            style={{ background: 'var(--accent-dark)', color: '#fff' }}
          >
            {saved ? '✓ Saved' : 'Save Settings'}
          </button>
        </Card>

        <Card>
          <h2 className="text-sm font-semibold mb-4" style={{ color: 'var(--text)' }}>System Diagnostics</h2>
          {startup && (
            <div className="space-y-2">
              {Object.entries(startup).filter(([k]) => k !== '_summary').map(([k, v]) => {
                const isObj = v !== null && typeof v === 'object'
                const isOk = isObj && v.ok
                const isDegraded = isObj && !v.ok && v.degraded
                return (
                  <div key={k} className="flex items-center justify-between p-2 rounded-lg" style={{ background: 'var(--surface2)' }}>
                    <span className="text-xs text-gray-400 capitalize">{k.replace(/_/g, ' ')}</span>
                    <Badge
                      label={isOk ? 'ok' : isDegraded ? 'degraded' : 'err'}
                      type={isOk ? 'green' : isDegraded ? 'yellow' : 'red'}
                    />
                  </div>
                )
              })}
              {startup._summary && (
                <p className="text-xs text-gray-500 mt-2">
                  {startup._summary.ok}/{startup._summary.total} checks passing
                </p>
              )}
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
