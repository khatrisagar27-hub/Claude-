import { Fragment, useEffect, useState } from 'react';
import { RefreshCw, SlidersHorizontal, Plus, X } from 'lucide-react';
import apiClient from '../api/client';
import { useAuthStore } from '../store/authStore';
import SeverityBadge from '../components/common/SeverityBadge';
import type { AuditRule } from '../types';

// business_area is the catalogue category (app/rules/catalogue.py)
const AREAS = [
  { value: 'revenue', label: 'Revenue' },
  { value: 'expenditure', label: 'Expenditure' },
  { value: 'inventory', label: 'Inventory' },
  { value: 'financial_reporting', label: 'Journals / Reporting' },
  { value: 'payroll', label: 'Payroll' },
  { value: 'bank_reconciliation', label: 'Bank / Treasury' },
  { value: 'related_party', label: 'Related Party' },
  { value: 'gst', label: 'GST' },
  { value: 'statutory', label: 'Statutory (Tax / MSME / PF)' },
];

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

const showValue = (v: unknown) => (typeof v === 'object' ? JSON.stringify(v) : String(v));

// A new key has no catalogue type to follow: numbers and booleans are read as such, anything else stays text
function parseLoose(raw: string): unknown {
  const t = raw.trim();
  if (t === 'true' || t === 'false') return t === 'true';
  if (t !== '' && !Number.isNaN(Number(t))) return Number(t);
  return t;
}

