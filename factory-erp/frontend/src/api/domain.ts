export interface Machine {
  id: string;
  code: string;
  name: string;
  category: string | null;
  rated_capacity_per_hour: number;
  status: string;
}

export interface Product {
  id: string;
  sku: string;
  name: string;
  category: string;
  uom: string;
  standard_cost: number;
  reorder_level: number;
}

export interface WorkOrder {
  id: string;
  order_number: string;
  product_id: string;
  machine_id: string;
  planned_qty: number;
  produced_qty: number;
  rejected_qty: number;
  status: string;
}
