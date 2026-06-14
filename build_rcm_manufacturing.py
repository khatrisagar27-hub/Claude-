"""
Risk Control Matrix (RCM) — Manufacturing Business
Generates: Risk_Control_Matrix_Manufacturing.xlsx
"""
import openpyxl
from datetime import date
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ── COLOURS ───────────────────────────────────────────────────────────────────
NAVY        = "1F3864"
GOLD        = "D4A017"
WHITE       = "FFFFFF"
LIGHT_BLUE  = "DCE6F1"
DARK_TEXT   = "1A1A2E"
QUERY_BG    = "F0F4F8"
QUERY_FC    = "1A237E"
FIELDS_BG   = "F5F5F5"

RISK_CLR  = {"High": "C00000", "Medium": "ED7D31", "Low": "375623"}
CTRL_CLR  = {"Preventive": "1F4E79", "Detective": "6F31A0", "Corrective": "1F8C7A"}
CAT_CLR   = {"Financial": "1A237E", "Operational": "1B5E20",
             "Compliance": "B71C1C", "Fraud": "4A148C"}

HEADERS = [
    "Sr.\nNo.", "Process / Sub-Process", "Risk\nCategory", "Risk Description",
    "Risk\nRating", "Control Objective", "Control\nType", "Control Activity",
    "Freq-\nuency", "Owner /\nResponsible", "Data Source /\nRegister",
    "Fields Required\nfor Query", "Audit Query / Test Procedure\n(SQL Logic)",
    "Expected Output /\nRed Flag", "Remarks /\nObservations"
]
COL_WIDTHS = [5, 26, 14, 36, 11, 30, 13, 38, 11, 20, 20, 28, 52, 34, 20]

# ── HELPERS ───────────────────────────────────────────────────────────────────
def hf(h): return PatternFill("solid", fgColor=h)

def bdr():
    s = Side(style="thin", color="BBBBBB")
    return Border(left=s, right=s, top=s, bottom=s)

def wc(ws, r, c, val, bg=None, fc=DARK_TEXT, bold=False, sz=9,
        wrap=True, ha="left", fn="Calibri"):
    cell = ws.cell(row=r, column=c, value=val)
    if bg: cell.fill = hf(bg)
    cell.font = Font(name=fn, size=sz, bold=bold, color=fc)
    cell.alignment = Alignment(horizontal=ha, vertical="top", wrap_text=wrap)
    cell.border = bdr()
    return cell

def scw(ws, ci, w):
    ws.column_dimensions[get_column_letter(ci)].width = w

def mtitle(ws, rng, text, bg, fc=WHITE, sz=12, bold=True):
    ws.merge_cells(rng)
    c = ws[rng.split(":")[0]]
    c.value, c.fill = text, hf(bg)
    c.font = Font(name="Calibri", size=sz, bold=bold, color=fc)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = bdr()

# ── DATA: 01 SALES ────────────────────────────────────────────────────────────
SALES_RCM = [
    {"process": "Sales – Invoice Generation", "risk_category": "Fraud",
     "risk_desc": "Duplicate invoices raised for same delivery leading to inflated revenue or double collection.",
     "risk_rating": "High", "control_obj": "Every invoice number is unique and maps to one delivery.",
     "control_type": "Detective", "control_activity": "Auto-sequential invoice numbering; monthly duplicate-check report by accounts team.",
     "frequency": "Monthly", "owner": "Accounts Manager", "data_source": "Sales Register / ERP",
     "fields_required": "invoice_no, party_name, invoice_date, taxable_value, gstin",
     "audit_query": "SELECT invoice_no, party_name, COUNT(*) AS cnt, SUM(taxable_value) AS total\nFROM sales_register\nGROUP BY invoice_no\nHAVING COUNT(*) > 1\nORDER BY cnt DESC;",
     "expected_output": "Zero rows expected. Any result = duplicate invoice — investigate immediately."},
    {"process": "Sales – Pricing", "risk_category": "Financial",
     "risk_desc": "Goods sold below cost price due to unauthorised discounts or pricing errors, eroding margins.",
     "risk_rating": "High", "control_obj": "All sales prices meet or exceed standard cost.",
     "control_type": "Preventive", "control_activity": "System block on invoices where unit price < standard cost; exceptions require CFO approval.",
     "frequency": "Daily", "owner": "Sales Manager / CFO", "data_source": "Sales Register, Cost Master",
     "fields_required": "invoice_no, item_code, unit_price, standard_cost, discount_pct",
     "audit_query": "SELECT s.invoice_no, s.item_code, s.unit_price, c.standard_cost,\n  ROUND((c.standard_cost - s.unit_price)/c.standard_cost*100,2) AS loss_pct\nFROM sales_register s JOIN cost_master c ON s.item_code = c.item_code\nWHERE s.unit_price < c.standard_cost;",
     "expected_output": "Any row = sale below cost. Review discount approval chain and pricing master."},
    {"process": "Sales – Invoice Dating", "risk_category": "Compliance",
     "risk_desc": "Back-dated or forward-dated invoices distort revenue recognition and GST period liability.",
     "risk_rating": "High", "control_obj": "Invoice date matches goods dispatch date; posting within same accounting period.",
     "control_type": "Detective", "control_activity": "System validation: invoice_date must be within ±3 days of e-way bill date; period-end review of posting dates.",
     "frequency": "Monthly", "owner": "Finance Manager", "data_source": "Sales Register, E-Way Bill Register",
     "fields_required": "invoice_no, invoice_date, posting_date, eway_bill_date",
     "audit_query": "SELECT invoice_no, invoice_date, posting_date,\n  DATEDIFF(posting_date, invoice_date) AS day_gap\nFROM sales_register\nWHERE ABS(DATEDIFF(posting_date, invoice_date)) > 7\nORDER BY day_gap DESC;",
     "expected_output": "Invoices with >7 day gap between invoice date and posting date. Likely period manipulation."},
    {"process": "Sales – Credit Control", "risk_category": "Financial",
     "risk_desc": "Sales made to customers who have exceeded their approved credit limit, increasing bad-debt risk.",
     "risk_rating": "High", "control_obj": "No sales order released when customer's outstanding exceeds credit limit.",
     "control_type": "Preventive", "control_activity": "ERP credit-hold rule blocks new orders when outstanding > credit limit; overrides require CFO approval with log.",
     "frequency": "Daily", "owner": "Credit Controller", "data_source": "Sales Register, Customer Master",
     "fields_required": "customer_id, invoice_no, outstanding_balance, credit_limit",
     "audit_query": "SELECT s.customer_id, s.party_name, SUM(s.invoice_value) AS outstanding,\n  c.credit_limit, (SUM(s.invoice_value)-c.credit_limit) AS excess\nFROM sales_register s JOIN customer_master c ON s.customer_id=c.id\nWHERE s.payment_status='Unpaid'\nGROUP BY s.customer_id HAVING outstanding > c.credit_limit;",
     "expected_output": "Customers with outstanding > credit limit. Verify if CFO override was obtained and documented."},
    {"process": "Sales – GST Compliance", "risk_category": "Compliance",
     "risk_desc": "Incorrect GST rate applied on invoice compared to HSN-linked rate, causing under/over-payment of GST.",
     "risk_rating": "High", "control_obj": "GST rate on every invoice matches the HSN master rate.",
     "control_type": "Detective", "control_activity": "Monthly GSTR-1 reconciliation vs books; HSN-linked rate auto-populated from item master.",
     "frequency": "Monthly", "owner": "Tax Manager", "data_source": "Sales Register, HSN Master",
     "fields_required": "invoice_no, hsn_code, gst_rate_charged, hsn_master_rate",
     "audit_query": "SELECT s.invoice_no, s.hsn_code, s.gst_rate AS charged,\n  h.gst_rate AS correct, s.taxable_value\nFROM sales_register s JOIN hsn_master h ON s.hsn_code=h.hsn_code\nWHERE s.gst_rate <> h.gst_rate;",
     "expected_output": "Any mismatch = potential GST liability. Raise credit/debit notes and amend GSTR-1."},
    {"process": "Sales – E-Way Bill", "risk_category": "Compliance",
     "risk_desc": "Goods dispatched without e-way bill for consignments > ₹50,000, violating GST rules.",
     "risk_rating": "High", "control_obj": "E-way bill generated before dispatch for all eligible consignments.",
     "control_type": "Detective", "control_activity": "Dispatch gate check: no vehicle release without e-way bill number; ERP auto-generates e-way bill on invoice save.",
     "frequency": "Daily", "owner": "Logistics / Tax Manager", "data_source": "Sales Register, E-Way Bill Portal",
     "fields_required": "invoice_no, invoice_value, dispatch_date, eway_bill_no, vehicle_no",
     "audit_query": "SELECT invoice_no, party_name, invoice_value, dispatch_date\nFROM sales_register\nWHERE invoice_value > 50000\n  AND (eway_bill_no IS NULL OR eway_bill_no = '')\n  AND dispatch_date IS NOT NULL;",
     "expected_output": "Invoices > ₹50K without e-way bill = GST rule violation. Penalty up to ₹10,000 per consignment."},
    {"process": "Sales – Sales Returns", "risk_category": "Financial",
     "risk_desc": "Sales returns accepted and recorded without a corresponding debit note, overstating revenue.",
     "risk_rating": "Medium", "control_obj": "Every sales return is supported by a debit note and inspection report.",
     "control_type": "Preventive", "control_activity": "ERP blocks GRN for sales return unless debit note number is entered; quality inspection required before acceptance.",
     "frequency": "Weekly", "owner": "Sales Manager", "data_source": "Sales Returns Register",
     "fields_required": "return_id, invoice_no, return_date, return_qty, debit_note_no, inspection_status",
     "audit_query": "SELECT return_id, invoice_no, return_date, return_qty, return_value\nFROM sales_returns\nWHERE (debit_note_no IS NULL OR debit_note_no='')\n   OR inspection_status != 'Approved';",
     "expected_output": "Returns without debit note = unverified revenue reduction. Could mask theft or fraudulent returns."},
    {"process": "Sales – Month-End Spike", "risk_category": "Fraud",
     "risk_desc": "Unusual spike in sales in last 3 days of month suggesting channel stuffing or fictitious sales.",
     "risk_rating": "Medium", "control_obj": "Sales distribution is consistent throughout the month.",
     "control_type": "Detective", "control_activity": "Monthly trend analysis of daily sales by finance; channel stuffing report reviewed by CFO.",
     "frequency": "Monthly", "owner": "CFO / Finance Manager", "data_source": "Sales Register",
     "fields_required": "invoice_no, invoice_date, invoice_value, party_name",
     "audit_query": "SELECT DATE(invoice_date) AS sale_date, COUNT(*) AS txn_cnt,\n  SUM(invoice_value) AS daily_sales\nFROM sales_register\nWHERE MONTH(invoice_date)=MONTH(CURRENT_DATE)\nGROUP BY DATE(invoice_date)\nORDER BY daily_sales DESC;",
     "expected_output": "If last-3-day sales > 50% of monthly total = potential channel stuffing. Cross-check with dispatch records."},
]

