# Rule catalogue

67 rules. Generated from the code by `python -m app.catalogue` — do not edit by hand.

Severity is the rule's inherent level; the amount involved can raise or lower it (see README, *How severity is set*). Thresholds shown are defaults and can be changed per engagement.

## Sales

### SAL-001 — Duplicate invoice number

Two or more live invoices carry the same number in one financial year.

- Severity: high
- Provision: CGST Rules, r.46(b): invoice number must be unique for a financial year
- Needs: sales

### SAL-002 — Gaps in invoice number series

Numbers missing inside a running invoice series. Cancelled invoices count as accounted for.

- Severity: medium
- Provision: CGST Rules, r.46(b): consecutive serial number
- Needs: sales
- Threshold `min_series`: Smallest series to test (invoices) — default 5

### SAL-003 — Sales entered after period end but dated within it

Invoices dated on or before the period end that were keyed in after it — a cut-off risk.

- Severity: high; fraud indicator
- Provision: AS 9 / Ind AS 115: revenue cut-off; SA 240 (presumed risk in revenue recognition)
- Needs: sales.entered_on
- Threshold `grace_days`: Days after period end allowed for entry — default 0

### SAL-004 — E-invoice (IRN) not generated

B2B invoices without an IRN. Runs only where e-invoicing is marked applicable on the engagement.

- Severity: high
- Provision: CGST Rules, r.48(4) and r.48(5): B2B invoice without IRN is not a valid tax invoice; penalty s.122
- Needs: sales

### SAL-005 — E-way bill not recorded

Goods invoices above the limit with no e-way bill number. Exempt goods and Rule 138(14) cases cannot be identified from the register — review the list.

- Severity: medium
- Provision: CGST Rules, r.138(1): consignment value exceeding Rs 50,000; penalty s.129
- Needs: sales
- Threshold `limit`: Consignment value limit (₹) — default 50,000

### SAL-006 — Wrong tax head for place of supply

IGST charged on an intra-State supply, or CGST/SGST on an inter-State one. Needs the client's GSTIN on record. SEZ supplies (IGST within the State) will appear here — exclude on review.

- Severity: high
- Provision: IGST Act s.5 (inter-State) / CGST Act s.9 (intra-State); refund route s.77 CGST, s.19 IGST
- Needs: sales.place_of_supply

### SAL-007 — Invoice arithmetic does not agree

Taxable value plus taxes does not equal the invoice total, or CGST differs from SGST.

- Severity: medium
- Needs: sales
- Threshold `tolerance`: Rounding tolerance (₹) — default 1.0

### SAL-008 — Receivables overdue beyond limit

Unpaid invoices more than the set number of days past due as at the data date.

- Severity: medium
- Provision: AS 4 / Ind AS 109: assess recoverability and provision
- Needs: sales
- Threshold `overdue_days`: Days past due date — default 180
- Threshold `default_credit_days`: Credit days where no due date — default 30

### SAL-009 — Sales to related parties

Total sales to each party marked as related in the party master.

- Severity: low
- Provision: Companies Act, 2013 s.188; AS 18 / Ind AS 24 disclosure
- Needs: sales, parties

### SAL-010 — Same customer, same day, same amount

Possible double billing: identical totals to one customer on one date under different numbers.

- Severity: medium
- Needs: sales
- Threshold `min_amount`: Minimum invoice total (₹) — default 10,000

### SAL-011 — Sales bunched at month end

Months in which the last few days carry an unusually large share of the month's sales.

- Severity: medium; fraud indicator
- Provision: SA 240: revenue recognition
- Needs: sales
- Threshold `last_days`: Days at month end — default 3
- Threshold `share_pct`: Share of month's sales (%) — default 40
- Threshold `min_invoices`: Minimum invoices in the month — default 20

### SAL-012 — High invoice cancellations

Months where cancelled invoices exceed the set share of all invoices raised.

- Severity: medium; fraud indicator
- Needs: sales
- Threshold `ratio_pct`: Cancelled share of invoices (%) — default 5
- Threshold `min_cancelled`: Minimum cancelled invoices — default 3

