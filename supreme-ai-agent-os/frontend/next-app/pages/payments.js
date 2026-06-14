import { Card, PageHeader, Badge } from '../components/Card'

export default function PaymentsPage() {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <PageHeader title="💳 Payments" subtitle="Payment verification and payout tracking" />

      <div className="mb-6 p-4 rounded-xl border border-blue-800 bg-blue-900 bg-opacity-20">
        <p className="text-blue-400 text-sm font-medium">ℹ Payment System Status</p>
        <p className="text-blue-600 text-xs mt-1">
          Stripe integration ready. Set <code className="bg-black bg-opacity-30 px-1 rounded">STRIPE_SECRET_KEY</code> to enable live payments.
          Blockchain verification available via wallet address lookup.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <h2 className="text-sm font-semibold mb-4" style={{ color: 'var(--text)' }}>Payment Methods</h2>
          <div className="space-y-3">
            {[
              { name: 'Stripe', status: 'config_required', note: 'Set STRIPE_SECRET_KEY' },
              { name: 'USDC (on-chain)', status: 'available', note: 'Via wallet address' },
              { name: 'ETH/ERC20', status: 'available', note: 'Gitcoin, Immunefi payouts' },
              { name: 'Bank Transfer', status: 'platform_managed', note: 'Via platform (Intigriti, YWH)' },
            ].map((m, i) => (
              <div key={i} className="flex items-center justify-between p-3 rounded-xl border" style={{ background: 'var(--surface2)', borderColor: 'var(--border)' }}>
                <div>
                  <p className="text-sm font-medium text-gray-200">{m.name}</p>
                  <p className="text-xs text-gray-500">{m.note}</p>
                </div>
                <Badge
                  label={m.status.replace(/_/g, ' ')}
                  type={m.status === 'available' ? 'green' : m.status === 'config_required' ? 'yellow' : 'blue'}
                />
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <h2 className="text-sm font-semibold mb-4" style={{ color: 'var(--text)' }}>Recent Payouts</h2>
          <p className="text-sm text-gray-500 text-center py-8">
            No payouts recorded yet.<br />
            <span className="text-xs">Payouts appear here after bounty submissions are approved.</span>
          </p>
        </Card>
      </div>
    </div>
  )
}