# ── DATA: 02 PURCHASES ────────────────────────────────────────────────────────
PURCHASE_RCM = [
    {"process": "Purchase – Invoice Verification", "risk_category": "Fraud",
     "risk_desc": "Duplicate vendor invoices paid twice for the same supply, resulting in financial loss.",
     "risk_rating": "High", "control_obj": "Each vendor invoice is recorded and paid only once.",
     "control_type": "Detective", "control_activity": "ERP duplicate-check on vendor ID + invoice number at entry; three-way match (PO-GRN-Invoice) mandatory.",
     "frequency": "Daily", "owner": "Accounts Payable Manager", "data_source": "Purchase Register / ERP",
     "fields_required": "vendor_id, vendor_invoice_no, invoice_date, invoice_amount",
     "audit_query": "SELECT vendor_id, vendor_invoice_no, COUNT(*) AS cnt, SUM(invoice_amount) AS total\nFROM purchase_register\nGROUP BY vendor_id, vendor_invoice_no\nHAVING COUNT(*) > 1;",
     "expected_output": "Zero rows expected. Any duplicate = risk of double payment. Verify payment records immediately."},
    {"process": "Purchase – PO Compliance", "risk_category": "Operational",
     "risk_desc": "Purchases made without an approved Purchase Order, bypassing procurement controls.",
     "risk_rating": "High", "control_obj": "All purchases are backed by an approved PO.",
     "control_type": "Preventive", "control_activity": "ERP blocks GRN entry without valid PO number; exceptions require MD approval with documented justification.",
     "frequency": "Weekly", "owner": "Purchase Manager", "data_source": "Purchase Register, PO Register",
     "fields_required": "grn_no, vendor_id, invoice_no, po_no, invoice_amount",
     "audit_query": "SELECT grn_no, vendor_id, invoice_no, invoice_amount, invoice_date\nFROM purchase_register\nWHERE po_no IS NULL OR po_no = ''\nORDER BY invoice_amount DESC;",
     "expected_output": "Purchases without PO = unauthorized procurement. High-value items require immediate investigation."},
    {"process": "Purchase – Price Verification", "risk_category": "Financial",
     "risk_desc": "Items purchased at rates significantly above approved price list, inflating material cost.",
     "risk_rating": "High", "control_obj": "Purchase price does not exceed approved rate by more than 5%.",
     "control_type": "Detective", "control_activity": "Monthly price variance report comparing invoice rate vs. rate contract / approved price list.",
     "frequency": "Monthly", "owner": "Purchase Manager / CFO", "data_source": "Purchase Register, Price List Master",
     "fields_required": "item_code, vendor_id, invoice_rate, approved_rate, quantity",
     "audit_query": "SELECT p.item_code, p.vendor_id, p.invoice_rate, pl.approved_rate,\n  ROUND(ABS(p.invoice_rate-pl.approved_rate)/pl.approved_rate*100,2) AS variance_pct\nFROM purchase_register p JOIN price_list pl ON p.item_code=pl.item_code\nWHERE ABS(p.invoice_rate-pl.approved_rate)/pl.approved_rate*100 > 5\nORDER BY variance_pct DESC;",
     "expected_output": "Variance >5% = possible price manipulation or collusion. Verify rate contract and approve exceptions."},
    {"process": "Purchase – GST Input Tax Credit", "risk_category": "Compliance",
     "risk_desc": "ITC claimed on invoices not reflecting in GSTR-2B, creating GST reversal liability.",
     "risk_rating": "High", "control_obj": "ITC claimed only matches amounts available in GSTR-2B.",
     "control_type": "Detective", "control_activity": "Monthly GSTR-2B vs purchase register reconciliation before ITC is availed in GSTR-3B.",
     "frequency": "Monthly", "owner": "Tax Manager", "data_source": "Purchase Register, GSTR-2B",
     "fields_required": "vendor_gstin, invoice_no, itc_claimed, gstr2b_amount, month",
     "audit_query": "SELECT vendor_gstin, invoice_no, itc_claimed, gstr2b_amount,\n  (itc_claimed - COALESCE(gstr2b_amount,0)) AS excess_itc\nFROM itc_register\nWHERE itc_claimed > COALESCE(gstr2b_amount,0);",
     "expected_output": "Excess ITC claimed = GST reversal + 18% interest risk. Reconcile before filing GSTR-3B."},
    {"process": "Purchase – Vendor Registration", "risk_category": "Compliance",
     "risk_desc": "Purchases from unregistered vendors with GST charged — not eligible for ITC.",
     "risk_rating": "Medium", "control_obj": "Only GST-registered vendors are approved for taxable supplies.",
     "control_type": "Preventive", "control_activity": "Vendor master set-up requires GSTIN validation on GST portal before activation; periodic re-validation.",
     "frequency": "Monthly", "owner": "Procurement / Tax Manager", "data_source": "Purchase Register, Vendor Master",
     "fields_required": "vendor_id, vendor_name, gstin, gst_charged, invoice_amount",
     "audit_query": "SELECT p.vendor_id, v.vendor_name, v.gstin, p.gst_charged, p.invoice_amount\nFROM purchase_register p JOIN vendor_master v ON p.vendor_id=v.id\nWHERE (v.gstin IS NULL OR v.gstin='') AND p.gst_charged > 0;",
     "expected_output": "Unregistered vendor charging GST = ITC ineligible + potential fake invoice. Reverse ITC claimed."},
    {"process": "Purchase – Related Party", "risk_category": "Fraud",
     "risk_desc": "Purchases made from entities related to directors/employees at non-arm's-length prices.",
     "risk_rating": "High", "control_obj": "Related-party transactions disclosed, approved by board, and priced at market rates.",
     "control_type": "Detective", "control_activity": "Related-party register maintained; all RPT purchases flagged in ERP; quarterly board disclosure.",
     "frequency": "Quarterly", "owner": "CFO / Board", "data_source": "Purchase Register, Related Party Register",
     "fields_required": "vendor_id, vendor_name, is_related_party, invoice_amount, market_rate",
     "audit_query": "SELECT p.vendor_id, v.vendor_name, SUM(p.invoice_amount) AS total_purchase,\n  v.relationship_to_director\nFROM purchase_register p JOIN vendor_master v ON p.vendor_id=v.id\nWHERE v.is_related_party='Yes'\nGROUP BY p.vendor_id ORDER BY total_purchase DESC;",
     "expected_output": "All RPT purchases should have board approval. Flag undisclosed RPTs to audit committee."},
    {"process": "Purchase – Advance Payments", "risk_category": "Financial",
     "risk_desc": "Advance payments made to vendors not adjusted against goods receipt, creating outstanding advances.",
     "risk_rating": "Medium", "control_obj": "All advances adjusted within 60 days of payment.",
     "control_type": "Detective", "control_activity": "Monthly advance reconciliation report; unadjusted advances >60 days escalated to CFO.",
     "frequency": "Monthly", "owner": "Accounts Payable", "data_source": "Advance Payment Register",
     "fields_required": "vendor_id, advance_amount, advance_date, grn_no, adjustment_date",
     "audit_query": "SELECT vendor_id, vendor_name, advance_amount, advance_date,\n  DATEDIFF(CURRENT_DATE, advance_date) AS days_outstanding\nFROM advance_payments\nWHERE grn_no IS NULL\n  AND DATEDIFF(CURRENT_DATE, advance_date) > 60\nORDER BY advance_amount DESC;",
     "expected_output": "Advances >60 days unadjusted = risk of fictitious vendor or prepayment misuse. Obtain GRN immediately."},
    {"process": "Purchase – GRNB Pending", "risk_category": "Financial",
     "risk_desc": "Goods received but vendor invoice not received/booked (GRNB), understating creditors liability.",
     "risk_rating": "Medium", "control_obj": "All GRNs have corresponding vendor invoices within 30 days.",
     "control_type": "Detective", "control_activity": "Weekly GRNB report reviewed by accounts payable; provision entry for GRNB at month-end.",
     "frequency": "Weekly", "owner": "Accounts Payable", "data_source": "GRN Register, Purchase Register",
     "fields_required": "grn_no, grn_date, item_code, grn_value, vendor_invoice_no",
     "audit_query": "SELECT g.grn_no, g.grn_date, g.vendor_id, g.grn_value,\n  DATEDIFF(CURRENT_DATE, g.grn_date) AS days_pending\nFROM grn_register g LEFT JOIN purchase_register p ON g.grn_no=p.grn_no\nWHERE p.vendor_invoice_no IS NULL\n  AND DATEDIFF(CURRENT_DATE, g.grn_date) > 30\nORDER BY g.grn_value DESC;",
     "expected_output": "GRNs >30 days without invoice = accrual required. High-value items may indicate delivery disputes."},
]

# ── DATA: 03 INVENTORY ────────────────────────────────────────────────────────
INVENTORY_RCM = [
    {"process": "Inventory – Stock Balance", "risk_category": "Operational",
     "risk_desc": "Negative stock balances in system indicating data entry errors or unauthorized issues.",
     "risk_rating": "High", "control_obj": "Stock balance is never negative for any item at any warehouse.",
     "control_type": "Detective", "control_activity": "Daily negative stock report run by storekeeper; ERP restriction on issuing stock beyond available quantity.",
     "frequency": "Daily", "owner": "Store Manager", "data_source": "Stock Ledger / ERP",
     "fields_required": "item_code, item_name, warehouse, closing_balance, unit",
     "audit_query": "SELECT item_code, item_name, warehouse,\n  closing_balance, unit\nFROM stock_ledger\nWHERE closing_balance < 0\nORDER BY closing_balance ASC;",
     "expected_output": "Zero rows expected. Negative stock = system bypass or unauthorized issue. Investigate immediately."},
    {"process": "Inventory – Physical Verification", "risk_category": "Fraud",
     "risk_desc": "Variance between physical stock count and system records indicating theft or data manipulation.",
     "risk_rating": "High", "control_obj": "System stock agrees with physical count within ±1% tolerance.",
     "control_type": "Detective", "control_activity": "Annual physical verification by independent team; perpetual cycle counts for high-value items; variance approval required.",
     "frequency": "Annually", "owner": "Internal Audit / Store Manager", "data_source": "Stock Verification Register",
     "fields_required": "item_code, system_qty, physical_qty, unit_cost",
     "audit_query": "SELECT item_code, system_qty, physical_qty,\n  (system_qty - physical_qty) AS variance_qty,\n  ROUND((system_qty - physical_qty) * unit_cost, 2) AS variance_value\nFROM stock_verification\nWHERE ABS(system_qty - physical_qty) > 0\nORDER BY ABS(variance_value) DESC;",
     "expected_output": "Unexplained variances = potential theft or inaccurate recording. Variances >₹10,000 require CFO approval."},
    {"process": "Inventory – Slow Moving Stock", "risk_category": "Financial",
     "risk_desc": "Slow-moving or obsolete stock not identified and provisioned, overstating inventory value.",
     "risk_rating": "Medium", "control_obj": "Slow-moving stock identified, reported, and provisioned at least annually.",
     "control_type": "Detective", "control_activity": "Quarterly slow-moving stock report; items with no movement in 90 days flagged for review and disposal decision.",
     "frequency": "Quarterly", "owner": "Store Manager / CFO", "data_source": "Stock Ledger",
     "fields_required": "item_code, item_name, closing_qty, last_movement_date, unit_cost",
     "audit_query": "SELECT item_code, item_name, closing_qty,\n  last_movement_date,\n  DATEDIFF(CURRENT_DATE, last_movement_date) AS days_idle,\n  ROUND(closing_qty * unit_cost, 2) AS stock_value\nFROM stock_ledger\nWHERE last_movement_date < DATE_SUB(CURRENT_DATE, INTERVAL 90 DAY)\n  AND closing_qty > 0\nORDER BY stock_value DESC;",
     "expected_output": "Stock idle >90 days = slow-moving. >180 days = dead stock. Provision and consider disposal."},
    {"process": "Inventory – Write-Offs", "risk_category": "Fraud",
     "risk_desc": "Unauthorized stock write-offs used to conceal pilferage or adjust physical shortages.",
     "risk_rating": "High", "control_obj": "All stock write-offs approved by CFO with supporting investigation report.",
     "control_type": "Preventive", "control_activity": "Write-off requires approval workflow: Store → Finance Manager → CFO; physical evidence (damaged goods photos) mandatory.",
     "frequency": "As needed", "owner": "CFO", "data_source": "Stock Adjustment Register",
     "fields_required": "adjustment_no, item_code, write_off_qty, write_off_value, approved_by, reason",
     "audit_query": "SELECT adjustment_no, item_code, write_off_qty,\n  write_off_value, adjustment_date, approved_by\nFROM stock_adjustments\nWHERE adjustment_type = 'Write-Off'\n  AND (approved_by IS NULL OR approval_date IS NULL)\nORDER BY write_off_value DESC;",
     "expected_output": "Unapproved write-offs = possible concealment of theft. Require immediate CFO review and documentation."},
    {"process": "Inventory – Reorder Level", "risk_category": "Operational",
     "risk_desc": "Key raw materials fall below reorder level causing production stoppages and emergency procurement costs.",
     "risk_rating": "Medium", "control_obj": "Procurement initiated when stock reaches reorder level to prevent stockouts.",
     "control_type": "Preventive", "control_activity": "ERP auto-alert when stock hits reorder level; purchase requisition auto-generated for critical items.",
     "frequency": "Daily", "owner": "Store Manager / Purchase Manager", "data_source": "Stock Ledger, Item Master",
     "fields_required": "item_code, item_name, closing_qty, reorder_level, lead_time_days",
     "audit_query": "SELECT s.item_code, i.item_name, s.closing_qty,\n  i.reorder_level, i.lead_time_days,\n  (i.reorder_level - s.closing_qty) AS shortfall\nFROM stock_ledger s JOIN item_master i ON s.item_code=i.item_code\nWHERE s.closing_qty < i.reorder_level\nORDER BY shortfall DESC;",
     "expected_output": "Items below reorder = production risk. Initiate procurement immediately for critical raw materials."},
    {"process": "Inventory – Issues Without Work Order", "risk_category": "Fraud",
     "risk_desc": "Raw materials issued from store without a valid production work order, enabling unauthorized removal.",
     "risk_rating": "High", "control_obj": "All material issues linked to an approved production or work order.",
     "control_type": "Preventive", "control_activity": "ERP gate: material issue transaction requires valid work order number; gate register maintained by security.",
     "frequency": "Daily", "owner": "Store Manager / Production Manager", "data_source": "Material Issue Register",
     "fields_required": "issue_no, item_code, issue_qty, issue_date, work_order_no, issued_to",
     "audit_query": "SELECT mi.issue_no, mi.item_code, mi.issue_qty,\n  mi.issue_date, mi.issued_to, mi.issue_value\nFROM material_issues mi\nLEFT JOIN production_orders po ON mi.work_order_no=po.work_order_no\nWHERE mi.work_order_no IS NULL OR po.work_order_no IS NULL\nORDER BY mi.issue_value DESC;",
     "expected_output": "Issues without work order = unauthorized material removal. Could indicate theft or off-book production."},
    {"process": "Inventory – High Value Adjustments", "risk_category": "Financial",
     "risk_desc": "High-value positive stock adjustments inflating inventory value without physical receipt of goods.",
     "risk_rating": "Medium", "control_obj": "Stock adjustments exceeding ₹1 lakh require documented justification and CFO approval.",
     "control_type": "Detective", "control_activity": "All positive adjustments > ₹1 lakh reported to CFO with supporting documents; internal audit spot-check.",
     "frequency": "Monthly", "owner": "Internal Audit / CFO", "data_source": "Stock Adjustment Register",
     "fields_required": "adjustment_no, item_code, adjustment_type, adjustment_qty, adjustment_value, approved_by",
     "audit_query": "SELECT adjustment_no, item_code, adjustment_type,\n  adjustment_qty, adjustment_value, adjustment_date, approved_by\nFROM stock_adjustments\nWHERE adjustment_type = 'Positive Adjustment'\n  AND adjustment_value > 100000\nORDER BY adjustment_value DESC;",
     "expected_output": "Large positive adjustments without supporting GRN/inspection report = fictitious stock inflation."},
]

