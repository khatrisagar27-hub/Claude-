import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import apiClient from '../api/client';
import { useAuthStore } from '../store/authStore';
import SeverityBadge from '../components/common/SeverityBadge';
import type { FraudIndicator } from '../types';

const benfordExpected = [
  { digit: '1', expected: 30.1, observed: 0 },
  { digit: '2', expected: 17.6, observed: 0 },
  { digit: '3', expected: 12.5, observed: 0 },
  { digit: '4', expected: 9.7, observed: 0 },
  { digit: '5', expected: 7.9, observed: 0 },
  { digit: '6', expected: 6.7, observed: 0 },
  { digit: '7', expected: 5.8, observed: 0 },
  { digit: '8', expected: 5.1, observed: 0 },
  { digit: '9', expected: 4.6, observed: 0 },
];

export default function FraudAnalytics() {
  const { companyId } = useAuthStore();
  const [indicators, setIndicators] = useState<FraudIndicator[]>([]);
  const [loading, setLoading] = useState(true);
  const [population, setPopulation] = useState('sales');

  useEffect(() => {
    if (!companyId) { setLoading(false); return; }
    apiClient.get(`/risk/fraud-indicators?company_id=${companyId}`).then(r => setIndicators(r.data)).finally(() => setLoading(false));
  }, [companyId]);

  // observed first-digit shares come from the Benford indicators the fraud engine stored
  const benford = indicators.filter(i => i.indicator_type === 'benford_deviation' && i.details_json?.observed);
  const pick = benford.find(i => String(i.details_json?.population || '').startsWith(population)) || benford[0];
  const chart = benfordExpected.map((d, k) => ({
    ...d,
    observed: pick ? Math.round(pick.details_json!.observed[k] * 1000) / 10 : 0,
  }));
  const band = (score: number) => (score >= 60 ? 'critical' : score >= 40 ? 'high' : score >= 20 ? 'medium' : 'low');

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white">Fraud Analytics</h1>
        <p className="text-sm text-gray-500">Benford's Law, duplicate detection, behavioral anomaly</p>
      </div>

      {/* Benford's chart */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
            Benford's Law Analysis — Leading Digit Distribution
          </h2>
          {benford.length > 1 && (
            <select aria-label="Benford population" value={population} onChange={e => setPopulation(e.target.value)}
              className="bg-navy-700 border border-navy-border text-xs text-gray-300 rounded px-2 py-1">
              {benford.map(b => {
                const p = String(b.details_json?.population || '').split(' ')[0];
                return <option key={b.id} value={p}>{b.details_json?.population}</option>;
              })}
            </select>
          )}
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={chart} barSize={20} barGap={4}>
            <XAxis dataKey="digit" stroke="#4B5563" tick={{ fill: '#9CA3AF', fontSize: 12 }} label={{ value: 'Leading Digit', fill: '#6B7280', fontSize: 11, position: 'insideBottom', offset: -5 }} />
            <YAxis stroke="#4B5563" tick={{ fill: '#6B7280', fontSize: 11 }} unit="%" />
            <Tooltip contentStyle={{ background: '#161B22', border: '1px solid #30363D' }} labelStyle={{ color: '#E5E7EB' }} />
            <Bar dataKey="expected" name="Benford Expected" fill="#C8A951" opacity={0.6} />
            <Bar dataKey="observed" name="Observed" fill="#3B82F6" />
          </BarChart>
        </ResponsiveContainer>
        <p className="text-xs text-gray-500 mt-2 text-center">
          {pick ? `${pick.details_json?.population}: n = ${pick.details_json?.n}, MAD ${Number(pick.details_json?.mad).toFixed(4)} — ${pick.details_json?.conformity} (Nigrini bands)`
            : 'Observed data will populate after an audit cycle runs'}
        </p>
      </div>

      {/* Fraud Indicators */}
      <div className="card p-0 overflow-hidden">
        <div className="px-4 py-3 border-b border-navy-border">
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Fraud Indicators</h2>
        </div>
        {loading ? (
          <div className="text-center py-12 text-gray-500">Loading…</div>
        ) : indicators.length === 0 ? (
          <div className="text-center py-12 text-gray-600">No fraud indicators detected yet.</div>
        ) : (
          <table className="w-full">
            <thead>
              <tr>
                {['Type', 'Description', 'Score', 'Exposure', 'Analysed'].map(h => (
                  <th key={h} className="table-header text-left">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {indicators.map(ind => (
                <tr key={ind.id} className="table-row">
                  <td className="table-cell font-mono text-xs text-gray-400">{ind.indicator_type.replace(/_/g, ' ')}</td>
                  <td className="table-cell text-gray-300 max-w-md">
                    <p className="text-sm">{ind.description}</p>
                  </td>
                  <td className="table-cell whitespace-nowrap">
                    <SeverityBadge severity={band(ind.score)} /> <span className="text-xs text-gray-500 ml-1">{ind.score.toFixed(1)}</span>
                  </td>
                  <td className="table-cell text-gray-400 text-xs">
                    {ind.financial_exposure ? `₹${Math.round(ind.financial_exposure).toLocaleString('en-IN')}` : `${ind.affected_transactions} txns`}
                  </td>
                  <td className="table-cell text-gray-500 text-xs">
                    {new Date(ind.analysis_date).toLocaleDateString('en-IN')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
