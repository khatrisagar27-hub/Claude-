import { useEffect, useState } from 'react';
import { Clock, RefreshCw } from 'lucide-react';
import apiClient from '../api/client';
import { useAuthStore } from '../store/authStore';
import AmountDisplay from '../components/common/AmountDisplay';

interface OverdueInvoice {
  invoice_number: string;
  customer: string;
  due_date: string | null;
  days_overdue: number | null;
  outstanding: number;
}

interface WCMetrics {
  dso: number;
  dpo: number;
  dio: number;
  ccc: number;
  stress_score: number;
  stress_components?: Record<string, number>;
  dio_basis?: string;
  receivables_total: number;
  receivables_overdue: number;
  payables_total: number;
  payables_overdue: number;
  inventory_value: number;
  receivables_aging: {
    current: number;
    d0_30: number;
    d31_60: number;
    d61_90: number;
    d90_plus: number;
  };
  top_overdue_receivables: OverdueInvoice[];
  as_of: string;
}

const AGING_BUCKETS: { key: keyof WCMetrics['receivables_aging']; label: string; color: string }[] = [
  { key: 'current', label: 'Current', color: 'bg-green-500' },
  { key: 'd0_30', label: '0–30 days', color: 'bg-yellow-500' },
  { key: 'd31_60', label: '31–60 days', color: 'bg-orange-500' },
  { key: 'd61_90', label: '61–90 days', color: 'bg-red-500' },
  { key: 'd90_plus', label: '90+ days', color: 'bg-red-700' },
];

