import { useEffect, useState } from 'react';
import { Upload, AlertTriangle } from 'lucide-react';
import apiClient from '../api/client';
import { useAuthStore } from '../store/authStore';
import AmountDisplay from '../components/common/AmountDisplay';
import type { GSTRecon } from '../types';

// Row shapes written by app/engines/gst_match.py into gst_reconciliation.details_json
interface MatchRow {
  gstin: string;
  inv_no_raw: string;
  inv_date: string | null;
  taxable: number;
  tax: number;
  supplier: string;
  b2_inv_date?: string | null;
  b2_taxable?: number;
  b2_tax?: number;
  diff_taxable?: number;
  diff_tax?: number;
  mismatch_on?: string;
  books_inv_no?: string;
  reason?: string;
  note?: string;
}

interface MatchSummary {
  matched_count: number;
  mismatch_count: number;
  missing_in_2b_count: number;
  missing_in_books_count: number;
  review_probable_count: number;
  books_itc: number;
  gstr2b_itc: number;
  itc_at_risk: number;
  itc_not_booked: number;
  tolerance: number;
}

interface ReconDetails {
  period: string;
  risk_amount: number;
  details: {
    mode?: 'invoice' | 'summary';
    mismatch?: MatchRow[];
    missing_in_2b?: MatchRow[];
    missing_in_books?: MatchRow[];
    review_probable?: MatchRow[];
    summary?: MatchSummary;
    books_output_tax?: number;
    gstr1_tax?: number | null;
    output_tax_gap?: number;
    itc_at_risk?: number;
  };
}

interface UploadResult {
  period: string;
  parse_stats: { data_rows: number; invalid_gstin: number } | null;
  result: { mode: string; risk_amount: number; summary: MatchSummary | null };
}

type Bucket = 'mismatch' | 'missing_in_2b' | 'missing_in_books' | 'review_probable';

const BUCKETS: { key: Bucket; label: string; hint: string; tone: string }[] = [
  { key: 'missing_in_2b', label: 'Missing in 2B', hint: 'In books, not reported by the supplier — ITC at risk', tone: 'text-red-400' },
  { key: 'mismatch', label: 'Mismatch', hint: 'Same GSTIN + invoice, but taxable / tax / date differ beyond tolerance', tone: 'text-orange-400' },
  { key: 'missing_in_books', label: 'Missing in books', hint: 'In GSTR-2B, not booked — ITC available but not taken', tone: 'text-yellow-400' },
  { key: 'review_probable', label: 'Review — probable', hint: 'Same GSTIN and tax, different invoice number. Not paired automatically: a person decides', tone: 'text-blue-400' },
];

const DETAIL_ROW_CAP = 500; // gst_engine.DETAIL_ROW_CAP

const Amt = ({ v, className = '' }: { v?: number | null; className?: string }) =>
  <AmountDisplay amount={v} exact className={className} />;

