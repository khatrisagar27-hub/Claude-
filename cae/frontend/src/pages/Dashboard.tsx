import { useEffect, useState } from 'react';
import { AlertTriangle, TrendingUp, FileText, CheckCircle, Activity, Shield } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import apiClient from '../api/client';
import { useAuthStore } from '../store/authStore';
import SeverityBadge from '../components/common/SeverityBadge';
import AmountDisplay from '../components/common/AmountDisplay';
import type { KPIs } from '../types';

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#DC2626',
  high: '#EA580C',
  medium: '#D97706',
  low: '#16A34A',
};

function KPICard({ title, value, sub, icon: Icon, accent = false }: {
  title: string; value: string | number; sub?: string; icon: any; accent?: boolean;
}) {
  return (
    <div className={`card flex items-start gap-4 ${accent ? 'border-gold/30 bg-gold/5' : ''}`}>
      <div className={`p-2 rounded-lg ${accent ? 'bg-gold/20' : 'bg-navy-700'}`}>
        <Icon className={`w-5 h-5 ${accent ? 'text-gold' : 'text-gray-400'}`} />
      </div>
      <div>
        <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">{title}</div>
        <div className="text-2xl font-bold text-white">{value}</div>
        {sub && <div className="text-xs text-gray-500 mt-0.5">{sub}</div>}
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { companyId } = useAuthStore();
  const [kpis, setKpis] = useState<KPIs | null>(null);
  const [topExceptions, setTopExceptions] = useState<any[]>([]);
  const [trend, setTrend] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!companyId) return;
    const cid = companyId;
    Promise.all([
      apiClient.get(`/dashboard/kpis?company_id=${cid}`),
      apiClient.get(`/dashboard/top-exceptions?company_id=${cid}&limit=8`),
      apiClient.get(`/dashboard/trend?company_id=${cid}&months=6`),
    ]).then(([k, t, tr]) => {
      setKpis(k.data);
      setTopExceptions(t.data);
      setTrend(tr.data);
    }).finally(() => setLoading(false));
  }, [companyId]);

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-2 border-gold/30 border-t-gold rounded-full animate-spin" />
    </div>
  );

  if (!companyId) return (
    <div className="text-center py-20 text-gray-500">
      No company selected. Please select a company to view the dashboard.
    </div>
  );

  const riskBandColor: Record<string, string> = {
    critical: 'text-red-400', high: 'text-orange-400',
    moderate: 'text-yellow-400', low: 'text-green-400',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Executive Dashboard</h1>
          <p className="text-sm text-gray-500 mt-0.5">Real-time audit risk intelligence</p>
        </div>
        <div className={`text-2xl font-bold font-mono ${riskBandColor[kpis?.risk_band || 'low']}`}>
          {kpis?.composite_risk_score?.toFixed(1)} <span className="text-sm font-normal uppercase">{kpis?.risk_band} risk</span>
        </div>
      </div>

      {/* KPI grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Total Exceptions"
          value={kpis?.total_exceptions ?? 0}
          sub={`${kpis?.resolved_this_month ?? 0} resolved this month`}
          icon={AlertTriangle}
          accent
        />
        <KPICard
          title="Critical Issues"
          value={kpis?.critical ?? 0}
          sub={`${kpis?.high ?? 0} High | ${kpis?.medium ?? 0} Medium`}
          icon={Activity}
        />
        <KPICard
          title="Open Queries"
          value={kpis?.open_queries ?? 0}
          sub={`${kpis?.overdue_queries ?? 0} overdue`}
          icon={FileText}
        />
        <KPICard
          title="Fraud Indicators"
          value={kpis?.fraud_indicators ?? 0}
          sub={`GST Risk: ₹${((kpis?.gst_risk_amount ?? 0) / 100000).toFixed(1)}L`}
          icon={Shield}
        />
      </div>

      {/* Charts + Top exceptions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trend chart */}
        <div className="lg:col-span-2 card">
          <h2 className="text-sm font-semibold text-gray-300 mb-4 uppercase tracking-wider">Exception Trend (6 months)</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={trend} barSize={8} barGap={2}>
              <XAxis dataKey="period" stroke="#4B5563" tick={{ fill: '#6B7280', fontSize: 11 }} />
              <YAxis stroke="#4B5563" tick={{ fill: '#6B7280', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: '#161B22', border: '1px solid #30363D', borderRadius: 6 }}
                labelStyle={{ color: '#E5E7EB' }}
              />
              {['critical', 'high', 'medium', 'low'].map(s => (
                <Bar key={s} dataKey={s} stackId="a" fill={SEVERITY_COLORS[s]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Top exceptions */}
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-300 mb-4 uppercase tracking-wider">Top Exceptions</h2>
          <div className="space-y-3">
            {topExceptions.slice(0, 6).map(exc => (
              <div key={exc.id} className="flex items-start gap-2">
                <SeverityBadge severity={exc.severity} />
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-gray-300 truncate">{exc.title}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-xs text-gray-600">{exc.business_area}</span>
                    {exc.financial_impact && (
                      <AmountDisplay amount={exc.financial_impact} className="text-xs text-gray-500" />
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Severity breakdown */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'Critical', value: kpis?.critical ?? 0, color: 'border-red-800/50 bg-red-900/10' },
          { label: 'High', value: kpis?.high ?? 0, color: 'border-orange-800/50 bg-orange-900/10' },
          { label: 'Medium', value: kpis?.medium ?? 0, color: 'border-yellow-800/50 bg-yellow-900/10' },
          { label: 'Low', value: kpis?.low ?? 0, color: 'border-green-800/50 bg-green-900/10' },
        ].map(({ label, value, color }) => (
          <div key={label} className={`border rounded-lg p-3 ${color}`}>
            <div className="text-xs text-gray-500 uppercase tracking-wider">{label}</div>
            <div className="text-3xl font-bold text-white mt-1">{value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
