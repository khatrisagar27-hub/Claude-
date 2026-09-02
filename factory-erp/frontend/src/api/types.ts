export interface Plant {
  id: string;
  code: string;
  name: string;
  location: string | null;
}

export interface OEEResult {
  machine_id: string;
  machine_name: string;
  planned_minutes: number;
  downtime_minutes: number;
  run_minutes: number;
  total_output: number;
  good_output: number;
  availability: number;
  performance: number;
  quality: number;
  oee: number;
}

export interface DowntimeReasonTotal {
  reason_category: string;
  total_minutes: number;
  occurrences: number;
}

export interface ReorderAlert {
  product_id: string;
  sku: string;
  name: string;
  on_hand: number;
  reorder_level: number;
  reorder_qty: number;
  shortfall: number;
}

export interface StockAgeing {
  product_id: string;
  sku: string;
  name: string;
  on_hand: number;
  days_since_last_movement: number | null;
  bucket: string;
}

export interface ProductionSummary {
  plant_id: string;
  total_planned_qty: number;
  total_produced_qty: number;
  total_rejected_qty: number;
  good_qty: number;
  rejection_rate: number;
  schedule_adherence: number;
}
