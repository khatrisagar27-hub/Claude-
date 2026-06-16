# Continuous Audit Engine — API Reference

Base URL: `http://localhost:8000/api/v1`

Interactive docs: `http://localhost:8000/api/docs`

## Authentication

All endpoints (except `/auth/login`) require a Bearer JWT token.

```
Authorization: Bearer <access_token>
```

---

## Auth

### POST /auth/login
Login and get JWT tokens.

**Body:**
```json
{ "email": "sagar@ska.in", "password": "CAE@2024" }
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### POST /auth/refresh
Exchange refresh token for new access token.

### POST /auth/logout
Invalidate session (client discards tokens).

### GET /auth/me
Get current user profile.

---

## Companies

### GET /companies
List all companies for the tenant.

### POST /companies
Create a new company. Roles: super_admin, partner.

### GET /companies/{id}
Get company details.

### PUT /companies/{id}
Update company. Roles: super_admin, partner.

---

## Data Ingestion

### POST /ingestion/upload
Upload Excel/CSV file for import.

**Form fields:** `company_id`, `file_type`, `file` (multipart)

**Supported file_types:** sales_invoices, purchase_invoices, journal_entries, bank_transactions, inventory, payroll

### POST /ingestion/sync
Trigger a full audit cycle.

**Query params:** `company_id`, `job_type=full_audit`

### GET /ingestion/jobs
List recent sync jobs. Query: `?company_id=...&limit=20`

---

## Audit Rules

### GET /rules
List rules. Filters: `?business_area=Sales&severity=critical&is_enabled=true`

### PUT /rules/{id}/toggle
Enable/disable a rule. Roles: super_admin, partner, manager.

### POST /rules/{id}/test
Run a single rule on-demand. Query: `?company_id=...`

---

## Exceptions

### GET /exceptions
Paginated list. Filters: `?company_id=...&severity=critical&status=open&page=1&page_size=50`

### GET /exceptions/{id}
Exception detail with evidence JSON.

### PATCH /exceptions/{id}/status
Update exception status. Body: `{ "status": "acknowledged", "comment": "..." }`

Valid transitions:
- open → acknowledged | query_raised | escalated | closed
- acknowledged → query_raised | escalated | resolved | closed
- query_raised → escalated | resolved | closed
- escalated → resolved | closed
- resolved → closed

### POST /exceptions/{id}/ai-explain
Get Claude AI explanation for the exception. Returns:
```json
{
  "explanation": "...",
  "business_impact": "...",
  "fraud_risk": "High — ...",
  "recommended_query": "Please provide...",
  "suggested_remediation": "..."
}
```

---

## Management Queries

### POST /queries
Raise a management query from an exception.

### GET /queries
List queries. Filters: `?company_id=...&status=open&severity=critical`

### GET /queries/{id}
Query detail.

### POST /queries/{id}/respond
Respond to a query. Body: `{ "response_text": "...", "attachment_url": "..." }`

### PATCH /queries/{id}/status
Update query status. Body: `{ "status": "resolved", "auditor_comment": "..." }`

---

## Remediation

### GET /remediation
List remediation actions. `?company_id=...&retest_outcome=pending`

### POST /remediation
Create remediation action.

### PUT /remediation/{id}
Update remediation action (add evidence, retest outcome).

---

## Risk

### GET /risk/scores
Daily risk scores by process area. `?company_id=...&score_date=2024-12-31`

### GET /risk/heatmap
Risk heatmap data for visualization. `?company_id=...`

### GET /risk/trend
Risk score trend over time. `?company_id=...&days=30`

### GET /risk/fraud-indicators
Detected fraud indicators. `?company_id=...`

---

## GST

### GET /gst/reconciliation
GST reconciliation records. `?company_id=...&period=2024-03`

### POST /gst/upload-gstr2b
Upload GSTR-2B JSON file for reconciliation.

**Form fields:** `company_id`, `period` (YYYY-MM), `file` (JSON)

### GET /gst/itc-risk
ITC risk summary. `?company_id=...`

---

## Dashboard

### GET /dashboard/kpis
Executive KPIs — exception counts, risk score, query counts.

### GET /dashboard/top-exceptions
Top open exceptions by financial impact. `?company_id=...&limit=10`

### GET /dashboard/trend
Exception trend by month. `?company_id=...&months=6`

### GET /dashboard/fraud-indicators
Recent fraud indicators for dashboard widget.

---

## Reports

### POST /reports/working-paper
Download full audit working paper (Excel). `?company_id=...&period=2024`

### POST /reports/exception-summary
Download exception summary (Excel). `?company_id=...`

### POST /reports/audit-deck
Download executive audit presentation (PDF). `?company_id=...`

---

## Risk Scoring Formula

```
risk_score = likelihood × impact × materiality × frequency × (1 + control_weakness)
```

| Factor | Range | Description |
|--------|-------|-------------|
| likelihood | 1-5 | Exception frequency pattern |
| impact | 1-5 | Maximum severity in area |
| materiality | 0.5-2.0 | Financial impact / revenue |
| frequency | 1-3 | Recurrence in period |
| control_weakness | 0-1 | 0=strong controls, 1=no controls |

**Risk Bands:** 0-20=Low | 21-50=Moderate | 51-80=High | 81+=Critical

---

## Roles & Permissions

| Role | Access |
|------|--------|
| super_admin | Full access |
| partner | Full access except super_admin |
| manager | Read/write exceptions, queries, remediation |
| auditor | Read/write exceptions and queries |
| cfo | Read-only dashboard and risk |
| management | Read-only queries assigned to them |
| process_owner | Read-only for their area |
| client_user | Dashboard KPIs only |
