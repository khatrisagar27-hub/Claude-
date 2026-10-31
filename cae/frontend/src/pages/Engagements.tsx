import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ClipboardCheck, Play, Plus, CheckCircle2, Loader2, AlertTriangle } from 'lucide-react';
import apiClient from '../api/client';
import { useAuthStore } from '../store/authStore';
import { AUDIT_TYPE_LABEL } from '../api/labels';
import type { AuditType, Engagement, SyncJob } from '../types';

const inr = (n?: number | null) => (n == null ? '—' : `₹${Math.round(n).toLocaleString('en-IN')}`);
const fyNow = () => { const d = new Date(); return d.getMonth() >= 3 ? d.getFullYear() : d.getFullYear() - 1; };

export function useJobPoller() {
  const [job, setJob] = useState<SyncJob | null>(null);
  useEffect(() => {
    if (!job || !['queued', 'running'].includes(job.status)) return;
    const t = setTimeout(() => apiClient.get(`/ingestion/jobs/${job.id}`).then(r => setJob(r.data)).catch(() => {}), 2000);
    return () => clearTimeout(t);
  }, [job]);
  return [job, setJob] as const;
}

export function JobStatus({ job }: { job: SyncJob | null }) {
  if (!job) return null;
  const busy = ['queued', 'running'].includes(job.status);
  const r = job.result || {};
  return (
    <div className={`rounded-md border px-3 py-2 text-sm ${job.status === 'failed' ? 'border-red-800 bg-red-900/20 text-red-300'
      : busy ? 'border-navy-border bg-navy-700/50 text-gray-300' : 'border-green-800 bg-green-900/20 text-green-300'}`}>
      <div className="flex items-center gap-2">
        {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : job.status === 'failed' ? <AlertTriangle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
        <span className="font-medium capitalize">{job.job_type.replace(/_/g, ' ')} — {job.status}</span>
        {job.run_mode === 'in_process' && <span className="text-xs text-gray-500">(worker unavailable — running inside the API)</span>}
      </div>
      {r.stage && busy && <div className="text-xs mt-1 text-gray-400">{r.stage}</div>}
      {job.status === 'completed' && r.rules_run != null && (
        <div className="text-xs mt-1">
          {r.rules_run} rules run · {r.exceptions_raised} new exceptions · {r.rule_errors} rule errors
          {r.failed_rules?.length ? ` · failed: ${r.failed_rules.map((f: any) => f.rule_code).join(', ')}` : ''}
        </div>
      )}
      {job.status === 'completed' && r.vouchers_read != null && (
        <div className="text-xs mt-1">
          {r.vouchers_read} vouchers read ({r.vouchers_in_books} in books) · {r.sales_invoices || 0} sales · {r.purchase_invoices || 0} purchases ·
          {' '}{r.bank_transactions || 0} bank/cash lines · {r.inventory_movements || 0} stock lines · {r.journal_entries || 0} journals
          {r.warnings?.length ? <div className="text-yellow-400 mt-1">{r.warnings.join(' · ')}</div> : null}
        </div>
      )}
      {job.error_message && <div className="text-xs mt-1">{job.error_message}</div>}
    </div>
  );
}

export default function Engagements() {
  const { companyId, engagement: selected, setEngagement, user } = useAuthStore();
  const navigate = useNavigate();
  const [rows, setRows] = useState<Engagement[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [type, setType] = useState<AuditType>('statutory');
  const [fy, setFy] = useState(fyNow() - 1);
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [caro, setCaro] = useState(false);
  const [ifc, setIfc] = useState(false);
  const [taxAudit, setTaxAudit] = useState(true);
  const [materiality, setMateriality] = useState('');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');
  const [job, setJob] = useJobPoller();
  const [summary, setSummary] = useState<any>(null);
  const canManage = ['super_admin', 'partner', 'manager'].includes(user?.role || '');

  const load = () => {
    if (!companyId) { setLoading(false); return; }
    apiClient.get(`/engagements?company_id=${companyId}`).then(r => setRows(r.data)).finally(() => setLoading(false));
  };
  useEffect(load, [companyId]);
  useEffect(() => {
    if (!selected) { setSummary(null); return; }
    apiClient.get(`/engagements/${selected.id}/summary`).then(r => setSummary(r.data)).catch(() => setSummary(null));
  }, [selected, job?.status]);
  useEffect(() => { if (job && job.status === 'completed') load(); }, [job?.status]);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    const body: any = { company_id: companyId, audit_type: type, scope_notes: notes || null,
      materiality: materiality ? Number(materiality) : null };
    if (type === 'statutory') Object.assign(body, { financial_year: fy, caro_applicable: caro, ifc_applicable: ifc, tax_audit_applicable: taxAudit });
    else Object.assign(body, { period_from: from, period_to: to });
    try {
      const r = await apiClient.post('/engagements', body);
      setShowForm(false);
      setEngagement({ id: r.data.id, label: r.data.label, audit_type: r.data.audit_type });
      window.dispatchEvent(new Event('cae:engagements-changed'));
      load();
    } catch (err: any) {
      const d = err.response?.data?.detail;
      setError(Array.isArray(d) ? d.map((x: any) => x.msg).join('; ') : d || 'Could not create the engagement');
    }
  };

  const run = async (eng: Engagement) => {
    setEngagement({ id: eng.id, label: eng.label, audit_type: eng.audit_type });
    const r = await apiClient.post(`/engagements/${eng.id}/run`);
    setJob(r.data);
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2"><ClipboardCheck className="w-5 h-5 text-gold" /> Audit Engagements</h1>
          <p className="text-sm text-gray-500">Run CAE as a Statutory audit of a financial year or an Internal audit of any period — every screen and report follows the engagement selected at the top.</p>
        </div>
        {canManage && (
          <button onClick={() => setShowForm(s => !s)} className="btn-primary flex items-center gap-2 text-sm">
            <Plus className="w-4 h-4" /> New engagement
          </button>
        )}
      </div>

      {showForm && (
        <form onSubmit={create} className="card space-y-4">
          <div className="flex gap-3">
            {(['statutory', 'internal'] as AuditType[]).map(t => (
              <button type="button" key={t} onClick={() => setType(t)}
                className={`px-4 py-2 rounded-md border text-sm ${type === t ? 'border-gold text-gold bg-gold/10' : 'border-navy-border text-gray-400'}`}>
                {AUDIT_TYPE_LABEL[t]}
              </button>
            ))}
          </div>
          {type === 'statutory' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <label className="text-sm text-gray-400">Financial year
                <select value={fy} onChange={e => setFy(Number(e.target.value))} className="input-field mt-1">
                  {Array.from({ length: 7 }, (_, i) => fyNow() - i).map(y => <option key={y} value={y}>FY {y}-{String(y + 1).slice(-2)}</option>)}
                </select>
              </label>
              <label className="text-sm text-gray-400">Overall materiality (₹, SA 320)
                <input type="number" min="0" value={materiality} onChange={e => setMateriality(e.target.value)} className="input-field mt-1" placeholder="optional" />
              </label>
              <div className="md:col-span-2 flex flex-wrap gap-5 text-sm text-gray-300">
                <label className="flex items-center gap-2"><input type="checkbox" checked={caro} onChange={e => setCaro(e.target.checked)} /> CARO 2020 applies</label>
                <label className="flex items-center gap-2"><input type="checkbox" checked={ifc} onChange={e => setIfc(e.target.checked)} /> IFC reporting s.143(3)(i) applies</label>
                <label className="flex items-center gap-2"><input type="checkbox" checked={taxAudit} onChange={e => setTaxAudit(e.target.checked)} /> Tax audit (Form 3CD) applies</label>
                <button type="button" onClick={() => navigate('/statutory')} className="text-xs text-gold hover:underline">Check applicability →</button>
              </div>
              <p className="md:col-span-2 text-xs text-gray-500">Statutory scope: tests that bear on the financial statements or a statutory report (CARO, tax audit, GST/TDS/MSME/PF, SA 240 / 501 / 550). Control-only tests join when IFC reporting applies; purely operational tests stay in Internal audits.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <label className="text-sm text-gray-400">Period from<input type="date" required value={from} onChange={e => setFrom(e.target.value)} className="input-field mt-1" /></label>
              <label className="text-sm text-gray-400">Period to<input type="date" required value={to} onChange={e => setTo(e.target.value)} className="input-field mt-1" /></label>
              <label className="text-sm text-gray-400">Reporting threshold (₹, optional)
                <input type="number" min="0" value={materiality} onChange={e => setMateriality(e.target.value)} className="input-field mt-1" />
              </label>
              <p className="md:col-span-3 text-xs text-gray-500">Internal audit scope: every active rule, reported by process (Order to Cash, Procure to Pay, Record to Report, Payroll, Inventory, Treasury, Tax & Statutory) with risk rating, management response and action plan.</p>
            </div>
          )}
          <label className="block text-sm text-gray-400">Scope notes
            <textarea value={notes} onChange={e => setNotes(e.target.value)} rows={2} className="input-field mt-1" placeholder="optional" />
          </label>
          {error && <div className="text-sm text-red-400">{error}</div>}
          <div className="flex gap-2">
            <button type="submit" className="btn-primary text-sm">Create engagement</button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-ghost text-sm">Cancel</button>
          </div>
        </form>
      )}

      <JobStatus job={job} />

      <div className="card p-0 overflow-hidden">
        <table className="w-full">
          <thead><tr>{['Engagement', 'Type', 'Period', 'Frame', 'Findings', 'Last run', ''].map(h => <th key={h} className="table-header text-left">{h}</th>)}</tr></thead>
          <tbody>
            {loading ? <tr><td colSpan={7} className="text-center py-10 text-gray-500">Loading…</td></tr>
              : rows.length === 0 ? <tr><td colSpan={7} className="text-center py-10 text-gray-500">No engagements yet — create a Statutory or Internal audit.</td></tr>
              : rows.map(e => (
                <tr key={e.id} className={`table-row ${selected?.id === e.id ? 'bg-gold/5' : ''}`}>
                  <td className="table-cell text-sm text-gray-200">{e.name}<div className="text-xs text-gray-500 capitalize">{e.status}</div></td>
                  <td className="table-cell text-sm">
                    <span className={e.audit_type === 'statutory' ? 'text-blue-300' : 'text-purple-300'}>{AUDIT_TYPE_LABEL[e.audit_type]}</span>
                  </td>
                  <td className="table-cell text-xs text-gray-400">{e.period_from} → {e.period_to}</td>
                  <td className="table-cell text-xs text-gray-400">
                    {e.audit_type === 'statutory'
                      ? [e.caro_applicable && 'CARO', e.ifc_applicable && 'IFC', e.tax_audit_applicable && '3CD'].filter(Boolean).join(' · ') || 'SA only'
                      : 'Process-wise'}
                    <div>{e.rules_in_scope} rules · {e.audit_type === 'statutory' ? 'materiality' : 'threshold'} {inr(e.materiality)}</div>
                  </td>
                  <td className="table-cell text-sm text-gray-300">{e.exception_count}</td>
                  <td className="table-cell text-xs text-gray-500">{e.last_run_at ? new Date(e.last_run_at).toLocaleString('en-IN') : 'never'}</td>
                  <td className="table-cell text-right whitespace-nowrap">
                    <button onClick={() => setEngagement({ id: e.id, label: e.label, audit_type: e.audit_type })} className="btn-ghost text-xs">Select</button>
                    <button onClick={() => run(e)} disabled={!!job && ['queued', 'running'].includes(job.status)}
                      className="btn-primary text-xs inline-flex items-center gap-1 disabled:opacity-50"><Play className="w-3 h-3" /> Run audit</button>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {summary && <EngagementSummary key={summary.engagement.id} s={summary} canManage={canManage} onChange={() => {
        load();
        window.dispatchEvent(new Event('cae:engagements-changed'));
        apiClient.get(`/engagements/${summary.engagement.id}/summary`).then(r => setSummary(r.data));
      }} />}
    </div>
  );
}

function EngagementSummary({ s, canManage, onChange }: { s: any; canManage: boolean; onChange: () => void }) {
  const e = s.engagement;
  const statutory = e.audit_type === 'statutory';
  const [mat, setMat] = useState(e.materiality ?? '');
  const save = async (patch: Record<string, unknown>) => {
    await apiClient.put(`/engagements/${e.id}`, patch);
    onChange();
  };
  return (
    <div className="space-y-4">
      <div className="card">
        <h2 className="text-sm font-semibold text-gold mb-3">{e.label} — results</h2>
        {canManage && (
          <div className="flex flex-wrap items-center gap-4 text-sm text-gray-300 mb-3">
            {statutory && ([['caro_applicable', 'CARO 2020'], ['ifc_applicable', 'IFC s.143(3)(i)'], ['tax_audit_applicable', 'Tax audit (3CD)']] as const).map(([k, label]) => (
              <label key={k} className="flex items-center gap-2">
                <input type="checkbox" checked={!!e[k]} onChange={ev => save({ [k]: ev.target.checked })} /> {label}
              </label>
            ))}
            <label className="flex items-center gap-2">{statutory ? 'Materiality ₹' : 'Threshold ₹'}
              <input type="number" min="0" value={mat} onChange={ev => setMat(ev.target.value)}
                onBlur={() => save({ materiality: mat === '' ? null : Number(mat) })} className="input-field py-1 w-36" />
            </label>
            <label className="flex items-center gap-2">Status
              <select value={e.status} onChange={ev => save({ status: ev.target.value })} className="bg-navy-700 border border-navy-border rounded px-2 py-1 text-sm">
                {['planning', 'fieldwork', 'reporting', 'closed'].map(st => <option key={st} value={st}>{st}</option>)}
              </select>
            </label>
            {statutory && <span className="text-xs text-gray-500">Scope changes apply on the next Run audit.</span>}
          </div>
        )}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
          <Stat label="Findings" value={s.total_findings} />
          <Stat label="Critical / High" value={`${s.by_severity.critical || 0} / ${s.by_severity.high || 0}`} />
          <Stat label="Medium / Low" value={`${s.by_severity.medium || 0} / ${s.by_severity.low || 0}`} />
          <Stat label="Financial impact" value={inr(s.total_financial_impact)} />
          <Stat label={statutory ? '≥ materiality' : '≥ threshold'} value={e.materiality ? s.material_findings : 'not set'} />
        </div>
      </div>
      {statutory && s.reporting_matrix?.length > 0 && (
        <div className="card p-0 overflow-hidden">
          <div className="px-4 py-3 text-sm font-semibold text-gray-200">Statutory reporting matrix</div>
          <table className="w-full">
            <thead><tr>{['Frame', 'Clause', 'Requirement', 'Findings', 'Impact', 'Draft position'].map(h => <th key={h} className="table-header text-left">{h}</th>)}</tr></thead>
            <tbody>{s.reporting_matrix.map((m: any) => (
              <tr key={m.frame + m.clause} className="table-row">
                <td className="table-cell text-xs text-gray-400">{m.frame.split(' (')[0]}</td>
                <td className="table-cell text-sm text-gray-200 whitespace-nowrap">{m.clause}</td>
                <td className="table-cell text-xs text-gray-400">{m.title}</td>
                <td className={`table-cell text-sm ${m.findings ? 'text-orange-300 font-semibold' : 'text-gray-500'}`}>{m.findings}</td>
                <td className="table-cell text-xs text-gray-400">{inr(m.financial_impact)}</td>
                <td className="table-cell text-xs text-gray-400">{m.draft_position}</td>
              </tr>))}
            </tbody>
          </table>
        </div>
      )}
      {statutory && s.ifc_deficiencies && (
        <div className="card p-0 overflow-hidden">
          <div className="px-4 py-3 text-sm font-semibold text-gray-200">IFC — control exceptions to evaluate</div>
          <table className="w-full"><thead><tr>{['Rule', 'Control tested', 'Exceptions', 'Impact', 'Classification'].map(h => <th key={h} className="table-header text-left">{h}</th>)}</tr></thead>
            <tbody>{s.ifc_deficiencies.length === 0 ? <tr><td colSpan={5} className="table-cell text-gray-500 text-sm">No control exceptions from CAE tests.</td></tr>
              : s.ifc_deficiencies.map((d: any) => (
                <tr key={d.rule_code} className="table-row"><td className="table-cell text-xs font-mono">{d.rule_code}</td><td className="table-cell text-sm">{d.rule_name}</td>
                  <td className="table-cell text-sm">{d.findings}</td><td className="table-cell text-xs">{inr(d.financial_impact)}</td><td className="table-cell text-xs text-gray-400">{d.classification}</td></tr>))}
            </tbody></table>
        </div>
      )}
      {!statutory && s.by_process && (
        <div className="card p-0 overflow-hidden">
          <div className="px-4 py-3 text-sm font-semibold text-gray-200">Observations by process</div>
          <table className="w-full"><thead><tr>{['Process', 'Observations', 'High', 'Medium', 'Low', 'Open', 'Impact'].map(h => <th key={h} className="table-header text-left">{h}</th>)}</tr></thead>
            <tbody>{s.by_process.map((p: any) => (
              <tr key={p.process} className="table-row"><td className="table-cell text-sm text-gray-200">{p.process}</td><td className="table-cell text-sm">{p.findings}</td>
                <td className="table-cell text-sm text-red-300">{p.high}</td><td className="table-cell text-sm text-yellow-300">{p.medium}</td><td className="table-cell text-sm text-green-300">{p.low}</td>
                <td className="table-cell text-sm">{p.open}</td><td className="table-cell text-xs">{inr(p.financial_impact)}</td></tr>))}
            </tbody></table>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: any }) {
  return <div className="bg-navy-700/50 rounded-md px-3 py-2"><div className="text-xs text-gray-500 uppercase">{label}</div><div className="text-lg font-semibold text-white">{value}</div></div>;
}
