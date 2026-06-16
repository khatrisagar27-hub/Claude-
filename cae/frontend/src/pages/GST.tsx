import { useEffect, useState } from 'react';
import apiClient from '../api/client';
import { useAuthStore } from '../store/authStore';
import AmountDisplay from '../components/common/AmountDisplay';
import type { GSTRecon } from '../types';

export default function GST() {
  const { companyId } = useAuthStore();
  const [recons, setRecons] = useState<GSTRecon[]>([]);
  const [itcRisk, setItcRisk] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!companyId) return;
    Promise.all([
      apiClient.get(`/gst/reconciliation?company_id=${companyId}`),
      apiClient.get(`/gst/itc-risk?company_id=${companyId}`),
    ]).then(([r, risk]) => {
      setRecons(r.data);
      setItcRisk(risk.data);
    }).finally(() => setLoading(false));
  }, [companyId]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white">GST Reconciliation</h1>
        <p className="text-sm text-gray-500">GSTR-1 / GSTR-3B / GSTR-2B vs Books</p>
      </div>

      {/* ITC Risk summary */}
      {itcRisk && (
        <div className="grid grid-cols-3 gap-4">
          <div className="card">
            <div className="text-xs text-gray-500 uppercase tracking-wider">Total ITC Risk</div>
            <div className="text-2xl font-bold text-red-400 mt-1">
              <AmountDisplay amount={itcRisk.total_itc_risk} className="text-red-400" />
            </div>
          </div>
          <div className="card">
            <div className="text-xs text-gray-500 uppercase tracking-wider">Periods at Risk</div>
            <div className="text-2xl font-bold text-white mt-1">{itcRisk.periods_at_risk}</div>
          </div>
          <div className="card">
            <div className="text-xs text-gray-500 uppercase tracking-wider">Total Periods Reconciled</div>
            <div className="text-2xl font-bold text-white mt-1">{recons.length}</div>
          </div>
        </div>
      )}

      <div className="card p-0 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr>
              {['Period', 'Books Turnover', 'GSTR-1 Turnover', 'Variance', 'Books ITC', 'GSTR-2B ITC', 'ITC Variance', 'Risk Amount', 'Status'].map(h => (
                <th key={h} className="table-header text-left">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={9} className="text-center py-12 text-gray-500">Loading…</td></tr>
            ) : recons.length === 0 ? (
              <tr><td colSpan={9} className="text-center py-12 text-gray-600">No GST reconciliation data. Upload GSTR-2B JSON to reconcile.</td></tr>
            ) : recons.map(r => (
              <tr key={r.id} className="table-row">
                <td className="table-cell font-mono text-gold">{r.period}</td>
                <td className="table-cell"><AmountDisplay amount={r.books_turnover} /></td>
                <td className="table-cell"><AmountDisplay amount={r.gstr1_turnover} /></td>
                <td className={`table-cell ${(r.variance_turnover || 0) > 100000 ? 'text-red-400' : 'text-gray-400'}`}>
                  <AmountDisplay amount={r.variance_turnover} />
                </td>
                <td className="table-cell"><AmountDisplay amount={r.books_itc} /></td>
                <td className="table-cell"><AmountDisplay amount={r.gstr2b_itc} /></td>
                <td className={`table-cell ${(r.variance_itc || 0) > 50000 ? 'text-red-400' : 'text-gray-400'}`}>
                  <AmountDisplay amount={r.variance_itc} />
                </td>
                <td className="table-cell text-red-400 font-semibold"><AmountDisplay amount={r.risk_amount} /></td>
                <td className="table-cell">
                  <span className="text-xs text-green-400 capitalize">{r.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
