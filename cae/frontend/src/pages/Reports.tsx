import { useState } from 'react';
import { Download, FileText, FileSpreadsheet } from 'lucide-react';
import apiClient from '../api/client';
import { useAuthStore } from '../store/authStore';
import { AUDIT_TYPE_LABEL, engagementQS } from '../api/labels';

export default function Reports() {
  const { companyId, engagement } = useAuthStore();
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState('');
  const statutory = engagement?.audit_type === 'statutory';

  const download = async (endpoint: string, fallbackName: string, label: string) => {
    if (!companyId) return;
    setLoading(label);
    setError('');
    try {
      const r = await apiClient.post(`${endpoint}?company_id=${companyId}${engagementQS(engagement?.id)}`, {}, { responseType: 'blob' });
      const disposition = r.headers['content-disposition'] || '';
      const filename = /filename="([^"]+)"/.exec(disposition)?.[1] || fallbackName;
      const url = URL.createObjectURL(new Blob([r.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.response?.status === 403 ? 'Your role cannot generate this report.' : 'Could not generate the report.');
    } finally {
      setLoading(null);
    }
  };

  const reports = engagement ? [
    {
      label: statutory ? 'Statutory Audit Working Paper' : 'Internal Audit Report',
      desc: statutory
        ? 'Cover with CARO / IFC / tax-audit applicability and materiality; every finding with its CARO 2020 / Form 3CD / IFC / SA reference; CARO and tax-audit clause matrices with draft positions; IFC control exceptions; rule scope (Excel)'
        : 'Process-wise observations rated High / Medium / Low with details, risk, recommendation, management response, action owner and target date; summary by process; action plan (Excel)',
      icon: FileSpreadsheet, endpoint: '/reports/working-paper', filename: 'engagement_report.xlsx',
    },
    {
      label: statutory ? 'Statutory Findings & Reporting Matrix' : 'Internal Audit Report (PDF)',
      desc: statutory
        ? 'Summary, reporting matrix and key findings with references — for partner review (PDF)'
        : 'Summary by process and key observations — for the audit committee / management (PDF)',
      icon: FileText, endpoint: '/reports/audit-deck', filename: 'engagement_report.pdf',
    },
  ] : [
    {
      label: 'Working Paper',
      desc: 'Continuous-monitoring working paper with all exceptions raised outside an engagement, evidence and audit trail (Excel)',
      icon: FileSpreadsheet, endpoint: '/reports/working-paper', filename: `working_paper_${companyId}.xlsx`,
    },
    {
      label: 'Exception Summary',
      desc: 'Summary of exceptions by severity and business area (Excel)',
      icon: FileSpreadsheet, endpoint: '/reports/exception-summary', filename: `exception_summary_${companyId}.xlsx`,
    },
    {
      label: 'Monitoring Deck',
      desc: 'Executive presentation with severity summary and top findings (PDF)',
      icon: FileText, endpoint: '/reports/audit-deck', filename: `audit_deck_${companyId}.pdf`,
    },
  ];

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-xl font-bold text-white">Reports</h1>
        <p className="text-sm text-gray-500">
          {engagement ? `${AUDIT_TYPE_LABEL[engagement.audit_type]} — ${engagement.label}`
            : 'Continuous monitoring — select an engagement at the top for Statutory or Internal audit reports'}
        </p>
      </div>

      {error && <div className="text-sm text-red-400">{error}</div>}
      <div className="space-y-4">
        {reports.map(({ label, desc, icon: Icon, endpoint, filename }) => (
          <div key={label} className="card flex items-start gap-4">
            <div className="p-2 bg-navy-700 rounded-lg shrink-0">
              <Icon className="w-5 h-5 text-gold" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-white">{label}</h3>
              <p className="text-sm text-gray-500 mt-0.5">{desc}</p>
            </div>
            <button
              onClick={() => download(endpoint, filename, label)}
              disabled={loading === label || !companyId}
              className="btn-primary flex items-center gap-2 text-sm shrink-0 disabled:opacity-50"
            >
              <Download className="w-4 h-4" />
              {loading === label ? 'Generating…' : 'Download'}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
