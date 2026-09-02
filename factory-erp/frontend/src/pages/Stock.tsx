import { useEffect, useState } from "react";

import { client } from "../api/client";
import { Product } from "../api/domain";
import { DataTable } from "../components/DataTable";
import { useAuthStore } from "../store/authStore";

interface ProductWithOnHand extends Product {
  on_hand?: number;
}

export function Stock() {
  const plantId = useAuthStore((s) => s.plantId);
  const [products, setProducts] = useState<ProductWithOnHand[]>([]);

  useEffect(() => {
    if (!plantId) return;
    client.get<Product[]>("/stock/products", { params: { plant_id: plantId } }).then(async (r) => {
      const withOnHand = await Promise.all(
        r.data.map(async (p) => {
          const onHand = await client.get(`/stock/products/${p.id}/on-hand`);
          return { ...p, on_hand: onHand.data.on_hand_qty };
        })
      );
      setProducts(withOnHand);
    });
  }, [plantId]);

  return (
    <div className="mx-auto max-w-6xl space-y-4 p-6">
      <h1 className="text-xl font-semibold text-slate-900">Stock</h1>
      <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
        <DataTable
          rows={products}
          keyFn={(p) => p.id}
          columns={[
            { header: "SKU", render: (p) => <span className="font-mono text-xs">{p.sku}</span> },
            { header: "Name", render: (p) => p.name },
            { header: "Category", render: (p) => p.category },
            { header: "UOM", render: (p) => p.uom },
            { header: "On hand", render: (p) => p.on_hand ?? "…", align: "right" },
            { header: "Reorder level", render: (p) => p.reorder_level, align: "right" },
            { header: "Std. cost (₹)", render: (p) => p.standard_cost, align: "right" },
          ]}
        />
      </div>
    </div>
  );
}