## Purchases

### PUR-001 — Vendor invoice booked more than once

The same vendor invoice number is booked two or more times.

- Severity: critical
- Needs: purchases

### PUR-002 — Probable duplicate: same vendor and amount, different number

Invoices from one vendor for an identical total within a short window under different numbers.

- Severity: high; fraud indicator
- Needs: purchases
- Threshold `window_days`: Days between the invoices — default 15
- Threshold `min_amount`: Minimum invoice total (₹) — default 10,000

### PUR-003 — Invoice without purchase order

Invoices at or above the limit with no purchase order reference.

- Severity: medium
- Needs: purchases.po_no
- Threshold `min_amount`: Minimum invoice total (₹) — default 100,000

### PUR-004 — Invoiced value exceeds purchase order

Total invoiced against a PO is more than the PO value plus tolerance.

- Severity: high
- Needs: purchases.po_amount
- Threshold `tolerance_pct`: Tolerance over PO value (%) — default 5

### PUR-005 — Paid before goods were received

Goods invoices paid with no goods receipt recorded, or paid before the receipt date.

- Severity: high
- Needs: purchases.grn_date

### PUR-006 — Delayed payment to micro or small enterprise

Micro and small suppliers not paid within the statutory period, counted from acceptance (goods receipt date, else invoice date). The period is the agreed credit days capped at 45, or 15 days where the engagement is marked as having no written agreement. Whether the supplier is a trader (outside s.43B(h) by common view) must be checked on review.

- Severity: high
- Provision: MSMED Act, 2006 s.15 and s.16 (interest at 3x bank rate, monthly rests); Income-tax Act, 1961 s.43B(h)
- Needs: purchases, parties.msme_category

### PUR-007 — Vendor shares bank account or PAN with an employee

A vendor's bank account or PAN is the same as an employee's — conflict of interest or a fictitious vendor.

- Severity: critical; fraud indicator
- Needs: parties, employees

### PUR-008 — Purchases split below approval limit

Several invoices from one vendor, each under the approval limit, that together exceed it within a few days.

- Severity: high; fraud indicator
- Needs: purchases
- Threshold `approval_limit`: Approval limit (₹) — default 100,000
- Threshold `window_days`: Window (days) — default 3

### PUR-009 — Purchases from related parties

Total purchases from each party marked as related in the party master.

- Severity: low
- Provision: Companies Act, 2013 s.188; Income-tax Act, 1961 s.40A(2)(b)
- Needs: purchases, parties

### PUR-010 — Paid before the invoice date without a PO

Payment made before the vendor's invoice date where no purchase order is recorded.

- Severity: medium
- Needs: purchases

### PUR-011 — Invoice arithmetic does not agree

Taxable value plus taxes does not equal the invoice total.

- Severity: medium
- Needs: purchases
- Threshold `tolerance`: Rounding tolerance (₹) — default 1.0

## GST

### GST-001 — ITC claimed on invoices not in GSTR-2B

Credit taken on invoices the supplier has not reported. Grouped by supplier.

- Severity: high
- Provision: CGST Act s.16(2)(aa); CGST Rules r.36(4)
- Needs: purchases, gstr2b
- Threshold `tolerance`: Matching tolerance (₹) — default 1.0

### GST-002 — ITC claimed exceeds tax in GSTR-2B

Invoice is in GSTR-2B but for a lower tax amount than the credit taken.

- Severity: high
- Provision: CGST Act s.16(2)(aa); CGST Rules r.36(4)
- Needs: purchases, gstr2b
- Threshold `tolerance`: Matching tolerance (₹) — default 1.0

### GST-003 — Invoices in GSTR-2B not booked

Supplier has reported invoices that are not in the purchase register: unrecorded purchases, credit not availed, or a supplier quoting the client's GSTIN in error.

- Severity: medium
- Needs: purchases, gstr2b
- Threshold `tolerance`: Matching tolerance (₹) — default 1.0

### GST-004 — Supplier not paid within 180 days — ITC reversal

ITC taken on invoices still unpaid, wholly or partly, beyond 180 days from the invoice date. Reversal is proportionate to the unpaid amount.

