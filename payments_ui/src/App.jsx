import { useState, useEffect } from 'react'

const API_BASE_URL = 'http://localhost:8000'

function App() {
  const [payments, setPayments] = useState([])
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    amount: 100,
    currency: 'USD',
    merchant_id: 'default_merchant',
    customer_id: 'cust_123'
  })
  const [result, setResult] = useState(null)

  const handleCharge = async (e) => {
    e.preventDefault()
    setLoading(true)
    setResult(null)
    try {
      const resp = await fetch(`${API_BASE_URL}/api/v1/payments/charge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })
      const data = await resp.json()
      setResult(data)
      // Refresh list
      fetchPayments()
    } catch (err) {
      console.error(err)
      alert('Failed to process payment')
    } finally {
      setLoading(false)
    }
  }

  const fetchPayments = async () => {
    try {
      const resp = await fetch(`${API_BASE_URL}/api/v1/payments/recent`)
      const data = await resp.json()
      setPayments(data)
    } catch (err) {
      console.error(err)
    }
  }

  useEffect(() => {
    fetchPayments()
  }, [])

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 p-8 font-sans">
      <header className="max-w-6xl mx-auto mb-12 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
            Agentic Payments
          </h1>
          <p className="text-slate-400">Intelligent Routing Dashboard</p>
        </div>
        <div className="flex gap-4">
          <span className="px-3 py-1 bg-slate-900 border border-slate-800 rounded-full text-xs text-emerald-400 flex items-center gap-2">
            <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></span>
            Backend Online
          </span>
        </div>
      </header>

      <main className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Payment Simulator */}
        <section className="lg:col-span-1 bg-slate-900/50 border border-slate-800 p-6 rounded-2xl backdrop-blur-sm self-start">
          <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
            <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Simulate Payment
          </h2>

          <form onSubmit={handleCharge} className="space-y-4">
            <div>
              <label className="block text-xs uppercase tracking-wider text-slate-500 mb-1 font-semibold">Amount</label>
              <input
                type="number"
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: parseFloat(e.target.value) })}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:border-blue-500 transition-colors"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs uppercase tracking-wider text-slate-500 mb-1 font-semibold">Currency</label>
                <select
                  value={formData.currency}
                  onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:border-blue-500 transition-colors appearance-none"
                >
                  <option>USD</option>
                  <option>EUR</option>
                  <option>GBP</option>
                </select>
              </div>
              <div>
                <label className="block text-xs uppercase tracking-wider text-slate-500 mb-1 font-semibold">Customer</label>
                <input
                  type="text"
                  value={formData.customer_id}
                  onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:border-blue-500 transition-colors"
                />
              </div>
            </div>
            <button
              disabled={loading}
              className="w-full bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white font-bold py-3 rounded-xl transition-all shadow-lg shadow-blue-900/20 active:scale-[0.98] disabled:opacity-50"
            >
              {loading ? 'Processing...' : 'Charge Now'}
            </button>
          </form>

          {result && (
            <div className="mt-8 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl animate-in fade-in slide-in-from-top-2">
              <div className="text-emerald-400 font-bold text-sm mb-1 uppercase tracking-tight">Decision Reached</div>
              <div className="text-2xl font-black mb-2 uppercase italic">{result.provider}</div>
              <p className="text-xs text-slate-400 leading-relaxed font-medium">
                {result.routing_decision || "Routed via Planner analysis of cost and performance metrics."}
              </p>
            </div>
          )}
        </section>

        {/* Transaction History */}
        <section className="lg:col-span-2 space-y-4">
          <div className="flex justify-between items-end mb-2 px-2">
            <h2 className="text-xl font-semibold">Recent Transactions</h2>
            <button onClick={fetchPayments} className="text-xs text-blue-400 hover:underline">Refresh List</button>
          </div>

          <div className="space-y-3">
            {payments.length === 0 ? (
              <div className="bg-slate-900/30 border border-dashed border-slate-800 p-12 rounded-2xl text-center text-slate-500">
                No recent transactions found.
              </div>
            ) : (
              payments.map((p) => (
                <div key={p.id} className="group bg-slate-900/50 border border-slate-800 p-5 rounded-2xl flex items-center justify-between hover:border-slate-700 transition-colors">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-slate-950 border border-slate-800 rounded-full flex items-center justify-center font-bold text-slate-400">
                      {p.currency === 'USD' ? '$' : '€'}
                    </div>
                    <div>
                      <div className="font-bold flex items-center gap-2 text-lg">
                        {p.amount.toFixed(2)} <span className="text-xs text-slate-500 uppercase">{p.currency}</span>
                      </div>
                      <div className="text-xs text-slate-500 flex items-center gap-1 font-medium">
                        ID: <span className="text-slate-400 font-mono italic">{p.id.substring(0, 8)}</span>
                        • Via <span className="text-blue-400 font-bold uppercase">{p.provider}</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-xs font-bold px-2 py-1 rounded-md mb-1 inline-block ${p.status === 'success' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-orange-500/10 text-orange-500'}`}>
                      {p.status || 'success'}
                    </div>
                    <div className="text-[10px] text-slate-600 block">
                      {new Date(p.created_at || Date.now()).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </main>
    </div>
  )
}

export default App