# ── DATA: 04 PRODUCTION / WIP ─────────────────────────────────────────────────
PRODUCTION_RCM = [
    {"process": "Production – WIP Conversion", "risk_category": "Operational",
     "risk_desc": "WIP balances not converted to finished goods within standard lead time, tying up capital.",
     "risk_rating": "Medium", "control_obj": "All production orders closed within standard lead time.",
     "control_type": "Detective", "control_activity": "Weekly WIP ageing report reviewed by Production Manager; escalated to CFO if overdue > 2 weeks.",
     "frequency": "Weekly", "owner": "Production Manager", "data_source": "Production Register / ERP",
     "fields_required": "prod_order_no, item_code, qty_ordered, qty_produced, planned_end, status",
     "audit_query": "SELECT prod_order_no, item_code, qty_ordered,\n  qty_produced, planned_end,\n  DATEDIFF(CURRENT_DATE, planned_end) AS days_overdue\nFROM production_orders\nWHERE status = 'WIP'\n  AND planned_end < CURRENT_DATE\nORDER BY days_overdue DESC;",
     "expected_output": "Overdue WIP = production bottleneck or incomplete recording. Investigate orders >30 days overdue."},
    {"process": "Production – BOM Consumption Variance", "risk_category": "Financial",
     "risk_desc": "Actual material consumption differs significantly from BOM standard, inflating cost or masking theft.",
     "risk_rating": "High", "control_obj": "Actual material usage within ±5% of BOM standard quantities.",
     "control_type": "Detective", "control_activity": "Monthly production variance report comparing actual vs BOM consumption; variances >5% investigated.",
     "frequency": "Monthly", "owner": "Production Manager / Finance", "data_source": "Production Register, BOM Master",
     "fields_required": "prod_order_no, item_code, actual_qty_used, std_qty_per_unit, qty_produced",
     "audit_query": "SELECT p.prod_order_no, p.item_code,\n  ROUND(b.std_qty_per_unit * p.qty_produced,3) AS std_consumption,\n  p.actual_qty_used AS actual,\n  ROUND((p.actual_qty_used - b.std_qty_per_unit*p.qty_produced)/\n    (b.std_qty_per_unit*p.qty_produced)*100,2) AS variance_pct\nFROM production_actuals p JOIN bom_master b ON p.item_code=b.item_code\nWHERE ABS((p.actual_qty_used-b.std_qty_per_unit*p.qty_produced)/\n  (b.std_qty_per_unit*p.qty_produced)*100) > 5;",
     "expected_output": "Variance >5% = investigate. Excess usage may indicate material theft or BOM inaccuracy."},
    {"process": "Production – Scrap & Rejection", "risk_category": "Operational",
     "risk_desc": "Rejection/scrap rate above acceptable threshold, indicating quality issues or material wastage.",
     "risk_rating": "Medium", "control_obj": "Rejection rate kept below 3% of production quantity.",
     "control_type": "Detective", "control_activity": "Daily production quality report; scrap disposal requires weighment and security witness; scrap sold through tender.",
     "frequency": "Daily", "owner": "QC Manager / Production Manager", "data_source": "Production Register, Scrap Register",
     "fields_required": "prod_order_no, produced_qty, rejected_qty, scrap_qty, rejection_reason",
     "audit_query": "SELECT prod_order_no, item_code, produced_qty,\n  rejected_qty, scrap_qty,\n  ROUND((rejected_qty/produced_qty)*100,2) AS rejection_pct\nFROM production_register\nWHERE produced_qty > 0\n  AND (rejected_qty/produced_qty)*100 > 3\nORDER BY rejection_pct DESC;",
     "expected_output": "Rejection >3% = quality failure. Scrap disposal without approval = possible theft of scrap material."},
    {"process": "Production – Rework Cost", "risk_category": "Financial",
     "risk_desc": "Excessive rework costs beyond threshold indicating recurring quality failures or cost manipulation.",
     "risk_rating": "Medium", "control_obj": "Rework cost does not exceed 5% of production cost.",
     "control_type": "Detective", "control_activity": "Monthly rework cost analysis by product line; root cause analysis mandatory if threshold breached.",
     "frequency": "Monthly", "owner": "Production Manager / QC", "data_source": "Production Register, Cost Records",
     "fields_required": "prod_order_no, item_code, standard_cost, rework_cost, rework_reason",
     "audit_query": "SELECT prod_order_no, item_code, standard_cost, rework_cost,\n  ROUND(rework_cost/standard_cost*100,2) AS rework_pct\nFROM production_register\nWHERE standard_cost > 0\n  AND rework_cost/standard_cost*100 > 5\nORDER BY rework_pct DESC;",
     "expected_output": "Rework >5% of cost = persistent quality issue or inflated cost reporting. Needs root-cause analysis."},
    {"process": "Production – Scrap Disposal", "risk_category": "Fraud",
     "risk_desc": "Scrap material disposed without proper authorization or at below-market value, causing revenue leakage.",
     "risk_rating": "High", "control_obj": "All scrap disposals authorized and sold through competitive tendering.",
     "control_type": "Preventive", "control_activity": "Scrap sale requires purchase committee approval; security weighment slip mandatory; proceeds deposited in company account.",
     "frequency": "As needed", "owner": "Purchase Committee / CFO", "data_source": "Scrap Register",
     "fields_required": "scrap_lot_no, scrap_weight, scrap_value, sale_rate, buyer_name, approval_ref",
     "audit_query": "SELECT scrap_lot_no, scrap_weight, scrap_value,\n  sale_rate, buyer_name, approval_ref\nFROM scrap_register\nWHERE approval_ref IS NULL\n   OR sale_rate < (SELECT market_rate FROM scrap_rate_master\n                   WHERE material_type=scrap_register.material_type);",
     "expected_output": "Unapproved scrap sales or below-market rates = potential fraud. Cross-check with weighment slips."},
    {"process": "Production – Labour Efficiency", "risk_category": "Financial",
     "risk_desc": "Actual machine/labour hours significantly exceed standard hours, inflating conversion cost.",
     "risk_rating": "Medium", "control_obj": "Actual hours within 10% of standard hours for each production order.",
     "control_type": "Detective", "control_activity": "Monthly labour efficiency variance report; excess hours require production supervisor approval and root cause note.",
     "frequency": "Monthly", "owner": "Production Manager / Finance", "data_source": "Time & Attendance, Production Register",
     "fields_required": "prod_order_no, standard_hours, actual_hours, labour_rate",
     "audit_query": "SELECT prod_order_no, standard_hours, actual_hours,\n  ROUND((actual_hours-standard_hours)/standard_hours*100,2) AS efficiency_loss_pct,\n  ROUND((actual_hours-standard_hours)*labour_rate,2) AS excess_cost\nFROM production_register\nWHERE standard_hours > 0\n  AND (actual_hours-standard_hours)/standard_hours*100 > 10\nORDER BY excess_cost DESC;",
     "expected_output": "Efficiency loss >10% = training need or downtime issue. Excess cost to be investigated and reported."},
]

# ── DATA: 05 PAYROLL ──────────────────────────────────────────────────────────
PAYROLL_RCM = [
    {"process": "Payroll – Ghost Employees", "risk_category": "Fraud",
     "risk_desc": "Salary paid to employees with zero attendance in biometric system — 'ghost employees' siphoning funds.",
     "risk_rating": "High", "control_obj": "Salary paid only to employees with verified attendance records.",
     "control_type": "Detective", "control_activity": "Monthly reconciliation of payroll list vs biometric attendance; payroll processed only after HR sign-off on attendance.",
     "frequency": "Monthly", "owner": "HR Manager / CFO", "data_source": "Payroll Register, Biometric Attendance",
     "fields_required": "emp_id, emp_name, pay_month, gross_salary, biometric_days, bank_account",
     "audit_query": "SELECT p.emp_id, p.emp_name, p.gross_salary, p.pay_month,\n  COALESCE(a.biometric_days, 0) AS biometric_days\nFROM payroll_register p\nLEFT JOIN attendance a ON p.emp_id=a.emp_id AND p.pay_month=a.month\nWHERE COALESCE(a.biometric_days,0) = 0 AND p.gross_salary > 0\nORDER BY p.gross_salary DESC;",
     "expected_output": "Any employee with salary but zero biometric days = ghost employee risk. Verify with ID and physical presence."},
    {"process": "Payroll – Duplicate Identity", "risk_category": "Fraud",
     "risk_desc": "Multiple employees sharing same PAN or Aadhaar number indicating duplicate or fictitious employees.",
     "risk_rating": "High", "control_obj": "Each employee has a unique PAN and Aadhaar on record.",
     "control_type": "Detective", "control_activity": "Payroll master validation: unique constraint on PAN and Aadhaar; annual re-verification with HR.",
     "frequency": "Annually", "owner": "HR Manager", "data_source": "Employee Master",
     "fields_required": "emp_id, emp_name, pan_no, aadhaar_no, bank_account",
     "audit_query": "SELECT pan_no, COUNT(*) AS cnt, GROUP_CONCAT(emp_id) AS emp_ids\nFROM employee_master\nWHERE pan_no IS NOT NULL\nGROUP BY pan_no HAVING COUNT(*) > 1\nUNION ALL\nSELECT aadhaar_no, COUNT(*), GROUP_CONCAT(emp_id)\nFROM employee_master WHERE aadhaar_no IS NOT NULL\nGROUP BY aadhaar_no HAVING COUNT(*) > 1;",
     "expected_output": "Duplicate PAN/Aadhaar = fictitious employee or data error. Verify KYC documents immediately."},
    {"process": "Payroll – Grade Compliance", "risk_category": "Financial",
     "risk_desc": "Salary paid above the maximum of the employee's approved pay grade without authorization.",
     "risk_rating": "High", "control_obj": "Gross salary of each employee does not exceed their approved grade maximum.",
     "control_type": "Preventive", "control_activity": "Payroll system blocks salary entry above grade maximum; exceptions require MD and HR approval with board resolution.",
     "frequency": "Monthly", "owner": "HR Manager / CFO", "data_source": "Payroll Register, Grade Master",
     "fields_required": "emp_id, emp_name, grade, gross_salary, max_salary_for_grade",
     "audit_query": "SELECT p.emp_id, p.emp_name, p.grade, p.gross_salary,\n  g.max_salary, (p.gross_salary - g.max_salary) AS excess\nFROM payroll_register p JOIN grade_master g ON p.grade=g.grade_code\nWHERE p.gross_salary > g.max_salary\nORDER BY excess DESC;",
     "expected_output": "Salary above grade max = unauthorized increment. Requires HR/CFO/MD approval documentation."},
    {"process": "Payroll – TDS Compliance", "risk_category": "Compliance",
     "risk_desc": "TDS not deducted on salaries above the exemption threshold, causing Section 192 default.",
     "risk_rating": "High", "control_obj": "TDS deducted on all employees with annual income above ₹2.5 lakh.",
     "control_type": "Preventive", "control_activity": "Payroll system auto-calculates TDS based on projected annual income; Form 16 generated annually.",
     "frequency": "Monthly", "owner": "Payroll Manager / Tax Manager", "data_source": "Payroll Register",
     "fields_required": "emp_id, gross_salary, projected_annual_income, tds_deducted, month",
     "audit_query": "SELECT emp_id, emp_name, gross_salary,\n  gross_salary*12 AS projected_annual,\n  tds_deducted, pay_month\nFROM payroll_register\nWHERE gross_salary * 12 > 250000\n  AND tds_deducted = 0\nORDER BY projected_annual DESC;",
     "expected_output": "Employees earning >₹2.5L annually with zero TDS = Section 192 default. File correction TDS statement."},
    {"process": "Payroll – PF/ESI Compliance", "risk_category": "Compliance",
     "risk_desc": "PF or ESI deduction/contribution not computed correctly, leading to statutory default.",
     "risk_rating": "High", "control_obj": "PF = 12% of basic salary; ESI = 0.75% employee + 3.25% employer on wages ≤ ₹21,000.",
     "control_type": "Detective", "control_activity": "Monthly reconciliation of payroll PF/ESI deductions vs ECR challan; auto-computation in payroll software.",
     "frequency": "Monthly", "owner": "HR / Compliance Manager", "data_source": "Payroll Register, PF Challan",
     "fields_required": "emp_id, basic_salary, pf_deducted, esi_deducted, gross_salary",
     "audit_query": "SELECT emp_id, basic_salary, pf_deducted,\n  ROUND(basic_salary*0.12,0) AS expected_pf,\n  ABS(pf_deducted - ROUND(basic_salary*0.12,0)) AS pf_diff\nFROM payroll_register\nWHERE ABS(pf_deducted - ROUND(basic_salary*0.12,0)) > 10;",
     "expected_output": "PF mismatch >₹10 = computation error. Risk of EPFO notice and penalty. Verify ECR filing."},
    {"process": "Payroll – Terminated Employees", "risk_category": "Fraud",
     "risk_desc": "Salary continues to be processed for employees who have been terminated, resigned, or retired.",
     "risk_rating": "High", "control_obj": "Payroll master updated immediately on employee separation; final settlement processed.",
     "control_type": "Preventive", "control_activity": "HR separation checklist triggers payroll deactivation; payroll team verifies active headcount vs HR master monthly.",
     "frequency": "Monthly", "owner": "HR Manager / Payroll Team", "data_source": "Payroll Register, HR Master",
     "fields_required": "emp_id, emp_name, termination_date, last_working_day, salary_paid, pay_month",
     "audit_query": "SELECT p.emp_id, p.emp_name, h.termination_date,\n  p.pay_month, p.gross_salary\nFROM payroll_register p JOIN hr_master h ON p.emp_id=h.emp_id\nWHERE h.termination_date IS NOT NULL\n  AND h.termination_date < STR_TO_DATE(CONCAT(p.pay_month,'-01'),'%Y-%m-%d')\nORDER BY h.termination_date;",
     "expected_output": "Ex-employee on payroll = fraud or delayed deactivation. Recover excess payment and deactivate immediately."},
    {"process": "Payroll – Cash Salary", "risk_category": "Compliance",
     "risk_desc": "Salary paid in cash above ₹20,000 violating Section 40A(3) of Income Tax Act.",
     "risk_rating": "High", "control_obj": "All salary payments above ₹20,000 made through bank transfer only.",
     "control_type": "Preventive", "control_activity": "Payroll policy mandates bank transfer for all employees; cash salary only permitted for daily wage workers ≤₹20,000.",
     "frequency": "Monthly", "owner": "CFO / Payroll Manager", "data_source": "Payroll Register, Bank Transfer Records",
     "fields_required": "emp_id, emp_name, gross_salary, payment_mode, pay_month",
     "audit_query": "SELECT emp_id, emp_name, gross_salary,\n  payment_mode, pay_month\nFROM payroll_register\nWHERE payment_mode = 'Cash'\n  AND gross_salary > 20000\nORDER BY gross_salary DESC;",
     "expected_output": "Cash salary >₹20K = Section 40A(3) disallowance risk. Shift to bank transfer immediately."},
]

