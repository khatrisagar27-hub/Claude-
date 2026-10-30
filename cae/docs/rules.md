# CAE rule catalogue

Generated from `app/rules/catalogue.py` and the rule docstrings by `scripts/gen_rule_docs.py` — do not edit by hand.

55 rules. Parameters are defaults; override per company with `PUT /rules/{id}/parameters`. Every ageing rule also accepts `as_on` (YYYY-MM-DD); without it the latest date in the data is used.

Statutory references switch by transaction date: before 01-04-2026 the Income-tax Act, 1961 section is cited; from that date the Income-tax Act, 2025 section, with the 1961 equivalent alongside (`GET /statutory/section-map`).

## Revenue

| Code | Rule | Severity | Runs | What it checks | Default parameters |
|---|---|---|---|---|---|
| SAL-001 | Duplicate Invoice Number in a Financial Year | critical | daily | Duplicate Invoice Number within a financial year (Rule 46(b) CGST Rules). | — |
| SAL-002 | Round Amount Invoice | medium | daily | Round Amount Invoice (at or above a value, exact multiple of a round figure). | `min_amount=100000`, `multiple=1000` |
| SAL-003 | Monthly Sales Spike | high | monthly | Monthly Sales Spike (more than N standard deviations above the mean). | `sigma=3`, `min_months=6` |
| SAL-004 | Revenue Cut-Off Manipulation | critical | monthly | Revenue Cut-Off — invoice entered well after the month it is dated in. Days that look like a bulk import are skipped (created_at is then the import date). | `grace_days=5`, `min_amount=100000` |
| SAL-005 | Excessive Discount | high | daily | Excessive Discount (discount / gross above the policy limit). | `max_discount_pct=15` |
| SAL-009 | Manual Invoice Override | critical | daily | Manual Invoice — entered outside the ERP. | `min_amount=100000` |
| SAL-010 | Credit Limit Breach | high | daily | Credit Limit Breach — customer outstanding above the approved limit. | — |
| SAL-016 | Invoice Cancellation Abuse | high | monthly | Invoice Cancellation Abuse — too many cancellations per customer per month. | `max_cancellations_per_month=5` |
| SAL-019 | Weekend Invoicing | medium | daily | Weekend Invoicing (high-value invoices dated Saturday or Sunday). | `min_amount=500000` |
| SAL-034 | Duplicate Sale Same Customer-Day-Amount | critical | daily | Multiple Invoices — Same Customer, Same Day, Same Amount. | — |

## Expenditure

| Code | Rule | Severity | Runs | What it checks | Default parameters |
|---|---|---|---|---|---|
| PUR-001 | Duplicate Vendor Invoice | critical | daily | Duplicate Vendor Invoice (same vendor, same invoice number, same financial year). | — |
| PUR-002 | PO-Invoice Amount Mismatch | high | daily | PO vs Invoice Amount Mismatch above tolerance. | `tolerance_pct=5` |
| PUR-004 | Invoice Without PO | high | daily | Invoice Without PO above a value. | `min_amount=100000` |
| PUR-006 | Split Purchases Below Approval Limit | high | monthly | Split purchases — several invoices each below the approval limit that together exceed it. | `approval_limit=100000`, `window_days=7`, `min_count=3` |
| PUR-010 | Payment to Account Not in Vendor Master | critical | daily | Vendor payment to a bank account that is not the one in the vendor master. | — |
| PUR-013 | Large Invoice Without Approval or PO | high | daily | Large invoice with no approver and no PO. | `min_amount=500000` |
| PUR-016 | Possible Duplicate Payment | critical | daily | Possible duplicate payment — same vendor, same amount, different invoice numbers, close dates, both paid. | `window_days=30` |
| PUR-021 | GRN Dated Before Supplier Invoice | high | daily | GRN dated before the supplier's invoice (goods recorded as received before they were billed). | `min_amount=100000` |

## GST

| Code | Rule | Severity | Runs | What it checks | Default parameters |
|---|---|---|---|---|---|
| SAL-007 | Missing E-Way Bill | high | daily | Missing E-Way Bill (consignment value above Rule 138 limit). | `threshold=50000` |
| SAL-021 | E-Invoice IRN Missing | high | daily | E-Invoice IRN Missing on a B2B invoice where e-invoicing applies (Rule 48(4)). | — |
| GST-001 | Removed GST Slab After 22-09-2025 | high | daily | Removed GST slab (12% / 28%) on an invoice dated on or after 22-09-2025. | `rate_tolerance=0.05` |
| GST-002 | Rule 37 ITC Reversal — Supplier Unpaid 180 Days | high | weekly | ITC on a supplier bill unpaid for more than 180 days (Rule 37 reversal). | — |
| GST-003 | ITC Booked After s.16(4) Time Limit | high | monthly | ITC-eligible bill booked after the s.16(4) time limit (30 November after the year end). Days that look like a bulk import are skipped (created_at is then the import date). | — |

## Statutory (income tax, MSME, PF/ESI)