function BucketTable({ bucket, rows }: { bucket: Bucket; rows: MatchRow[] }) {
  const head: Record<Bucket, string[]> = {
    missing_in_2b: ['Supplier GSTIN', 'Supplier', 'Invoice', 'Date', 'Taxable', 'Tax (ITC at risk)'],
    missing_in_books: ['Supplier GSTIN', 'Supplier', 'Invoice', 'Date', 'Taxable', 'Tax'],
    mismatch: ['Supplier GSTIN', 'Supplier', 'Invoice', 'Books date', '2B date', 'Books taxable', '2B taxable', 'Books tax', '2B tax', 'Tax diff', 'Differs on'],
    review_probable: ['Supplier GSTIN', 'Supplier', '2B invoice', 'Books invoice', 'Date', 'Taxable', 'Tax'],
  };
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr>
            {head[bucket].map(h => <th key={h} className="table-header text-left whitespace-nowrap">{h}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr><td colSpan={head[bucket].length} className="text-center py-8 text-gray-600">Nothing in this bucket.</td></tr>
          ) : rows.map((r, i) => (
            <tr key={`${r.gstin}-${r.inv_no_raw}-${i}`} className="table-row">
              <td className="table-cell font-mono text-xs">{r.gstin}</td>
              <td className="table-cell text-gray-400 max-w-[14rem] truncate" title={r.supplier}>{r.supplier || '—'}</td>
              <td className="table-cell font-mono text-gold">{r.inv_no_raw}</td>
              {bucket === 'review_probable' && <td className="table-cell font-mono text-blue-400">{r.books_inv_no}</td>}
              <td className="table-cell text-gray-400 whitespace-nowrap">{r.inv_date || '—'}</td>
              {bucket === 'mismatch' ? (
                <>
                  <td className={`table-cell whitespace-nowrap ${r.mismatch_on?.includes('date') ? 'text-orange-400' : 'text-gray-400'}`}>{r.b2_inv_date || '—'}</td>
                  <td className="table-cell"><Amt v={r.taxable} /></td>
                  <td className="table-cell"><Amt v={r.b2_taxable} /></td>
                  <td className="table-cell"><Amt v={r.tax} /></td>
                  <td className="table-cell"><Amt v={r.b2_tax} /></td>
                  <td className="table-cell"><Amt v={r.diff_tax} className={(r.diff_tax || 0) > 0 ? 'text-red-400' : 'text-gray-400'} /></td>
                  <td className="table-cell text-xs text-orange-400">{r.mismatch_on}</td>
                </>
              ) : (
                <>
                  <td className="table-cell"><Amt v={r.taxable} /></td>
                  <td className="table-cell"><Amt v={r.tax} className={bucket === 'missing_in_2b' ? 'text-red-400' : ''} /></td>
                </>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function GST() {
  const { companyId } = useAuthStore();
  const [recons, setRecons] = useState<GSTRecon[]>([]);
  const [itcRisk, setItcRisk] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const [period, setPeriod] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [tolerance, setTolerance] = useState('1');
  const [gstr1Tax, setGstr1Tax] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);

  const [selected, setSelected] = useState<string | null>(null);
  const [details, setDetails] = useState<ReconDetails | null>(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [bucket, setBucket] = useState<Bucket>('missing_in_2b');

  const loadList = () => {
    if (!companyId) return;
    Promise.all([
      apiClient.get(`/gst/reconciliation?company_id=${companyId}`),
      apiClient.get(`/gst/itc-risk?company_id=${companyId}`),
    ]).then(([r, risk]) => {
      setRecons(r.data);
      setItcRisk(risk.data);
    }).finally(() => setLoading(false));
  };

  useEffect(loadList, [companyId]);

  useEffect(() => {
    if (!companyId || !selected) { setDetails(null); return; }
    setDetailsLoading(true);
    apiClient.get(`/gst/reconciliation/${selected}/details?company_id=${companyId}`)
      .then(r => setDetails(r.data))
      .catch(() => setDetails(null))
      .finally(() => setDetailsLoading(false));
  }, [companyId, selected, uploadResult]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!companyId || !file || !period) return;
    setUploading(true);
    setUploadError(null);
    setUploadResult(null);
    const form = new FormData();
    form.append('company_id', companyId);
    form.append('period', period);
    form.append('file', file);
    if (tolerance !== '') form.append('tolerance', tolerance);
    if (gstr1Tax !== '') form.append('gstr1_tax', gstr1Tax);
    try {
      const r = await apiClient.post('/gst/upload-gstr2b', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setUploadResult(r.data);
      setSelected(period);
      setBucket('missing_in_2b');
      loadList();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setUploadError(typeof detail === 'string' ? detail : detail ? JSON.stringify(detail) : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const d = details?.details;
  const s = d?.summary;
  const countOf = (b: Bucket) => (s ? s[`${b}_count` as keyof MatchSummary] : 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white">GST Reconciliation</h1>
        <p className="text-sm text-gray-500">GSTR-1 / GSTR-3B / GSTR-2B vs Books</p>
      </div>

      {/* ITC Risk summary */}
      {itcRisk && (
        <div className="grid grid-cols-3 gap-4">
          <div className="card">
            <div className="text-xs text-gray-500 uppercase tracking-wider">Total ITC Risk</div>
            <div className="text-2xl font-bold text-red-400 mt-1">
              <AmountDisplay amount={itcRisk.total_itc_risk} className="text-red-400" />
            </div>
          </div>
          <div className="card">
            <div className="text-xs text-gray-500 uppercase tracking-wider">Periods at Risk</div>
            <div className="text-2xl font-bold text-white mt-1">{itcRisk.periods_at_risk}</div>
          </div>
          <div className="card">
            <div className="text-xs text-gray-500 uppercase tracking-wider">Total Periods Reconciled</div>
            <div className="text-2xl font-bold text-white mt-1">{recons.length}</div>
          </div>
        </div>
      )}

      {/* GSTR-2B upload */}
      <form onSubmit={handleUpload} className="card space-y-4">
        <div>
          <div className="text-sm font-semibold text-white">Upload GSTR-2B</div>
          <p className="text-xs text-gray-500 mt-0.5">
            Portal GSTR-2B Excel, or a CSV with the same headers. Matched invoice by invoice on supplier GSTIN +
            normalised invoice number — deterministic, no fuzzy pairing.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <label className="text-xs text-gray-400 space-y-1">
            <span>Return period *</span>
            <input type="month" required value={period} onChange={e => setPeriod(e.target.value)} className="input-field" />
          </label>
          <label className="text-xs text-gray-400 space-y-1">
            <span>GSTR-2B file (.xlsx / .csv / .json) *</span>
            <input type="file" required accept=".xlsx,.xlsm,.csv,.json"
              onChange={e => setFile(e.target.files?.[0] || null)}
              className="input-field text-xs file:mr-2 file:rounded file:border-0 file:bg-navy-600 file:px-2 file:py-1 file:text-gray-200" />
          </label>
          <label className="text-xs text-gray-400 space-y-1">
            <span>Tolerance per invoice (₹)</span>
            <input type="number" min="0" step="0.01" value={tolerance} onChange={e => setTolerance(e.target.value)} className="input-field" />
          </label>
          <label className="text-xs text-gray-400 space-y-1">
            <span>GSTR-1 output tax (₹, optional)</span>
            <input type="number" min="0" step="0.01" value={gstr1Tax} onChange={e => setGstr1Tax(e.target.value)}
              placeholder="Compared with books output tax" className="input-field" />
          </label>
        </div>
        <div className="flex items-center gap-4">
          <button type="submit" disabled={uploading || !file || !period || !companyId}
            className="btn-primary flex items-center gap-2 text-sm disabled:opacity-50">
            <Upload className="w-4 h-4" />
            {uploading ? 'Reconciling…' : 'Reconcile'}
          </button>
          {uploadError && <span className="text-sm text-red-400">{uploadError}</span>}
          {uploadResult && (
            <span className="text-sm text-green-400">
              {uploadResult.period} reconciled ({uploadResult.result.mode} level)
              {uploadResult.parse_stats && <> · {uploadResult.parse_stats.data_rows} 2B rows read</>}
            </span>
          )}
        </div>
        {uploadResult?.parse_stats && uploadResult.parse_stats.invalid_gstin > 0 && (
          <div className="flex items-start gap-2 text-xs text-yellow-400 bg-yellow-900/20 border border-yellow-800/40 rounded p-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            {uploadResult.parse_stats.invalid_gstin} of {uploadResult.parse_stats.data_rows} rows in the file have an
            invalid supplier GSTIN and were left out of the match. Check them in the source file.
          </div>
        )}
      </form>

      <div className="card p-0 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr>
              {['Period', 'Books Turnover', 'GSTR-1 Turnover', 'Variance', 'Books ITC', 'GSTR-2B ITC', 'ITC Variance', 'Risk Amount', 'Status'].map(h => (
                <th key={h} className="table-header text-left">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={9} className="text-center py-12 text-gray-500">Loading…</td></tr>
            ) : recons.length === 0 ? (
              <tr><td colSpan={9} className="text-center py-12 text-gray-600">No GST reconciliation data. Upload GSTR-2B to reconcile.</td></tr>
            ) : recons.map(r => (
              <tr key={r.id} onClick={() => setSelected(r.period)}
                className={`table-row cursor-pointer ${selected === r.period ? 'bg-gold/5' : ''}`}>
                <td className="table-cell font-mono text-gold">{r.period}</td>
                <td className="table-cell"><AmountDisplay amount={r.books_turnover} /></td>
                <td className="table-cell"><AmountDisplay amount={r.gstr1_turnover} /></td>
                <td className={`table-cell ${(r.variance_turnover || 0) > 100000 ? 'text-red-400' : 'text-gray-400'}`}>
                  <AmountDisplay amount={r.variance_turnover} />
                </td>
                <td className="table-cell"><AmountDisplay amount={r.books_itc} /></td>
                <td className="table-cell"><AmountDisplay amount={r.gstr2b_itc} /></td>
                <td className={`table-cell ${(r.variance_itc || 0) > 50000 ? 'text-red-400' : 'text-gray-400'}`}>
                  <AmountDisplay amount={r.variance_itc} />
                </td>
                <td className="table-cell text-red-400 font-semibold"><AmountDisplay amount={r.risk_amount} /></td>
                <td className="table-cell">
                  <span className="text-xs text-green-400 capitalize">{r.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {recons.length > 0 && !selected && (
          <div className="px-4 py-2 text-xs text-gray-600 border-t border-navy-border">Click a period for the invoice-level buckets.</div>
        )}
      </div>

      {/* Invoice-level detail for the selected period */}
      {selected && (
        <div className="space-y-4">
          <div className="text-sm font-semibold text-white">Invoice-level reconciliation — <span className="font-mono text-gold">{selected}</span></div>
          {detailsLoading ? (
            <div className="card text-center py-8 text-gray-500">Loading…</div>
          ) : !details ? (
            <div className="card text-center py-8 text-gray-600">No reconciliation stored for {selected}.</div>
          ) : d?.mode !== 'invoice' || !s ? (
            <div className="card text-sm text-gray-400">
              {selected} was reconciled at summary level only (no invoice rows in the upload), so there are no
              invoice buckets. Risk amount: <Amt v={details.risk_amount} className="text-red-400" />.
              Upload the portal GSTR-2B Excel / CSV for this period to get an invoice-level match.
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <div className="card">
                  <div className="text-xs text-gray-500 uppercase">Books ITC</div>
                  <Amt v={s.books_itc} className="text-base font-bold text-white block mt-1" />
                </div>
                <div className="card">
                  <div className="text-xs text-gray-500 uppercase">GSTR-2B ITC</div>
                  <Amt v={s.gstr2b_itc} className="text-base font-bold text-white block mt-1" />
                </div>
                <div className="card border-red-800/50">
                  <div className="text-xs text-gray-500 uppercase">ITC at risk</div>
                  <Amt v={s.itc_at_risk} className="text-base font-bold text-red-400 block mt-1" />
                  <div className="text-[10px] text-gray-600 mt-0.5">Missing in 2B + excess books tax on mismatches</div>
                </div>
                <div className="card">
                  <div className="text-xs text-gray-500 uppercase">ITC not booked</div>
                  <Amt v={s.itc_not_booked} className="text-base font-bold text-yellow-400 block mt-1" />
                </div>
                <div className="card">
                  <div className="text-xs text-gray-500 uppercase">Output tax gap</div>
                  {d.gstr1_tax == null ? (
                    <div className="text-xs text-gray-600 mt-1">No GSTR-1 tax given</div>
                  ) : (
                    <>
                      <Amt v={d.output_tax_gap} className="text-base font-bold text-white block mt-1" />
                      <div className="text-[10px] text-gray-600 mt-0.5">Books <Amt v={d.books_output_tax} /> vs GSTR-1 <Amt v={d.gstr1_tax} /></div>
                    </>
                  )}
                </div>
                <div className="card">
                  <div className="text-xs text-gray-500 uppercase">Risk amount</div>
                  <Amt v={details.risk_amount} className="text-base font-bold text-red-400 block mt-1" />
                  <div className="text-[10px] text-gray-600 mt-0.5">ITC at risk + output tax gap</div>
                </div>
              </div>

              <div className="card p-0 overflow-hidden">
                <div className="flex flex-wrap gap-2 p-3 border-b border-navy-border items-center">
                  <span className="text-xs text-gray-500 mr-2">
                    Matched: <span className="text-green-400 font-semibold">{s.matched_count}</span> · tolerance <Amt v={s.tolerance} />
                  </span>
                  {BUCKETS.map(b => (
                    <button key={b.key} onClick={() => setBucket(b.key)}
                      className={`px-3 py-1.5 rounded text-xs font-medium ${bucket === b.key ? 'bg-gold text-navy-900' : 'bg-navy-700 text-gray-400 hover:text-gray-200'}`}>
                      {b.label} <span className={bucket === b.key ? '' : b.tone}>({countOf(b.key)})</span>
                    </button>
                  ))}
                </div>
                <div className="px-4 py-2 text-xs text-gray-500">
                  {BUCKETS.find(b => b.key === bucket)?.hint}
                  {countOf(bucket) > DETAIL_ROW_CAP && (
                    <span className="text-yellow-400"> · showing the first {DETAIL_ROW_CAP} of {countOf(bucket)} rows</span>
                  )}
                </div>
                <BucketTable bucket={bucket} rows={d[bucket] || []} />
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
