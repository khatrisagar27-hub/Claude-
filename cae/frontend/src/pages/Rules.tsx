import { useEffect, useState } from 'react';
import { Toggle } from 'lucide-react';
import apiClient from '../api/client';
import SeverityBadge from '../components/common/SeverityBadge';
import type { AuditRule } from '../types';

export default function Rules() {
  const [rules, setRules] = useState<AuditRule[]>([]);
  const [area, setArea] = useState('');
  const [loading, setLoading] = useState(true);

  const areas = ['Sales', 'Purchase', 'Inventory', 'Journal Entry', 'Payroll', 'Treasury', 'GST'];

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (area) params.set('business_area', area);
    apiClient.get(`/rules?${params}`).then(r => setRules(r.data)).finally(() => setLoading(false));
  }, [area]);

  const toggleRule = async (ruleId: string) => {
    await apiClient.put(`/rules/${ruleId}/toggle`);
    setRules(rs => rs.map(r => r.id === ruleId ? { ...r, is_enabled: !r.is_enabled } : r));
  };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-white">Audit Rule Library</h1>
        <p className="text-sm text-gray-500">{rules.length} rules loaded</p>
      </div>

      <div className="card flex items-center gap-3 flex-wrap">
        <button onClick={() => setArea('')}
          className={`px-3 py-1.5 rounded text-xs font-medium ${!area ? 'bg-gold text-navy-900' : 'bg-navy-700 text-gray-400 hover:text-gray-200'}`}>
          All
        </button>
        {areas.map(a => (
          <button key={a} onClick={() => setArea(a)}
            className={`px-3 py-1.5 rounded text-xs font-medium ${area === a ? 'bg-gold text-navy-900' : 'bg-navy-700 text-gray-400 hover:text-gray-200'}`}>
            {a}
          </button>
        ))}
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr>
              {['Rule Code', 'Name', 'Business Area', 'Severity', 'Frequency', 'Enabled'].map(h => (
                <th key={h} className="table-header text-left">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="text-center py-12 text-gray-500">Loading…</td></tr>
            ) : rules.map(rule => (
              <tr key={rule.id} className="table-row">
                <td className="table-cell font-mono text-gold text-xs">{rule.rule_code}</td>
                <td className="table-cell text-gray-300 max-w-xs">
                  <p className="truncate">{rule.name}</p>
                </td>
                <td className="table-cell text-gray-400 text-xs">{rule.business_area}</td>
                <td className="table-cell"><SeverityBadge severity={rule.severity} /></td>
                <td className="table-cell text-gray-500 text-xs capitalize">{rule.frequency}</td>
                <td className="table-cell">
                  <button
                    onClick={() => toggleRule(rule.id)}
                    className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${rule.is_enabled ? 'bg-green-600' : 'bg-navy-600'}`}
                  >
                    <span className={`inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform ${rule.is_enabled ? 'translate-x-4' : 'translate-x-1'}`} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
