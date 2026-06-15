import { useEffect, useState } from 'react';
import apiClient from '../api/client';
import { useAuthStore } from '../store/authStore';
import SeverityBadge from '../components/common/SeverityBadge';
import StatusBadge from '../components/common/StatusBadge';
import type { ManagementQuery } from '../types';

export default function Queries() {
  const { companyId } = useAuthStore();
  const [queries, setQueries] = useState<ManagementQuery[]>([]);
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!companyId) return;
    setLoading(true);
    const params = new URLSearchParams({ company_id: companyId });
    if (status) params.set('status', status);
    apiClient.get(`/queries?${params}`).then(r => setQueries(r.data)).finally(() => setLoading(false));
  }, [companyId, status]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Management Queries</h1>
          <p className="text-sm text-gray-500">{queries.length} queries</p>
        </div>
      </div>

      <div className="card flex items-center gap-3">
        <select value={status} onChange={e => setStatus(e.target.value)}
          className="bg-navy-700 border border-navy-border text-sm text-gray-300 rounded px-2 py-1.5 focus:outline-none focus:border-gold">
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="pending">Pending</option>
          <option value="responded">Responded</option>
          <option value="escalated">Escalated</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
        </select>
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr>
              {['Query No', 'Process Area', 'Severity', 'Description', 'Due Date', 'Status'].map(h => (
                <th key={h} className="table-header text-left">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="text-center py-12 text-gray-500">Loading…</td></tr>
            ) : queries.length === 0 ? (
              <tr><td colSpan={6} className="text-center py-12 text-gray-500">No queries found</td></tr>
            ) : queries.map(q => (
              <tr key={q.id} className="table-row">
                <td className="table-cell font-mono text-gold text-xs">{q.query_no}</td>
                <td className="table-cell text-gray-400">{q.process_area}</td>
                <td className="table-cell"><SeverityBadge severity={q.severity} /></td>
                <td className="table-cell max-w-xs">
                  <p className="truncate text-gray-300">{q.description}</p>
                </td>
                <td className="table-cell text-gray-500 text-xs">
                  {q.due_date ? new Date(q.due_date).toLocaleDateString('en-IN') : '—'}
                </td>
                <td className="table-cell"><StatusBadge status={q.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
