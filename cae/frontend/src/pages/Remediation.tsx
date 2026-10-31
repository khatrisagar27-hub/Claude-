import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../api/client';
import { useAuthStore } from '../store/authStore';
import type { RemediationAction } from '../types';

const outcomeColors: Record<string, string> = {
  effective: 'text-green-400',
  partially_effective: 'text-yellow-400',
  ineffective: 'text-red-400',
  pending: 'text-gray-400',
};

export default function Remediation() {
  const { companyId } = useAuthStore();
  const [actions, setActions] = useState<RemediationAction[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    if (!companyId) { setLoading(false); return; }
    apiClient.get(`/remediation?company_id=${companyId}`).then(r => setActions(r.data)).finally(() => setLoading(false));
  };
  useEffect(load, [companyId]);

  const retest = async (a: RemediationAction, outcome: string) => {
    const today = new Date().toISOString().slice(0, 10);
    await apiClient.put(`/remediation/${a.id}`, {
      retest_outcome: outcome,
      ...(outcome === 'effective' ? { actual_closure_date: today, status: 'closed' } : { status: 'open' }),
    });
    load();
  };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-white">Remediation Tracker</h1>
        <p className="text-sm text-gray-500">{actions.length} control improvement actions · start one from any exception (Update Status → Start Remediation)</p>
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr>
              {['Control Gap', 'Action Plan', 'Owner', 'Target Date', 'Closure Date', 'Status', 'Re-test'].map(h => (
                <th key={h} className="table-header text-left">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} className="text-center py-12 text-gray-500">Loading…</td></tr>
            ) : actions.length === 0 ? (
              <tr><td colSpan={7} className="text-center py-12 text-gray-500">No remediation actions found</td></tr>
            ) : actions.map(a => (
              <tr key={a.id} className="table-row">
                <td className="table-cell max-w-xs">
                  <Link to={`/exceptions/${a.exception_id}`} className="text-gray-300 hover:text-gold line-clamp-2">{a.control_gap_description}</Link>
                </td>
                <td className="table-cell max-w-xs"><p className="text-gray-400 line-clamp-2 text-sm">{a.action_plan}</p></td>
                <td className="table-cell text-gray-400 text-xs">{a.responsible_name || '—'}</td>
                <td className="table-cell text-gray-500 text-xs">{a.target_date ? new Date(a.target_date).toLocaleDateString('en-IN') : '—'}</td>
                <td className="table-cell text-gray-500 text-xs">{a.actual_closure_date ? new Date(a.actual_closure_date).toLocaleDateString('en-IN') : '—'}</td>
                <td className="table-cell text-xs capitalize text-gray-400">{a.status || 'open'}</td>
                <td className="table-cell">
                  <select aria-label="Re-test outcome" value={a.retest_outcome || ''} onChange={e => e.target.value && retest(a, e.target.value)}
                    className={`bg-navy-700 border border-navy-border text-xs rounded px-1.5 py-1 ${outcomeColors[a.retest_outcome || 'pending']}`}>
                    <option value="">pending</option>
                    <option value="effective">effective</option>
                    <option value="partially_effective">partially effective</option>
                    <option value="ineffective">ineffective</option>
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
