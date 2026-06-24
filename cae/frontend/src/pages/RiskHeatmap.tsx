import { useEffect, useState } from 'react';
import apiClient from '../api/client';
import { useAuthStore } from '../store/authStore';

const bandColors: Record<string, string> = {
  critical: 'bg-red-900/60 border-red-700 text-red-300',
  high: 'bg-orange-900/60 border-orange-700 text-orange-300',
  moderate: 'bg-yellow-900/60 border-yellow-700 text-yellow-300',
  low: 'bg-green-900/60 border-green-700 text-green-300',
};

export default function RiskHeatmap() {
  const { companyId } = useAuthStore();
  const [cells, setCells] = useState<any[]>([]);
  const [scores, setScores] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!companyId) return;
    Promise.all([
      apiClient.get(`/risk/heatmap?company_id=${companyId}`),
      apiClient.get(`/risk/scores?company_id=${companyId}`),
    ]).then(([h, s]) => {
      setCells(h.data.cells || []);
      setScores(s.data);
    }).finally(() => setLoading(false));
  }, [companyId]);

  if (loading) return <div className="text-center py-20 text-gray-500">Loading risk heatmap…</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white">Risk Heatmap</h1>
        <p className="text-sm text-gray-500">Process-level risk scores — updated daily</p>
      </div>

      {/* Heatmap grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {cells.length === 0 && scores.length === 0 ? (
          <div className="col-span-4 text-center py-12 text-gray-600">
            No risk scores computed yet. Trigger an audit cycle to generate scores.
          </div>
        ) : (
          cells.map((cell, i) => (
            <div key={i} className={`border rounded-lg p-4 ${bandColors[cell.band] || bandColors.low}`}>
              <div className="text-xs uppercase tracking-wider opacity-70 mb-1">{cell.process}</div>
              <div className="font-semibold">{cell.entity}</div>
              <div className="text-3xl font-bold font-mono mt-2">{cell.score?.toFixed(0)}</div>
              <div className="text-xs uppercase mt-1 opacity-80">{cell.band} risk</div>
              <div className="text-xs opacity-60 mt-0.5">{cell.exception_count} exceptions</div>
            </div>
          ))
        )}
      </div>

      {/* Score table */}
      {scores.length > 0 && (
        <div className="card p-0 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr>
                {['Process', 'Likelihood', 'Impact', 'Frequency', 'Control Weakness', 'Score', 'Band'].map(h => (
                  <th key={h} className="table-header text-left">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {scores.map((s: any) => (
                <tr key={s.id} className="table-row">
                  <td className="table-cell text-gray-300">{s.entity_name}</td>
                  <td className="table-cell text-gray-400">{s.likelihood?.toFixed(1)}</td>
                  <td className="table-cell text-gray-400">{s.impact?.toFixed(1)}</td>
                  <td className="table-cell text-gray-400">{s.frequency?.toFixed(1)}</td>
                  <td className="table-cell text-gray-400">{(s.control_weakness * 100).toFixed(0)}%</td>
                  <td className="table-cell font-mono font-bold text-white">{s.composite_score?.toFixed(1)}</td>
                  <td className="table-cell">
                    <span className={`text-xs font-semibold uppercase ${
                      s.risk_band === 'critical' ? 'text-red-400' :
                      s.risk_band === 'high' ? 'text-orange-400' :
                      s.risk_band === 'moderate' ? 'text-yellow-400' : 'text-green-400'
                    }`}>{s.risk_band}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
