import { useEffect, useState, useRef } from 'react';
import { Upload, Play, CheckCircle, AlertCircle, Scan, ArrowRight, RotateCcw, Database, RefreshCw } from 'lucide-react';
import apiClient from '../api/client';
import { useAuthStore } from '../store/authStore';
import { JobStatus, useJobPoller } from './Engagements';
import { AUDIT_TYPE_LABEL } from '../api/labels';

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

type Upload = { id: string; filename: string; file_type: string; status: string; rows_imported: number | null;
  parse_errors: string[] | null; created_at: string };

function RecentUploads({ companyId, refreshKey }: { companyId: string | null; refreshKey: number }) {
  const [rows, setRows] = useState<Upload[]>([]);
  useEffect(() => {
    if (!companyId) return;
    let timer: any;
    const load = () => apiClient.get(`/ingestion/uploads?company_id=${companyId}&limit=8`).then(r => {
      setRows(r.data);
      if (r.data.some((u: Upload) => ['uploaded', 'processing'].includes(u.status))) timer = setTimeout(load, 2500);
    }).catch(() => {});
    load();
    return () => clearTimeout(timer);
  }, [companyId, refreshKey]);
  if (!rows.length) return null;
  return (
    <div className="card p-0 overflow-hidden">
      <div className="px-4 py-3 text-sm font-semibold text-gray-300 uppercase tracking-wider">Recent file imports</div>
      <table className="w-full"><thead><tr>{['File', 'Status', 'Rows imported', 'Errors', 'When'].map(h => <th key={h} className="table-header text-left">{h}</th>)}</tr></thead>
        <tbody>{rows.map(u => (
          <tr key={u.id} className="table-row">
            <td className="table-cell text-sm text-gray-300">{u.filename}</td>
            <td className={`table-cell text-xs font-semibold ${u.status === 'imported' ? 'text-green-400' : u.status === 'failed' ? 'text-red-400' : 'text-yellow-400'}`}>{u.status}</td>
            <td className="table-cell text-sm">{u.rows_imported ?? '—'}</td>
            <td className="table-cell text-xs text-red-300 max-w-md">{(u.parse_errors || []).slice(0, 3).join('; ')}</td>
            <td className="table-cell text-xs text-gray-500">{new Date(u.created_at).toLocaleString('en-IN')}</td>
          </tr>))}
        </tbody></table>
    </div>
  );
}