- Severity: high
- Provision: CGST Act s.16(2) second proviso; CGST Rules r.37; interest s.50
- Needs: purchases

### GST-005 — ITC booked after the time limit

Credit on an invoice booked after 30 November following the end of the financial year to which the invoice belongs. Uses booking date; where absent, the test cannot be made.

- Severity: critical
- Provision: CGST Act s.16(4): 30 November following the financial year of the invoice
- Needs: purchases

### GST-006 — ITC claimed against a missing or invalid GSTIN

Credit taken where the supplier GSTIN is blank or fails the check-digit test.

- Severity: high
- Provision: CGST Act s.16(2)(a); CGST Rules r.36(1), r.46
- Needs: purchases

### GST-007 — ITC claimed where GSTR-2B shows credit not available

GSTR-2B flags the invoice as 'ITC not available' but credit has been taken.

- Severity: high
- Provision: CGST Act s.16(2)(aa), s.16(4), s.38
- Needs: purchases, gstr2b
- Threshold `tolerance`: Matching tolerance (₹) — default 1.0

### GST-008 — ITC claimed on blocked credits

Credit taken on purchases whose nature falls under s.17(5): motor vehicles, food and beverages, club membership, health insurance, works contract for immovable property, gifts, personal use. Exceptions within s.17(5) (e.g. vehicles for transport of goods) need review.

- Severity: high
- Provision: CGST Act s.17(5)
- Needs: purchases

### GST-009 — ITC claimed exceeds tax charged on the invoice

Credit recorded is more than the GST shown on the invoice.

- Severity: high
- Needs: purchases
- Threshold `tolerance`: Matching tolerance (₹) — default 1.0

## TDS

### TDS-001 — TDS not deducted

Payments crossing the section threshold on which no tax was deducted.

- Severity: high
- Provision: Income-tax Act, 1961 ss.194C/194J/194I/194H/194A/194Q, s.201, s.40(a)(ia)
- Needs: purchases
- Threshold `tolerance`: Shortfall ignored up to (₹) — default 10.0

### TDS-002 — TDS short deducted

Tax deducted is less than the amount due at the applicable rate.

- Severity: high
- Provision: Income-tax Act, 1961 ss.194C/194J/194I/194H/194A/194Q, s.201, s.40(a)(ia)
- Needs: purchases
- Threshold `tolerance`: Shortfall ignored up to (₹) — default 10.0

### TDS-003 — Deductee PAN missing or invalid

Vendors liable to TDS with no valid PAN on record; the higher rate has been used in TDS-001/002.

- Severity: medium
- Provision: Income-tax Act, 1961 s.206AA: deduct at 20% where PAN is not furnished
- Needs: purchases

## Books

### JE-001 — Voucher does not balance

Total debits differ from total credits within a voucher — the extract is incomplete or the books are corrupt.

- Severity: critical
- Needs: ledger

### JE-002 — Journals without narration

Journal vouchers at or above the limit with no narration on any line.

- Severity: medium
- Provision: SA 240 para 33(a): testing of journal entries
- Needs: ledger
- Threshold `min_amount`: Minimum voucher value (₹) — default 50,000

### JE-003 — Large journal entry

Individual journal vouchers at or above the limit.

- Severity: medium
- Provision: SA 240 para 33(a): testing of journal entries
- Needs: ledger
- Threshold `min_amount`: Voucher value at or above (₹) — default 1,000,000

### JE-004 — Back-dated voucher

Vouchers keyed in long after the date they bear.

- Severity: medium; fraud indicator
- Provision: SA 240 para 33(a): testing of journal entries
- Needs: ledger.entered_on
- Threshold `lag_days`: Days between voucher date and entry — default 30
- Threshold `min_amount`: Minimum voucher value (₹) — default 100,000

### JE-005 — Journal voucher touching cash or bank

Cash or bank moved through a journal instead of a payment, receipt or contra voucher, bypassing the usual cash/bank controls.

- Severity: medium
- Provision: SA 240 para 33(a): testing of journal entries
- Needs: ledger
- Threshold `min_amount`: Minimum voucher value (₹) — default 10,000

