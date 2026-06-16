import { useState } from 'react';
import { Download, FileText, FileSpreadsheet } from 'lucide-react';
import apiClient from '../api/client';
import { useAuthStore } from '../store/authStore';

export default function Reports() {
  const { companyId } = useAuthStore();
  const [loading, setLoading] = useState<string | null>(null);

  const download = async (endpoint: string, filename: string, label: string) => {
    if (!companyId) return;
    setLoading(label);
    try {
      const r = await apiClient.post(`${endpoint}?company_id=${companyId}`, {}, { responseType: 'blob' });
      const url = URL.createObjectURL(new Blob([r.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setLoading(null);
    }
  };

  const reports = [
    {
      label: 'Working Paper',
      desc: 'Complete working paper with all exceptions, evidence, and audit trail (Excel)',
      icon: FileSpreadsheet,
      endpoint: '/reports/working-paper',
      filename: `working_paper_${companyId}.xlsx`,
    },
    {
      label: 'Exception Summary',
      desc: 'Summary of exceptions by severity and business area (Excel)',
      icon: FileSpreadsheet,
      endpoint: '/reports/exception-summary',
      filename: `exception_summary_${companyId}.xlsx`,
    },
    {
      label: 'Audit Deck',
      desc: 'Executive audit presentation with risk heatmap and top findings (PDF)',
      icon: FileText,
      endpoint: '/reports/audit-deck',
      filename: `audit_deck_${companyId}.pdf`,
    },
  ];

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-xl font-bold text-white">Reports</h1>
        <p className="text-sm text-gray-500">Generate and download working papers and audit reports</p>
      </div>

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