function TallyLive() {
  const { companyId, engagement, setCompanyId } = useAuthStore();
  const [status, setStatus] = useState<any>(null);
  const [checking, setChecking] = useState(false);
  const [tallyCo, setTallyCo] = useState('');
  const fy = (() => { const d = new Date(); const y = d.getMonth() >= 3 ? d.getFullYear() - 1 : d.getFullYear() - 2; return y; })();
  const [from, setFrom] = useState(`${fy}-04-01`);
  const [to, setTo] = useState(`${fy + 1}-03-31`);
  const [target, setTarget] = useState<'new' | 'current'>('new');
  const [extended, setExtended] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<any>(null);
  const [job, setJob] = useJobPoller();

  const check = () => {
    setChecking(true);
    apiClient.get('/tally/status').then(r => {
      setStatus(r.data);
      if (r.data.companies?.length && !tallyCo) setTallyCo(r.data.companies[0].name);
    }).finally(() => setChecking(false));
  };
  useEffect(check, []);
  useEffect(() => {
    if (engagement) {
      apiClient.get(`/engagements/${engagement.id}`).then(r => { setFrom(r.data.period_from); setTo(r.data.period_to); }).catch(() => {});
    }
  }, [engagement?.id]);

  const start = async () => {
    setError('');
    try {
      const r = await apiClient.post('/tally/import', {
        tally_company: tallyCo, from_date: from, to_date: to, extended_ledger_details: extended,
        company_id: target === 'current' ? companyId : null,
      });
      setResult(r.data);
      setJob(r.data.job);
    } catch (err: any) {
      const d = err.response?.data?.detail;
      setError(Array.isArray(d) ? d.map((x: any) => x.msg).join('; ') : d || 'Import failed to start');
    }
  };
  const busy = !!job && ['queued', 'running'].includes(job.status);

  return (
    <div className="card space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider flex items-center gap-2"><Database className="w-4 h-4 text-gold" /> Tally Prime — live data</h2>
        <button onClick={check} className="btn-ghost text-xs flex items-center gap-1"><RefreshCw className={`w-3 h-3 ${checking ? 'animate-spin' : ''}`} /> Check Tally</button>
      </div>
      {status && (
        <div className={`text-sm rounded px-3 py-2 border ${status.running ? 'border-green-800 bg-green-900/20 text-green-300' : 'border-red-800 bg-red-900/20 text-red-300'}`}>
          {status.running ? `Connected to ${status.url} — ${status.companies.length} compan${status.companies.length === 1 ? 'y' : 'ies'} open in Tally` : status.message}
        </div>
      )}
      {status?.running && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label className="text-sm text-gray-400 md:col-span-2">Tally company
            <select value={tallyCo} onChange={e => setTallyCo(e.target.value)} className="input-field mt-1">
              {status.companies.map((c: any) => <option key={c.name} value={c.name}>{c.name}{c.books_from ? ` (books from ${c.books_from})` : ''}</option>)}
            </select>
          </label>
          <label className="text-sm text-gray-400">From<input type="date" value={from} onChange={e => setFrom(e.target.value)} className="input-field mt-1" /></label>
          <label className="text-sm text-gray-400">To<input type="date" value={to} onChange={e => setTo(e.target.value)} className="input-field mt-1" /></label>
          <div className="md:col-span-2 flex flex-wrap gap-5 text-sm text-gray-300">
            <label className="flex items-center gap-2"><input type="radio" checked={target === 'new'} onChange={() => setTarget('new')} /> Load into a CAE company named after the Tally company</label>
            <label className="flex items-center gap-2"><input type="radio" checked={target === 'current'} onChange={() => setTarget('current')} disabled={!companyId} /> Load into the company selected above</label>
            <label className="flex items-center gap-2"><input type="checkbox" checked={extended} onChange={e => setExtended(e.target.checked)} /> Read ledger GSTIN / MSME details (slower on large files)</label>
          </div>
          <p className="md:col-span-2 text-xs text-gray-500">
            Read-only on Tally. Pulls masters, then vouchers month by month (sales, purchases, bank / cash, journals, stock), bill-wise outstanding and settlement dates.
            Re-importing the same period replaces the earlier Tally rows. {engagement ? `Dates follow the selected ${AUDIT_TYPE_LABEL[engagement.audit_type]}.` : ''}
          </p>
          <div className="md:col-span-2">
            <button onClick={start} disabled={busy || !tallyCo} className="btn-primary flex items-center gap-2 text-sm disabled:opacity-50">
              <Database className="w-4 h-4" /> {busy ? 'Importing…' : 'Import from Tally'}
            </button>
          </div>
        </div>
      )}
      {error && <div className="text-sm text-red-400">{error}</div>}
      <JobStatus job={job} />
      {job?.status === 'completed' && result && result.company_id !== companyId && (
        <button onClick={() => setCompanyId(result.company_id)} className="btn-ghost text-sm border border-navy-border">
          Switch to “{result.company_name}” to audit it
        </button>
      )}
    </div>
  );
}

export default function DataIngestion() {
  const { companyId, engagement } = useAuthStore();
  const [tab, setTab] = useState<Tab>('smart');
  const [uploadsKey, setUploadsKey] = useState(0);
  const [auditJob, setAuditJob] = useJobPoller();

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
      setUploadsKey(k => k + 1);
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
      setUploadsKey(k => k + 1);
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
      const scope = engagement ? `&engagement_id=${engagement.id}` : '';
      const r = await apiClient.post(`/ingestion/sync?company_id=${companyId}&job_type=${engagement ? `${engagement.audit_type}_audit` : 'full_audit'}${scope}`);
      setSyncResult({ success: true, data: r.data });
      setAuditJob(r.data);
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
                  ? `Uploaded "${importResult.data.filename}" as ${FILE_TYPE_LABELS[importResult.type]} — see Recent file imports below for the result.`
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
                  ? `Uploaded: ${uploadResult.data.filename} — see Recent file imports below for the result.`
                  : uploadResult.error}
              </div>
            </div>
          )}
        </div>
      )}

      <RecentUploads companyId={companyId} refreshKey={uploadsKey} />

      <TallyLive />

      {/* ─── Audit Trigger ───────────────────────────────────────── */}
      <div className="card">
        <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-2">Run Audit Cycle</h2>
        <p className="text-sm text-gray-500 mb-4">
          {engagement
            ? `Runs the ${AUDIT_TYPE_LABEL[engagement.audit_type]} (${engagement.label}): every in-scope rule over the engagement period, then fraud analytics, risk scores and working capital.`
            : 'Continuous monitoring run — every enabled rule (daily, weekly and monthly) over all data, then fraud analytics, risk scores and working capital. Select an engagement at the top to audit a period.'}
        </p>
        <button onClick={handleSync} disabled={syncing || !companyId}
          className="btn-primary flex items-center gap-2 disabled:opacity-50">
          <Play className="w-4 h-4" />
          {syncing ? 'Triggering…' : 'Run Full Audit Now'}
        </button>

        {syncResult && !syncResult.success && (
          <div className="mt-4 rounded p-3 flex items-start gap-2 bg-red-900/20 border border-red-800/40">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <div className="text-sm">{syncResult.error}</div>
          </div>
        )}
        <div className="mt-4"><JobStatus job={auditJob} /></div>
      </div>
    </div>
  );
}
