import { Fragment, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
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
  const [open, setOpen] = useState<string | null>(null);
  const [reply, setReply] = useState('');
  const [busy, setBusy] = useState(false);

  const load = () => {
    if (!companyId) { setLoading(false); return; }
    setLoading(true);
    const params = new URLSearchParams({ company_id: companyId });
    if (status) params.set('status', status);
    apiClient.get(`/queries?${params}`).then(r => setQueries(r.data)).finally(() => setLoading(false));
  };
  useEffect(load, [companyId, status]);

  const respond = async (q: ManagementQuery) => {
    if (!reply.trim()) return;
    setBusy(true);
    try {
      await apiClient.post(`/queries/${q.id}/respond`, { response_text: reply });
      setReply('');
      load();
    } finally { setBusy(false); }
  };

  const close = async (q: ManagementQuery) => {
    setBusy(true);
    try {
      await apiClient.patch(`/queries/${q.id}/status`, { status: 'closed' });
      load();
    } finally { setBusy(false); }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Management Queries</h1>
          <p className="text-sm text-gray-500">{queries.length} queries · raise one from any exception (Update Status → Send Query to Management)</p>
        </div>
      </div>

      <div className="card flex items-center gap-3">
        <select value={status} onChange={e => setStatus(e.target.value)}
          className="bg-navy-700 border border-navy-border text-sm text-gray-300 rounded px-2 py-1.5 focus:outline-none focus:border-gold">
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="responded">Responded</option>
          <option value="closed">Closed</option>
        </select>
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr>
              {['Query No', 'Process Area', 'Severity', 'Finding', 'Raised by', 'Due Date', 'Status'].map(h => (
                <th key={h} className="table-header text-left">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} className="text-center py-12 text-gray-500">Loading…</td></tr>
            ) : queries.length === 0 ? (
              <tr><td colSpan={7} className="text-center py-12 text-gray-500">No queries found</td></tr>
            ) : queries.map(q => (
              <Fragment key={q.id}>
                <tr className="table-row cursor-pointer hover:bg-navy-700/50" onClick={() => { setOpen(open === q.id ? null : q.id); setReply(''); }}>
                  <td className="table-cell font-mono text-gold text-xs">{q.query_no}</td>
                  <td className="table-cell text-gray-400 text-sm">{q.process_area}</td>
                  <td className="table-cell"><SeverityBadge severity={q.severity} /></td>
                  <td className="table-cell max-w-xs"><p className="truncate text-gray-300">{q.description}</p></td>
                  <td className="table-cell text-gray-500 text-xs">{q.raised_by_name || '—'}</td>
                  <td className="table-cell text-gray-500 text-xs">{q.due_date ? new Date(q.due_date).toLocaleDateString('en-IN') : '—'}</td>
                  <td className="table-cell"><StatusBadge status={q.status} /></td>
                </tr>
                {open === q.id && (
                  <tr>
                    <td colSpan={7} className="bg-navy-900/60 px-6 py-4 space-y-3">
                      <div className="text-sm"><span className="text-gray-500">Question: </span><span className="text-gray-200">{q.suggested_question}</span></div>
                      <Link to={`/exceptions/${q.exception_id}`} className="text-xs text-gold hover:underline">Open the exception →</Link>
                      {(q.responses || []).map(r => (
                        <div key={r.id} className="text-sm border-l-2 border-gold/50 pl-3">
                          <div className="text-gray-200">{r.response_text}</div>
                          <div className="text-xs text-gray-500">{r.responded_by_name} · {new Date(r.responded_at).toLocaleString('en-IN')}</div>
                        </div>
                      ))}
                      {q.status !== 'closed' && (
                        <div className="flex flex-col gap-2 max-w-2xl">
                          <textarea rows={2} value={reply} onChange={e => setReply(e.target.value)} className="input-field"
                            placeholder="Record management's response" />
                          <div className="flex gap-2">
                            <button disabled={busy || !reply.trim()} onClick={() => respond(q)} className="btn-primary text-sm disabled:opacity-50">Save response</button>
                            <button disabled={busy} onClick={() => close(q)} className="btn-ghost text-sm border border-navy-border">Close query</button>
                          </div>
                        </div>
                      )}
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