# ── DATA: 06 FIXED ASSETS ─────────────────────────────────────────────────────
FIXED_ASSETS_RCM = [
    {"process": "Fixed Assets – Capitalisation", "risk_category": "Financial",
     "risk_desc": "Capital expenditure items below the threshold of ₹5,000 capitalised as fixed assets instead of being expensed.",
     "risk_rating": "Medium", "control_obj": "Items below capitalisation threshold are charged to expense in the year of purchase.",
     "control_type": "Preventive", "control_activity": "ERP capitalisation policy enforced: items < ₹5,000 auto-routed to expense ledger; Finance Manager reviews exceptions.",
     "frequency": "Monthly", "owner": "Finance Manager", "data_source": "Fixed Asset Register",
     "fields_required": "asset_id, asset_description, asset_value, capitalisation_date, account_head",
     "audit_query": "SELECT asset_id, asset_description, asset_value,\n  capitalisation_date, account_head\nFROM fixed_asset_register\nWHERE asset_value < 5000\nORDER BY asset_value;",
     "expected_output": "Assets < ₹5K in FAR = mis-capitalisation. Write back to P&L expense for current year."},
    {"process": "Fixed Assets – Disposal Authorization", "risk_category": "Fraud",
     "risk_desc": "Fixed assets disposed/scrapped without proper authorization, resulting in loss of company property.",
     "risk_rating": "High", "control_obj": "All asset disposals approved by MD with documented disposal memo.",
     "control_type": "Preventive", "control_activity": "Asset disposal form signed by department head, CFO, and MD; physical inspection before disposal; proceeds deposited to company account.",
     "frequency": "As needed", "owner": "CFO / MD", "data_source": "Asset Disposal Register",
     "fields_required": "asset_id, asset_description, wdv, disposal_date, sale_value, approved_by",
     "audit_query": "SELECT asset_id, asset_description, wdv,\n  disposal_date, sale_value, approved_by\nFROM asset_disposal_register\nWHERE approved_by IS NULL\n   OR approval_date IS NULL\nORDER BY wdv DESC;",
     "expected_output": "Unapproved disposals = risk of asset misappropriation. Verify physical existence and trace proceeds."},
    {"process": "Fixed Assets – Depreciation Rate", "risk_category": "Compliance",
     "risk_desc": "Depreciation applied at rates not complying with Companies Act 2013 Schedule II.",
     "risk_rating": "High", "control_obj": "All assets depreciated at rates prescribed in Schedule II or higher.",
     "control_type": "Detective", "control_activity": "Annual review of depreciation rates vs Schedule II by auditor; rate master maintained and approved by CA.",
     "frequency": "Annually", "owner": "Finance Manager / Statutory Auditor", "data_source": "Fixed Asset Register, Schedule II",
     "fields_required": "asset_id, asset_category, dep_rate_applied, schedule_ii_rate",
     "audit_query": "SELECT f.asset_id, f.asset_category, f.dep_rate,\n  s.prescribed_rate,\n  ABS(f.dep_rate - s.prescribed_rate) AS rate_diff\nFROM fixed_asset_register f\nJOIN schedule_ii_rates s ON f.asset_category=s.category\nWHERE f.dep_rate < s.prescribed_rate;",
     "expected_output": "Under-depreciation = inflated asset values + Companies Act non-compliance. Restate accounts."},
    {"process": "Fixed Assets – Idle Assets", "risk_category": "Financial",
     "risk_desc": "Assets not in productive use continuing to be depreciated, distorting true asset position.",
     "risk_rating": "Medium", "control_obj": "Idle assets identified, disclosed in notes, and depreciation reassessed.",
     "control_type": "Detective", "control_activity": "Annual asset verification includes in-use/idle status; idle assets >6 months flagged for disposal decision.",
     "frequency": "Annually", "owner": "Internal Audit / Finance Manager", "data_source": "Fixed Asset Register",
     "fields_required": "asset_id, asset_description, wdv, in_use_flag, idle_since, annual_depreciation",
     "audit_query": "SELECT asset_id, asset_description, wdv,\n  idle_since, annual_depreciation,\n  DATEDIFF(CURRENT_DATE, idle_since) AS days_idle\nFROM fixed_asset_register\nWHERE in_use_flag = 'No'\n  AND wdv > 0\n  AND annual_depreciation > 0\nORDER BY annual_depreciation DESC;",
     "expected_output": "Idle assets with depreciation = AS-10 disclosure required. Review for disposal or redeployment."},
    {"process": "Fixed Assets – Capex vs Opex", "risk_category": "Financial",
     "risk_desc": "Capital expenditure incorrectly charged to revenue (expenses), understating assets and overstating costs.",
     "risk_rating": "High", "control_obj": "All expenditure ≥ ₹5,000 and with useful life > 1 year is capitalised.",
     "control_type": "Detective", "control_activity": "Monthly review of Repairs & Maintenance and other expense ledgers for items that meet capitalisation criteria.",
     "frequency": "Monthly", "owner": "Finance Manager / CFO", "data_source": "Expense Ledger, Fixed Asset Register",
     "fields_required": "voucher_no, expense_account, amount, description, vendor_name",
     "audit_query": "SELECT voucher_no, expense_account, amount,\n  description, vendor_name, voucher_date\nFROM expense_ledger\nWHERE expense_account IN ('Repairs & Maintenance','Office Expenses','IT Expenses')\n  AND amount > 50000\nORDER BY amount DESC;",
     "expected_output": "High-value expense in R&M or similar = review for capitalisation. Items like AC, computers may qualify."},
    {"process": "Fixed Assets – Insurance Coverage", "risk_category": "Operational",
     "risk_desc": "Fixed assets not adequately insured, exposing company to unrecovered losses in case of fire/theft.",
     "risk_rating": "Medium", "control_obj": "All assets above ₹50,000 covered under adequate insurance policy.",
     "control_type": "Preventive", "control_activity": "Annual insurance review: insured value reconciled with gross block; policy renewed before expiry.",
     "frequency": "Annually", "owner": "CFO / Admin Manager", "data_source": "Fixed Asset Register, Insurance Register",
     "fields_required": "asset_id, gross_block, insured_value, policy_no, policy_expiry",
     "audit_query": "SELECT f.asset_id, f.asset_description, f.gross_block,\n  i.insured_value, i.policy_expiry,\n  (f.gross_block - COALESCE(i.insured_value,0)) AS underinsured_amount\nFROM fixed_asset_register f\nLEFT JOIN insurance_register i ON f.asset_id=i.asset_id\nWHERE f.gross_block > 50000\n  AND (i.policy_expiry < CURRENT_DATE OR i.insured_value IS NULL);",
     "expected_output": "Uninsured or underinsured assets = financial risk. Renew policies and update sum insured."},
]

# ── DATA: 07 CASH & BANK ──────────────────────────────────────────────────────
CASH_BANK_RCM = [
    {"process": "Cash – Payment Limit (Sec 40A(3))", "risk_category": "Compliance",
     "risk_desc": "Cash payments made above ₹10,000 per transaction risking Section 40A(3) disallowance.",
     "risk_rating": "High", "control_obj": "No single cash payment exceeds ₹10,000 to any party on any day.",
     "control_type": "Preventive", "control_activity": "ERP blocks cash payment vouchers above ₹10,000; petty cash reimbursement policy enforced.",
     "frequency": "Daily", "owner": "Cashier / Finance Manager", "data_source": "Cash Book",
     "fields_required": "voucher_no, payee_name, payment_amount, payment_date, mode",
     "audit_query": "SELECT voucher_no, payee_name, payment_amount,\n  payment_date, narration\nFROM cash_book\nWHERE mode = 'Cash' AND payment_amount > 10000\nORDER BY payment_amount DESC;",
     "expected_output": "Any cash payment > ₹10K = Section 40A(3) exposure. Expenditure disallowed in Income Tax. Raise journal to correct."},
    {"process": "Bank – Reconciliation", "risk_category": "Financial",
     "risk_desc": "Unreconciled bank items older than 30 days indicating unrecorded transactions or misappropriation.",
     "risk_rating": "High", "control_obj": "All bank items reconciled within 30 days; no stale unreconciled items.",
     "control_type": "Detective", "control_activity": "Monthly bank reconciliation prepared within 3 working days of month-end; CFO reviews and signs off.",
     "frequency": "Monthly", "owner": "Finance Manager / CFO", "data_source": "Bank Reconciliation Statement",
     "fields_required": "bank_account_no, transaction_date, description, amount, reconciled_status",
     "audit_query": "SELECT bank_account_no, transaction_date, description,\n  amount, reconciled_status,\n  DATEDIFF(CURRENT_DATE, transaction_date) AS days_unreconciled\nFROM bank_reconciliation\nWHERE reconciled_status = 'Unreconciled'\n  AND transaction_date < DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)\nORDER BY ABS(amount) DESC;",
     "expected_output": "Stale unreconciled items = risk of unrecorded transactions or misappropriation. Investigate immediately."},
    {"process": "Bank – Bearer / Cash Cheques", "risk_category": "Fraud",
     "risk_desc": "Cheques issued in favour of 'Cash', 'Bearer', or 'Self' enabling misappropriation without trail.",
     "risk_rating": "High", "control_obj": "All cheques are crossed account-payee and issued to specific named payees.",
     "control_type": "Preventive", "control_activity": "Cheque printing policy: all cheques pre-printed 'A/C Payee Only'; payee name required in ERP before cheque release.",
     "frequency": "Daily", "owner": "CFO / Finance Manager", "data_source": "Cheque Register / Bank Book",
     "fields_required": "cheque_no, payee_name, amount, issue_date, bank_account",
     "audit_query": "SELECT cheque_no, payee_name, amount,\n  issue_date, bank_account\nFROM cheque_register\nWHERE UPPER(payee_name) IN ('CASH','BEARER','SELF','TO SELF','A/C PAYEE')\nORDER BY amount DESC;",
     "expected_output": "Cash/bearer cheques = high fraud risk. All such payments require investigation and MD pre-approval."},
    {"process": "Cash – Petty Cash Controls", "risk_category": "Financial",
     "risk_desc": "Petty cash expenditures paid without supporting bills/receipts, enabling fictitious expense claims.",
     "risk_rating": "Medium", "control_obj": "Every petty cash payment is supported by an original receipt and approved by supervisor.",
     "control_type": "Preventive", "control_activity": "Petty cash voucher system: original bill mandatory for reimbursement; surprise petty cash count monthly.",
     "frequency": "Monthly", "owner": "Petty Cash Custodian / Finance Manager", "data_source": "Petty Cash Register",
     "fields_required": "voucher_no, amount, payee, purpose, receipt_attached, approved_by",
     "audit_query": "SELECT voucher_no, amount, payee, purpose,\n  receipt_attached, approved_by, voucher_date\nFROM petty_cash_register\nWHERE receipt_attached = 'No'\n   OR approved_by IS NULL\nORDER BY amount DESC;",
     "expected_output": "Vouchers without receipts or approval = fictitious expense risk. Physical receipts must be stapled to vouchers."},
    {"process": "Bank – Unusual Transfers", "risk_category": "Fraud",
     "risk_desc": "Large bank transfers to individual personal accounts without adequate business justification.",
     "risk_rating": "High", "control_obj": "All bank transfers are to registered business entities with documented purpose.",
     "control_type": "Detective", "control_activity": "Monthly review of bank statements for transfers to individuals; two-factor authorization for transfers > ₹5 lakh.",
     "frequency": "Monthly", "owner": "CFO / MD", "data_source": "Bank Statement / Bank Transfer Register",
     "fields_required": "txn_ref, beneficiary_name, beneficiary_account, amount, transfer_date, purpose",
     "audit_query": "SELECT txn_ref, beneficiary_name, amount,\n  transfer_date, purpose\nFROM bank_transfers\nWHERE beneficiary_type = 'Individual'\n  AND amount > 100000\nORDER BY amount DESC;",
     "expected_output": "Large transfers to individuals = fund diversion risk. Obtain board resolution and detailed justification."},
    {"process": "Bank – After-Hours Payments", "risk_category": "Fraud",
     "risk_desc": "Bank payments initiated outside business hours (before 9AM or after 6PM) without authorisation.",
     "risk_rating": "Medium", "control_obj": "All bank payments initiated during business hours with dual authorisation.",
     "control_type": "Detective", "control_activity": "Weekly report of payments outside business hours; bank dual-authorisation (Maker-Checker) enabled for all NEFT/RTGS.",
     "frequency": "Weekly", "owner": "CFO / Finance Manager", "data_source": "Bank Portal Log / Bank Statement",
     "fields_required": "txn_ref, amount, beneficiary_name, initiation_time, initiation_date, initiated_by",
     "audit_query": "SELECT txn_ref, amount, beneficiary_name,\n  initiation_time, initiation_date, initiated_by\nFROM bank_transactions\nWHERE TIME(initiation_time) NOT BETWEEN '09:00:00' AND '18:00:00'\n   OR DAYOFWEEK(initiation_date) IN (1,7)\nORDER BY amount DESC;",
     "expected_output": "Off-hours or weekend payments without pre-approval = unauthorised transaction risk. Verify with MD."},
    {"process": "Cash – Round Figure Withdrawals", "risk_category": "Fraud",
     "risk_desc": "Recurring round-figure cash withdrawals that may indicate systematic fund diversion.",
     "risk_rating": "Medium", "control_obj": "Cash withdrawals are for specific purposes with documented usage.",
     "control_type": "Detective", "control_activity": "Monthly cash book analysis for pattern of round-figure withdrawals; CFO review of all withdrawals > ₹50,000.",
     "frequency": "Monthly", "owner": "CFO / Internal Audit", "data_source": "Cash Book / Bank Statement",
     "fields_required": "voucher_no, withdrawal_amount, withdrawal_date, purpose, withdrawn_by",
     "audit_query": "SELECT voucher_no, withdrawal_amount, withdrawal_date,\n  purpose, withdrawn_by\nFROM cash_book\nWHERE withdrawal_amount > 50000\n  AND MOD(withdrawal_amount, 10000) = 0\nORDER BY withdrawal_date;",
     "expected_output": "Pattern of round-figure withdrawals = possible fund diversion. Cross-check with usage records and bank statement."},
]

