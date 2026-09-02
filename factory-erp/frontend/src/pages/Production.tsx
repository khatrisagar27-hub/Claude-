import { useEffect, useState } from "react";

import { client } from "../api/client";
import { WorkOrder } from "../api/domain";
import { DataTable } from "../components/DataTable";
import { useAuthStore } from "../store/authStore";

const STATUS_COLOR: Record<string, string> = {
  planned: "text-slate-600 bg-slate-100",
  in_progress: "text-blue-700 bg-blue-50",
  completed: "text-green-700 bg-green-50",
  cancelled: "text-red-700 bg-red-50",
};

export function Production() {
  const plantId = useAuthStore((s) => s.plantId);
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);

  useEffect(() => {
    if (!plantId) return;
    client.get<WorkOrder[]>("/production/work-orders", { params: { plant_id: plantId } }).then((r) =>
      setWorkOrders(r.data)
    );
  }, [plantId]);

  return (
    <div className="mx-auto max-w-6xl space-y-4 p-6">
      <h1 className="text-xl font-semibold text-slate-900">Production — work orders</h1>
      <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
        <DataTable
          rows={workOrders}
          keyFn={(w) => w.id}
          columns={[
            { header: "Order #", render: (w) => <span className="font-mono text-xs">{w.order_number}</span> },
            { header: "Planned", render: (w) => w.planned_qty, align: "right" },
            { header: "Produced", render: (w) => w.produced_qty, align: "right" },
            { header: "Rejected", render: (w) => w.rejected_qty, align: "right" },
            {
              header: "Status",
              render: (w) => (
                <span className={`rounded px-2 py-0.5 text-xs ${STATUS_COLOR[w.status] ?? ""}`}>
                  {w.status}
                </span>
              ),
            },
          ]}
        />
      </div>
    </div>
  );
}
