export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  tenant_id: string;
  company_id?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface Company {
  id: string;
  tenant_id: string;
  name: string;
  gstin?: string;
  pan?: string;
  entity_type?: string;
  industry_sector?: string;
  city?: string;
  state?: string;
  is_active: boolean;
  annual_turnover?: number | null;
}

export interface AuditException {
  id: string;
  company_id: string;
  rule_id: string | null;
  detected_on: string;
  category: string;
  title: string;
  description: string | null;
  severity: 'critical' | 'high' | 'medium' | 'low';
  risk_impact: string | null;
  financial_impact?: number | null;
  supporting_data?: any | null;
  ai_analysis?: string | null;
  status: string;
  rule_code?: string | null;
  engagement_id?: string | null;
  process?: string | null;
  audit_refs?: AuditRef[];
  material?: boolean | null;
}

export interface AuditRef {
  frame: string;
  ref: string;
  title?: string;
  note?: string;
}

export type AuditType = 'statutory' | 'internal';

export interface EngagementRef {
  id: string;
  label: string;
  audit_type: AuditType;
}

export interface Engagement extends EngagementRef {
  company_id: string;
  name: string;
  financial_year: number | null;
  period_from: string;
  period_to: string;
  status: string;
  caro_applicable: boolean;
  ifc_applicable: boolean;
  tax_audit_applicable: boolean;
  materiality: number | null;
  scope_notes: string | null;
  exception_count: number;
  rules_in_scope: number;
  last_run_at: string | null;
}

export interface SyncJob {
  id: string;
  company_id: string;
  job_type: string;
  status: string;
  records_processed: number;
  exceptions_raised: number;
  error_message: string | null;
  created_at: string;
  completed_at?: string | null;
  engagement_id?: string | null;
  run_mode?: string | null;
  result?: Record<string, any> | null;
}

export interface QueryResponse {
  id: string;
  response_text: string;
  responded_at: string;
  responded_by_name?: string | null;
}

export interface ManagementQuery {
  id: string;
  exception_id: string;
  company_id: string;
  query_no: string;
  process_area: string;
  severity: string;
  description: string;
  evidence_summary: string;
  suggested_question: string;
  assigned_to_user_id?: string;
  due_date?: string;
  status: string;
  raised_at: string;
  raised_by_name?: string | null;
  auditor_comment?: string | null;
  responses?: QueryResponse[];
}

export interface RiskScore {
  id: string;
  company_id: string;
  score_date: string;
  entity_level: string;
  entity_name: string;
  likelihood: number;
  impact: number;
  composite_score: number;
  risk_band: 'critical' | 'high' | 'moderate' | 'low';
}

export interface KPIs {
  total_exceptions: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  open_queries: number;
  overdue_queries: number;
  resolved_this_month: number;
  composite_risk_score: number;
  risk_band: string;
  fraud_indicators: number;
  gst_risk_amount: number;
  engagement_label?: string | null;
  audit_type?: AuditType | null;
  total_financial_impact?: number;
}

export interface AuditRule {
  id: string;
  rule_code: string;
  name: string;
  description: string;
  business_area: string;
  severity: string;
  likelihood: number;
  risk_category: string;
  frequency: string;
  is_enabled: boolean;
  parameters: Record<string, unknown> | null;
  audit_scope?: 'statutory' | 'ifc' | 'internal' | null;
  process?: string | null;
}

export interface RemediationAction {
  id: string;
  company_id: string;
  exception_id: string;
  control_gap_description: string;
  root_cause?: string;
  action_plan: string;
  target_date?: string;
  actual_closure_date?: string;
  retest_outcome?: string;
  residual_risk_score?: number;
  responsible_name?: string;
  status?: string;
}

export interface FraudIndicator {
  id: string;
  indicator_type: string;
  description: string;
  score: number;
  analysis_date: string;
  affected_transactions: number;
  financial_exposure?: number | null;
  details_json?: Record<string, any> | null;
}

export interface GSTRecon {
  id: string;
  period: string;
  books_turnover?: number;
  gstr1_turnover?: number;
  variance_turnover?: number;
  books_itc?: number;
  gstr2b_itc?: number;
  variance_itc?: number;
  risk_amount?: number;
  status: string;
}

export type Severity = 'critical' | 'high' | 'medium' | 'low';
export type RiskBand = 'critical' | 'high' | 'moderate' | 'low';