# ── DATA: 08 DEBTORS / AR ─────────────────────────────────────────────────────
DEBTORS_RCM = [
    {"process": "Debtors – Overdue Monitoring", "risk_category": "Financial",
     "risk_desc": "Debtors outstanding beyond 90 days not monitored or followed up, increasing bad-debt risk.",
     "risk_rating": "High", "control_obj": "All debtor balances >90 days are actively followed up and provisioned.",
     "control_type": "Detective", "control_activity": "Monthly ageing analysis; collection calls initiated at 45 days; legal notice at 90 days; CFO review at 120 days.",
     "frequency": "Monthly", "owner": "Credit Controller / CFO", "data_source": "Debtors Ledger / AR Ageing",
     "fields_required": "party_name, invoice_no, invoice_date, due_date, outstanding_amount, overdue_days",
     "audit_query": "SELECT party_name, COUNT(invoice_no) AS invoices,\n  SUM(outstanding_amount) AS total_outstanding,\n  MAX(overdue_days) AS max_overdue\nFROM debtors_ledger\nWHERE overdue_days > 90 AND outstanding_amount > 0\nGROUP BY party_name\nORDER BY total_outstanding DESC;",
     "expected_output": "Debtors >90 days = bad debt risk. Provision @25% for 90-180 days, @50% for 180-365 days, @100% >365 days."},
    {"process": "Debtors – Credit Limit Monitoring", "risk_category": "Financial",
     "risk_desc": "Outstanding debtor balance exceeds approved credit limit, increasing collection risk.",
     "risk_rating": "High", "control_obj": "No debtor balance exceeds approved credit limit without CFO override.",
     "control_type": "Preventive", "control_activity": "ERP credit-hold blocks new sales orders when outstanding > credit limit; exceptions need CFO written approval.",
     "frequency": "Daily", "owner": "Credit Controller", "data_source": "Debtors Ledger, Customer Master",
     "fields_required": "customer_id, party_name, outstanding_balance, credit_limit",
     "audit_query": "SELECT d.customer_id, d.party_name,\n  SUM(d.outstanding_amount) AS outstanding,\n  c.credit_limit,\n  SUM(d.outstanding_amount) - c.credit_limit AS excess\nFROM debtors_ledger d JOIN customer_master c ON d.customer_id=c.id\nWHERE d.outstanding_amount > 0\nGROUP BY d.customer_id HAVING outstanding > c.credit_limit\nORDER BY excess DESC;",
     "expected_output": "Balance above credit limit = further exposure. Freeze new supplies and initiate recovery."},
    {"process": "Debtors – Provision for Doubtful Debts", "risk_category": "Financial",
     "risk_desc": "Provision for doubtful debts not created for debtors outstanding >180 days, overstating receivables.",
     "risk_rating": "High", "control_obj": "Provision created per company policy and AS-9 / Ind AS 109 requirements.",
     "control_type": "Detective", "control_activity": "Quarterly review by Finance Manager; provision schedule prepared and approved by CFO before accounts finalisation.",
     "frequency": "Quarterly", "owner": "Finance Manager / CFO", "data_source": "Debtors Ageing Report",
     "fields_required": "party_name, overdue_days, outstanding_amount, provision_amount",
     "audit_query": "SELECT party_name, overdue_days, outstanding_amount,\n  COALESCE(provision_amount,0) AS provision_made,\n  CASE WHEN overdue_days BETWEEN 180 AND 365 THEN outstanding_amount*0.5\n       WHEN overdue_days > 365 THEN outstanding_amount\n       ELSE 0 END AS required_provision\nFROM debtors_ledger\nWHERE overdue_days > 180\nHAVING required_provision > COALESCE(provision_amount,0);",
     "expected_output": "Insufficient provision = inflated debtors. Pass provision journal and disclose in notes to accounts."},
    {"process": "Debtors – Advance Adjustment", "risk_category": "Financial",
     "risk_desc": "Advance receipts from customers not adjusted against invoices, overstating both debtors and advances.",
     "risk_rating": "Medium", "control_obj": "All customer advances adjusted against invoices within 60 days.",
     "control_type": "Detective", "control_activity": "Monthly advance adjustment report; unadjusted advances >60 days escalated to Sales Manager.",
     "frequency": "Monthly", "owner": "Accounts Receivable", "data_source": "Customer Advance Register",
     "fields_required": "customer_id, advance_amount, advance_date, invoice_no, adjustment_date",
     "audit_query": "SELECT customer_id, party_name, advance_amount,\n  advance_date,\n  DATEDIFF(CURRENT_DATE, advance_date) AS days_pending\nFROM customer_advances\nWHERE adjusted_invoice IS NULL\n  AND DATEDIFF(CURRENT_DATE, advance_date) > 60\nORDER BY advance_amount DESC;",
     "expected_output": "Unadjusted advances >60 days = overstatement of liability. Obtain invoice details and adjust immediately."},
    {"process": "Debtors – Write-Off Authorization", "risk_category": "Fraud",
     "risk_desc": "Debtor balances written off without board/CFO approval, potentially to benefit related parties.",
     "risk_rating": "High", "control_obj": "All write-offs approved by CFO and Board with documented recovery efforts.",
     "control_type": "Preventive", "control_activity": "Write-off requires: legal recovery proof, CFO approval, and Board resolution; tax implications reviewed by CA.",
     "frequency": "As needed", "owner": "CFO / Board", "data_source": "Debtors Ledger, Write-Off Register",
     "fields_required": "party_name, write_off_amount, write_off_date, approval_ref, recovery_efforts",
     "audit_query": "SELECT party_name, write_off_amount, write_off_date,\n  approved_by, board_resolution_no\nFROM debtors_write_off\nWHERE approved_by IS NULL\n   OR board_resolution_no IS NULL\nORDER BY write_off_amount DESC;",
     "expected_output": "Unapproved write-offs = potential fraud or preferential treatment. Requires immediate CFO review."},
    {"process": "Debtors – Credit Note Validity", "risk_category": "Fraud",
     "risk_desc": "Credit notes issued without reference to original invoice or sales return, enabling fictitious reduction.",
     "risk_rating": "Medium", "control_obj": "Every credit note references an original invoice and is supported by inspection-approved return.",
     "control_type": "Preventive", "control_activity": "ERP mandates original invoice number for credit note creation; credit notes > ₹50,000 require Sales Manager approval.",
     "frequency": "Weekly", "owner": "Sales Manager / Finance", "data_source": "Credit Note Register",
     "fields_required": "credit_note_no, party_name, amount, original_invoice_no, reason",
     "audit_query": "SELECT credit_note_no, party_name, amount,\n  credit_note_date, reason\nFROM credit_note_register\nWHERE (original_invoice_no IS NULL OR original_invoice_no = '')\n   OR (amount > 50000 AND approved_by IS NULL)\nORDER BY amount DESC;",
     "expected_output": "Credit notes without invoice reference = fictitious reduction of debtor balance. Investigate and reverse if unsupported."},
    {"process": "Debtors – Same Party Creditor", "risk_category": "Financial",
     "risk_desc": "Same party appearing as both debtor and creditor without netting, inflating both sides of balance sheet.",
     "risk_rating": "Medium", "control_obj": "Where legally permitted, debtor and creditor balances of the same party are netted.",
     "control_type": "Detective", "control_activity": "Quarterly party-wise netting review; set-off agreements obtained; balance sheet reflected on net basis.",
     "frequency": "Quarterly", "owner": "Finance Manager", "data_source": "Debtors Ledger, Creditors Ledger",
     "fields_required": "party_name, debtor_balance, creditor_balance",
     "audit_query": "SELECT d.party_name,\n  SUM(d.outstanding_amount) AS debtor_balance,\n  SUM(c.outstanding_amount) AS creditor_balance\nFROM debtors_ledger d\nJOIN creditors_ledger c ON UPPER(d.party_name)=UPPER(c.party_name)\nGROUP BY d.party_name\nHAVING debtor_balance > 0 AND creditor_balance > 0;",
     "expected_output": "Same party on both sides = inflated balance sheet. Obtain set-off consent and pass netting entry."},
]

# ── DATA: 09 CREDITORS / AP ───────────────────────────────────────────────────
CREDITORS_RCM = [
    {"process": "Creditors – Duplicate Payment", "risk_category": "Fraud",
     "risk_desc": "Same vendor invoice paid twice due to lack of three-way match, causing financial loss.",
     "risk_rating": "High", "control_obj": "Each vendor invoice is paid exactly once.",
     "control_type": "Detective", "control_activity": "Three-way match (PO-GRN-Invoice) mandatory; duplicate payment check in ERP before payment release.",
     "frequency": "Daily", "owner": "Accounts Payable / CFO", "data_source": "Creditors Ledger, Payment Register",
     "fields_required": "vendor_id, vendor_invoice_no, payment_amount, payment_date, payment_ref",
     "audit_query": "SELECT vendor_id, vendor_invoice_no,\n  COUNT(*) AS payment_cnt,\n  SUM(payment_amount) AS total_paid\nFROM payment_register\nGROUP BY vendor_id, vendor_invoice_no\nHAVING COUNT(*) > 1\nORDER BY total_paid DESC;",
     "expected_output": "Duplicate payments = financial loss. Recover excess payment from vendor immediately."},
    {"process": "Creditors – MSME Payment Compliance", "risk_category": "Compliance",
     "risk_desc": "MSME vendors not paid within 45 days as mandated by MSMED Act 2006, causing penal interest and disclosure.",
     "risk_rating": "High", "control_obj": "All MSME vendors paid within 45 days of invoice date.",
     "control_type": "Detective", "control_activity": "Weekly MSME ageing report; MSME payables >30 days flagged to CFO; disclosed in Form MSME-1 half-yearly.",
     "frequency": "Weekly", "owner": "CFO / Finance Manager", "data_source": "Creditors Ledger, Vendor Master",
     "fields_required": "vendor_id, vendor_name, msme_flag, invoice_date, due_date, outstanding_amount, overdue_days",
     "audit_query": "SELECT c.vendor_id, v.vendor_name, v.udyam_no,\n  c.invoice_date, c.outstanding_amount,\n  DATEDIFF(CURRENT_DATE, c.invoice_date) AS days_outstanding\nFROM creditors_ledger c JOIN vendor_master v ON c.vendor_id=v.id\nWHERE v.msme_flag = 'Yes'\n  AND c.outstanding_amount > 0\n  AND DATEDIFF(CURRENT_DATE, c.invoice_date) > 45\nORDER BY days_outstanding DESC;",
     "expected_output": "MSME overdue >45 days = MSMED Act violation. Penal interest at 3× bank rate + mandatory MSME-1 disclosure."},
    {"process": "Creditors – Early Payment Loss", "risk_category": "Financial",
     "risk_desc": "Payments made before due date losing the benefit of credit period and straining working capital.",
     "risk_rating": "Medium", "control_obj": "Payments made on due date to optimise working capital (except early payment discounts).",
     "control_type": "Detective", "control_activity": "Weekly cash flow review; ERP payment scheduler uses due date; early payment requires Finance Manager approval.",
     "frequency": "Weekly", "owner": "Finance Manager", "data_source": "Payment Register, Creditors Ledger",
     "fields_required": "vendor_id, vendor_name, invoice_date, due_date, payment_date, payment_amount",
     "audit_query": "SELECT vendor_id, vendor_name, invoice_date,\n  due_date, payment_date, payment_amount,\n  DATEDIFF(due_date, payment_date) AS early_days\nFROM payment_register\nWHERE payment_date < DATE_SUB(due_date, INTERVAL 10 DAY)\nORDER BY early_days DESC;",
     "expected_output": "Early payments >10 days before due date = working capital loss. Verify if early payment discount availed."},
    {"process": "Creditors – Advance Non-Adjustment", "risk_category": "Financial",
     "risk_desc": "Vendor advances outstanding for >60 days not adjusted against invoices, inflating advance balance.",
     "risk_rating": "Medium", "control_obj": "All vendor advances adjusted within 60 days of payment.",
     "control_type": "Detective", "control_activity": "Monthly advance ageing; advances >60 days escalated to CFO; advance TDS compliance verified.",
     "frequency": "Monthly", "owner": "Accounts Payable", "data_source": "Vendor Advance Register",
     "fields_required": "vendor_id, advance_amount, advance_date, grn_no, adjustment_date",
     "audit_query": "SELECT vendor_id, vendor_name, advance_amount,\n  advance_date,\n  DATEDIFF(CURRENT_DATE, advance_date) AS days_outstanding\nFROM vendor_advances\nWHERE grn_no IS NULL\n  AND adjustment_date IS NULL\n  AND DATEDIFF(CURRENT_DATE, advance_date) > 60\nORDER BY advance_amount DESC;",
     "expected_output": "Unadjusted advances >60 days = prepayment misuse or vendor dispute. Verify supply and adjust immediately."},
    {"process": "Creditors – Inactive Vendor Payments", "risk_category": "Fraud",
     "risk_desc": "Payments made to vendors marked inactive in the master, possibly indicating fictitious vendors.",
     "risk_rating": "High", "control_obj": "No payments to inactive or blacklisted vendors.",
     "control_type": "Preventive", "control_activity": "ERP blocks payment to vendors with status = Inactive/Blacklisted; vendor reactivation requires MD approval.",
     "frequency": "Daily", "owner": "CFO / Procurement Manager", "data_source": "Payment Register, Vendor Master",
     "fields_required": "vendor_id, vendor_name, vendor_status, payment_amount, payment_date",
     "audit_query": "SELECT p.vendor_id, v.vendor_name, v.status,\n  p.payment_amount, p.payment_date\nFROM payment_register p JOIN vendor_master v ON p.vendor_id=v.id\nWHERE v.status IN ('Inactive','Blacklisted','Suspended')\n  AND p.payment_amount > 0\nORDER BY p.payment_amount DESC;",
     "expected_output": "Payments to inactive vendors = fictitious payment risk. Trace to invoice and bank confirmation urgently."},
    {"process": "Creditors – Bank Authorization", "risk_category": "Fraud",
     "risk_desc": "Vendor payments processed via NEFT/RTGS without bank authorization reference, bypassing dual control.",
     "risk_rating": "High", "control_obj": "All online payments have bank maker-checker authorization reference.",
     "control_type": "Preventive", "control_activity": "Bank portal configured with Maker-Checker: payment initiated by Finance, authorized by CFO/MD; bank ref captured in ERP.",
     "frequency": "Daily", "owner": "CFO / Finance Manager", "data_source": "Payment Register, Bank Statement",
     "fields_required": "payment_ref, vendor_id, amount, bank_auth_ref, payment_date",
     "audit_query": "SELECT payment_ref, vendor_id, amount,\n  payment_date, payment_mode\nFROM payment_register\nWHERE payment_mode IN ('NEFT','RTGS','IMPS')\n  AND (bank_auth_ref IS NULL OR bank_auth_ref = '')\nORDER BY amount DESC;",
     "expected_output": "Online payments without bank auth ref = dual control bypass. Could indicate unauthorized transfer. Verify immediately."},
    {"process": "Creditors – Stale Creditors", "risk_category": "Financial",
     "risk_desc": "Creditor balances outstanding >1 year that may require reversal (unclaimed credit) under income tax.",
     "risk_rating": "Medium", "control_obj": "Creditor balances >1 year reviewed and cleared or reversed as per law.",
     "control_type": "Detective", "control_activity": "Annual review of creditor balances; confirmation letters sent; old creditors reversed with CFO approval and tax advice.",
     "frequency": "Annually", "owner": "Finance Manager / Tax Manager", "data_source": "Creditors Ledger",
     "fields_required": "vendor_id, vendor_name, outstanding_amount, oldest_invoice_date",
     "audit_query": "SELECT vendor_id, vendor_name,\n  SUM(outstanding_amount) AS balance,\n  MIN(invoice_date) AS oldest_invoice\nFROM creditors_ledger\nWHERE outstanding_amount > 0\nGROUP BY vendor_id\nHAVING MIN(invoice_date) < DATE_SUB(CURRENT_DATE, INTERVAL 365 DAY)\nORDER BY balance DESC;",
     "expected_output": "Creditors >1 year old = assess for reversal. Section 41(1) income if liability ceased — taxable income."},
]

