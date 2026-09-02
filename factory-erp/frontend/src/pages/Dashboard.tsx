import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { client } from "../api/client";
import { DowntimeReasonTotal, OEEResult, ProductionSummary, ReorderAlert } from "../api/types";
import { KpiCard } from "../components/KpiCard";
import { useAuthStore } from "../store/authStore";

// Validated categorical palette — dataviz skill reference/palette.md, slots 1 & 2.
const COLOR_OEE = "#2a78d6";
const COLOR_DOWNTIME = "#eb6834";

export function Dashboard() {
  const plantId = useAuthStore((s) => s.plantId);
  const [oee, setOee] = useState<OEEResult[]>([]);
  const [downtime, setDowntime] = useState<DowntimeReasonTotal[]>([]);
  const [reorders, setReorders] = useState<ReorderAlert[]>([]);
  const [summary, setSummary] = useState<ProductionSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!plantId) return;
    setLoading(true);
    Promise.all([
      client.get<OEEResult[]>(`/analytics/oee/plant/${plantId}`),
      client.get<DowntimeReasonTotal[]>("/analytics/downtime-pareto"),
      client.get<ReorderAlert[]>(`/analytics/stock/reorder-alerts/${plantId}`),
      client.get<ProductionSummary>(`/analytics/production-summary/${plantId}`),
    ])
      .then(([oeeRes, downtimeRes, reorderRes, summaryRes]) => {
        setOee(oeeRes.data);
        setDowntime(downtimeRes.data);
        setReorders(reorderRes.data);
        setSummary(summaryRes.data);
      })
      .finally(() => setLoading(false));
  }, [plantId]);

  if (!plantId) {
    return <div className="p-6 text-sm text-slate-500">No plant found for this account yet.</div>;
  }
  if (loading) {
    return <div className="p-6 text-sm text-slate-500">Loading…</div>;
  }

  const avgOee =
    oee.length > 0 ? oee.reduce((sum, m) => sum + m.oee, 0) / oee.length : 0;

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <h1 className="text-xl font-semibold text-slate-900">Plant Dashboard — last 30 days</h1>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <KpiCard label="Average OEE" value={`${(avgOee * 100).toFixed(1)}%`} sublabel={`${oee.length} machine(s)`} />
        <KpiCard
          label="Produced / Planned"
          value={summary ? `${summary.total_produced_qty} / ${summary.total_planned_qty}` : "—"}
        />
        <KpiCard
          label="Rejection rate"
          value={summary ? `${(summary.rejection_rate * 100).toFixed(2)}%` : "—"}
        />
        <KpiCard label="Reorder alerts" value={String(reorders.length)} sublabel="items below reorder level" />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <h2 className="mb-3 text-sm font-medium text-slate-700">OEE by machine</h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={oee.map((m) => ({ name: m.machine_name, oee: Math.round(m.oee * 1000) / 10 }))}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} stroke="#94a3b8" />
              <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" unit="%" />
              <Tooltip formatter={(v: number) => [`${v}%`, "OEE"]} />
              <Bar dataKey="oee" fill={COLOR_OEE} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <h2 className="mb-3 text-sm font-medium text-slate-700">Downtime by reason (Pareto)</h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={downtime.map((d) => ({ name: d.reason_category, minutes: d.total_minutes }))}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} stroke="#94a3b8" />
              <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" />
              <Tooltip formatter={(v: number) => [`${v} min`, "Downtime"]} />
              <Bar dataKey="minutes" fill={COLOR_DOWNTIME} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
        <h2 className="border-b border-slate-200 p-4 text-sm font-medium text-slate-700">
          Reorder alerts
        </h2>
        {reorders.length === 0 ? (
          <div className="p-4 text-sm text-slate-400">Nothing below reorder level.</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500">
                <th className="px-4 py-2">SKU</th>
                <th className="px-4 py-2">Name</th>
                <th className="px-4 py-2 text-right">On hand</th>
                <th className="px-4 py-2 text-right">Reorder level</th>
                <th className="px-4 py-2 text-right">Shortfall</th>
              </tr>
            </thead>
            <tbody>
              {reorders.map((r) => (
                <tr key={r.product_id} className="border-t border-slate-100">
                  <td className="px-4 py-2 font-mono text-xs">{r.sku}</td>
                  <td className="px-4 py-2">{r.name}</td>
                  <td className="px-4 py-2 text-right">{r.on_hand}</td>
                  <td className="px-4 py-2 text-right">{r.reorder_level}</td>
                  <td className="px-4 py-2 text-right text-red-600">{r.shortfall}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
