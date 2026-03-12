import { useState, useEffect } from 'react'

const API_BASE_URL = 'http://localhost:8000'

function App() {
  const [payments, setPayments] = useState([])
  const [providerHealth, setProviderHealth] = useState([])
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    amount: 100,
    currency: 'USD',
    merchant_id: 'default_merchant',
    customer_id: 'cust_123',
    payment_method: {
      type: 'credit_card',
      bin: '400022',
      brand: 'Visa'
    }
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

  const fetchHealth = async () => {
    try {
      const resp = await fetch(`${API_BASE_URL}/api/v1/payments/providers/health`)
      const data = await resp.json()
      setProviderHealth(data)
    } catch (err) {
      console.error(err)
    }
  }

  useEffect(() => {
    fetchPayments()
    fetchHealth()
    const interval = setInterval(fetchHealth, 10000) // Poll every 10s
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 p-8 font-sans selection:bg-blue-500/30">
      {/* Background Decor */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/10 rounded-full blur-[120px]"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-emerald-600/10 rounded-full blur-[120px]"></div>
      </div>

      <header className="max-w-6xl mx-auto mb-12 flex flex-col md:flex-row justify-between items-start md:items-center gap-6 relative z-10">
        <div>
          <h1 className="text-4xl font-black bg-gradient-to-r from-blue-400 via-indigo-400 to-emerald-400 bg-clip-text text-transparent tracking-tight">
            Antigravity Payments
          </h1>
          <p className="text-slate-400 font-medium mt-1">Intelligent Multi-Processor Core</p>
        </div>

        <div className="flex flex-wrap gap-3">
          {providerHealth.map(p => (
            <div key={p.provider} className="px-3 py-1.5 bg-slate-900/80 border border-slate-800 rounded-xl flex items-center gap-2.5 backdrop-blur-md shadow-xl shadow-black/20">
              <span className={`w-2 h-2 rounded-full shadow-[0_0_8px] ${p.status === 'up' ? 'bg-emerald-400 shadow-emerald-400/50' : 'bg-red-400 shadow-red-400/50 blink'}`}></span>
              <span className="text-[10px] uppercase tracking-widest font-bold text-slate-300">{p.provider}</span>
              <span className="text-[10px] text-slate-500 font-mono">{p.latency_ms}ms</span>
            </div>
          ))}
        </div>
      </header>

      <main className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 relative z-10">
        {/* Payment Simulator */}
        <section className="lg:col-span-4 bg-slate-900/40 border border-slate-800/50 p-8 rounded-[2rem] backdrop-blur-xl self-start shadow-2xl shadow-black/40">
          <h2 className="text-xl font-bold mb-8 flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-500/10 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            Terminal
          </h2>

          <form onSubmit={handleCharge} className="space-y-6">
            <div>
              <label className="block text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-2 font-black">Transaction Amount</label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 font-bold">$</span>
                <input
                  type="number"
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: parseFloat(e.target.value) })}
                  className="w-full bg-slate-950/50 border border-slate-800 rounded-2xl pl-10 pr-4 py-4 text-xl font-bold focus:outline-none focus:border-blue-500/50 focus:ring-4 focus:ring-blue-500/10 transition-all"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-2 font-black">Currency</label>
                <select
                  value={formData.currency}
                  onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                  className="w-full bg-slate-950/50 border border-slate-800 rounded-2xl px-4 py-4 focus:outline-none focus:border-blue-500/50 transition-all appearance-none font-bold"
                >
                  <option>USD</option>
                  <option>EUR</option>
                  <option>GBP</option>
                </select>
              </div>
              <div>
                <label className="block text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-2 font-black">Context</label>
                <div className="w-full bg-slate-950/50 border border-slate-800 rounded-2xl px-4 py-4 text-slate-400 font-bold text-sm">
                  Visa Debit
                </div>
              </div>
            </div>

            <button
              disabled={loading}
              className="w-full bg-gradient-to-br from-blue-500 to-indigo-600 hover:from-blue-400 hover:to-indigo-500 text-white font-black py-4 rounded-2xl transition-all shadow-xl shadow-blue-500/20 active:scale-[0.98] disabled:opacity-50 text-lg tracking-tight"
            >
              {loading ? 'Analyzing Route...' : 'Execute Charge'}
            </button>
          </form>

          {result && (
            <div className="mt-8 p-6 bg-gradient-to-br from-emerald-500/10 to-teal-500/10 border border-emerald-500/20 rounded-[1.5rem] animate-in fade-in slide-in-from-top-4 duration-500">
              <div className="flex items-center justify-between mb-4">
                <div className="text-emerald-400 font-black text-[10px] uppercase tracking-[0.2em]">Route Optimized</div>
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse shadow-[0_0_8px_emerald_400]"></div>
              </div>
              <div className="text-3xl font-black mb-3 tracking-tighter text-white uppercase italic drop-shadow-sm">
                {result.provider}
              </div>
              <div className="space-y-3">
                <p className="text-xs text-slate-300 leading-relaxed font-bold border-l-2 border-emerald-500/30 pl-3 py-1">
                  {result.routing_decision || "Strategically routed via specialist agent consensus."}
                </p>
                <div className="flex gap-2">
                  <span className="text-[9px] bg-slate-950/50 text-slate-400 px-2 py-1 rounded-md border border-slate-800 font-mono">auth_rate: 0.99</span>
                  <span className="text-[9px] bg-slate-950/50 text-slate-400 px-2 py-1 rounded-md border border-slate-800 font-mono">lat: 142ms</span>
                </div>
              </div>
            </div>
          )}
        </section>

        {/* Transaction History */}
        <section className="lg:col-span-8 space-y-6">
          <div className="flex justify-between items-center mb-4 px-4">
            <h2 className="text-2xl font-black tracking-tight">Ledger</h2>
            <div className="flex gap-4">
              <button onClick={fetchPayments} className="text-[10px] font-black uppercase tracking-widest text-blue-400 hover:text-blue-300 transition-colors">Force Sync</button>
            </div>
          </div>

          <div className="space-y-4">
            {payments.length === 0 ? (
              <div className="bg-slate-900/20 border-2 border-dashed border-slate-800/50 p-20 rounded-[2rem] text-center">
                <div className="text-slate-600 font-black text-lg uppercase tracking-widest">Awaiting Transactions</div>
              </div>
            ) : (
              payments.map((p) => (
                <div key={p.id} className="group bg-slate-900/30 border border-slate-800/50 p-6 rounded-[1.5rem] flex items-center justify-between hover:bg-slate-900/50 hover:border-blue-500/30 transition-all duration-300">
                  <div className="flex items-center gap-6">
                    <div className="w-14 h-14 bg-slate-950 border border-slate-800 rounded-2xl flex items-center justify-center text-2xl group-hover:scale-110 transition-transform duration-500">
                      {p.currency === 'USD' ? '🇺🇸' : '🇪🇺'}
                    </div>
                    <div>
                      <div className="font-black text-2xl tracking-tighter flex items-center gap-3">
                        {p.amount.toFixed(2)} <span className="text-xs text-slate-500 font-mono">{p.currency}</span>
                      </div>
                      <div className="text-[10px] text-slate-500 flex items-center gap-2 font-bold uppercase tracking-widest mt-1">
                        <span className="text-slate-400 font-mono italic normal-case tracking-normal">{p.id.substring(0, 8)}</span>
                        <span className="w-1 h-1 bg-slate-700 rounded-full"></span>
                        <span className="text-blue-400 font-black">{p.provider}</span>
                        {p.provider === 'braintree' && <span className="px-1.5 py-0.5 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded text-[8px]">SDK</span>}
                        {p.provider === 'paypal' && <span className="px-1.5 py-0.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded text-[8px]">REST</span>}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-[10px] font-black uppercase tracking-[0.1em] px-3 py-1.5 rounded-xl mb-2 inline-block shadow-sm ${p.status === 'success' || !p.status ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20' : 'bg-orange-500/10 text-orange-500 border border-orange-500/20'}`}>
                      {p.status || 'captured'}
                    </div>
                    <div className="text-[10px] text-slate-600 font-black block tracking-tight uppercase">
                      {new Date(p.created_at || Date.now()).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </main>

      {/* Global CSS for animations */}
      <style dangerouslySetInnerHTML={{
        __html: `
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
        .blink { animation: blink 1.5s ease-in-out infinite; }
      `}} />
    </div>
  )
}

export default App
