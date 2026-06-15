import { useState, useRef } from 'react';
import { Upload, Play, FileText, CheckCircle, AlertCircle } from 'lucide-react';
import apiClient from '../api/client';
import { useAuthStore } from '../store/authStore';

const FILE_TYPES = ['sales_invoices', 'purchase_invoices', 'journal_entries', 'bank_transactions', 'inventory', 'payroll'];

export default function DataIngestion() {
  const { companyId } = useAuthStore();
  const [fileType, setFileType] = useState('sales_invoices');
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<any>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!file || !companyId) return;

    setUploading(true);
    setUploadResult(null);
    const form = new FormData();
    form.append('company_id', companyId);
    form.append('file_type', fileType);
    form.append('file', file);
    try {
      const r = await apiClient.post('/ingestion/upload', form, { headers: { 'Content-Type': 'multipart/form-data' } });
      setUploadResult({ success: true, data: r.data });
    } catch (err: any) {
      setUploadResult({ success: false, error: err.response?.data?.detail || 'Upload failed' });
    } finally {
      setUploading(false);
    }
  };

  const handleSync = async () => {
    if (!companyId) return;
    setSyncing(true);
    setSyncResult(null);
    try {
      const r = await apiClient.post(`/ingestion/sync?company_id=${companyId}&job_type=full_audit`);
      setSyncResult({ success: true, data: r.data });
    } catch (err: any) {
      setSyncResult({ success: false, error: err.response?.data?.detail || 'Sync failed' });
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-xl font-bold text-white">Data Ingestion</h1>
        <p className="text-sm text-gray-500">Upload Excel/CSV data or trigger audit cycle</p>
      </div>

      {/* File upload */}
      <div className="card">
        <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">Upload Transaction Data</h2>
        <form onSubmit={handleUpload} className="space-y-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1.5 uppercase tracking-wider">Data Type</label>
            <select value={fileType} onChange={e => setFileType(e.target.value)} className="input-field">
              {FILE_TYPES.map(t => (
                <option key={t} value={t}>{t.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1.5 uppercase tracking-wider">File (Excel / CSV)</label>
            <input ref={fileRef} type="file" accept=".xlsx,.xls,.csv" required
              className="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-gold file:text-navy-900 hover:file:bg-gold-light" />
          </div>
          <button type="submit" disabled={uploading || !companyId}
            className="btn-primary flex items-center gap-2 disabled:opacity-50">
            <Upload className="w-4 h-4" />
            {uploading ? 'Uploading…' : 'Upload & Import'}
          </button>
        </form>

        {uploadResult && (
          <div className={`mt-4 rounded p-3 flex items-start gap-2 ${uploadResult.success ? 'bg-green-900/20 border border-green-800/40' : 'bg-red-900/20 border border-red-800/40'}`}>
            {uploadResult.success ? <CheckCircle className="w-4 h-4 text-green-400 shrink-0 mt-0.5" /> : <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />}
            <div className="text-sm">
              {uploadResult.success
                ? `Uploaded: ${uploadResult.data.filename}. Processing started.`
                : uploadResult.error}
            </div>
          </div>
        )}
      </div>

      {/* Trigger audit */}
      <div className="card">
        <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-2">Run Audit Cycle</h2>
        <p className="text-sm text-gray-500 mb-4">
          Trigger a full audit cycle — runs all enabled rules, computes fraud indicators, risk scores, and working capital metrics.
        </p>
        <button onClick={handleSync} disabled={syncing || !companyId}
          className="btn-primary flex items-center gap-2 disabled:opacity-50">
          <Play className="w-4 h-4" />
          {syncing ? 'Triggering…' : 'Run Full Audit Now'}
        </button>

        {syncResult && (
          <div className={`mt-4 rounded p-3 flex items-start gap-2 ${syncResult.success ? 'bg-green-900/20 border border-green-800/40' : 'bg-red-900/20 border border-red-800/40'}`}>
            {syncResult.success ? <CheckCircle className="w-4 h-4 text-green-400 shrink-0 mt-0.5" /> : <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />}
            <div className="text-sm">
              {syncResult.success
                ? `Audit cycle queued: Job ${syncResult.data.id}. Status: ${syncResult.data.status}`
                : syncResult.error}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
