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
}

export interface FraudIndicator {
  id: string;
  type: string;
  description: string;
  severity: string;
  detected_at: string;
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