export default function WorkingCapital() {
  const { companyId } = useAuthStore();
  const [metrics, setMetrics] = useState<WCMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    if (!companyId) return;
    setLoading(true);
    setError(null);
    apiClient
      .get(`/working-capital/metrics?company_id=${companyId}`)
      .then((res) => setMetrics(res.data))
      .catch((e) => setError(e?.response?.data?.detail || 'Failed to load working capital metrics'))
      .finally(() => setLoading(false));
  };

  useEffect(load, [companyId]);

  const stressColor = (score: number) => {
    if (score >= 70) return 'text-red-400';
    if (score >= 40) return 'text-yellow-400';
    return 'text-green-400';
  };

  const agingTotal = metrics
    ? AGING_BUCKETS.reduce((sum, b) => sum + (metrics.receivables_aging[b.key] || 0), 0)
    : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Working Capital Intelligence</h1>
          <p className="text-sm text-gray-500">
            DSO / DPO / DIO / CCC, receivables aging and stress score
            {metrics?.as_of && <span className="ml-2 text-gray-600">· as of {metrics.as_of}</span>}
          </p>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="flex items-center gap-2 text-xs text-gray-400 hover:text-gold border border-gray-700 rounded px-3 py-1.5 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="card text-center py-12 text-gray-500">Computing working capital metrics…</div>
      ) : error ? (
        <div className="card text-center py-12">
          <Clock className="w-12 h-12 text-gray-700 mx-auto mb-4" />
          <p className="text-red-400">{error}</p>
        </div>
      ) : !metrics ? (
        <div className="card text-center py-12 text-gray-500">No company selected.</div>
      ) : (
        <>
          {/* Cycle metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="card">
              <div className="text-xs text-gray-500 uppercase">DSO (days)</div>
              <div className="text-3xl font-bold font-mono text-white mt-1">{metrics.dso}</div>
              <div className="text-xs text-gray-600 mt-0.5">Days Sales Outstanding</div>
            </div>
            <div className="card">
              <div className="text-xs text-gray-500 uppercase">DPO (days)</div>
              <div className="text-3xl font-bold font-mono text-white mt-1">{metrics.dpo}</div>
              <div className="text-xs text-gray-600 mt-0.5">Days Payable Outstanding</div>
            </div>
            <div className="card">
              <div className="text-xs text-gray-500 uppercase">DIO (days)</div>
              <div className="text-3xl font-bold font-mono text-white mt-1">{metrics.dio}</div>
              <div className="text-xs text-gray-600 mt-0.5">Days Inventory Outstanding{metrics.dio_basis ? ` · on ${metrics.dio_basis}` : ''}</div>
            </div>
            <div className="card">
              <div className="text-xs text-gray-500 uppercase">CCC (days)</div>
              <div className={`text-3xl font-bold font-mono mt-1 ${metrics.ccc > 90 ? 'text-red-400' : 'text-white'}`}>
                {metrics.ccc}
              </div>
              <div className="text-xs text-gray-600 mt-0.5">Cash Conversion Cycle</div>
            </div>
          </div>

          {/* Balances + stress */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="card">
              <div className="text-xs text-gray-500 uppercase">Total Receivables</div>
              <AmountDisplay amount={metrics.receivables_total} className="text-xl font-bold text-white block mt-1" />
              <div className="text-xs text-red-400 mt-0.5">
                Overdue: <AmountDisplay amount={metrics.receivables_overdue} className="text-red-400" />
              </div>
            </div>
            <div className="card">
              <div className="text-xs text-gray-500 uppercase">Total Payables</div>
              <AmountDisplay amount={metrics.payables_total} className="text-xl font-bold text-white block mt-1" />
              <div className="text-xs text-yellow-400 mt-0.5">
                Overdue: <AmountDisplay amount={metrics.payables_overdue} className="text-yellow-400" />
              </div>
            </div>
            <div className="card">
              <div className="text-xs text-gray-500 uppercase">Inventory Value</div>
              <AmountDisplay amount={metrics.inventory_value} className="text-xl font-bold text-white block mt-1" />
            </div>
            <div className="card">
              <div className="text-xs text-gray-500 uppercase mb-1">WC Stress Score</div>
              <div className={`text-4xl font-bold font-mono ${stressColor(metrics.stress_score)}`}>
                {metrics.stress_score?.toFixed(0)}
              </div>
              <div className="text-xs text-gray-600 mt-0.5">0=Healthy, 100=Critical</div>
              {metrics.stress_components && (
                <dl className="mt-2 space-y-0.5 text-[11px] text-gray-500">
                  {Object.entries({
                    receivables_90_plus: 'Receivables 90+ days (30%)', receivables_overdue: 'Receivables overdue (20%)',
                    dso_vs_180: 'DSO vs 180 days (20%)', payables_overdue: 'Payables overdue (15%)', ccc_vs_180: 'CCC vs 180 days (15%)',
                  }).map(([k, label]) => (
                    <div key={k} className="flex justify-between gap-2"><dt>{label}</dt><dd className="text-gray-300">{metrics.stress_components![k]}%</dd></div>
                  ))}
                </dl>
              )}
            </div>
          </div>

          {/* Receivables aging */}
          <div className="card">
            <div className="text-sm font-semibold text-white mb-3">Receivables Aging</div>
            {agingTotal > 0 ? (
              <>
                <div className="flex h-4 w-full rounded overflow-hidden mb-4">
                  {AGING_BUCKETS.map((b) => {
                    const val = metrics.receivables_aging[b.key] || 0;
                    const pct = (val / agingTotal) * 100;
                    if (pct <= 0) return null;
                    return <div key={b.key} className={b.color} style={{ width: `${pct}%` }} title={`${b.label}: ${pct.toFixed(1)}%`} />;
                  })}
                </div>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                  {AGING_BUCKETS.map((b) => {
                    const val = metrics.receivables_aging[b.key] || 0;
                    const pct = (val / agingTotal) * 100;
                    return (
                      <div key={b.key}>
                        <div className="flex items-center gap-1.5 text-xs text-gray-400">
                          <span className={`w-2.5 h-2.5 rounded-sm ${b.color}`} />
                          {b.label}
                        </div>
                        <AmountDisplay amount={val} className="text-sm font-semibold text-white block mt-0.5" />
                        <div className="text-xs text-gray-600">{pct.toFixed(1)}%</div>
                      </div>
                    );
                  })}
                </div>
              </>
            ) : (
              <p className="text-gray-600 text-sm">No outstanding receivables.</p>
            )}
          </div>

          {/* Top overdue receivables */}
          <div className="card p-0 overflow-hidden">
            <div className="text-sm font-semibold text-white px-4 pt-4 pb-2">Top Overdue Receivables</div>
            <table className="w-full">
              <thead>
                <tr>
                  {['Invoice', 'Customer', 'Due Date', 'Days Overdue', 'Outstanding'].map((h) => (
                    <th key={h} className="table-header text-left">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {metrics.top_overdue_receivables.length === 0 ? (
                  <tr><td colSpan={5} className="text-center py-8 text-gray-600">No overdue receivables. 🎉</td></tr>
                ) : metrics.top_overdue_receivables.map((inv, i) => (
                  <tr key={`${inv.invoice_number}-${i}`} className="table-row">
                    <td className="table-cell font-mono text-gold">{inv.invoice_number}</td>
                    <td className="table-cell">{inv.customer}</td>
                    <td className="table-cell text-gray-400">{inv.due_date || '—'}</td>
                    <td className={`table-cell font-mono ${(inv.days_overdue || 0) > 90 ? 'text-red-400' : 'text-yellow-400'}`}>
                      {inv.days_overdue != null ? `${inv.days_overdue}d` : '—'}
                    </td>
                    <td className="table-cell font-semibold"><AmountDisplay amount={inv.outstanding} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
