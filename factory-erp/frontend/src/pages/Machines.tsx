import { useEffect, useState } from "react";

import { client } from "../api/client";
import { Machine } from "../api/domain";
import { DataTable } from "../components/DataTable";
import { useAuthStore } from "../store/authStore";

const STATUS_COLOR: Record<string, string> = {
  running: "text-green-700 bg-green-50",
  idle: "text-slate-600 bg-slate-100",
  breakdown: "text-red-700 bg-red-50",
  maintenance: "text-amber-700 bg-amber-50",
};

export function Machines() {
  const plantId = useAuthStore((s) => s.plantId);
  const [machines, setMachines] = useState<Machine[]>([]);

  useEffect(() => {
    if (!plantId) return;
    client.get<Machine[]>("/machines", { params: { plant_id: plantId } }).then((r) => setMachines(r.data));
  }, [plantId]);

  return (
    <div className="mx-auto max-w-6xl space-y-4 p-6">
      <h1 className="text-xl font-semibold text-slate-900">Machines</h1>
      <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
        <DataTable
          rows={machines}
          keyFn={(m) => m.id}
          columns={[
            { header: "Code", render: (m) => <span className="font-mono text-xs">{m.code}</span> },
            { header: "Name", render: (m) => m.name },
            { header: "Category", render: (m) => m.category ?? "—" },
            { header: "Rated cap./hr", render: (m) => m.rated_capacity_per_hour, align: "right" },
            {
              header: "Status",
              render: (m) => (
                <span className={`rounded px-2 py-0.5 text-xs ${STATUS_COLOR[m.status] ?? ""}`}>
                  {m.status}
                </span>
              ),
            },
          ]}
        />
      </div>
    </div>
  );
}
