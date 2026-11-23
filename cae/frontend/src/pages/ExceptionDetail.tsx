import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Sparkles, MessageSquare, Loader2, ChevronDown } from 'lucide-react';
import apiClient from '../api/client';
import SeverityBadge from '../components/common/SeverityBadge';
import StatusBadge from '../components/common/StatusBadge';
import AmountDisplay from '../components/common/AmountDisplay';
import type { AuditException } from '../types';
import { areaLabel } from '../api/labels';
import { useAuthStore } from '../store/authStore';

const STATUS_TRANSITIONS: Record<string, { value: string; label: string }[]> = {
  open: [
    { value: 'in_review', label: 'Mark In Review' },
    { value: 'management_query_sent', label: 'Send Query to Management' },
    { value: 'remediation_in_progress', label: 'Start Remediation' },
    { value: 'false_positive', label: 'Mark False Positive' },
    { value: 'closed', label: 'Close' },
  ],
  in_review: [
    { value: 'management_query_sent', label: 'Send Query to Management' },
    { value: 'remediation_in_progress', label: 'Start Remediation' },
    { value: 'resolved', label: 'Mark Resolved' },
    { value: 'false_positive', label: 'Mark False Positive' },
    { value: 'closed', label: 'Close' },
  ],
  management_query_sent: [
    { value: 'remediation_in_progress', label: 'Start Remediation' },
    { value: 'resolved', label: 'Mark Resolved' },
    { value: 'closed', label: 'Close' },
  ],
  remediation_in_progress: [
    { value: 'resolved', label: 'Mark Resolved' },
    { value: 'closed', label: 'Close' },
  ],
  resolved: [{ value: 'closed', label: 'Close' }],
};