### JE-006 — Journal to income accounts at period end

Journals hitting sales/income ledgers in the last days of the period, or dated in the period but entered after it.

- Severity: high; fraud indicator
- Provision: SA 240 para 27 (presumed fraud risk in revenue) and para 33(a)
- Needs: ledger
- Threshold `last_days`: Days before period end — default 5
- Threshold `min_amount`: Minimum voucher value (₹) — default 100,000

### JE-007 — Suspense account not cleared

Ledgers named or grouped as suspense that carry a balance as at the data date.

- Severity: high
- Provision: Schedule III, Companies Act 2013: balances must be classified by nature
- Needs: ledger

### JE-008 — Vouchers dated outside the engagement period

Entries dated before the period start or after the period end (opening balances excluded).

- Severity: medium
- Needs: ledger

### JE-009 — Cash balance goes negative

Day-end balance of a cash ledger falls below zero. Needs the opening balance in the extract (voucher type 'opening'); without it, days before the first receipts may show falsely.

- Severity: high
- Provision: Books cannot show a credit cash balance; indicates unrecorded receipts or payments recorded early
- Needs: ledger

### JE-010 — Round-sum journals

Journals for exact multiples of the round unit — often estimates or adjustments without workings.

- Severity: low; fraud indicator
- Provision: SA 240 para 33(a): testing of journal entries
- Needs: ledger
- Threshold `round_unit`: Multiple of (₹) — default 100,000
- Threshold `min_amount`: Minimum voucher value (₹) — default 100,000

### JE-011 — Voucher amounts depart from Benford's law

First-digit distribution of voucher values compared with Benford's expected frequencies. A mean absolute deviation above 0.015 is Nigrini's threshold for nonconformity. This is an indicator for where to sample, not evidence of misstatement.

- Severity: low; fraud indicator
- Provision: SA 240 para 33(a): testing of journal entries
- Needs: ledger
- Threshold `min_vouchers`: Minimum vouchers to test — default 300
- Threshold `mad_limit`: Mean absolute deviation limit — default 0.015

### JE-012 — Journals dated on Sundays

Journal vouchers dated on a Sunday at or above the limit.

- Severity: low; fraud indicator
- Provision: SA 240 para 33(a): testing of journal entries
- Needs: ledger
- Threshold `min_amount`: Minimum voucher value (₹) — default 100,000

## Treasury

### TRE-001 — Cash payment above the s.40A(3) limit

Cash paid to one ledger in one day above the limit. The whole payment is disallowable. Loan repayments are tested under TRE-003; Rule 6DD exceptions need review.

- Severity: high
- Provision: Income-tax Act, 1961 s.40A(3): Rs 10,000 per person per day (Rs 35,000 for goods carriage); exceptions in Rule 6DD
- Needs: ledger
- Threshold `limit`: Limit per person per day (₹) — default 10,000
- Threshold `transport_limit`: Limit for goods carriage (₹) — default 35,000

### TRE-002 — Cash receipt of Rs 2 lakh or more

Cash received from one ledger in one day at or above the limit. Receipts in respect of a single transaction or one event spread over days also count and need review.

- Severity: critical
- Provision: Income-tax Act, 1961 s.269ST; penalty s.271DA equal to the amount received
- Needs: ledger
- Threshold `limit`: Limit (₹) — default 200,000

### TRE-003 — Loan or deposit taken or repaid in cash

Cash movements of the limit or more against loan/deposit ledgers. The sections also apply where the outstanding balance reaches the limit — check smaller amounts on review.

- Severity: critical
- Provision: Income-tax Act, 1961 s.269SS (acceptance) and s.269T (repayment); penalties s.271D, s.271E
- Needs: ledger.ledger_group
- Threshold `limit`: Limit (₹) — default 20,000

### TRE-004 — Money paid out and returned by the same party

A bank payment to a party and a deposit of the same amount from that party within a few days.

- Severity: high; fraud indicator
- Needs: bank.counterparty
- Threshold `window_days`: Days between payment and return — default 3
- Threshold `min_amount`: Minimum amount (₹) — default 100,000

