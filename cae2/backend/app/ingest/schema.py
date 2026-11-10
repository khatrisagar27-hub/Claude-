"""What each uploadable dataset looks like: its columns, which are mandatory,
and the header spellings we accept for each (Tally and common Excel exports)."""
from dataclasses import dataclass, field

from app import models as m


@dataclass
class Col:
    name: str
    kind: str = "str"  # str | date | month | money | qty | int | bool | choice
    required: bool = False
    aliases: tuple = ()
    choices: dict = field(default_factory=dict)  # accepted spelling -> stored value
    help: str = ""


@dataclass
class Dataset:
    key: str
    label: str
    model: type
    cols: list
    help: str = ""

    def col(self, name):
        return next(c for c in self.cols if c.name == name)


def _choices(*values, **synonyms):
    out = {v: v for v in values}
    out.update(synonyms)
    return out


GST = [
    Col("taxable_value", "money", True, ("taxable", "taxable amount", "assessable value", "basic amount", "value")),
    Col("cgst", "money", aliases=("cgst amount", "central tax")),
    Col("sgst", "money", aliases=("sgst amount", "state tax", "sgst/utgst", "utgst")),
    Col("igst", "money", aliases=("igst amount", "integrated tax")),
]

DATASETS = {d.key: d for d in [
    Dataset("parties", "Party master (customers and vendors)", m.Party, [
        Col("code", required=True, aliases=("party code", "ledger code", "vendor code", "customer code", "alias")),
        Col("name", required=True, aliases=("party name", "ledger name", "vendor name", "customer name")),
        Col("kind", "choice", choices=_choices("customer", "vendor", "both", debtor="customer", creditor="vendor",
            supplier="vendor", **{"sundry debtors": "customer", "sundry creditors": "vendor"}), aliases=("type", "party type", "group")),
        Col("gstin", aliases=("gstin/uin", "gst no", "gst number", "gstn")),
        Col("pan", aliases=("pan no", "pan number", "pan/it no")),
        Col("bank_account", aliases=("bank account no", "account no", "bank a/c", "a/c no")),
        Col("address"),
        Col("msme_category", "choice", choices=_choices("micro", "small", "medium"), aliases=("msme", "msme type", "udyam category"),
            help="micro / small / medium; leave blank if not MSME-registered"),
        Col("is_related_party", "bool", aliases=("related party", "related")),
        Col("credit_days", "int", aliases=("credit period", "payment terms days")),
    ]),
    Dataset("ledger", "Day book / ledger entries", m.LedgerEntry, [
        Col("voucher_no", required=True, aliases=("vch no", "voucher number", "vch no.", "document no")),
        Col("voucher_date", "date", True, ("date", "vch date", "posting date")),
        Col("voucher_type", "choice", True, ("vch type", "type"), choices=_choices(
            "sales", "purchase", "payment", "receipt", "journal", "contra", "credit_note", "debit_note", "opening",
            **{"credit note": "credit_note", "debit note": "debit_note", "opening balance": "opening", "jv": "journal"})),
        Col("ledger", required=True, aliases=("ledger name", "particulars", "account", "account name", "gl account")),
        Col("ledger_group", aliases=("group", "under", "parent", "account group"),
            help="Tally group, e.g. Cash-in-Hand, Bank Accounts, Sales Accounts, Loans (Liability)"),
        Col("debit", "money", aliases=("dr", "debit amount", "dr amount")),
        Col("credit", "money", aliases=("cr", "credit amount", "cr amount")),
        Col("narration", aliases=("remarks", "description")),
        Col("entered_by", aliases=("user", "created by", "entered by user")),
        Col("entered_on", "date", aliases=("created on", "entry date", "created date", "altered on")),
    ], help="One row per voucher line. Tally Day Book XML can be uploaded directly."),
    Dataset("sales", "Sales register", m.SalesInvoice, [
        Col("invoice_no", required=True, aliases=("invoice number", "voucher no", "bill no", "vch no", "doc no")),
        Col("invoice_date", "date", True, ("date", "bill date", "voucher date", "doc date")),
        Col("customer_code", aliases=("party code",)),
        Col("customer_name", required=True, aliases=("customer", "party", "party name", "buyer", "particulars")),
        Col("customer_gstin", aliases=("gstin", "gstin/uin", "buyer gstin", "party gstin")),
        Col("place_of_supply", aliases=("pos", "state code"), help="2-digit GST state code"),
        Col("supply_type", "choice", choices=_choices("goods", "services", service="services", good="goods")),
        *GST,
        Col("total", "money", aliases=("invoice value", "invoice amount", "gross total", "total amount", "bill amount")),
        Col("irn", aliases=("irn no", "e-invoice irn", "einvoice irn")),
        Col("eway_bill_no", aliases=("e-way bill no", "eway bill", "e way bill no", "ewb no")),
        Col("due_date", "date"),
        Col("amount_received", "money", aliases=("received", "receipt amount")),
        Col("is_cancelled", "bool", aliases=("cancelled", "canceled")),
        Col("entered_on", "date", aliases=("created on", "entry date", "created date")),
    ]),
    Dataset("purchases", "Purchase register", m.PurchaseInvoice, [
        Col("invoice_no", required=True, aliases=("invoice number", "supplier invoice no", "bill no", "ref no")),
        Col("invoice_date", "date", True, ("date", "bill date", "supplier invoice date")),
        Col("booking_date", "date", aliases=("voucher date", "posting date", "entry date")),
        Col("vendor_code", aliases=("party code", "supplier code")),
        Col("vendor_name", required=True, aliases=("vendor", "supplier", "party", "party name", "particulars")),
        Col("vendor_gstin", aliases=("gstin", "gstin/uin", "supplier gstin", "party gstin")),
        Col("nature", "choice", aliases=("expense nature", "nature of payment", "tds nature"), choices=_choices(
            "goods", "contract", "professional", "technical", "rent", "rent_machinery", "commission", "interest",
            "motor_vehicle", "food_beverage", "club_membership", "health_insurance", "personal",
            "works_contract_immovable", "gift", "other", contractor="contract", brokerage="commission"),
            help="goods / contract / professional / technical / rent / commission / interest / other"),
        *GST,
        Col("total", "money", aliases=("invoice value", "invoice amount", "gross total", "total amount", "bill amount")),
        Col("itc_claimed", "money", aliases=("itc", "itc availed", "input credit")),
        Col("tds_deducted", "money", aliases=("tds", "tds amount")),
        Col("po_no", aliases=("po number", "purchase order", "order no")),
        Col("po_amount", "money", aliases=("po value",)),
        Col("grn_date", "date", aliases=("receipt date", "goods receipt date", "acceptance date")),
        Col("due_date", "date"),
        Col("paid_date", "date", aliases=("payment date",)),
        Col("amount_paid", "money", aliases=("paid", "paid amount", "payment amount")),
    ]),
    Dataset("bank", "Bank statement", m.BankTxn, [
        Col("account", aliases=("bank account", "account no", "bank")),
        Col("txn_date", "date", True, ("date", "transaction date", "value date", "tran date")),
        Col("description", aliases=("narration", "particulars", "remarks", "transaction remarks")),
        Col("reference", aliases=("ref no", "cheque no", "chq no", "utr", "chq/ref no", "ref no./cheque no.")),
        Col("counterparty", aliases=("party", "beneficiary", "payee")),
        Col("mode", "choice", choices=_choices("neft", "rtgs", "imps", "upi", "cheque", "cash", "other", chq="cheque")),
        Col("withdrawal", "money", aliases=("debit", "dr", "withdrawal amt", "withdrawals", "debit amount")),
        Col("deposit", "money", aliases=("credit", "cr", "deposit amt", "deposits", "credit amount")),
    ]),
    Dataset("stock", "Stock movements", m.StockMove, [
        Col("move_date", "date", True, ("date", "voucher date")),
        Col("item_code", required=True, aliases=("item", "stock item", "sku", "name of item")),
        Col("item_name", aliases=("description",)),
        Col("location", aliases=("godown", "warehouse")),
        Col("movement_type", "choice", True, ("type", "voucher type", "movement"), choices=_choices(
            "opening", "receipt", "issue", "adjust_in", "adjust_out", inward="receipt", outward="issue",
            purchase="receipt", sales="issue", grn="receipt", shortage="adjust_out", excess="adjust_in",
            **{"write off": "adjust_out", "goods receipt": "receipt", "opening balance": "opening"})),
        Col("quantity", "qty", True, ("qty",)),
        Col("rate", "money", aliases=("unit rate", "cost")),
        Col("reference", aliases=("ref no", "voucher no", "document no")),
    ], help="Quantity is always positive; the movement type gives the direction."),
    Dataset("employees", "Employee master", m.Employee, [
        Col("emp_code", required=True, aliases=("employee code", "emp id", "employee id", "emp no")),
        Col("name", required=True, aliases=("employee name", "emp name")),
        Col("pan", aliases=("pan no",)),
        Col("bank_account", aliases=("bank account no", "account no", "bank a/c")),
        Col("address"),
        Col("date_joined", "date", aliases=("doj", "joining date", "date of joining")),
        Col("date_left", "date", aliases=("dol", "leaving date", "date of leaving", "relieving date", "exit date")),
    ]),
    Dataset("payroll", "Payroll register", m.PayrollLine, [
        Col("emp_code", required=True, aliases=("employee code", "emp id", "employee id", "emp no")),
        Col("pay_month", "month", True, ("month", "wage month", "salary month", "period")),
        Col("basic", "money", aliases=("basic + da", "basic and da", "pf wages", "basic salary")),
        Col("gross", "money", True, ("gross pay", "gross salary", "gross earnings")),
        Col("pf_employee", "money", aliases=("pf", "epf", "employee pf", "pf deduction")),
        Col("esi_employee", "money", aliases=("esi", "esic", "employee esi", "esi deduction")),
        Col("other_deductions", "money", aliases=("other deduction", "pt + tds", "deductions")),
        Col("net_pay", "money", True, ("net salary", "net payable", "take home", "net")),
    ]),
    Dataset("gstr2b", "GSTR-2B (inward supplies)", m.Gstr2bLine, [
        Col("supplier_gstin", required=True, aliases=("gstin of supplier", "gstin", "supplier gstin")),
        Col("supplier_name", aliases=("trade/legal name", "trade name", "legal name", "supplier")),
        Col("invoice_no", required=True, aliases=("invoice number", "document number")),
        Col("invoice_date", "date", aliases=("document date",)),
        *GST,
        Col("itc_available", "bool", aliases=("itc availability", "itc available")),
        Col("return_period", aliases=("period", "gstr-1 period", "gstr-1/iff/gstr-5 period")),
    ]),
]}
