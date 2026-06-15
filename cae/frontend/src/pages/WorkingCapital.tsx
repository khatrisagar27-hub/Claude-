import { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, Clock } from 'lucide-react';
import apiClient from '../api/client';
import { useAuthStore } from '../store/authStore';
import AmountDisplay from '../components/common/AmountDisplay';

export default function WorkingCapital() {
  const { companyId } = useAuthStore();
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!companyId) return;
    // Working capital is computed via the engine endpoint (no dedicated API route — use dashboard or trigger)
    setLoading(false);
  }, [companyId]);

  const stressColor = (score: number) => {
    if (score >= 70) return 'text-red-400';
    if (score >= 40) return 'text-yellow-400';
    return 'text-green-400';
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white">Working Capital Intelligence</h1>
        <p className="text-sm text-gray-500">DSO / DPO / DIO / CCC and stress score</p>
      </div>

      {!metrics ? (
        <div className="card text-center py-12">
          <Clock className="w-12 h-12 text-gray-700 mx-auto mb-4" />
          <p className="text-gray-500">Working capital metrics are computed during the daily audit cycle.</p>
          <p className="text-gray-600 text-sm mt-1">Trigger an audit cycle from Data Ingestion to populate this view.</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="card">
              <div className="text-xs text-gray-500 uppercase">DSO (days)</div>
              <div className="text-3xl font-bold font-mono text-white mt-1">{metrics.dso}</div>
              <div className="text-xs text-gray-600 mt-0.5">Days Sales Outstanding</div>
            </div>
            <div className="card">
              <div className="text-xs text-gray-500 uppercase">DPO (days)</div>
              <div className="text-3xl font-bold font-mono text-white mt-1">{metrics.dpo}</div>
              <div className="text-xs text-gray-600 mt-0.5">Days Payable Outstanding</div>
            </div>
            <div className="card">
              <div className="text-xs text-gray-500 uppercase">DIO (days)</div>
              <div className="text-3xl font-bold font-mono text-white mt-1">{metrics.dio}</div>
              <div className="text-xs text-gray-600 mt-0.5">Days Inventory Outstanding</div>
            </div>
            <div className="card">
              <div className="text-xs text-gray-500 uppercase">CCC (days)</div>
              <div className={`text-3xl font-bold font-mono mt-1 ${metrics.ccc > 90 ? 'text-red-400' : 'text-white'}`}>
                {metrics.ccc}
              </div>
              <div className="text-xs text-gray-600 mt-0.5">Cash Conversion Cycle</div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="card">
              <div className="text-xs text-gray-500 uppercase">Total Receivables</div>
              <AmountDisplay amount={metrics.total_receivables} className="text-xl font-bold text-white block mt-1" />
            </div>
            <div className="card">
              <div className="text-xs text-gray-500 uppercase">Total Payables</div>
              <AmountDisplay amount={metrics.total_payables} className="text-xl font-bold text-white block mt-1" />
            </div>
            <div className="card">
              <div className="text-xs text-gray-500 uppercase mb-1">WC Stress Score</div>
              <div className={`text-4xl font-bold font-mono ${stressColor(metrics.stress_score)}`}>
                {metrics.stress_score?.toFixed(0)}
              </div>
              <div className="text-xs text-gray-600 mt-0.5">0=Healthy, 100=Critical</div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
