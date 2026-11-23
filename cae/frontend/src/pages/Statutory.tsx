import { useState } from 'react';
import { CheckCircle2, XCircle, Dices, Info } from 'lucide-react';
import apiClient from '../api/client';
import { useAuthStore } from '../store/authStore';
import AmountDisplay, { formatINRExact } from '../components/common/AmountDisplay';

// Every figure on this page comes from /statutory (app/statutory/*). Nothing here is computed client-side.

interface Test { applies: boolean; reasons: string[] }

interface ApplicabilityOut {
  balance_sheet_date: string;
  inputs: { preceding_year_turnover: number; total_revenue: number; latest_audited_turnover: number; sources: Record<string, string> };
  small_company: Test;
  caro_2020: Test;
  ifc_reporting_143_3_i: Test;
  e_invoicing: Test;
  irp_30_day_reporting_limit: Test;
  electronic_payment_facility: Test;
  note: string;
}

interface MsmeBill {
  vendor: string;
  msme_status: string;
  invoice_number: string;
  invoice_date: string;
  principal: number;
  paid_on: string | null;
  appointed_day: string;
  credit_days_applied: number;
  end_date: string;
  delay_days: number;
  bank_rate: number;
  rate_pa: number;
  interest: number;
}

interface MsmeOut {
  as_on: string;
  bills: MsmeBill[];
  total_interest_s16: number;
  unpaid_beyond_s15_limit: number;
  disallowance_ref: string;
  s43bh?: {
    financial_year: string; this_year: number; this_year_bills: number; within_limit_at_year_end: number;
    within_limit_bills: number; earlier_years_unpaid: number; before_provision_unpaid: number;
  };
  notes: string[];
}

interface SampleItem { id: string; reference: string; date: string | null; amount: number; stratum: 'key_item' | 'random' }

interface SampleOut {
  population_source: string;
  filters: { from: string | null; to: string | null };
  method: string;
  seed: number;
  high_value_threshold: number;
  population_count: number;
  population_value: number;
  key_items: number;
  random_items: number;
  selected_value: number;
  value_coverage_pct: number;
  sample: SampleItem[];
}

interface Clause44Out {
  financial_year: string;
  basis: string;
  col2_total_expenditure: number;
  col3_exempt: number;
  col4_composition: number;
  col5_other_registered: number;
  col6_total_registered: number;
  col7_unregistered: number;
  unattributed: number;
  working_79_4: Record<string, number>;
  balance_for_clause_44: number;
  tie_out_difference: number;
  vendor_table_79_20: { gstin: string; vendor: string; amount: number; column: string }[];
  remarks: string[];
}

type Tab = 'applicability' | 'msme' | 'sample' | 'clause44';

const TABS: { key: Tab; label: string }[] = [
  { key: 'applicability', label: 'Applicability' },
  { key: 'msme', label: 'MSME interest' },
  { key: 'sample', label: 'SA 530 sample' },
  { key: 'clause44', label: 'Clause 44 (3CD)' },
];

const errText = (err: any, fallback: string) => {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map((d: any) => `${(d.loc || []).slice(1).join('.')}: ${d.msg}`).join('; ');
  return fallback;
};

const Amt = ({ v, className = '' }: { v?: number | null; className?: string }) =>
  <AmountDisplay amount={v} exact className={className} />;

function Field({ label, children, hint }: { label: string; children: React.ReactNode; hint?: React.ReactNode }) {
  return (
    <label className="text-xs text-gray-400 space-y-1 block">
      <span>{label}</span>
      {children}
      {hint && <span className="block text-[10px] text-gray-600 font-mono">{hint}</span>}
    </label>
  );
}

function ErrorLine({ msg }: { msg: string | null }) {
  return msg ? <div className="card text-sm text-red-400">{msg}</div> : null;
}

// ---------------------------------------------------------------- Applicability

const APPLICABILITY_TESTS: { key: keyof ApplicabilityOut; label: string }[] = [
  { key: 'small_company', label: 'Small company — s.2(85) Companies Act' },
  { key: 'caro_2020', label: 'CARO 2020' },
  { key: 'ifc_reporting_143_3_i', label: 'IFC reporting — s.143(3)(i)' },
  { key: 'e_invoicing', label: 'E-invoicing — Rule 48(4) CGST Rules' },
  { key: 'irp_30_day_reporting_limit', label: 'IRP 30-day reporting limit' },
  { key: 'electronic_payment_facility', label: 'Electronic payment facility (Income-tax)' },
];