# ── DATA: 10 GST COMPLIANCE ───────────────────────────────────────────────────
GST_RCM = [
    {"process": "GST – GSTR-1 vs Books", "risk_category": "Compliance",
     "risk_desc": "Sales reported in GSTR-1 differ from books of accounts, creating reconciliation issues and scrutiny risk.",
     "risk_rating": "High", "control_obj": "GSTR-1 data exactly matches sales register for each month.",
     "control_type": "Detective", "control_activity": "Monthly reconciliation before GSTR-1 filing; differences corrected via amendments; reconciliation approved by Tax Manager.",
     "frequency": "Monthly", "owner": "Tax Manager", "data_source": "Sales Register, GSTR-1 Data",
     "fields_required": "month, taxable_value_books, taxable_value_gstr1, igst_books, igst_gstr1",
     "audit_query": "SELECT month,\n  SUM(taxable_value_books) AS books_taxable,\n  SUM(taxable_value_gstr1) AS gstr1_taxable,\n  ABS(SUM(taxable_value_books) - SUM(taxable_value_gstr1)) AS difference\nFROM gst_reconciliation\nGROUP BY month\nHAVING ABS(SUM(taxable_value_books) - SUM(taxable_value_gstr1)) > 1000\nORDER BY month DESC;",
     "expected_output": "Mismatch > ₹1,000 per month = GSTR-1 amendment required. Carry forward to next period if within time limit."},
    {"process": "GST – ITC vs GSTR-2B", "risk_category": "Compliance",
     "risk_desc": "Input Tax Credit claimed in GSTR-3B exceeds amount available in GSTR-2B, creating reversal liability.",
     "risk_rating": "High", "control_obj": "ITC availed ≤ ITC available in GSTR-2B.",
     "control_type": "Detective", "control_activity": "Monthly GSTR-2B download and reconciliation with purchase register before filing GSTR-3B.",
     "frequency": "Monthly", "owner": "Tax Manager", "data_source": "Purchase Register, GSTR-2B Portal",
     "fields_required": "vendor_gstin, invoice_no, itc_in_books, itc_in_gstr2b, month",
     "audit_query": "SELECT vendor_gstin, month,\n  SUM(itc_in_books) AS claimed,\n  SUM(COALESCE(itc_in_gstr2b,0)) AS available_2b,\n  SUM(itc_in_books) - SUM(COALESCE(itc_in_gstr2b,0)) AS excess_itc\nFROM itc_reconciliation\nGROUP BY vendor_gstin, month\nHAVING excess_itc > 0\nORDER BY excess_itc DESC;",
     "expected_output": "Excess ITC = GST reversal + 18% interest. Reverse before next GSTR-3B or face notice under Section 73/74."},
    {"process": "GST – E-Invoice Compliance", "risk_category": "Compliance",
     "risk_desc": "E-invoices (IRN) not generated for B2B transactions by businesses with turnover >₹5Cr.",
     "risk_rating": "High", "control_obj": "All eligible B2B invoices have IRN generated before supply.",
     "control_type": "Preventive", "control_activity": "ERP integrated with IRP portal; invoice saved only after IRN generation; QR code printed on invoice.",
     "frequency": "Daily", "owner": "Tax Manager / IT Manager", "data_source": "Sales Register, IRP Portal",
     "fields_required": "invoice_no, invoice_date, party_gstin, invoice_value, irn, qr_code",
     "audit_query": "SELECT invoice_no, party_name, party_gstin,\n  invoice_date, invoice_value\nFROM sales_register\nWHERE (irn IS NULL OR irn = '')\n  AND invoice_date >= '2023-08-01'\n  AND invoice_value > 0\n  AND party_gstin IS NOT NULL\nORDER BY invoice_value DESC;",
     "expected_output": "Missing IRN = penalty up to ₹10,000 per invoice (Rule 48(5)). Regenerate IRN or raise credit/debit note."},
    {"process": "GST – Reverse Charge Mechanism", "risk_category": "Compliance",
     "risk_desc": "RCM liability not paid on purchases from unregistered persons or specified services.",
     "risk_rating": "High", "control_obj": "RCM liability identified, self-invoiced, and paid in cash (not via ITC).",
     "control_type": "Detective", "control_activity": "Monthly RCM register review; self-invoice raised for unregistered purchases; RCM paid via GSTR-3B cash column.",
     "frequency": "Monthly", "owner": "Tax Manager", "data_source": "Purchase Register, RCM Register",
     "fields_required": "vendor_id, vendor_name, vendor_type, taxable_value, rcm_applicable, rcm_paid",
     "audit_query": "SELECT vendor_id, vendor_name, vendor_type,\n  taxable_value, rcm_applicable, rcm_paid\nFROM purchase_register\nWHERE (vendor_type = 'Unregistered'\n   OR service_category IN ('Legal','Advocate','GTA','Security'))\n  AND (rcm_paid = 'No' OR rcm_paid IS NULL);",
     "expected_output": "Unpaid RCM = GST demand + penalty + interest. Pay in next GSTR-3B and take ITC in following month."},
    {"process": "GST – Section 17(5) Blocked Credit", "risk_category": "Compliance",
     "risk_desc": "ITC availed on goods/services blocked under Section 17(5) (food, club, personal use, etc.).",
     "risk_rating": "High", "control_obj": "ITC not claimed on ineligible items per Section 17(5).",
     "control_type": "Preventive", "control_activity": "Blocked credit list embedded in ERP item master; such purchases auto-routed to expense, not ITC.",
     "frequency": "Monthly", "owner": "Tax Manager", "data_source": "Purchase Register, ITC Register",
     "fields_required": "item_code, item_description, expense_category, itc_claimed, blocked_under_sec17",
     "audit_query": "SELECT p.invoice_no, p.item_description,\n  p.gst_amount AS itc_claimed, b.block_reason\nFROM purchase_register p\nJOIN blocked_credit_list b ON p.expense_category=b.expense_category\nWHERE p.itc_claimed > 0;",
     "expected_output": "ITC on blocked items = GST demand with 100% penalty. Reverse ITC immediately via GSTR-3B Table 4(B)(2)."},
    {"process": "GST – Late Filing", "risk_category": "Compliance",
     "risk_desc": "GSTR-1, GSTR-3B, or annual return filed after due date, attracting late fees and interest.",
     "risk_rating": "Medium", "control_obj": "All GST returns filed on or before due date.",
     "control_type": "Preventive", "control_activity": "GST compliance calendar maintained; auto-reminders set 7 days before due date; Tax Manager accountable for timely filing.",
     "frequency": "Monthly", "owner": "Tax Manager", "data_source": "GST Portal Filing Records",
     "fields_required": "return_type, tax_period, due_date, filing_date, late_fee_paid",
     "audit_query": "SELECT return_type, tax_period, due_date,\n  filing_date,\n  DATEDIFF(filing_date, due_date) AS days_late,\n  late_fee_paid\nFROM gst_filing_register\nWHERE filing_date > due_date\nORDER BY days_late DESC;",
     "expected_output": "Late filing = ₹50/day (₹25 CGST + ₹25 SGST) + 18% interest on tax. Ensure timely future filings."},
    {"process": "GST – Annual Return Reconciliation", "risk_category": "Compliance",
     "risk_desc": "GSTR-9 annual return data differs from audited financials, creating scrutiny risk.",
     "risk_rating": "Medium", "control_obj": "GSTR-9 figures reconcile with audited P&L and balance sheet.",
     "control_type": "Detective", "control_activity": "Annual GSTR-9 reconciliation with audited financials before filing; differences explained in GSTR-9C.",
     "frequency": "Annually", "owner": "CFO / Statutory Auditor", "data_source": "GSTR-9, Audited Financials",
     "fields_required": "head, gstr9_value, audit_value, difference",
     "audit_query": "SELECT head,\n  gstr9_value, audit_value,\n  (gstr9_value - audit_value) AS difference\nFROM gstr9_reconciliation\nWHERE ABS(gstr9_value - audit_value) > 10000\nORDER BY ABS(difference) DESC;",
     "expected_output": "Differences >₹10K = explain in GSTR-9C. Unreconciled differences may trigger audit by GST department."},
]

