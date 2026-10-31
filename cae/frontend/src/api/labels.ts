/** Display labels shared by the screens. */
export const AREA_LABELS: Record<string, string> = {
  revenue: 'Revenue',
  expenditure: 'Expenditure',
  payroll: 'Payroll',
  gst: 'GST',
  inventory: 'Inventory',
  bank_reconciliation: 'Bank / Treasury',
  related_party: 'Related Party',
  statutory: 'Statutory (Tax / MSME / PF)',
  financial_reporting: 'Journals / Reporting',
};

export const areaLabel = (area?: string | null) =>
  (area && AREA_LABELS[area]) || (area || '').replace(/_/g, ' ');

export const AUDIT_TYPE_LABEL = { statutory: 'Statutory Audit', internal: 'Internal Audit' } as const;

/** Query-string scope for the selected engagement ('' = continuous monitoring). */
export const engagementQS = (engagementId?: string | null) => (engagementId ? `&engagement_id=${engagementId}` : '');