function EvidencePanel({ data }: { data: any }) {
  if (!data) return null;
  if (typeof data !== 'object') {
    return <pre className="text-xs text-gray-400 bg-navy-900 rounded p-3 overflow-auto">{String(data)}</pre>;
  }
  const entries = Array.isArray(data) ? data : Object.entries(data);
  if (Array.isArray(data)) {
    return (
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <tbody>
            {data.map((item: any, i: number) => (
              <tr key={i} className="border-b border-navy-border last:border-0">
                {typeof item === 'object' ? (
                  Object.entries(item).map(([k, v]) => (
                    <td key={k} className="py-1.5 pr-4">
                      <span className="text-gray-500 mr-1">{k}:</span>
                      <span className="text-gray-200">{String(v)}</span>
                    </td>
                  ))
                ) : (
                  <td className="py-1.5 text-gray-200">{String(item)}</td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }
  return (
    <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2">
      {(entries as [string, any][]).map(([k, v]) => (
        <div key={k} className="flex items-start gap-2">
          <dt className="text-xs text-gray-500 min-w-0 shrink-0 capitalize">{k.replace(/_/g, ' ')}:</dt>
          <dd className="text-xs text-gray-200 break-all">
            {typeof v === 'object' ? JSON.stringify(v) : String(v)}
          </dd>
        </div>
      ))}
    </dl>
  );
}

export default function ExceptionDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [exc, setExc] = useState<AuditException | null>(null);
  const [aiResult, setAiResult] = useState<any>(null);
  const [loadingAI, setLoadingAI] = useState(false);
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [showStatusMenu, setShowStatusMenu] = useState(false);
  const [form, setForm] = useState<'query' | 'remediation' | null>(null);
  const [question, setQuestion] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [gap, setGap] = useState('');
  const [plan, setPlan] = useState('');
  const [owner, setOwner] = useState('');
  const [notice, setNotice] = useState('');
  const { engagement } = useAuthStore();

  useEffect(() => {
    apiClient.get(`/exceptions/${id}`).then(r => setExc(r.data));
  }, [id]);

  const explainWithAI = async () => {
    setLoadingAI(true);
    try {
      const r = await apiClient.post(`/exceptions/${id}/ai-explain`);
      setAiResult(r.data);
      setExc(prev => prev ? { ...prev, ai_analysis: r.data.explanation } : prev);
    } finally {
      setLoadingAI(false);
    }
  };

  const openForm = (kind: 'query' | 'remediation') => {
    setShowStatusMenu(false);
    setNotice('');
    if (kind === 'query') {
      setQuestion(aiResult?.recommended_query || `Please explain and provide supporting documents for: ${exc?.title}. ${exc?.description || ''}`.trim());
    } else {
      setGap(exc?.title || '');
      setPlan(aiResult?.suggested_remediation || '');
    }
    setForm(kind);
  };

  const submitForm = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!exc) return;
    setUpdatingStatus(true);
    try {
      if (form === 'query') {
        const r = await apiClient.post('/queries', {
          exception_id: exc.id, process_area: exc.process || exc.category, severity: exc.severity,
          description: exc.title, evidence_summary: exc.description || '', suggested_question: question,
          due_date: dueDate || null,
        });
        setExc({ ...exc, status: 'management_query_sent' });
        setNotice(`Query ${r.data.query_no} raised — response due ${r.data.due_date}. Track it under Queries.`);
      } else {
        const r = await apiClient.post('/remediation', {
          company_id: exc.company_id, exception_id: exc.id, control_gap_description: gap, action_plan: plan,
          responsible_name: owner || null, target_date: dueDate || null,
        });
        setExc({ ...exc, status: 'remediation_in_progress' });
        setNotice(`Remediation action added — owner ${r.data.responsible_name}, target ${r.data.target_date}.`);
      }
      setForm(null);
    } catch (err: any) {
      setNotice(err.response?.data?.detail || 'Could not save');
    } finally {
      setUpdatingStatus(false);
    }
  };

  const updateStatus = async (newStatus: string) => {
    if (newStatus === 'management_query_sent') return openForm('query');
    if (newStatus === 'remediation_in_progress') return openForm('remediation');
    setUpdatingStatus(true);
    setShowStatusMenu(false);
    try {
      await apiClient.patch(`/exceptions/${id}/status`, { status: newStatus });
      setExc(prev => prev ? { ...prev, status: newStatus } : prev);
    } finally {
      setUpdatingStatus(false);
    }
  };

  if (!exc) return (
    <div className="flex items-center justify-center h-64">
      <Loader2 className="w-6 h-6 text-gold animate-spin" />
    </div>
  );

  const transitions = STATUS_TRANSITIONS[exc.status] || [];

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center gap-3">
        <Link to="/exceptions" className="text-gray-500 hover:text-gray-300">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <h1 className="text-xl font-bold text-white truncate flex-1">{exc.title}</h1>
      </div>

      {/* Header row */}
      <div className="flex items-center gap-3 flex-wrap">
        <SeverityBadge severity={exc.severity} />
        <StatusBadge status={exc.status} />
        <span className="text-xs bg-navy-700 border border-navy-border text-gray-400 px-2 py-0.5 rounded">
          {areaLabel(exc.category)}
        </span>
        {exc.rule_code && <span className="text-xs font-mono text-gray-500">{exc.rule_code}</span>}
        {exc.material && <span className="text-xs font-semibold text-red-300 border border-red-800/60 rounded px-1.5">At or above materiality</span>}
        {exc.risk_impact && (
          <span className="text-xs text-gray-500">{exc.risk_impact}</span>
        )}
        {exc.financial_impact != null && (
          <AmountDisplay amount={exc.financial_impact} className="text-sm font-semibold text-orange-400" />
        )}
        <span className="text-xs text-gray-600">
          Detected: {new Date(exc.detected_on).toLocaleDateString('en-IN', { day: '2-digit', month: 'long', year: 'numeric' })}
        </span>
      </div>

      {/* Description */}
      {exc.description && (
        <div className="card">
          <h2 className="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wider">Description</h2>
          <p className="text-gray-300 text-sm leading-relaxed">{exc.description}</p>
        </div>
      )}

      {/* Audit-type view: statutory reporting references or internal-audit process */}
      {exc.engagement_id && (
        <div className="card">
          <h2 className="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wider">
            {engagement?.audit_type === 'internal' || exc.audit_refs?.[0]?.frame === 'Process' ? 'Internal audit — process' : 'Statutory reporting reference'}
          </h2>
          {exc.audit_refs?.length ? (
            <ul className="space-y-1.5">
              {exc.audit_refs.map((r, i) => (
                <li key={i} className="text-sm text-gray-300">
                  <span className="text-gold font-medium">{r.frame}</span> {r.frame !== 'Process' && <span className="font-mono">{r.ref}</span>}
                  {r.frame === 'Process' && <span>{r.ref}</span>}
                  {r.title && <span className="text-gray-400"> — {r.title}</span>}
                  {r.note && <span className="text-gray-500"> ({r.note})</span>}
                </li>
              ))}
            </ul>
          ) : <p className="text-sm text-gray-500">Financial-statement matter — evaluate under the Standards on Auditing.</p>}
        </div>
      )}

      {/* Evidence / Supporting Data */}
      {exc.supporting_data && (
        <div className="card">
          <h2 className="text-xs font-semibold text-gray-500 mb-3 uppercase tracking-wider">Evidence & Transaction Data</h2>
          <EvidencePanel data={exc.supporting_data} />
        </div>
      )}

      {/* AI Analysis */}
      <div className="card">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">AI Analysis</h2>
          <button onClick={explainWithAI} disabled={loadingAI}
            className="btn-primary flex items-center gap-2 text-sm py-1.5">
            {loadingAI ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            {loadingAI ? 'Analysing…' : 'Explain with Claude'}
          </button>
        </div>

        {(aiResult || exc.ai_analysis) ? (
          <div className="space-y-4">
            {aiResult ? (
              <>
                <div>
                  <h3 className="text-xs font-semibold text-gold uppercase tracking-wider mb-1">Explanation</h3>
                  <p className="text-sm text-gray-300">{aiResult.explanation}</p>
                </div>
                <div>
                  <h3 className="text-xs font-semibold text-gold uppercase tracking-wider mb-1">Business Impact</h3>
                  <p className="text-sm text-gray-300">{aiResult.business_impact}</p>
                </div>
                <div>
                  <h3 className="text-xs font-semibold text-gold uppercase tracking-wider mb-1">Fraud Risk</h3>
                  <p className="text-sm text-gray-300">{aiResult.fraud_risk}</p>
                </div>
                <div>
                  <h3 className="text-xs font-semibold text-gold uppercase tracking-wider mb-1">Recommended Query</h3>
                  <p className="text-sm text-gray-300 italic">"{aiResult.recommended_query}"</p>
                </div>
                <div>
                  <h3 className="text-xs font-semibold text-gold uppercase tracking-wider mb-1">Suggested Remediation</h3>
                  <p className="text-sm text-gray-300">{aiResult.suggested_remediation}</p>
                </div>
              </>
            ) : (
              <p className="text-sm text-gray-300">{exc.ai_analysis}</p>
            )}
          </div>
        ) : (
          <p className="text-sm text-gray-600">Click "Explain with Claude" to get an AI-powered analysis of this exception.</p>
        )}
      </div>

      {notice && <div className="text-sm text-green-300 bg-green-900/20 border border-green-800 rounded px-3 py-2">{notice}</div>}

      {form && (
        <form onSubmit={submitForm} className="card space-y-3">
          <h2 className="text-sm font-semibold text-gold">{form === 'query' ? 'Raise management query' : 'Start remediation'}</h2>
          {form === 'query' ? (
            <label className="block text-sm text-gray-400">Question to management
              <textarea required rows={4} value={question} onChange={e => setQuestion(e.target.value)} className="input-field mt-1" />
            </label>
          ) : (
            <>
              <label className="block text-sm text-gray-400">Control gap
                <input required value={gap} onChange={e => setGap(e.target.value)} className="input-field mt-1" />
              </label>
              <label className="block text-sm text-gray-400">Agreed action plan
                <textarea required rows={3} value={plan} onChange={e => setPlan(e.target.value)} className="input-field mt-1" />
              </label>
              <label className="block text-sm text-gray-400">Action owner
                <input value={owner} onChange={e => setOwner(e.target.value)} className="input-field mt-1" placeholder="defaults to you" />
              </label>
            </>
          )}
          <label className="block text-sm text-gray-400">{form === 'query' ? 'Response due by' : 'Target date'}
            <input type="date" value={dueDate} onChange={e => setDueDate(e.target.value)} className="input-field mt-1 max-w-xs" />
            <span className="text-xs text-gray-500 ml-2">blank = {form === 'query' ? '7' : '30'} days</span>
          </label>
          <div className="flex gap-2">
            <button type="submit" disabled={updatingStatus} className="btn-primary text-sm">{form === 'query' ? 'Send query' : 'Save action'}</button>
            <button type="button" onClick={() => setForm(null)} className="btn-ghost text-sm">Cancel</button>
          </div>
        </form>
      )}

      {/* Actions */}
      <div className="flex gap-3 flex-wrap">
        <button
          onClick={() => navigate('/queries')}
          className="btn-primary flex items-center gap-2 text-sm"
        >
          <MessageSquare className="w-4 h-4" />
          View Management Queries
        </button>

        {transitions.length > 0 && (
          <div className="relative">
            <button
              onClick={() => setShowStatusMenu(s => !s)}
              disabled={updatingStatus}
              className="btn-ghost flex items-center gap-2 text-sm border border-navy-border"
            >
              {updatingStatus ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              Update Status
              <ChevronDown className="w-4 h-4" />
            </button>
            {showStatusMenu && (
              <div className="absolute left-0 bottom-full mb-1 bg-navy-800 border border-navy-border rounded-lg shadow-xl z-10 min-w-[200px]">
                {transitions.map(t => (
                  <button
                    key={t.value}
                    onClick={() => updateStatus(t.value)}
                    className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-navy-700 first:rounded-t-lg last:rounded-b-lg"
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