# ── DATA: 11 JOURNAL ENTRIES ──────────────────────────────────────────────────
JOURNAL_RCM = [
    {"process": "JE – Weekend / Holiday Postings", "risk_category": "Fraud",
     "risk_desc": "Journal entries posted on weekends or public holidays when oversight is absent, enabling manipulation.",
     "risk_rating": "High", "control_obj": "All JEs posted during business hours on working days only.",
     "control_type": "Detective", "control_activity": "Weekly exception report of JEs posted on non-working days; mandatory explanation and senior approval for off-day postings.",
     "frequency": "Weekly", "owner": "CFO / Internal Audit", "data_source": "General Ledger / Journal Register",
     "fields_required": "je_id, posting_date, posting_time, amount_dr, amount_cr, posted_by, narration",
     "audit_query": "SELECT je_id, posting_date, DAYNAME(posting_date) AS day_name,\n  amount_dr, narration, posted_by\nFROM journal_entries\nWHERE DAYOFWEEK(posting_date) IN (1,7)\n   OR posting_date IN (SELECT holiday_date FROM holiday_master)\nORDER BY posting_date DESC;",
     "expected_output": "JEs on weekends/holidays = high fraud risk. Obtain written justification from posting user and CFO sign-off."},
    {"process": "JE – Round Number Entries", "risk_category": "Fraud",
     "risk_desc": "Journal entries with suspiciously round amounts indicating estimates or fictitious entries.",
     "risk_rating": "Medium", "control_obj": "JE amounts are supported by actual calculations, not round estimates.",
     "control_type": "Detective", "control_activity": "Monthly Benford's Law analysis on JE amounts; round-number JEs >₹1 lakh reviewed by CFO.",
     "frequency": "Monthly", "owner": "Internal Audit / CFO", "data_source": "Journal Register",
     "fields_required": "je_id, amount_dr, amount_cr, narration, posted_by, posting_date",
     "audit_query": "SELECT je_id, amount_dr, posting_date,\n  narration, posted_by\nFROM journal_entries\nWHERE amount_dr > 100000\n  AND MOD(amount_dr, 10000) = 0\nORDER BY amount_dr DESC;",
     "expected_output": "Round-number high-value JEs = possible estimation or fictitious entry. Verify supporting calculation."},
    {"process": "JE – Missing Narration", "risk_category": "Compliance",
     "risk_desc": "Journal entries without narration or document reference, making it impossible to audit or explain.",
     "risk_rating": "Medium", "control_obj": "Every JE has a narration explaining purpose and a document reference number.",
     "control_type": "Preventive", "control_activity": "ERP mandatory field: narration and document reference required before JE can be saved.",
     "frequency": "Daily", "owner": "Finance Manager", "data_source": "Journal Register",
     "fields_required": "je_id, posting_date, amount_dr, narration, document_ref",
     "audit_query": "SELECT je_id, posting_date, amount_dr,\n  narration, document_ref\nFROM journal_entries\nWHERE (narration IS NULL OR TRIM(narration) = '')\n   OR (document_ref IS NULL OR TRIM(document_ref) = '')\nORDER BY amount_dr DESC;",
     "expected_output": "JEs without narration or reference = untraceable. Finance Manager to update narration with source document."},
    {"process": "JE – Backdated Entries", "risk_category": "Fraud",
     "risk_desc": "Journal entries posted in closed periods to manipulate prior-period financials.",
     "risk_rating": "High", "control_obj": "No JEs allowed in closed accounting periods.",
     "control_type": "Preventive", "control_activity": "ERP period-lock enforced: only CFO can unlock closed period; period-unlock log reviewed by auditor.",
     "frequency": "Monthly", "owner": "CFO / ERP Admin", "data_source": "Journal Register, Period Lock Log",
     "fields_required": "je_id, posting_date, creation_date, amount_dr, posted_by",
     "audit_query": "SELECT je_id, posting_date, creation_date,\n  amount_dr, posted_by,\n  DATEDIFF(creation_date, posting_date) AS back_date_days\nFROM journal_entries\nWHERE creation_date > posting_date\n  AND DATEDIFF(creation_date, posting_date) > 30\nORDER BY back_date_days DESC;",
     "expected_output": "JEs created >30 days after posting date = prior period manipulation. Requires CFO justification and disclosure."},
    {"process": "JE – Unauthorized High-Value", "risk_category": "Fraud",
     "risk_desc": "High-value journal entries posted by users without appropriate authority level.",
     "risk_rating": "High", "control_obj": "JEs above ₹5 lakh posted only by Finance Manager or CFO.",
     "control_type": "Preventive", "control_activity": "ERP user-role matrix: JE above ₹5L requires CFO user ID; above ₹50L requires MD counter-signature in system.",
     "frequency": "Daily", "owner": "ERP Admin / Internal Audit", "data_source": "Journal Register, User Master",
     "fields_required": "je_id, amount_dr, posted_by, user_role, posting_date",
     "audit_query": "SELECT j.je_id, j.amount_dr, j.posting_date,\n  j.posted_by, u.user_role\nFROM journal_entries j JOIN user_master u ON j.posted_by=u.user_id\nWHERE j.amount_dr > 500000\n  AND u.user_role NOT IN ('CFO','Finance Manager','MD','Director')\nORDER BY j.amount_dr DESC;",
     "expected_output": "High-value JE by unauthorized user = control failure. Reverse and repost after proper authorization."},
    {"process": "JE – Suspense Account Clearing", "risk_category": "Financial",
     "risk_desc": "Suspense account balances not cleared within 30 days indicating unresolved transactions.",
     "risk_rating": "Medium", "control_obj": "All suspense account entries cleared within 30 days.",
     "control_type": "Detective", "control_activity": "Monthly suspense account ageing report reviewed by Finance Manager; all balances cleared before month-end close.",
     "frequency": "Monthly", "owner": "Finance Manager", "data_source": "General Ledger",
     "fields_required": "account_code, account_name, balance, oldest_entry_date",
     "audit_query": "SELECT gl.account_code, am.account_name,\n  SUM(gl.balance) AS total_balance,\n  MIN(gl.entry_date) AS oldest_entry\nFROM gl_balances gl JOIN account_master am ON gl.account_code=am.code\nWHERE am.account_type = 'Suspense'\n  AND gl.balance != 0\nGROUP BY gl.account_code\nHAVING MIN(gl.entry_date) < DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)\nORDER BY ABS(total_balance) DESC;",
     "expected_output": "Suspense balances >30 days = unresolved transactions. Identify underlying transaction and pass correct entry."},
    {"process": "JE – Debit/Credit Imbalance", "risk_category": "Financial",
     "risk_desc": "Journal entries where total debits do not equal total credits, indicating data corruption or error.",
     "risk_rating": "High", "control_obj": "Every JE balances: sum of debits = sum of credits.",
     "control_type": "Detective", "control_activity": "ERP validation ensures balanced JE at save; daily trial balance check confirms overall debit = credit.",
     "frequency": "Daily", "owner": "Finance Manager / ERP Admin", "data_source": "Journal Register",
     "fields_required": "je_id, sum_debit, sum_credit, posting_date",
     "audit_query": "SELECT je_id, posting_date,\n  SUM(debit_amount) AS total_dr,\n  SUM(credit_amount) AS total_cr,\n  ABS(SUM(debit_amount) - SUM(credit_amount)) AS imbalance\nFROM journal_line_items\nGROUP BY je_id\nHAVING ABS(SUM(debit_amount) - SUM(credit_amount)) > 1\nORDER BY imbalance DESC;",
     "expected_output": "Any imbalance = system corruption or deliberate manipulation. Identify and correct immediately before period close."},
]

# ── DATA: 12 EXPENSES ─────────────────────────────────────────────────────────
EXPENSE_RCM = [
    {"process": "Expenses – Budget Compliance", "risk_category": "Financial",
     "risk_desc": "Actual expenses exceed approved budget by >10% without CFO approval, indicating poor cost control.",
     "risk_rating": "Medium", "control_obj": "Expenses stay within approved budget; overruns flagged and approved.",
     "control_type": "Detective", "control_activity": "Monthly budget vs. actual report reviewed by department heads and CFO; overruns >10% require CFO approval.",
     "frequency": "Monthly", "owner": "Department Heads / CFO", "data_source": "Expense Ledger, Budget Master",
     "fields_required": "dept_code, expense_head, budget_amount, actual_amount, month",
     "audit_query": "SELECT dept_code, expense_head, budget_amount,\n  actual_amount,\n  ROUND((actual_amount-budget_amount)/budget_amount*100,2) AS overrun_pct\nFROM budget_vs_actual\nWHERE actual_amount > budget_amount * 1.10\nORDER BY overrun_pct DESC;",
     "expected_output": "Overrun >10% = requires CFO approval and explanation. Persistent overruns need budget revision."},
    {"process": "Expenses – Personal Expenses", "risk_category": "Fraud",
     "risk_desc": "Personal expenses of directors/employees charged to company accounts, inflating company costs.",
     "risk_rating": "High", "control_obj": "Company funds used only for legitimate business purposes.",
     "control_type": "Detective", "control_activity": "Expense claim review by HR/Finance: each claim verified against business purpose; director expenses reviewed by audit committee.",
     "frequency": "Monthly", "owner": "Finance Manager / CFO", "data_source": "Expense Ledger",
     "fields_required": "voucher_no, expense_category, amount, claimed_by, business_purpose",
     "audit_query": "SELECT voucher_no, expense_category, amount,\n  claimed_by, voucher_date, business_purpose\nFROM expense_claims\nWHERE LOWER(expense_category) LIKE '%personal%'\n   OR LOWER(expense_category) LIKE '%family%'\n   OR LOWER(expense_category) LIKE '%holiday%'\n   OR business_purpose IS NULL\nORDER BY amount DESC;",
     "expected_output": "Personal expenses charged to company = perquisite under income tax. Disallow and recover from employee."},
    {"process": "Expenses – Expense Splitting", "risk_category": "Fraud",
     "risk_desc": "Single expense split into multiple smaller bills to avoid approval thresholds.",
     "risk_rating": "High", "control_obj": "Aggregate expenses to same vendor on same date evaluated against approval threshold.",
     "control_type": "Detective", "control_activity": "Monthly review for same-vendor, same-date multiple claims by same employee below threshold; internal audit spot checks.",
     "frequency": "Monthly", "owner": "Internal Audit / CFO", "data_source": "Expense Claims Register",
     "fields_required": "claimed_by, vendor_name, expense_date, amount, bill_no",
     "audit_query": "SELECT claimed_by, vendor_name, expense_date,\n  COUNT(*) AS bill_count, SUM(amount) AS total_amount\nFROM expense_claims\nGROUP BY claimed_by, vendor_name, expense_date\nHAVING COUNT(*) > 2\n   AND SUM(amount) > (SELECT approval_threshold FROM expense_policy LIMIT 1)\nORDER BY total_amount DESC;",
     "expected_output": "Multiple bills to same vendor on same day = possible threshold bypass. Aggregate and reprocess for approval."},
    {"process": "Expenses – Missing Bills", "risk_category": "Financial",
     "risk_desc": "Expenses reimbursed without supporting original bills, enabling fictitious claims.",
     "risk_rating": "Medium", "control_obj": "Every expense reimbursement is supported by an original bill/receipt.",
     "control_type": "Preventive", "control_activity": "Expense claim system mandates bill upload; claims without bills rejected at Finance level; spot audits conducted.",
     "frequency": "Monthly", "owner": "Finance Manager", "data_source": "Expense Claims Register",
     "fields_required": "voucher_no, claimed_by, amount, bill_attached, approval_status",
     "audit_query": "SELECT voucher_no, claimed_by, amount,\n  expense_date, expense_category\nFROM expense_claims\nWHERE bill_attached = 'No'\n  AND amount > 1000\nORDER BY amount DESC;",
     "expected_output": "Reimbursements without bills = unsubstantiated claims. Obtain original bills or recover amount."},
    {"process": "Expenses – R&M Capitalisation Review", "risk_category": "Financial",
     "risk_desc": "High-value repairs/maintenance expenditure that should be capitalised is wrongly expensed.",
     "risk_rating": "Medium", "control_obj": "R&M items that extend asset life or add new capability are capitalised.",
     "control_type": "Detective", "control_activity": "Monthly review of R&M expenses >₹50,000 by Finance Manager; technical assessment for capitalisation eligibility.",
     "frequency": "Monthly", "owner": "Finance Manager / CFO", "data_source": "Expense Ledger",
     "fields_required": "voucher_no, expense_head, amount, vendor_name, description",
     "audit_query": "SELECT voucher_no, expense_head, amount,\n  vendor_name, description, voucher_date\nFROM expense_ledger\nWHERE expense_head = 'Repairs & Maintenance'\n  AND amount > 50000\nORDER BY amount DESC;",
     "expected_output": "R&M items >₹50K = assess for capitalisation. If asset life extended, capitalise and reverse expense."},
    {"process": "Expenses – Director Expense Disclosure", "risk_category": "Compliance",
     "risk_desc": "Director-related expenses not disclosed in board minutes or annual report as required by Companies Act.",
     "risk_rating": "High", "control_obj": "All director expenses approved by board and disclosed in annual accounts.",
     "control_type": "Preventive", "control_activity": "Director expense register maintained; all items presented at board meeting; statutory auditor reviews as part of audit.",
     "frequency": "Quarterly", "owner": "Company Secretary / CFO", "data_source": "Director Expense Register",
     "fields_required": "expense_id, director_name, amount, expense_type, board_approval_date",
     "audit_query": "SELECT expense_id, director_name, amount,\n  expense_type, expense_date, board_approval_date\nFROM director_expenses\nWHERE board_approval_date IS NULL\n  OR board_approval_date > expense_date + INTERVAL 90 DAY\nORDER BY amount DESC;",
     "expected_output": "Unapproved director expenses = Companies Act non-compliance. Obtain retroactive board approval and disclose."},
    {"process": "Expenses – Duplicate Claims", "risk_category": "Fraud",
     "risk_desc": "Same expense claimed multiple times by the same employee, causing double reimbursement.",
     "risk_rating": "High", "control_obj": "No duplicate expense claims from any employee.",
     "control_type": "Detective", "control_activity": "Duplicate check in expense system: same employee + same date + same amount flagged for Finance review.",
     "frequency": "Monthly", "owner": "Finance Manager", "data_source": "Expense Claims Register",
     "fields_required": "claimed_by, expense_date, amount, bill_no, expense_category",
     "audit_query": "SELECT claimed_by, expense_date, amount,\n  COUNT(*) AS duplicate_cnt\nFROM expense_claims\nGROUP BY claimed_by, expense_date, amount\nHAVING COUNT(*) > 1\nORDER BY amount DESC;",
     "expected_output": "Duplicate claims = double reimbursement fraud. Recover excess and review employee's full claim history."},
]

