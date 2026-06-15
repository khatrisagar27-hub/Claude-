import { useEffect, useState } from 'react';
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

  useEffect(() => {
    if (!companyId) return;
    apiClient.get(`/remediation?company_id=${companyId}`).then(r => setActions(r.data)).finally(() => setLoading(false));
  }, [companyId]);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-white">Remediation Tracker</h1>
        <p className="text-sm text-gray-500">{actions.length} control improvement actions</p>
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr>
              {['Control Gap', 'Action Plan', 'Target Date', 'Closure Date', 'Retest Outcome'].map(h => (
                <th key={h} className="table-header text-left">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} className="text-center py-12 text-gray-500">Loading…</td></tr>
            ) : actions.length === 0 ? (
              <tr><td colSpan={5} className="text-center py-12 text-gray-500">No remediation actions found</td></tr>
            ) : actions.map(a => (
              <tr key={a.id} className="table-row">
                <td className="table-cell max-w-xs">
                  <p className="text-gray-300 truncate">{a.control_gap_description}</p>
                </td>
                <td className="table-cell max-w-xs">
                  <p className="text-gray-400 truncate">{a.action_plan}</p>
                </td>
                <td className="table-cell text-gray-500 text-xs">
                  {a.target_date ? new Date(a.target_date).toLocaleDateString('en-IN') : '—'}
                </td>
                <td className="table-cell text-gray-500 text-xs">
                  {a.actual_closure_date ? new Date(a.actual_closure_date).toLocaleDateString('en-IN') : '—'}
                </td>
                <td className="table-cell">
                  <span className={`text-xs font-medium capitalize ${outcomeColors[a.retest_outcome || 'pending']}`}>
                    {(a.retest_outcome || 'pending').replace('_', ' ')}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