| Code | Rule | Severity | Runs | What it checks | Default parameters |
|---|---|---|---|---|---|
| SAL-022 | Cash Receipt of Rs.2 Lakh or More | critical | daily | Cash Receipt of Rs.2 lakh or more from a person in a day (s.186 / s.269ST). | `threshold=200000` |
| PUR-031 | MSME Payment Beyond s.15 Limit | high | weekly | MSME dues beyond the MSMED s.15 time limit — s.16 interest and s.37(2)(g) / s.43B(h) exposure. | — |
| TDS-001 | TDS on Purchase of Goods Not Deducted | high | monthly | TDS on purchase of goods not deducted after a vendor crosses Rs.50 lakh in the year (s.393(1) Table Sl.8(ii) / s.194Q). Applies only if the buyer's turnover in the preceding year exceeded Rs.10 crore. | — |
| TDS-002 | TDS Short-Deducted | medium | monthly | TDS deducted below the minimum rate for the section recorded on the bill. | `tolerance=1` |
| PAY-005 | PF/ESI Not Deposited by Due Date | high | monthly | PF/ESI contributions not deposited by the 15th of the following month. PF and ESI are matched to bank debits separately, by narration and amount (tolerance covers EPF admin charges). | `amount_tolerance_pct=5` |
| TRE-001 | Cash Payment Above Daily Limit | high | daily | Cash expenditure to one person in a day above Rs.10,000 (Rs.35,000 for goods-carriage hire) — s.36(4)/(6) of the 2025 Act / s.40A(3) of the 1961 Act. | `tax_rate=0.25168` |
| TRE-003 | Cash Loan Taken or Repaid | critical | daily | Cash loan/deposit taken or repaid of Rs.20,000 or more (s.185 / s.188; 1961: s.269SS / s.269T). | — |

## Related party

| Code | Rule | Severity | Runs | What it checks | Default parameters |
|---|---|---|---|---|---|
| PUR-022 | Vendor Shares Bank Account or PAN with Employee | critical | daily | Vendor shares a bank account or PAN with an employee. | — |
| TRE-006 | Director/Loan Payment | critical | daily | Large payments described as director/loan payments (s.185/s.186/s.188 Companies Act review). | `min_amount=100000` |

## Inventory

| Code | Rule | Severity | Runs | What it checks | Default parameters |
|---|---|---|---|---|---|
| INV-001 | Negative Stock Balance | critical | daily | Negative Stock Balance (item level). | — |
| INV-002 | Inventory Shrinkage Above Limit | high | monthly | Inventory shrinkage — negative adjustments above N% of receipts. | `max_shrinkage_pct=2` |
| INV-005 | Slow Moving Stock | medium | monthly | Slow-moving stock — on-hand items with no movement for N days. | `max_idle_days=180` |
| INV-007 | Ghost Inventory | critical | monthly | Ghost inventory — high on-hand value carried by very few movements. | `min_value=500000`, `max_movements=2` |
| INV-010 | Weekend Inventory Movement | high | daily | High-value inventory movements dated Saturday or Sunday. | `min_value=200000` |
| INV-015 | Multiple GRNs on One Reference | high | daily | Several GRNs against the same reference document and item. | `max_grns=2` |

## Journals and financial reporting

| Code | Rule | Severity | Runs | What it checks | Default parameters |
|---|---|---|---|---|---|
| JE-001 | Manual JE Without Narration | high | daily | Manual JE Without Narration. | `min_amount=100000` |
| JE-002 | Late-Posted JE | critical | monthly | JE posted well after its entry date (late posting). | `max_days=10` |
| JE-003 | Large Manual JE | high | daily | Large Value Manual JE. | `min_amount=1000000` |
| JE-005 | Uncleared Suspense Account | high | weekly | Suspense account carrying a balance older than N days. | `max_days=30` |
| JE-006 | Orphan Reversal | critical | daily | Reversal JE without a reference to the original entry. | — |
| JE-009 | Unbalanced Journal Entry | critical | daily | Unbalanced JE (line debits not equal to line credits). | — |
| JE-011 | Single-User High-Volume JE Posting | critical | daily | One user posting a high volume of large JEs (segregation-of-duties indicator). | `min_count=10` |
| JE-015 | Prior Period JE | high | monthly | Prior-period JE — dated in one financial year (Apr-Mar) but posted in a later one. | — |

## Payroll

| Code | Rule | Severity | Runs | What it checks | Default parameters |
|---|---|---|---|---|---|
| PAY-001 | Ghost Employee | critical | monthly | Salary paid to an employee marked inactive with no leaving date recorded. | — |
| PAY-002 | Salary Spike Month-on-Month | high | monthly | Gross salary up more than N% on the previous month (year boundary handled). | `max_increase_pct=50` |
| PAY-003 | Duplicate Bank Account in Payroll | critical | monthly | Same bank account receiving salary for more than one employee. | — |
| PAY-004 | Post-Termination Pay | critical | monthly | Salary paid for a period that starts after the employee's leaving date. | — |
| PAY-009 | High Payroll Deductions | medium | monthly | Deductions above a share of gross pay (recoveries, advances or payroll errors). | `max_deduction_share=0.33` |

## Bank and treasury

| Code | Rule | Severity | Runs | What it checks | Default parameters |
|---|---|---|---|---|---|
| TRE-002 | Circular Bank Transfer | critical | daily | Circular Bank Transfer — money out to a party and back within a short window. | `window_days=2` |
| TRE-004 | Unreferenced Transfer Above Limit | critical | daily | Large electronic transfer with no reference or UTR. | `min_amount=500000` |
| TRE-005 | Multiple Payments Same Party Day | high | daily | Multiple payments to the same party on the same day. | `min_count=3` |
| TRE-010 | Structured Cash Withdrawal | critical | daily | Structured cash withdrawals just below the Rs.10 lakh cash-transaction-report level. | — |
