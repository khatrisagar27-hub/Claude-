import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Filter } from 'lucide-react';
import apiClient from '../api/client';
import { useAuthStore } from '../store/authStore';
import SeverityBadge from '../components/common/SeverityBadge';
import StatusBadge from '../components/common/StatusBadge';
import AmountDisplay from '../components/common/AmountDisplay';
import type { AuditException } from '../types';

const CATEGORIES = [
  { value: '', label: 'All Areas' },
  { value: 'revenue', label: 'Revenue' },
  { value: 'expenditure', label: 'Expenditure' },
  { value: 'payroll', label: 'Payroll' },
  { value: 'gst', label: 'GST' },
  { value: 'inventory', label: 'Inventory' },
  { value: 'bank_reconciliation', label: 'Bank / Treasury' },
  { value: 'related_party', label: 'Related Party' },
  { value: 'statutory', label: 'Statutory' },
];

export default function Exceptions() {
  const { companyId } = useAuthStore();
  const navigate = useNavigate();
  const [exceptions, setExceptions] = useState<AuditException[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [severity, setSeverity] = useState('');
  const [status, setStatus] = useState('');
  const [category, setCategory] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!companyId) { setLoading(false); return; }
    setLoading(true);
    const params = new URLSearchParams({ company_id: companyId, page: String(page), page_size: '50' });
    if (severity) params.set('severity', severity);
    if (status) params.set('status', status);
    if (category) params.set('category', category);
    apiClient.get(`/exceptions?${params}`).then(r => {
      setExceptions(r.data.items);
      setTotal(r.data.total);
    }).finally(() => setLoading(false));
  }, [companyId, page, severity, status, category]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Exceptions</h1>
          <p className="text-sm text-gray-500">{total} total exceptions</p>
        </div>
      </div>

      {/* Filters */}
      <div className="card flex items-center gap-3 flex-wrap">
        <Filter className="w-4 h-4 text-gray-500" />
        <select value={severity} onChange={e => { setSeverity(e.target.value); setPage(1); }}
          className="bg-navy-700 border border-navy-border text-sm text-gray-300 rounded px-2 py-1.5 focus:outline-none focus:border-gold">
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select value={status} onChange={e => { setStatus(e.target.value); setPage(1); }}
          className="bg-navy-700 border border-navy-border text-sm text-gray-300 rounded px-2 py-1.5 focus:outline-none focus:border-gold">
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="in_review">In Review</option>
          <option value="management_query_sent">Query Sent</option>
          <option value="remediation_in_progress">Remediation</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
          <option value="false_positive">False Positive</option>
        </select>
        <select value={category} onChange={e => { setCategory(e.target.value); setPage(1); }}
          className="bg-navy-700 border border-navy-border text-sm text-gray-300 rounded px-2 py-1.5 focus:outline-none focus:border-gold">
          {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
        </select>
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr>
              {['Severity', 'Title', 'Business Area', 'Financial Impact', 'Status', 'Detected'].map(h => (
                <th key={h} className="table-header text-left">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="text-center py-12 text-gray-500">Loading…</td></tr>
            ) : exceptions.length === 0 ? (
              <tr><td colSpan={6} className="text-center py-12 text-gray-500">No exceptions found</td></tr>
            ) : exceptions.map(exc => (
              <tr
                key={exc.id}
                className="table-row cursor-pointer hover:bg-navy-700/50"
                onClick={() => navigate(`/exceptions/${exc.id}`)}
              >
                <td className="table-cell"><SeverityBadge severity={exc.severity} /></td>
                <td className="table-cell max-w-xs">
                  <span className="text-gray-200 line-clamp-2 text-sm">{exc.title}</span>
                </td>
                <td className="table-cell text-gray-400 capitalize">{exc.category?.replace(/_/g, ' ')}</td>
                <td className="table-cell"><AmountDisplay amount={exc.financial_impact} /></td>
                <td className="table-cell"><StatusBadge status={exc.status} /></td>
                <td className="table-cell text-gray-500 text-xs">
                  {new Date(exc.detected_on).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: '2-digit' })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {total > 50 && (
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>Showing {(page - 1) * 50 + 1}–{Math.min(page * 50, total)} of {total}</span>
          <div className="flex gap-2">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
              className="btn-ghost disabled:opacity-40">Previous</button>
            <button onClick={() => setPage(p => p + 1)} disabled={page * 50 >= total}
              className="btn-ghost disabled:opacity-40">Next</button>
          </div>
        </div>
      )}
    </div>
  );
}
