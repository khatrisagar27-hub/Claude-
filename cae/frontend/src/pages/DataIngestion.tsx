import { useState, useRef } from 'react';
import { Upload, Play, CheckCircle, AlertCircle, Scan, ArrowRight, RotateCcw } from 'lucide-react';
import apiClient from '../api/client';
import { useAuthStore } from '../store/authStore';

const FILE_TYPE_LABELS: Record<string, string> = {
  sales_invoices: 'Sales Invoices',
  purchase_invoices: 'Purchase / Vendor Invoices',
  journal_entries: 'Journal Entries',
  bank_transactions: 'Bank Transactions',
  inventory: 'Inventory Movements',
  payroll: 'Payroll Records',
};

type AnalysisResult = {
  detected_type: string;
  detected_label: string;
  confidence_pct: number;
  columns_found: string[];
  column_mapping: Record<string, string>;
  unmapped_columns: string[];
  preview_rows: Record<string, string | null>[];
};

type Tab = 'smart' | 'manual';

export default function DataIngestion() {
  const { companyId } = useAuthStore();
  const [tab, setTab] = useState<Tab>('smart');

  // Smart (auto-detect) state
  const smartFileRef = useRef<HTMLInputElement>(null);
  const [analysing, setAnalysing] = useState(false);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [overrideType, setOverrideType] = useState('');
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<any>(null);

  // Manual state
  const manualFileRef = useRef<HTMLInputElement>(null);
  const [manualType, setManualType] = useState('sales_invoices');
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);

  // Audit sync state
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<any>(null);

  const handleAnalyse = async () => {
    const file = smartFileRef.current?.files?.[0];
    if (!file || !companyId) return;
    setAnalysing(true);
    setAnalysis(null);
    setImportResult(null);
    const form = new FormData();
    form.append('company_id', companyId);
    form.append('file', file);
    try {
      const r = await apiClient.post('/ingestion/analyze', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setAnalysis(r.data);
      setOverrideType('');
    } catch (err: any) {
      setImportResult({ success: false, error: err.response?.data?.detail || 'Analysis failed' });
    } finally {
      setAnalysing(false);
    }
  };

  const handleSmartImport = async () => {
    const file = smartFileRef.current?.files?.[0];
    if (!file || !companyId || !analysis) return;
    setImporting(true);
    setImportResult(null);
    const confirmedType = overrideType || analysis.detected_type;
    const form = new FormData();
    form.append('company_id', companyId);
    form.append('file_type', 'auto');
    form.append('detected_type', confirmedType);
    form.append('file', file);
    try {
      const r = await apiClient.post('/ingestion/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setImportResult({ success: true, data: r.data, type: confirmedType });
    } catch (err: any) {
      setImportResult({ success: false, error: err.response?.data?.detail || 'Import failed' });
    } finally {
      setImporting(false);
    }
  };

  const handleManualUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    const file = manualFileRef.current?.files?.[0];
    if (!file || !companyId) return;
    setUploading(true);
    setUploadResult(null);
    const form = new FormData();
    form.append('company_id', companyId);
    form.append('file_type', manualType);
    form.append('file', file);
    try {
      const r = await apiClient.post('/ingestion/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
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

  const confidence = analysis?.confidence_pct ?? 0;
  const confidenceColor = confidence >= 70 ? 'text-green-400' : confidence >= 40 ? 'text-yellow-400' : 'text-red-400';

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-xl font-bold text-white">Data Ingestion</h1>
        <p className="text-sm text-gray-500">Upload transaction data or trigger an audit cycle</p>
      </div>

      {/* Tab switcher */}
      <div className="flex gap-1 bg-navy-900 border border-navy-border rounded-lg p-1 w-fit">
        {(['smart', 'manual'] as Tab[]).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${
              tab === t ? 'bg-gold text-navy-900' : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            {t === 'smart' ? '✦ Auto-Detect (Smart)' : 'Manual'}
          </button>
        ))}
      </div>

      {/* ─── Smart Tab ───────────────────────────────────────────── */}
      {tab === 'smart' && (
        <div className="card space-y-5">
          <div>
            <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-1">
              Smart File Import
            </h2>
            <p className="text-xs text-gray-500">
              Upload any Excel or CSV file. The platform will detect the data type and map columns automatically.
            </p>
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1.5 uppercase tracking-wider">
              File (any structure)
            </label>
            <input
              ref={smartFileRef}
              type="file"
              accept=".xlsx,.xls,.csv"
              onChange={() => { setAnalysis(null); setImportResult(null); }}
              className="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-gold file:text-navy-900 hover:file:bg-gold-light"
            />
          </div>

          <button
            onClick={handleAnalyse}
            disabled={analysing || !companyId}
            className="btn-primary flex items-center gap-2 disabled:opacity-50"
          >
            <Scan className="w-4 h-4" />
            {analysing ? 'Analysing…' : 'Analyse File'}
          </button>

          {/* Analysis Result */}
          {analysis && !importResult && (
            <div className="space-y-4 border-t border-navy-border pt-4">
              {/* Detection summary */}
              <div className="flex items-center gap-3 flex-wrap">
                <div className="bg-navy-700 border border-navy-border rounded-lg px-4 py-2">
                  <div className="text-xs text-gray-500 uppercase tracking-wider">Detected As</div>
                  <div className="text-sm font-semibold text-white mt-0.5">{analysis.detected_label}</div>
                </div>
                <div className="bg-navy-700 border border-navy-border rounded-lg px-4 py-2">
                  <div className="text-xs text-gray-500 uppercase tracking-wider">Confidence</div>
                  <div className={`text-sm font-semibold mt-0.5 ${confidenceColor}`}>
                    {analysis.confidence_pct}%
                  </div>
                </div>
                <div className="bg-navy-700 border border-navy-border rounded-lg px-4 py-2">
                  <div className="text-xs text-gray-500 uppercase tracking-wider">Columns Found</div>
                  <div className="text-sm font-semibold text-white mt-0.5">{analysis.columns_found.length}</div>
                </div>
              </div>

              {/* Column mapping table */}
              <div>
                <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Column Mapping</div>
                <div className="rounded-lg overflow-hidden border border-navy-border">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="bg-navy-900">
                        <th className="text-left px-3 py-2 text-gray-500 font-medium">Your Column</th>
                        <th className="px-2 py-2 text-gray-600">→</th>
                        <th className="text-left px-3 py-2 text-gray-500 font-medium">Maps To Field</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(analysis.column_mapping).map(([field, col]) => (
                        <tr key={field} className="border-t border-navy-border/50">
                          <td className="px-3 py-1.5 text-gray-300 font-mono">{col}</td>
                          <td className="px-2 py-1.5 text-gray-600 text-center">→</td>
                          <td className="px-3 py-1.5 text-gold font-mono">{field}</td>
                        </tr>
                      ))}
                      {analysis.unmapped_columns.map(col => (
                        <tr key={col} className="border-t border-navy-border/50">
                          <td className="px-3 py-1.5 text-amber-500/70 font-mono">{col}</td>
                          <td className="px-2 py-1.5 text-gray-600 text-center">—</td>
                          <td className="px-3 py-1.5 text-gray-600 italic">unmapped (will be skipped)</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Preview rows */}
              {analysis.preview_rows.length > 0 && (
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Data Preview (first 3 rows)</div>
                  <div className="overflow-x-auto rounded-lg border border-navy-border">
                    <table className="text-xs w-max min-w-full">
                      <thead>
                        <tr className="bg-navy-900">
                          {analysis.columns_found.map(c => (
                            <th key={c} className="px-3 py-2 text-left text-gray-500 font-medium whitespace-nowrap">{c}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {analysis.preview_rows.map((row, i) => (
                          <tr key={i} className="border-t border-navy-border/50">
                            {analysis.columns_found.map(c => (
                              <td key={c} className="px-3 py-1.5 text-gray-300 whitespace-nowrap max-w-[180px] truncate">
                                {row[c] ?? '—'}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Override */}
              <div>
                <label className="block text-xs text-gray-500 mb-1.5 uppercase tracking-wider">
                  Override Detected Type (optional)
                </label>
                <select
                  value={overrideType}
                  onChange={e => setOverrideType(e.target.value)}
                  className="bg-navy-700 border border-navy-border text-sm text-gray-300 rounded px-3 py-1.5 focus:outline-none focus:border-gold"
                >
                  <option value="">Use detected: {analysis.detected_label}</option>
                  {Object.entries(FILE_TYPE_LABELS).map(([k, v]) => (
                    <option key={k} value={k}>{v}</option>
                  ))}
                </select>
              </div>

              {/* Confirm import */}
              <div className="flex gap-3">
                <button
                  onClick={handleSmartImport}
                  disabled={importing}
                  className="btn-primary flex items-center gap-2 disabled:opacity-50"
                >
                  <ArrowRight className="w-4 h-4" />
                  {importing ? 'Importing…' : `Confirm & Import as ${FILE_TYPE_LABELS[overrideType || analysis.detected_type]}`}
                </button>
                <button
                  onClick={() => { setAnalysis(null); setImportResult(null); if (smartFileRef.current) smartFileRef.current.value = ''; }}
                  className="btn-ghost flex items-center gap-2 text-sm"
                >
                  <RotateCcw className="w-4 h-4" />
                  Reset
                </button>
              </div>
            </div>
          )}

          {importResult && (
            <div className={`rounded p-3 flex items-start gap-2 ${importResult.success ? 'bg-green-900/20 border border-green-800/40' : 'bg-red-900/20 border border-red-800/40'}`}>
              {importResult.success
                ? <CheckCircle className="w-4 h-4 text-green-400 shrink-0 mt-0.5" />
                : <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />}
              <div className="text-sm">
                {importResult.success
                  ? `Imported "${importResult.data.filename}" as ${FILE_TYPE_LABELS[importResult.type]}. Processing started in background.`
                  : importResult.error}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ─── Manual Tab ──────────────────────────────────────────── */}
      {tab === 'manual' && (
        <div className="card space-y-4">
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Manual Upload</h2>
          <form onSubmit={handleManualUpload} className="space-y-4">
            <div>
              <label className="block text-xs text-gray-500 mb-1.5 uppercase tracking-wider">Data Type</label>
              <select value={manualType} onChange={e => setManualType(e.target.value)} className="input-field">
                {Object.entries(FILE_TYPE_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>{v}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1.5 uppercase tracking-wider">File (Excel / CSV)</label>
              <input ref={manualFileRef} type="file" accept=".xlsx,.xls,.csv" required
                className="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-gold file:text-navy-900 hover:file:bg-gold-light" />
            </div>
            <button type="submit" disabled={uploading || !companyId}
              className="btn-primary flex items-center gap-2 disabled:opacity-50">
              <Upload className="w-4 h-4" />
              {uploading ? 'Uploading…' : 'Upload & Import'}
            </button>
          </form>

          {uploadResult && (
            <div className={`rounded p-3 flex items-start gap-2 ${uploadResult.success ? 'bg-green-900/20 border border-green-800/40' : 'bg-red-900/20 border border-red-800/40'}`}>
              {uploadResult.success ? <CheckCircle className="w-4 h-4 text-green-400 shrink-0 mt-0.5" /> : <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />}
              <div className="text-sm">
                {uploadResult.success
                  ? `Uploaded: ${uploadResult.data.filename}. Processing started.`
                  : uploadResult.error}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ─── Audit Trigger ───────────────────────────────────────── */}
      <div className="card">
        <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-2">Run Audit Cycle</h2>
        <p className="text-sm text-gray-500 mb-4">
          Trigger a full audit cycle — runs all enabled rules, computes fraud indicators, risk scores, and working capital metrics against imported data.
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
                ? `Audit cycle queued — Job ID: ${syncResult.data.id}. Status: ${syncResult.data.status}`
                : syncResult.error}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