function ParamEditor({ rule, onSaved, onClose }: {
  rule: AuditRule;
  onSaved: (params: Record<string, unknown>) => void;
  onClose: () => void;
}) {
  const current = rule.parameters || {};
  const [draft, setDraft] = useState<Record<string, string | boolean>>(() =>
    Object.fromEntries(Object.entries(current).map(([k, v]) => [k, typeof v === 'boolean' ? v : showValue(v)])));
  const [newKey, setNewKey] = useState('');
  const [newValue, setNewValue] = useState('');
  const [added, setAdded] = useState<Record<string, unknown>>({});
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const addParam = () => {
    const k = newKey.trim();
    if (!k || k in draft || k in added) return;
    setAdded(a => ({ ...a, [k]: parseLoose(newValue) }));
    setNewKey('');
    setNewValue('');
  };

  const save = async () => {
    const changes: Record<string, unknown> = { ...added };
    for (const [k, orig] of Object.entries(current)) {
      const v = draft[k];
      let next: unknown = v;
      if (typeof orig === 'number') {
        next = Number(v);
        if (v === '' || Number.isNaN(next)) { setError(`${k} must be a number`); return; }
      } else if (typeof orig === 'object' && orig !== null) {
        try { next = JSON.parse(String(v)); } catch { setError(`${k} must be valid JSON`); return; }
      }
      if (showValue(next) !== showValue(orig)) changes[k] = next;
    }
    if (Object.keys(changes).length === 0) { onClose(); return; }
    setSaving(true);
    setError(null);
    try {
      const r = await apiClient.put(`/rules/${rule.id}/parameters`, { parameters: changes });
      onSaved(r.data.parameters);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Could not save parameters');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="bg-navy-900/60 border border-navy-border rounded-md p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="text-xs text-gray-400">
          Parameters for <span className="font-mono text-gold">{rule.rule_code}</span> — catalogue defaults are listed;
          saved values are merged into the rule and used from the next run.
        </div>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-200"><X className="w-4 h-4" /></button>
      </div>
      {Object.keys(current).length === 0 && Object.keys(added).length === 0 && (
        <p className="text-xs text-gray-600">This rule has no tunable parameters in the catalogue.</p>
      )}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {Object.entries(current).map(([k, orig]) => (
          <label key={k} className="text-xs text-gray-400 space-y-1 block">
            <span className="font-mono">{k}</span>
            {typeof orig === 'boolean' ? (
              <input type="checkbox" checked={draft[k] as boolean} onChange={e => setDraft(d => ({ ...d, [k]: e.target.checked }))}
                className="block accent-[#C8A951]" />
            ) : (
              <input type={typeof orig === 'number' ? 'number' : ISO_DATE.test(String(orig)) ? 'date' : 'text'}
                step="any" value={draft[k] as string} onChange={e => setDraft(d => ({ ...d, [k]: e.target.value }))}
                className="input-field font-mono text-sm" />
            )}
          </label>
        ))}
        {Object.entries(added).map(([k, v]) => (
          <div key={k} className="text-xs text-gray-400 space-y-1">
            <span className="font-mono text-green-400">{k} (new)</span>
            <div className="flex items-center gap-2">
              <span className="input-field font-mono text-sm">{showValue(v)}</span>
              <button onClick={() => setAdded(a => { const { [k]: _, ...rest } = a; return rest; })}
                className="text-gray-500 hover:text-red-400"><X className="w-4 h-4" /></button>
            </div>
          </div>
        ))}
      </div>
      <div className="flex flex-wrap items-end gap-2 pt-1 border-t border-navy-border">
        <label className="text-xs text-gray-400 space-y-1">
          <span>Add parameter</span>
          <input value={newKey} onChange={e => setNewKey(e.target.value)} placeholder="e.g. as_on" className="input-field font-mono text-sm w-40" />
        </label>
        <label className="text-xs text-gray-400 space-y-1">
          <span>Value</span>
          <input value={newValue} onChange={e => setNewValue(e.target.value)} placeholder="e.g. 2026-03-31" className="input-field font-mono text-sm w-40" />
        </label>
        <button onClick={addParam} disabled={!newKey.trim()} className="btn-ghost border border-navy-border text-xs flex items-center gap-1 disabled:opacity-50">
          <Plus className="w-3.5 h-3.5" /> Add
        </button>
        <span className="text-[10px] text-gray-600 basis-full">Ageing rules accept <span className="font-mono">as_on</span> (YYYY-MM-DD); default is the latest date in the data. Per-rule defaults: docs/rules.md.</span>
      </div>
      <div className="flex items-center gap-3">
        <button onClick={save} disabled={saving} className="btn-primary text-xs disabled:opacity-50">{saving ? 'Saving…' : 'Save parameters'}</button>
        <button onClick={onClose} className="btn-ghost text-xs">Cancel</button>
        {error && <span className="text-xs text-red-400">{error}</span>}
      </div>
    </div>
  );
}

export default function Rules() {
  const { companyId } = useAuthStore();
  const [rules, setRules] = useState<AuditRule[]>([]);
  const [area, setArea] = useState('');
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const load = () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (companyId) params.set('company_id', companyId);
    if (area) params.set('business_area', area);
    apiClient.get(`/rules?${params}`).then(r => setRules(r.data)).finally(() => setLoading(false));
  };

  useEffect(load, [area, companyId]);

  const toggleRule = async (ruleId: string) => {
    await apiClient.put(`/rules/${ruleId}/toggle`);
    setRules(rs => rs.map(r => r.id === ruleId ? { ...r, is_enabled: !r.is_enabled } : r));
  };

  const syncCatalogue = async () => {
    if (!companyId) return;
    setSyncing(true);
    setSyncMsg(null);
    try {
      const r = await apiClient.post(`/rules/sync?company_id=${companyId}`);
      setSyncMsg({ ok: true, text: `Catalogue of ${r.data.catalogue_size} rules synced — ${r.data.created} created, ${r.data.updated} updated. Your parameters and enable flags were kept.` });
      load();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setSyncMsg({ ok: false, text: typeof detail === 'string' ? detail : 'Catalogue sync failed' });
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Audit Rule Library</h1>
          <p className="text-sm text-gray-500">{rules.length} rules loaded</p>
        </div>
        <button onClick={syncCatalogue} disabled={syncing || !companyId}
          className="flex items-center gap-2 text-xs text-gray-400 hover:text-gold border border-gray-700 rounded px-3 py-1.5 disabled:opacity-50">
          <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
          Sync catalogue
        </button>
      </div>

      {syncMsg && (
        <div className={`card text-xs ${syncMsg.ok ? 'text-green-400' : 'text-red-400'}`}>{syncMsg.text}</div>
      )}

      <div className="card flex items-center gap-3 flex-wrap">
        <button onClick={() => setArea('')}
          className={`px-3 py-1.5 rounded text-xs font-medium ${!area ? 'bg-gold text-navy-900' : 'bg-navy-700 text-gray-400 hover:text-gray-200'}`}>
          All
        </button>
        {AREAS.map(a => (
          <button key={a.value} onClick={() => setArea(a.value)}
            className={`px-3 py-1.5 rounded text-xs font-medium ${area === a.value ? 'bg-gold text-navy-900' : 'bg-navy-700 text-gray-400 hover:text-gray-200'}`}>
            {a.label}
          </button>
        ))}
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr>
              {['Rule Code', 'Name', 'Business Area', 'Severity', 'Frequency', 'Parameters', 'Enabled'].map(h => (
                <th key={h} className="table-header text-left">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} className="text-center py-12 text-gray-500">Loading…</td></tr>
            ) : rules.map(rule => (
              <Fragment key={rule.id}>
                <tr className="table-row">
                  <td className="table-cell font-mono text-gold text-xs">{rule.rule_code}</td>
                  <td className="table-cell text-gray-300 max-w-xs">
                    <p className="truncate">{rule.name}</p>
                  </td>
                  <td className="table-cell text-gray-400 text-xs">{AREAS.find(a => a.value === rule.business_area)?.label || rule.business_area}</td>
                  <td className="table-cell"><SeverityBadge severity={rule.severity} /></td>
                  <td className="table-cell text-gray-500 text-xs capitalize">{rule.frequency}</td>
                  <td className="table-cell">
                    <button onClick={() => setEditing(editing === rule.id ? null : rule.id)}
                      className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gold max-w-[16rem]">
                      <SlidersHorizontal className="w-3.5 h-3.5 shrink-0" />
                      <span className="font-mono truncate">
                        {rule.parameters && Object.keys(rule.parameters).length
                          ? Object.entries(rule.parameters).map(([k, v]) => `${k}=${showValue(v)}`).join(' · ')
                          : 'none'}
                      </span>
                    </button>
                  </td>
                  <td className="table-cell">
                    <button
                      onClick={() => toggleRule(rule.id)}
                      className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${rule.is_enabled ? 'bg-green-600' : 'bg-navy-600'}`}
                    >
                      <span className={`inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform ${rule.is_enabled ? 'translate-x-4' : 'translate-x-1'}`} />
                    </button>
                  </td>
                </tr>
                {editing === rule.id && (
                  <tr className="border-b border-navy-border">
                    <td colSpan={7} className="px-4 py-3">
                      <ParamEditor rule={rule} onClose={() => setEditing(null)}
                        onSaved={params => {
                          setRules(rs => rs.map(r => r.id === rule.id ? { ...r, parameters: params } : r));
                          setEditing(null);
                        }} />
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
