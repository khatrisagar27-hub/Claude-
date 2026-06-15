import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Sparkles, MessageSquare, Loader2 } from 'lucide-react';
import apiClient from '../api/client';
import SeverityBadge from '../components/common/SeverityBadge';
import StatusBadge from '../components/common/StatusBadge';
import AmountDisplay from '../components/common/AmountDisplay';
import type { AuditException } from '../types';

export default function ExceptionDetail() {
  const { id } = useParams();
  const [exc, setExc] = useState<AuditException | null>(null);
  const [aiResult, setAiResult] = useState<any>(null);
  const [loadingAI, setLoadingAI] = useState(false);

  useEffect(() => {
    apiClient.get(`/exceptions/${id}`).then(r => setExc(r.data));
  }, [id]);

  const explainWithAI = async () => {
    setLoadingAI(true);
    try {
      const r = await apiClient.post(`/exceptions/${id}/ai-explain`);
      setAiResult(r.data);
    } finally {
      setLoadingAI(false);
    }
  };

  if (!exc) return (
    <div className="flex items-center justify-center h-64">
      <Loader2 className="w-6 h-6 text-gold animate-spin" />
    </div>
  );

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center gap-3">
        <Link to="/exceptions" className="text-gray-500 hover:text-gray-300">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <h1 className="text-xl font-bold text-white truncate">{exc.title}</h1>
      </div>

      {/* Header badges */}
      <div className="flex items-center gap-3 flex-wrap">
        <SeverityBadge severity={exc.severity} />
        <StatusBadge status={exc.status} />
        <span className="text-xs text-gray-500">{exc.business_area}</span>
        <span className="text-xs text-gray-500">{exc.risk_category}</span>
        {exc.financial_impact && (
          <AmountDisplay amount={exc.financial_impact} className="text-sm font-semibold text-orange-400" />
        )}
      </div>

      {/* Description */}
      <div className="card">
        <h2 className="text-sm font-semibold text-gray-300 mb-2 uppercase tracking-wider">Description</h2>
        <p className="text-gray-300 text-sm leading-relaxed">{exc.description}</p>
      </div>

      {/* Evidence */}
      {exc.evidence_json && (
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-300 mb-2 uppercase tracking-wider">Evidence</h2>
          <pre className="text-xs text-gray-400 bg-navy-900 rounded p-3 overflow-auto">
            {JSON.stringify(exc.evidence_json, null, 2)}
          </pre>
        </div>
      )}

      {/* AI Explanation */}
      <div className="card">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">AI Analysis</h2>
          <button onClick={explainWithAI} disabled={loadingAI}
            className="btn-primary flex items-center gap-2 text-sm py-1.5">
            {loadingAI ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            {loadingAI ? 'Analysing…' : 'Explain with Claude'}
          </button>
        </div>

        {(aiResult || exc.ai_explanation) ? (
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
                  <h3 className="text-xs font-semibold text-gold uppercase tracking-wider mb-1">Fraud Risk Assessment</h3>
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
              <p className="text-sm text-gray-300">{exc.ai_explanation}</p>
            )}
          </div>
        ) : (
          <p className="text-sm text-gray-600">Click "Explain with Claude" to get an AI-powered analysis of this exception.</p>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button className="btn-primary flex items-center gap-2 text-sm">
          <MessageSquare className="w-4 h-4" />
          Raise Management Query
        </button>
      </div>
    </div>
  );
}