### TRE-005 — Large bank payments without a reference

Withdrawals at or above the limit with no cheque/UTR reference recorded.

- Severity: medium
- Needs: bank
- Threshold `min_amount`: Minimum amount (₹) — default 100,000

### TRE-006 — Same amount paid twice to a party on one day

Two or more bank payments of the same amount to the same party (or with the same description) on the same day.

- Severity: high; fraud indicator
- Needs: bank
- Threshold `min_amount`: Minimum amount (₹) — default 10,000

## Payroll

### PAY-001 — Salary paid to a person not in the employee master

Payroll lines whose employee code does not exist in the employee master.

- Severity: critical; fraud indicator
- Needs: payroll, employees

### PAY-002 — Salary paid after the date of leaving

Salary for wage months after the month of leaving plus the grace period.

- Severity: critical; fraud indicator
- Needs: payroll, employees.date_left
- Threshold `grace_months`: Months allowed for full and final settlement — default 1

### PAY-003 — Employees sharing a bank account

Two or more employees with the same salary bank account.

- Severity: high; fraud indicator
- Needs: employees.bank_account

### PAY-004 — Employees sharing a PAN

Two or more employee records with the same PAN — a duplicate or fictitious record.

- Severity: high; fraud indicator
- Needs: employees.pan

### PAY-005 — Sharp rise in gross pay

Gross pay higher than the employee's previous month by more than the set percentage.

- Severity: medium
- Needs: payroll
- Threshold `rise_pct`: Month-on-month rise (%) — default 50
- Threshold `min_rise`: Minimum rise (₹) — default 5,000

### PAY-006 — Provident fund short deducted

Employees with basic + DA up to the wage ceiling whose PF deduction is below 12%. Employees above the ceiling may be excluded employees and are not tested.

- Severity: high
- Provision: EPF Scheme, 1952 para 26 and 29: 12% of basic + DA; compulsory up to Rs 15,000
- Needs: payroll.basic

### PAY-007 — ESI short deducted

Employees with gross wages up to the ceiling whose ESI deduction is below 0.75% (rounded up to the next rupee). An employee who crosses the ceiling mid contribution period stays covered until it ends — those months are not tested here.

- Severity: high
- Provision: ESI Act, 1948 s.39; ESI (Central) Rules r.50, r.51: employee 0.75% on wages up to Rs 21,000
- Needs: payroll

### PAY-008 — Net pay exceeds gross less deductions

Net pay is more than gross minus PF, ESI and other deductions.

- Severity: high
- Needs: payroll
- Threshold `tolerance`: Rounding tolerance (₹) — default 1.0

### PAY-009 — Employee paid twice for a month

More than one payroll line for the same employee and wage month.

- Severity: critical; fraud indicator
- Needs: payroll

## Inventory

### INV-001 — Stock balance goes negative

Running quantity of an item at a location falls below zero — issues recorded before receipts, or missing receipts.

- Severity: high
- Needs: stock

### INV-002 — Non-moving stock

Items held at the data date with no issue for the set number of days. Value at weighted average inward rate.

- Severity: medium
- Provision: AS 2 / Ind AS 2: lower of cost and net realisable value
- Needs: stock
- Threshold `days`: Days without an issue — default 180

### INV-003 — High stock write-offs and shortages

Quantity adjusted out (shortage, write-off) as a share of opening plus receipts.

- Severity: high
- Provision: CARO 2020 para 3(ii)(a): report discrepancies of 10% or more in aggregate for each class of inventory
- Needs: stock
- Threshold `pct`: Adjusted-out share of inward quantity (%) — default 2

### INV-004 — Receipt rate far from the item's average

Receipts priced well above or below the item's weighted average inward rate.

- Severity: medium
- Needs: stock.rate
- Threshold `variance_pct`: Variance from average rate (%) — default 25
- Threshold `min_receipts`: Minimum receipts for the item — default 3

### INV-005 — Stock movements without a reference document

Receipts, issues and adjustments with no document reference.

- Severity: low
- Needs: stock.reference