# ── SHEET REGISTRY ─────────────────────────────────────────────────────────────
SHEET_REGISTRY = [
    {"name": "01 · Sales Register",    "area": "Sales",              "data": SALES_RCM,
     "tab": "1F3864",
     "title": "RISK CONTROL MATRIX — SALES REGISTER | Manufacturing Business",
     "sub": "Covers: Invoice generation, pricing, GST compliance, credit control, e-way bills, sales returns"},
    {"name": "02 · Purchase Register", "area": "Purchases",          "data": PURCHASE_RCM,
     "tab": "D4A017",
     "title": "RISK CONTROL MATRIX — PURCHASE REGISTER | Manufacturing Business",
     "sub": "Covers: Vendor invoices, PO compliance, price variance, GST ITC, related parties, GRNB"},
    {"name": "03 · Inventory & Stock", "area": "Inventory & Stock",  "data": INVENTORY_RCM,
     "tab": "27AE60",
     "title": "RISK CONTROL MATRIX — INVENTORY & STOCK TRANSACTIONS",
     "sub": "Covers: Stock balances, physical verification, slow-moving, write-offs, reorder, material issues"},
    {"name": "04 · Production & WIP",  "area": "Production & WIP",   "data": PRODUCTION_RCM,
     "tab": "E67E22",
     "title": "RISK CONTROL MATRIX — PRODUCTION / WORK-IN-PROGRESS",
     "sub": "Covers: WIP conversion, BOM consumption variance, scrap/rejection, rework, scrap disposal, labour efficiency"},
    {"name": "05 · Payroll & Labour",  "area": "Payroll & Labour",   "data": PAYROLL_RCM,
     "tab": "8E44AD",
     "title": "RISK CONTROL MATRIX — PAYROLL & LABOUR COST",
     "sub": "Covers: Ghost employees, duplicate identity, grade compliance, TDS, PF/ESI, terminated employees, cash salary"},
    {"name": "06 · Fixed Assets",      "area": "Fixed Assets",       "data": FIXED_ASSETS_RCM,
     "tab": "2980B9",
     "title": "RISK CONTROL MATRIX — FIXED ASSETS (CAPEX / DEPRECIATION)",
     "sub": "Covers: Capitalisation threshold, disposal authorisation, depreciation rates, idle assets, capex vs opex, insurance"},
    {"name": "07 · Cash & Bank",       "area": "Cash & Bank",        "data": CASH_BANK_RCM,
     "tab": "16A085",
     "title": "RISK CONTROL MATRIX — CASH & BANK TRANSACTIONS",
     "sub": "Covers: Cash payment limits, bank reconciliation, bearer cheques, petty cash, unusual transfers, after-hours payments"},
    {"name": "08 · Debtors AR",         "area": "Debtors / AR",       "data": DEBTORS_RCM,
     "tab": "C0392B",
     "title": "RISK CONTROL MATRIX — DEBTORS / ACCOUNTS RECEIVABLE",
     "sub": "Covers: Overdue monitoring, credit limits, provisioning, advance adjustment, write-offs, credit notes, netting"},
    {"name": "09 · Creditors AP",       "area": "Creditors / AP",     "data": CREDITORS_RCM,
     "tab": "D35400",
     "title": "RISK CONTROL MATRIX — CREDITORS / ACCOUNTS PAYABLE",
     "sub": "Covers: Duplicate payments, MSME compliance, early payment, advance non-adjustment, inactive vendors, stale creditors"},
    {"name": "10 · GST Compliance",    "area": "GST & Tax",          "data": GST_RCM,
     "tab": "1ABC9C",
     "title": "RISK CONTROL MATRIX — GST / TAX COMPLIANCE",
     "sub": "Covers: GSTR-1 vs books, ITC vs GSTR-2B, e-invoice, RCM, blocked credit, late filing, annual return"},
    {"name": "11 · Journal Entries",   "area": "Journal Entries",    "data": JOURNAL_RCM,
     "tab": "F39C12",
     "title": "RISK CONTROL MATRIX — JOURNAL ENTRIES / MANUAL ENTRIES",
     "sub": "Covers: Weekend JEs, round-number JEs, missing narration, backdated entries, unauthorised users, suspense clearing"},
    {"name": "12 · Expenses",          "area": "Overheads & Expenses","data": EXPENSE_RCM,
     "tab": "7F8C8D",
     "title": "RISK CONTROL MATRIX — EXPENSE TRANSACTIONS (OVERHEADS & ADMIN)",
     "sub": "Covers: Budget compliance, personal expenses, expense splitting, missing bills, R&M capitalisation, director expenses"},
]

# ── SHEET BUILDER ──────────────────────────────────────────────────────────────
def build_sheet(wb, reg):
    ws = wb.create_sheet(reg["name"])
    ws.sheet_view.showGridLines = False
    ws.sheet_properties.tabColor = reg["tab"]

    mtitle(ws, "A1:O1", reg["title"], NAVY, GOLD, sz=12)
    ws.row_dimensions[1].height = 30

    today_str = date.today().strftime("%d %B %Y")
    mtitle(ws, "A2:O2",
           f"{reg['sub']}  |  Prepared: {today_str}  |  Adapt table/field names to your ERP schema",
           "2C3E50", "BDC3C7", sz=9, bold=False)
    ws.row_dimensions[2].height = 18

    # Row 3: legend
    legend = [
        ("Risk:", "555555", DARK_TEXT), ("HIGH", "C00000", WHITE), ("MED", "ED7D31", WHITE),
        ("LOW", "375623", WHITE), ("", WHITE, WHITE),
        ("Control:", "555555", DARK_TEXT), ("PREV", "1F4E79", WHITE),
        ("DET", "6F31A0", WHITE), ("CORR", "1F8C7A", WHITE),
        ("", WHITE, WHITE), ("Cat:", "555555", DARK_TEXT),
        ("FIN", "1A237E", WHITE), ("OPS", "1B5E20", WHITE),
        ("COMP", "B71C1C", WHITE), ("FRAUD", "4A148C", WHITE),
    ]
    for ci, (txt, bg, fc) in enumerate(legend, 1):
        c = ws.cell(row=3, column=ci, value=txt)
        c.fill = hf(bg)
        c.font = Font(name="Calibri", size=8, bold=True, color=fc)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = bdr()
    ws.row_dimensions[3].height = 15

    # Row 4: headers
    for ci, h in enumerate(HEADERS, 1):
        wc(ws, 4, ci, h, NAVY, WHITE, bold=True, sz=9, ha="center")
    ws.row_dimensions[4].height = 32

    # Data rows
    for idx, entry in enumerate(reg["data"]):
        row = 5 + idx
        bg = LIGHT_BLUE if idx % 2 == 0 else WHITE
        wc(ws, row, 1, idx+1,                          bg,                  ha="center", bold=True)
        wc(ws, row, 2, entry["process"],                bg,                  bold=True)
        wc(ws, row, 3, entry["risk_category"],          CAT_CLR.get(entry["risk_category"], NAVY), WHITE, bold=True, sz=8, ha="center")
        wc(ws, row, 4, entry["risk_desc"],              bg)
        wc(ws, row, 5, entry["risk_rating"],            RISK_CLR.get(entry["risk_rating"], "ED7D31"), WHITE, bold=True, ha="center")
        wc(ws, row, 6, entry["control_obj"],            bg)
        wc(ws, row, 7, entry["control_type"],           CTRL_CLR.get(entry["control_type"], NAVY), WHITE, bold=True, sz=8, ha="center")
        wc(ws, row, 8, entry["control_activity"],       bg)
        wc(ws, row, 9, entry["frequency"],              bg,                  ha="center")
        wc(ws, row, 10, entry["owner"],                 bg)
        wc(ws, row, 11, entry["data_source"],           bg)
        wc(ws, row, 12, entry["fields_required"],       FIELDS_BG,           sz=8, fn="Courier New")
        wc(ws, row, 13, entry["audit_query"],           QUERY_BG,            fc=QUERY_FC, sz=8, fn="Courier New")
        wc(ws, row, 14, entry["expected_output"],       bg,                  fc="8B0000")
        wc(ws, row, 15, "",                             "FAFAFA")
        ws.row_dimensions[row].height = 90

    last_row = 4 + len(reg["data"])
    ws.auto_filter.ref = f"A4:O{last_row}"
    ws.freeze_panes = "A5"

    foot = last_row + 2
    ws.merge_cells(f"A{foot}:O{foot}")
    fc = ws[f"A{foot}"]
    fc.value = ("NOTE: All SQL queries are indicative. Adapt table/field names to your ERP or Tally export. "
                "For Excel-based books, convert SELECT…GROUP BY logic to COUNTIF / SUMIF / VLOOKUP / Pivot Tables.")
    fc.fill = hf("2C3E50"); fc.font = Font(name="Calibri", size=8, color="BDC3C7")
    fc.alignment = Alignment(wrap_text=True, vertical="center")
    ws.row_dimensions[foot].height = 24

    for ci, w in enumerate(COL_WIDTHS, 1):
        scw(ws, ci, w)

    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.print_title_rows = "1:4"
    return ws


# ── SUMMARY SHEET ──────────────────────────────────────────────────────────────
def build_summary(wb):
    ws = wb.create_sheet("00 · INDEX", 0)
    ws.sheet_view.showGridLines = False
    ws.sheet_properties.tabColor = "0D2137"

    today_str = date.today().strftime("%d %B %Y")
    mtitle(ws, "A1:H1", "RISK CONTROL MATRIX — MANUFACTURING BUSINESS", "0D2137", GOLD, sz=14)
    ws.row_dimensions[1].height = 38
    mtitle(ws, "A2:H2",
           f"Comprehensive Internal Audit Framework  ·  12 Transaction Areas  ·  Generated: {today_str}",
           "2C3E50", "BDC3C7", sz=10, bold=False)
    ws.row_dimensions[2].height = 22

    total_ctrl  = sum(len(r["data"]) for r in SHEET_REGISTRY)
    total_high  = sum(sum(1 for e in r["data"] if e["risk_rating"]=="High")   for r in SHEET_REGISTRY)
    total_med   = sum(sum(1 for e in r["data"] if e["risk_rating"]=="Medium") for r in SHEET_REGISTRY)
    total_low   = sum(sum(1 for e in r["data"] if e["risk_rating"]=="Low")    for r in SHEET_REGISTRY)

    kpis = [
        (f"Total Controls\n{total_ctrl}",  "1F3864"),
        (f"High Risk\n{total_high}",        "C00000"),
        (f"Medium Risk\n{total_med}",       "ED7D31"),
        (f"Low Risk\n{total_low}",          "375623"),
        (f"Process Areas\n12",              "6F31A0"),
    ]
    for ci, (txt, bg) in enumerate(kpis, 1):
        c = ws.cell(row=4, column=ci, value=txt)
        c.fill = hf(bg); c.font = Font(name="Calibri", size=13, bold=True, color=WHITE)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = bdr()
    ws.row_dimensions[4].height = 50

    idx_hdrs = ["#", "Transaction Area", "Sheet Tab Name", "High", "Medium", "Low", "Total", "Primary Risk"]
    for ci, h in enumerate(idx_hdrs, 1):
        wc(ws, 6, ci, h, NAVY, WHITE, bold=True, ha="center")
    ws.row_dimensions[6].height = 22

    for i, reg in enumerate(SHEET_REGISTRY):
        row = 7 + i
        bg = LIGHT_BLUE if i % 2 == 0 else WHITE
        h = sum(1 for e in reg["data"] if e["risk_rating"]=="High")
        m = sum(1 for e in reg["data"] if e["risk_rating"]=="Medium")
        l = sum(1 for e in reg["data"] if e["risk_rating"]=="Low")
        cats = [e["risk_category"] for e in reg["data"]]
        primary = max(set(cats), key=cats.count)
        wc(ws, row, 1, i+1,          bg,        ha="center")
        wc(ws, row, 2, reg["area"],  bg,        bold=True)
        wc(ws, row, 3, reg["name"],  bg)
        wc(ws, row, 4, h, "C00000", WHITE, bold=True, ha="center")
        wc(ws, row, 5, m, "ED7D31", WHITE, bold=True, ha="center")
        wc(ws, row, 6, l, "375623", WHITE, bold=True, ha="center")
        wc(ws, row, 7, len(reg["data"]), bg, bold=True, ha="center")
        wc(ws, row, 8, primary,      CAT_CLR.get(primary, NAVY), WHITE)
        ws.row_dimensions[row].height = 20

    leg_row = 7 + len(SHEET_REGISTRY) + 2
    mtitle(ws, f"A{leg_row}:H{leg_row}", "COLOR LEGEND", "2C3E50", "BDC3C7", sz=10)
    ws.row_dimensions[leg_row].height = 20
    leg_items = [
        ("HIGH RISK","C00000"), ("MEDIUM RISK","ED7D31"), ("LOW RISK","375623"), ("",WHITE),
        ("PREVENTIVE","1F4E79"), ("DETECTIVE","6F31A0"), ("CORRECTIVE","1F8C7A"), ("",WHITE),
    ]
    for ci, (txt, bg) in enumerate(leg_items, 1):
        c = ws.cell(row=leg_row+1, column=ci, value=txt)
        c.fill = hf(bg); c.font = Font(name="Calibri", size=9, bold=True, color=WHITE if bg!=WHITE else DARK_TEXT)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = bdr()
    ws.row_dimensions[leg_row+1].height = 22

    how_row = leg_row + 3
    mtitle(ws, f"A{how_row}:H{how_row}", "HOW TO USE THIS RISK CONTROL MATRIX", "1F3864", GOLD, sz=10)
    ws.row_dimensions[how_row].height = 22
    steps = [
        "1. Go to the relevant transaction sheet (e.g. '01 · Sales Register' for a sales audit).",
        "2. Filter Column E (Risk Rating) = 'High' to prioritise high-risk controls first.",
        "3. Copy the SQL from Column M and run against your ERP/Tally export or database.",
        "4. For Excel-based books: convert SELECT…GROUP BY to COUNTIF / SUMIF / Pivot Table equivalents.",
        "5. Document findings in Column O (Remarks) and escalate red flags from Column N to management.",
        "6. Update Owner (Col J) and Frequency (Col I) to reflect your actual organisation structure.",
        "7. Review this matrix annually or whenever there is a process or ERP change.",
    ]
    for j, step in enumerate(steps):
        r = how_row + 1 + j
        ws.merge_cells(f"A{r}:H{r}")
        c = ws[f"A{r}"]
        c.value = step
        c.fill = hf(LIGHT_BLUE if j % 2 == 0 else WHITE)
        c.font = Font(name="Calibri", size=9, color=DARK_TEXT)
        c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True, indent=1)
        c.border = bdr()
        ws.row_dimensions[r].height = 18

    for ci, w in enumerate([5, 28, 26, 10, 12, 8, 10, 22], 1):
        scw(ws, ci, w)

    ws.page_setup.orientation = "landscape"
    ws.freeze_panes = "A7"


# ── MAIN ───────────────────────────────────────────────────────────────────────
def main():
    OUTPUT = "/home/user/Claude-/Risk_Control_Matrix_Manufacturing.xlsx"
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    build_summary(wb)
    for reg in SHEET_REGISTRY:
        build_sheet(wb, reg)
        print(f"  ✓  {reg['name']}  ({len(reg['data'])} controls)")

    wb.save(OUTPUT)
    total = sum(len(r["data"]) for r in SHEET_REGISTRY)
    print(f"\nSaved → {OUTPUT}")
    print(f"Sheets: {len(wb.sheetnames)} (1 Index + 12 process areas)")
    print(f"Total RCM controls: {total}")


if __name__ == "__main__":
    main()