const MONEY_FIELDS = [
  { key: 'paid_up_capital', label: 'Paid-up capital (₹) *', required: true },
  { key: 'reserves_and_surplus', label: 'Reserves and surplus (₹)' },
  { key: 'peak_bank_borrowings', label: 'Peak bank / FI borrowings (₹)' },
  { key: 'peak_total_borrowings', label: 'Peak total borrowings (₹)' },
  { key: 'preceding_year_turnover', label: 'Preceding-year turnover (₹)', books: true },
  { key: 'total_revenue', label: 'Total revenue — ops + other income (₹)', books: true },
  { key: 'latest_audited_turnover', label: 'Latest audited turnover (₹)', books: true },
] as const;

const FLAGS = [
  { key: 'is_holding', label: 'Holding company' },
  { key: 'is_subsidiary', label: 'Subsidiary company' },
  { key: 'is_subsidiary_or_holding_of_public', label: 'Holding / subsidiary of a public company' },
  { key: 'governed_by_special_act', label: 'Governed by a special Act' },
  { key: 'filing_default', label: 'Default in filing financial statements / annual return' },
] as const;

function Applicability({ companyId }: { companyId: string }) {
  const [bsDate, setBsDate] = useState('2026-03-31');
  const [companyType, setCompanyType] = useState('private');
  const [money, setMoney] = useState<Record<string, string>>({ paid_up_capital: '' });
  const [flags, setFlags] = useState<Record<string, boolean>>({});
  const [result, setResult] = useState<ApplicabilityOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const body: Record<string, unknown> = { company_id: companyId, balance_sheet_date: bsDate, company_type: companyType, ...flags };
    for (const f of MONEY_FIELDS) {
      // blank turnover fields are omitted so the backend falls back to the books
      if (money[f.key] !== undefined && money[f.key] !== '') body[f.key] = Number(money[f.key]);
    }
    try {
      const r = await apiClient.post('/statutory/applicability', body);
      setResult(r.data);
    } catch (err) {
      setResult(null);
      setError(errText(err, 'Applicability check failed'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      <form onSubmit={submit} className="card space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <Field label="Balance sheet date *">
            <input type="date" required value={bsDate} onChange={e => setBsDate(e.target.value)} className="input-field" />
          </Field>
          <Field label="Company type">
            <select value={companyType} onChange={e => setCompanyType(e.target.value)} className="input-field">
              {['private', 'public', 'opc', 'section8', 'banking', 'insurance'].map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </Field>
          {MONEY_FIELDS.map(f => (
            <Field key={f.key} label={f.label}
              hint={money[f.key] ? formatINRExact(Number(money[f.key])) : ('books' in f ? 'blank = from books' : undefined)}>
              <input type="number" min="0" step="0.01" required={'required' in f}
                value={money[f.key] ?? ''} onChange={e => setMoney(m => ({ ...m, [f.key]: e.target.value }))}
                placeholder={'books' in f ? 'From books' : '0'} className="input-field" />
            </Field>
          ))}
        </div>
        <div className="flex flex-wrap gap-x-6 gap-y-2">
          {FLAGS.map(f => (
            <label key={f.key} className="flex items-center gap-2 text-xs text-gray-300">
              <input type="checkbox" checked={!!flags[f.key]} onChange={e => setFlags(s => ({ ...s, [f.key]: e.target.checked }))}
                className="accent-[#C8A951]" />
              {f.label}
            </label>
          ))}
        </div>
        <button type="submit" disabled={busy} className="btn-primary text-sm disabled:opacity-50">
          {busy ? 'Checking…' : 'Check applicability'}
        </button>
      </form>

      <ErrorLine msg={error} />

      {result && (
        <>
          <div className="card">
            <div className="text-xs text-gray-500 uppercase mb-2">Inputs used — balance sheet date {result.balance_sheet_date}</div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {(['preceding_year_turnover', 'total_revenue', 'latest_audited_turnover'] as const).map(k => (
                <div key={k}>
                  <div className="text-xs text-gray-400">{k.replace(/_/g, ' ')}</div>
                  <Amt v={result.inputs[k]} className="text-sm font-semibold text-white" />
                  <div className={`text-[10px] ${result.inputs.sources[k] === 'supplied' ? 'text-gray-500' : 'text-yellow-500'}`}>
                    {result.inputs.sources[k]}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {APPLICABILITY_TESTS.map(({ key, label }) => {
              const t = result[key] as Test;
              return (
                <div key={key} className={`card border-l-4 ${t.applies ? 'border-l-gold' : 'border-l-navy-600'}`}>
                  <div className="flex items-center justify-between gap-2">
                    <div className="text-sm font-semibold text-white">{label}</div>
                    <span className={`flex items-center gap-1 text-xs font-semibold ${t.applies ? 'text-gold' : 'text-gray-500'}`}>
                      {t.applies ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                      {t.applies ? 'Applies' : 'Does not apply'}
                    </span>
                  </div>
                  <ul className="mt-2 space-y-1 list-disc list-inside text-xs text-gray-400">
                    {t.reasons.map((r, i) => <li key={i}>{r}</li>)}
                  </ul>
                </div>
              );
            })}
          </div>
          <p className="text-xs text-yellow-500 flex items-center gap-1.5"><Info className="w-3.5 h-3.5" />{result.note}</p>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------- MSME interest

function MsmeInterest({ companyId }: { companyId: string }) {
  const [asOn, setAsOn] = useState('');
  const [result, setResult] = useState<MsmeOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const params = new URLSearchParams({ company_id: companyId });
    if (asOn) params.set('as_on', asOn);
    try {
      const r = await apiClient.get(`/statutory/msme-interest?${params}`);
      setResult(r.data);
    } catch (err) {
      setResult(null);
      setError(errText(err, 'Could not compute MSME interest'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      <form onSubmit={load} className="card flex flex-wrap items-end gap-3">
        <Field label="As on (blank = latest purchase invoice date)">
          <input type="date" value={asOn} onChange={e => setAsOn(e.target.value)} className="input-field w-56" />
        </Field>
        <button type="submit" disabled={busy} className="btn-primary text-sm disabled:opacity-50">
          {busy ? 'Computing…' : 'Compute s.16 interest'}
        </button>
        <p className="text-xs text-gray-500 basis-full">
          Micro and small suppliers only. Interest u/s 16 MSMED at three times the RBI bank rate, compounded
          monthly, from the appointed day; bills paid within the s.15 limit are not listed.
        </p>
      </form>

      <ErrorLine msg={error} />

      {result && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="card">
              <div className="text-xs text-gray-500 uppercase">Interest u/s 16 MSMED</div>
              <Amt v={result.total_interest_s16} className="text-xl font-bold text-red-400 block mt-1" />
              <div className="text-xs text-gray-600 mt-0.5">as on {result.as_on} · {result.bills.length} delayed bills</div>
            </div>
            <div className="card">
              <div className="text-xs text-gray-500 uppercase">Unpaid beyond the s.15 limit (all years)</div>
              <Amt v={result.unpaid_beyond_s15_limit} className="text-xl font-bold text-yellow-400 block mt-1" />
              <div className="text-xs text-gray-600 mt-0.5">Principal incl. GST — the MSME dues to disclose</div>
            </div>
            {result.s43bh && (
              <div className="card">
                <div className="text-xs text-gray-500 uppercase">{result.disallowance_ref} — FY {result.s43bh.financial_year}</div>
                <Amt v={result.s43bh.this_year} className="text-xl font-bold text-orange-400 block mt-1" />
                <div className="text-xs text-gray-500 mt-0.5 space-y-0.5">
                  <div>{result.s43bh.this_year_bills} bills of this year unpaid at year-end past the limit (expense value)</div>
                  <div>Watch — within limit at year-end: <Amt v={result.s43bh.within_limit_at_year_end} /> ({result.s43bh.within_limit_bills} bills, allowed only if paid in time)</div>
                  <div>Earlier years' bills still unpaid: <Amt v={result.s43bh.earlier_years_unpaid} /> (disallowed in their own year; deductible when paid)</div>
                  <div>Bills before 01-04-2023: <Amt v={result.s43bh.before_provision_unpaid} /> (s.43B(h) not applicable)</div>
                </div>
              </div>
            )}
            <div className="card text-xs text-gray-400 space-y-1">
              {result.notes.map((n, i) => <p key={i}>{n}</p>)}
            </div>
          </div>
          <div className="card p-0 overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr>
                  {['Supplier', 'Status', 'Invoice', 'Inv. date', 'Principal', 'Credit days', 'Appointed day', 'Paid / as on', 'Delay', 'Rate p.a.', 'Interest'].map(h => (
                    <th key={h} className="table-header text-left whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result.bills.length === 0 ? (
                  <tr><td colSpan={11} className="text-center py-8 text-gray-600">No micro / small supplier bill is beyond the s.15 limit.</td></tr>
                ) : result.bills.map((b, i) => (
                  <tr key={`${b.invoice_number}-${i}`} className="table-row">
                    <td className="table-cell max-w-[14rem] truncate" title={b.vendor}>{b.vendor}</td>
                    <td className="table-cell text-xs capitalize text-gray-400">{b.msme_status}</td>
                    <td className="table-cell font-mono text-gold">{b.invoice_number}</td>
                    <td className="table-cell text-gray-400 whitespace-nowrap">{b.invoice_date}</td>
                    <td className="table-cell"><Amt v={b.principal} /></td>
                    <td className="table-cell font-mono text-gray-400">{b.credit_days_applied}</td>
                    <td className="table-cell text-gray-400 whitespace-nowrap">{b.appointed_day}</td>
                    <td className="table-cell whitespace-nowrap">
                      {b.end_date}{' '}
                      <span className={`text-[10px] ${b.paid_on ? 'text-green-500' : 'text-red-400'}`}>{b.paid_on ? 'paid' : 'unpaid'}</span>
                    </td>
                    <td className="table-cell font-mono">{b.delay_days}d</td>
                    <td className="table-cell font-mono text-gray-400">{b.rate_pa}%</td>
                    <td className="table-cell font-semibold"><Amt v={b.interest} className="text-red-400" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------- SA 530 sample

const POPULATIONS = [
  { value: 'purchase_invoices', label: 'Purchase invoices' },
  { value: 'sales_invoices', label: 'Sales invoices' },
  { value: 'journal_entries', label: 'Journal entries' },
  { value: 'exceptions', label: 'Audit exceptions' },
];

function Sample({ companyId }: { companyId: string }) {
  const [population, setPopulation] = useState('purchase_invoices');
  const [seed, setSeed] = useState('');
  const [n, setN] = useState('25');
  const [threshold, setThreshold] = useState('0');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [result, setResult] = useState<SampleOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const body: Record<string, unknown> = {
      company_id: companyId, population, seed: Number(seed), n: Number(n), high_value_threshold: Number(threshold || 0),
    };
    if (dateFrom) body.date_from = dateFrom;
    if (dateTo) body.date_to = dateTo;
    try {
      const r = await apiClient.post('/statutory/sample', body);
      setResult(r.data);
    } catch (err) {
      setResult(null);
      setError(errText(err, 'Sampling failed'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      <form onSubmit={submit} className="card space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <Field label="Population">
            <select value={population} onChange={e => setPopulation(e.target.value)} className="input-field">
              {POPULATIONS.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
            </select>
          </Field>
          <Field label="Seed * (record in the working paper)">
            <div className="flex gap-1">
              <input type="number" required step="1" value={seed} onChange={e => setSeed(e.target.value)} className="input-field" />
              <button type="button" title="Pick a seed" onClick={() => setSeed(String(Math.floor(Math.random() * 1_000_000)))}
                className="btn-ghost border border-navy-border px-2"><Dices className="w-4 h-4" /></button>
            </div>
          </Field>
          <Field label="Random items (n)">
            <input type="number" min="0" max="1000" step="1" value={n} onChange={e => setN(e.target.value)} className="input-field" />
          </Field>
          <Field label="Key-item threshold (₹, 0 = none)" hint={Number(threshold) > 0 ? formatINRExact(Number(threshold)) : undefined}>
            <input type="number" min="0" step="0.01" value={threshold} onChange={e => setThreshold(e.target.value)} className="input-field" />
          </Field>
          <Field label="Date from">
            <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} className="input-field" />
          </Field>
          <Field label="Date to">
            <input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} className="input-field" />
          </Field>
        </div>
        <button type="submit" disabled={busy || seed === ''} className="btn-primary text-sm disabled:opacity-50">
          {busy ? 'Selecting…' : 'Select sample'}
        </button>
      </form>

      <ErrorLine msg={error} />

      {result && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="card border-2 border-gold/60 bg-gold/5">
              <div className="text-xs text-gold uppercase tracking-wider">Seed</div>
              <div className="text-4xl font-bold font-mono text-gold mt-1">{result.seed}</div>
              <p className="text-xs text-gray-400 mt-2">
                Record this seed with the population and filters in the working paper. The same inputs always
                return the same sample, so a reviewer can re-perform the selection.
              </p>
            </div>
            <div className="card lg:col-span-2 grid grid-cols-2 md:grid-cols-3 gap-3 text-xs">
              <div className="col-span-2 md:col-span-3 text-gray-400">{result.method}</div>
              <div><div className="text-gray-500">Population</div><div className="text-white font-semibold">{POPULATIONS.find(p => p.value === result.population_source)?.label} · {result.population_count}</div></div>
              <div><div className="text-gray-500">Population value</div><Amt v={result.population_value} className="text-white font-semibold" /></div>
              <div><div className="text-gray-500">Filters</div><div className="text-white">{result.filters.from || 'start'} → {result.filters.to || 'end'}</div></div>
              <div><div className="text-gray-500">Key items (100%)</div><div className="text-white font-semibold">{result.key_items} at ≥ <Amt v={result.high_value_threshold} /></div></div>
              <div><div className="text-gray-500">Random items</div><div className="text-white font-semibold">{result.random_items}</div></div>
              <div><div className="text-gray-500">Selected value · coverage</div><div className="text-white font-semibold"><Amt v={result.selected_value} /> · {result.value_coverage_pct}%</div></div>
            </div>
          </div>
          <div className="card p-0 overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr>{['#', 'Stratum', 'Reference', 'Date', 'Amount'].map(h => <th key={h} className="table-header text-left">{h}</th>)}</tr>
              </thead>
              <tbody>
                {result.sample.map((s, i) => (
                  <tr key={s.id} className="table-row">
                    <td className="table-cell text-gray-500 font-mono">{i + 1}</td>
                    <td className="table-cell">
                      <span className={`text-xs px-2 py-0.5 rounded ${s.stratum === 'key_item' ? 'bg-gold/15 text-gold' : 'bg-navy-700 text-gray-400'}`}>
                        {s.stratum === 'key_item' ? 'Key item' : 'Random'}
                      </span>
                    </td>
                    <td className="table-cell font-mono text-gray-200 max-w-md truncate" title={s.reference}>{s.reference}</td>
                    <td className="table-cell text-gray-400">{s.date || '—'}</td>
                    <td className="table-cell"><Amt v={s.amount} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------- Clause 44

const COLUMNS: { key: keyof Clause44Out; label: string; strong?: boolean }[] = [
  { key: 'col2_total_expenditure', label: 'Col 2 — Total expenditure', strong: true },
  { key: 'col3_exempt', label: 'Col 3 — Registered: exempt goods / services' },
  { key: 'col4_composition', label: 'Col 4 — Registered: composition dealers' },
  { key: 'col5_other_registered', label: 'Col 5 — Other registered entities' },
  { key: 'col6_total_registered', label: 'Col 6 — Total registered (3 + 4 + 5)', strong: true },
  { key: 'col7_unregistered', label: 'Col 7 — Unregistered entities' },
  { key: 'unattributed', label: 'Unattributed — no party in the data' },
];

function Clause44({ companyId }: { companyId: string }) {
  const today = new Date();
  const lastClosedFy = (today.getMonth() >= 3 ? today.getFullYear() : today.getFullYear() - 1) - 1;
  const [fy, setFy] = useState(String(lastClosedFy));
  const [result, setResult] = useState<Clause44Out | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const r = await apiClient.get(`/statutory/clause44?company_id=${companyId}&fy=${fy}`);
      setResult(r.data);
    } catch (err) {
      setResult(null);
      setError(errText(err, 'Could not build the clause 44 draft'));
    } finally {
      setBusy(false);
    }
  };

  const fyOptions = Array.from({ length: 6 }, (_, i) => lastClosedFy + 1 - i);

  return (
    <div className="space-y-4">
      <form onSubmit={load} className="card flex flex-wrap items-end gap-3">
        <Field label="Financial year">
          <select value={fy} onChange={e => setFy(e.target.value)} className="input-field w-40">
            {fyOptions.map(y => <option key={y} value={y}>FY {y}-{String(y + 1).slice(-2)}</option>)}
          </select>
        </Field>
        <button type="submit" disabled={busy} className="btn-primary text-sm disabled:opacity-50">
          {busy ? 'Building…' : 'Build clause 44 draft'}
        </button>
      </form>

      <ErrorLine msg={error} />

      {result && (
        <>
          <div className="text-xs text-gray-500">FY {result.financial_year} · {result.basis}</div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="card p-0 overflow-hidden">
              <div className="text-sm font-semibold text-white px-4 pt-4 pb-2">Clause 44 columns</div>
              <table className="w-full">
                <tbody>
                  {COLUMNS.map(c => (
                    <tr key={c.key} className="table-row">
                      <td className={`table-cell ${c.strong ? 'text-white font-semibold' : ''} ${c.key === 'unattributed' && result.unattributed ? 'text-yellow-400' : ''}`}>{c.label}</td>
                      <td className="table-cell text-right"><Amt v={result[c.key] as number} className={c.strong ? 'font-semibold text-white' : ''} /></td>
                    </tr>
                  ))}
                  <tr className="table-row">
                    <td className="table-cell text-white font-semibold">Balance for clause 44 (GN 79.4)</td>
                    <td className="table-cell text-right"><Amt v={result.balance_for_clause_44} className="font-semibold text-white" /></td>
                  </tr>
                  <tr>
                    <td className="table-cell">Tie-out difference</td>
                    <td className="table-cell text-right">
                      <Amt v={result.tie_out_difference} className={result.tie_out_difference === 0 ? 'text-green-400' : 'text-red-400 font-semibold'} />
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div className="card p-0 overflow-hidden">
              <div className="text-sm font-semibold text-white px-4 pt-4 pb-2">GN 79.4 working</div>
              <table className="w-full">
                <tbody>
                  {Object.entries(result.working_79_4)
                    .sort(([a], [b]) => Number(a.startsWith('less_')) - Number(b.startsWith('less_')))
                    .map(([k, v]) => (
                    <tr key={k} className="table-row">
                      <td className="table-cell">{k.replace(/^less_/, 'Less: ').replace(/_/g, ' ')}</td>
                      <td className="table-cell text-right"><Amt v={v} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <ul className="p-4 space-y-1 list-disc list-inside text-xs text-yellow-500/90">
                {result.remarks.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          </div>
          <div className="card p-0 overflow-x-auto">
            <div className="text-sm font-semibold text-white px-4 pt-4 pb-2">GN 79.20 vendor table · {result.vendor_table_79_20.length} parties</div>
            <table className="w-full">
              <thead>
                <tr>{['GSTIN', 'Vendor', 'Column', 'Amount'].map(h => <th key={h} className="table-header text-left">{h}</th>)}</tr>
              </thead>
              <tbody>
                {result.vendor_table_79_20.length === 0 ? (
                  <tr><td colSpan={4} className="text-center py-8 text-gray-600">No party-attributed expenditure for this year.</td></tr>
                ) : result.vendor_table_79_20.map((v, i) => (
                  <tr key={`${v.gstin}-${i}`} className="table-row">
                    <td className="table-cell font-mono text-xs">{v.gstin}</td>
                    <td className="table-cell">{v.vendor || '—'}</td>
                    <td className="table-cell text-xs text-gray-400">{v.column.replace(/_/g, ' ')}</td>
                    <td className="table-cell"><Amt v={v.amount} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------- Page

export default function Statutory() {
  const { companyId } = useAuthStore();
  const [tab, setTab] = useState<Tab>('applicability');

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-white">Statutory</h1>
        <p className="text-sm text-gray-500">
          Deterministic statutory computations — each result names the provisions and inputs used, staged for the auditor's review
        </p>
      </div>

      <div className="card flex items-center gap-2 flex-wrap">
        {TABS.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`px-3 py-1.5 rounded text-xs font-medium ${tab === t.key ? 'bg-gold text-navy-900' : 'bg-navy-700 text-gray-400 hover:text-gray-200'}`}>
            {t.label}
          </button>
        ))}
      </div>

      {!companyId ? (
        <div className="card text-center py-12 text-gray-500">No company selected.</div>
      ) : tab === 'applicability' ? <Applicability companyId={companyId} />
        : tab === 'msme' ? <MsmeInterest companyId={companyId} />
        : tab === 'sample' ? <Sample companyId={companyId} />
        : <Clause44 companyId={companyId} />}
    </div>
  );
}
