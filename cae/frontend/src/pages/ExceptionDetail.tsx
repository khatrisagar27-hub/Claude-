import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Sparkles, MessageSquare, Loader2, ChevronDown } from 'lucide-react';
import apiClient from '../api/client';
import SeverityBadge from '../components/common/SeverityBadge';
import StatusBadge from '../components/common/StatusBadge';
import AmountDisplay from '../components/common/AmountDisplay';
import type { AuditException } from '../types';

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

  const updateStatus = async (newStatus: string) => {
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
        <span className="text-xs bg-navy-700 border border-navy-border text-gray-400 px-2 py-0.5 rounded capitalize">
          {exc.category?.replace(/_/g, ' ')}
        </span>
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
