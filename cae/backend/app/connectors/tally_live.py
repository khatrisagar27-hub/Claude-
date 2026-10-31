"""
Live Tally Prime connector — reads a company straight from the Tally XML gateway (port 9000)
and loads it into CAE's tables, so an engagement can be audited on live books. Read-only:
nothing is ever written to Tally.

Gateway traps (proven against live Tally, see the firm's Tally notes):
- SVFROMDATE / SVTODATE always carry TYPE="Date", or Tally silently serves its current period;
  every pull asserts the voucher dates fall inside the window asked for.
- Only self-contained <COLLECTION>s with explicit FETCH — the bare built-in Voucher collection
  raises a TDL error dialog in Tally that freezes the gateway until someone clicks OK.
- Never FETCH CLOSINGBALANCE on Ledger / StockItem collections (pegs Tally for minutes).
  Bill-wise closing comes from the Bills collection instead.
- Invoice vouchers repeat entries under ALLLEDGERENTRIES and LEDGERENTRIES: take one list only.
- Tally emits illegal numeric entities and an undeclared UDF: prefix; clean() fixes both.
- Vouchers are pulled month by month so no single request runs long.

Mapping (Tally -> CAE): ledgers under Sundry Debtors / Creditors -> customers / vendors; every
ledger -> gl_accounts; every voucher in the books -> journal_entries + lines; Sales / Purchase
vouchers -> sales / purchase invoices (taxable, CGST / SGST / IGST / cess, TDS, bill-wise
outstanding and settlement date); bank and cash lines -> bank_transactions; stock lines ->
inventory_movements (issues costed at running weighted average; opening stock from the item
masters). Payroll is not read from Tally.
"""
from __future__ import annotations

import hashlib
import logging
import re
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from xml.sax.saxutils import escape

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------- gateway
_BAD = dict.fromkeys(list(range(0, 9)) + [11, 12] + list(range(14, 32)))
_ENT = re.compile(r"&#(?:0*(?:[0-8]|1[124-9]|2\d|3[01]));")
_HEXENT = re.compile(r"&#[xX]0*(?:[0-8]|[bBcC]|[eEfF]|1[0-9a-fA-F]);")


class TallyError(Exception):
    pass


def clean(s: str) -> str:
    s = _ENT.sub("", s)
    s = _HEXENT.sub("", s)
    s = s.translate(_BAD)
    if "xmlns:UDF" not in s[:500]:
        s = s.replace("<ENVELOPE>", '<ENVELOPE xmlns:UDF="TallyUDF">', 1)
    return s


class Gateway:
    def __init__(self, url: str | None = None):
        from app.config import settings
        self.url = url or settings.TALLY_URL

    def post(self, xml: str, timeout: int = 120) -> str:
        try:
            r = urllib.request.urlopen(self.url, data=xml.encode("utf-8"), timeout=timeout)
            return r.read().decode("utf-8", "ignore")
        except OSError as e:
            msg = str(e).lower()
            if "refused" in msg or "10061" in msg or "name or service" in msg:
                why = "Tally Prime is not running, or its XML port (9000) is off"
            elif "timed out" in msg:
                why = "Tally took too long to answer — a dialog may be open in Tally"
            else:
                why = f"Tally could not be reached ({e})"
            raise TallyError(f"{why} at {self.url}. Open Tally Prime, load the company, close any dialog, retry.")

    def ping(self) -> str:
        try:
            return urllib.request.urlopen(self.url, timeout=5).read().decode("utf-8", "ignore").strip()
        except OSError as e:
            raise TallyError(f"Tally Prime is not reachable at {self.url} ({e})")

    @staticmethod
    def _sv(company=None, frm=None, to=None) -> str:
        sv = "<SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>"
        if company:
            sv += f"<SVCURRENTCOMPANY>{escape(company)}</SVCURRENTCOMPANY>"
        if frm:
            sv += f'<SVFROMDATE TYPE="Date">{frm}</SVFROMDATE><SVTODATE TYPE="Date">{to}</SVTODATE>'
        return f"<STATICVARIABLES>{sv}</STATICVARIABLES>"

    def collection(self, company, name, tally_type, fetch, frm=None, to=None, timeout=120) -> ET.Element:
        fetchxml = "".join(f"<FETCH>{f}</FETCH>" for f in fetch)
        xml = (f"<ENVELOPE><HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST><TYPE>Collection</TYPE>"
               f"<ID>{name}</ID></HEADER><BODY><DESC>{self._sv(company, frm, to)}<TDL><TDLMESSAGE>"
               f'<COLLECTION NAME="{name}" ISMODIFY="No"><TYPE>{tally_type}</TYPE>{fetchxml}</COLLECTION>'
               f"</TDLMESSAGE></TDL></DESC></BODY></ENVELOPE>")
        return ET.fromstring(clean(self.post(xml, timeout)))

    def companies(self) -> list[dict]:
        root = self.collection(None, "CAECoList", "Company", ["NAME", "STARTINGFROM", "BOOKSFROM"], timeout=15)
        out = []
        for c in root.iter("COMPANY"):
            name = (c.get("NAME") or txt(c, "NAME")).strip()
            if name:
                out.append({"name": name, "books_from": _tdate(txt(c, "BOOKSFROM")),
                            "starting_from": _tdate(txt(c, "STARTINGFROM"))})
        return out


# ---------------------------------------------------------------------------- parsing helpers
def txt(el, tag, default="") -> str:
    n = el.find(tag)
    return "".join(n.itertext()).strip() if n is not None else default


def num(s) -> float:
    s = (s or "").replace(",", "").strip()
    if not s:
        return 0.0
    tok = s.split()[0].split("/")[0]          # qty "12.000 Nos", rate "88000.00/Nos"
    try:
        return float(tok)
    except ValueError:
        return 0.0


def _unit(s) -> str:
    parts = (s or "").split()
    return parts[1] if len(parts) > 1 else "NOS"


def _tdate(s) -> date | None:
    s = (s or "").strip()
    try:
        return datetime.strptime(s[:8], "%Y%m%d").date() if s else None
    except ValueError:
        return None


def _code(prefix: str, name: str, n: int = 8) -> str:
    return f"{prefix}{hashlib.md5(name.encode('utf-8')).hexdigest()[:n].upper()}"


def months(frm: date, to: date):
    a = frm
    while a <= to:
        nxt = (a.replace(day=1) + timedelta(days=32)).replace(day=1)
        b = min(nxt - timedelta(days=1), to)
        yield a, b
        a = b + timedelta(days=1)


GROUP_F = ["NAME", "PARENT", "RESERVEDNAME"]
LEDGER_F = ["NAME", "PARENT", "OPENINGBALANCE", "ISBILLWISEON", "INCOMETAXNUMBER", "LEDSTATENAME", "PARTYGSTIN"]
LEDGER_EXT_F = ["NAME", "LEDGSTREGDETAILS.*", "LEDMSMEREGISTRATIONDETAILS.*"]
STOCKITEM_F = ["NAME", "PARENT", "BASEUNITS", "OPENINGBALANCE", "OPENINGVALUE", "OPENINGRATE", "HSNCODE"]
VTYPE_F = ["NAME", "PARENT"]
VOUCHER_F = ["DATE", "VOUCHERTYPENAME", "VOUCHERNUMBER", "GUID", "MASTERID", "REFERENCE", "REFERENCEDATE",
             "PARTYLEDGERNAME", "NARRATION", "ISCANCELLED", "ISOPTIONAL", "ISDELETED", "ISINVOICE", "ENTEREDBY",
             "PARTYGSTIN", "IRN", "IRNACKNO", "IRNACKDATE", "EWAYBILLDETAILS.*",
             "ALLLEDGERENTRIES.*", "LEDGERENTRIES.*", "ALLINVENTORYENTRIES.*", "INVENTORYENTRIES.*",
             "INVENTORYENTRIESIN.*", "INVENTORYENTRIESOUT.*"]
BILLS_F = ["NAME", "PARENT", "BILLDATE", "BILLCREDITPERIOD", "ISADVANCE", "CLOSINGBALANCE"]

NON_ACCOUNTING = {"Sales Order", "Purchase Order", "Job Work In Order", "Job Work Out Order", "Memorandum",
                  "Reversing Journal", "Attendance", "Payroll"}
STOCK_ONLY = {"Delivery Note", "Receipt Note", "Material In", "Material Out", "Physical Stock",
              "Stock Journal", "Rejections In", "Rejections Out"}
STOCK_SKIP = {"Delivery Note", "Receipt Note", "Physical Stock"}   # would double-count or are counts, not moves

# Tally's predefined groups that decide how CAE treats a ledger (nearest one up the tree wins)
KEY_GROUPS = {
    "Sundry Debtors": ("Asset", "debit"), "Sundry Creditors": ("Liability", "credit"),
    "Bank Accounts": ("Asset", "debit"), "Bank OD A/c": ("Liability", "credit"), "Cash-in-Hand": ("Asset", "debit"),
    "Duties & Taxes": ("Liability", "credit"), "Sales Accounts": ("Revenue", "credit"),
    "Purchase Accounts": ("Expense", "debit"), "Direct Expenses": ("Expense", "debit"),
    "Indirect Expenses": ("Expense", "debit"), "Direct Incomes": ("Revenue", "credit"),
    "Indirect Incomes": ("Revenue", "credit"), "Fixed Assets": ("Asset", "debit"), "Investments": ("Asset", "debit"),
    "Stock-in-Hand": ("Asset", "debit"), "Deposits (Asset)": ("Asset", "debit"),
    "Loans & Advances (Asset)": ("Asset", "debit"), "Secured Loans": ("Liability", "credit"),
    "Unsecured Loans": ("Liability", "credit"), "Loans (Liability)": ("Liability", "credit"),
    "Capital Account": ("Equity", "credit"), "Reserves & Surplus": ("Equity", "credit"),
    "Provisions": ("Liability", "credit"), "Current Assets": ("Asset", "debit"),
    "Current Liabilities": ("Liability", "credit"), "Suspense A/c": ("Liability", "credit"),
    "Misc. Expenses (ASSET)": ("Asset", "debit"), "Branch / Divisions": ("Asset", "debit"),
}
_MODE = [("rtgs", "RTGS"), ("neft", "NEFT"), ("imps", "IMPS"), ("upi", "UPI"), ("cheque", "cheque"),
         ("chq", "cheque"), ("dd", "cheque"), ("ecs", "ECS"), ("e-fund", "NEFT")]


def _base_parent(vt: str, vtypes: dict) -> str:
    seen, v = set(), vt
    while v in vtypes and v not in seen:
        seen.add(v)
        p = vtypes[v]
        if not p or p == v:
            break
        v = p
    return v


def _group_class(group: str, groups: dict) -> str | None:
    seen, g = set(), group
    while g and g not in seen:
        seen.add(g)
        reserved, parent = groups.get(g, ("", ""))
        for candidate in (reserved, g):
            if candidate in KEY_GROUPS:
                return candidate
        if not parent or parent == g or parent == "Primary":
            break
        g = parent
    return None


def _credit_days(s: str) -> int | None:
    m = re.search(r"(\d+)", s or "")
    return int(m.group(1)) if m else None


# ---------------------------------------------------------------------------- pull
def pull(gw: Gateway, company: str, frm: date, to: date, extended: bool = False, progress=None) -> dict:
    say = progress or (lambda m: log.info(m))
    f, t = frm.strftime("%Y%m%d"), to.strftime("%Y%m%d")
    warnings: list[str] = []

    say("masters: groups, voucher types")
    groups = {}
    for g in gw.collection(company, "CAEGrp", "Group", GROUP_F).iter("GROUP"):
        name = (g.get("NAME") or txt(g, "NAME")).strip()
        if name:
            groups[name] = (txt(g, "RESERVEDNAME"), txt(g, "PARENT"))
    vtypes = {}
    for v in gw.collection(company, "CAEVt", "VoucherType", VTYPE_F).iter("VOUCHERTYPE"):
        name = (v.get("NAME") or txt(v, "NAME")).strip()
        if name:
            vtypes[name] = txt(v, "PARENT")

    say("masters: ledgers")
    ledgers = {}
    for el in gw.collection(company, "CAELed", "Ledger", LEDGER_F, f, t, timeout=300).iter("LEDGER"):
        name = (el.get("NAME") or txt(el, "NAME")).strip()
        if not name:
            continue
        gstin = txt(el, "PARTYGSTIN")
        for g in el.iter("LEDGSTREGDETAILS.LIST"):
            gstin = gstin or txt(g, "GSTIN")
        ledgers[name] = {"parent": txt(el, "PARENT"), "pan": txt(el, "INCOMETAXNUMBER"), "gstin": gstin,
                         "state": txt(el, "LEDSTATENAME"), "billwise": txt(el, "ISBILLWISEON") == "Yes",
                         "opening": num(txt(el, "OPENINGBALANCE")), "msme": ""}
    if extended:
        say("masters: ledger GST / MSME details (extended)")
        try:
            for el in gw.collection(company, "CAELedX", "Ledger", LEDGER_EXT_F, timeout=300).iter("LEDGER"):
                name = (el.get("NAME") or txt(el, "NAME")).strip()
                if name not in ledgers:
                    continue
                for g in el.iter("LEDGSTREGDETAILS.LIST"):
                    ledgers[name]["gstin"] = ledgers[name]["gstin"] or txt(g, "GSTIN")
                for m in el.iter("LEDMSMEREGISTRATIONDETAILS.LIST"):
                    ledgers[name]["msme"] = txt(m, "MSMEENTERPRISETYPE") or txt(m, "TYPEOFENTERPRISE") or ledgers[name]["msme"]
        except TallyError as e:
            warnings.append(f"extended ledger details skipped: {e}")

    say("masters: stock items")
    items = {}
    try:
        for el in gw.collection(company, "CAESi", "StockItem", STOCKITEM_F, f, t, timeout=300).iter("STOCKITEM"):
            name = (el.get("NAME") or txt(el, "NAME")).strip()
            if name:
                raw_qty = txt(el, "OPENINGBALANCE")
                items[name] = {"group": txt(el, "PARENT"), "unit": txt(el, "BASEUNITS") or _unit(raw_qty),
                               "qty": num(raw_qty), "value": abs(num(txt(el, "OPENINGVALUE"))),
                               "rate": num(txt(el, "OPENINGRATE")), "hsn": txt(el, "HSNCODE")}
    except TallyError as e:
        warnings.append(f"stock items skipped: {e}")

    vouchers = []
    for a, b in months(frm, to):
        say(f"vouchers {a:%d-%m-%Y} to {b:%d-%m-%Y}")
        root = gw.collection(company, "CAEVch", "Voucher", VOUCHER_F, a.strftime("%Y%m%d"), b.strftime("%Y%m%d"),
                             timeout=300)
        for v in root.iter("VOUCHER"):
            if len(v) == 0:          # <CMPINFO><VOUCHER>n</VOUCHER> count element
                continue
            parsed = _parse_voucher(v, vtypes)
            if parsed["date"] and not (a <= parsed["date"] <= b):
                raise TallyError(f"Tally returned a voucher dated {parsed['date']} for the window {a}..{b} — "
                                 "the period was not applied; nothing was imported")
            vouchers.append(parsed)

    say("bill-wise outstanding")
    bills = {}
    try:
        for b in gw.collection(company, "CAEBills", "Bills", BILLS_F, f, t, timeout=300).iter("BILL"):
            ref = (b.get("NAME") or txt(b, "NAME")).strip()
            party = txt(b, "PARENT").strip()
            if ref and party:
                bills[(party, ref)] = {"closing": num(txt(b, "CLOSINGBALANCE")), "date": _tdate(txt(b, "BILLDATE")),
                                       "credit_days": _credit_days(txt(b, "BILLCREDITPERIOD"))}
    except TallyError as e:
        warnings.append(f"bill-wise outstanding not available ({e}); outstanding left unknown")
        bills = None
    return {"company": company, "from": frm, "to": to, "groups": groups, "vtypes": vtypes, "ledgers": ledgers,
            "items": items, "vouchers": vouchers, "bills": bills, "warnings": warnings}


def _parse_voucher(v, vtypes) -> dict:
    vt = txt(v, "VOUCHERTYPENAME") or v.get("VCHTYPE", "")
    parent = _base_parent(vt, vtypes)
    excluded = next((label for flag, label in (("ISCANCELLED", "cancelled"), ("ISDELETED", "deleted"),
                                              ("ISOPTIONAL", "optional")) if txt(v, flag) == "Yes"), None)
    if excluded:
        books = False
    else:
        books = parent not in NON_ACCOUNTING and parent not in STOCK_ONLY
    tag = "ALLLEDGERENTRIES.LIST" if v.find("ALLLEDGERENTRIES.LIST") is not None else "LEDGERENTRIES.LIST"
    lines = []
    for e in v.findall(tag):
        led = txt(e, "LEDGERNAME")
        if not led:
            continue
        bank = [{"type": txt(b, "TRANSACTIONTYPE"), "instrument": txt(b, "INSTRUMENTNUMBER"),
                 "utr": txt(b, "UNIQUEREFERENCENUMBER")} for b in e.findall("BANKALLOCATIONS.LIST")]
        lines.append({"ledger": led, "amount": num(txt(e, "AMOUNT")), "is_party": txt(e, "ISPARTYLEDGER") == "Yes",
                      "bills": [{"ref": txt(b, "NAME"), "type": txt(b, "BILLTYPE"), "amount": num(txt(b, "AMOUNT")),
                                 "credit_days": _credit_days(txt(b, "BILLCREDITPERIOD"))}
                                for b in e.findall("BILLALLOCATIONS.LIST") if txt(b, "NAME")],
                      "bank": [b for b in bank if any(b.values())]})
    itags = ["ALLINVENTORYENTRIES.LIST"] if v.find("ALLINVENTORYENTRIES.LIST") is not None else ["INVENTORYENTRIES.LIST"]
    stock = []
    for t in itags + ["INVENTORYENTRIESIN.LIST", "INVENTORYENTRIESOUT.LIST"]:
        for e in v.findall(t):
            item = txt(e, "STOCKITEMNAME")
            if not item:
                continue
            godown = ""
            for ba in e.findall("BATCHALLOCATIONS.LIST"):
                godown = txt(ba, "GODOWNNAME") or godown
            qty_raw = txt(e, "ACTUALQTY") or txt(e, "BILLEDQTY")
            inward = txt(e, "ISDEEMEDPOSITIVE") == "Yes" if t not in ("INVENTORYENTRIESIN.LIST", "INVENTORYENTRIESOUT.LIST") \
                else t == "INVENTORYENTRIESIN.LIST"
            stock.append({"item": item, "qty": abs(num(qty_raw)), "unit": _unit(qty_raw), "rate": num(txt(e, "RATE")),
                          "amount": abs(num(txt(e, "AMOUNT"))), "inward": inward, "godown": godown})
    eway = ""
    for ew in v.iter("EWAYBILLDETAILS.LIST"):
        eway = txt(ew, "BILLNUMBER") or eway
    return {"guid": v.get("REMOTEID") or txt(v, "GUID"), "date": _tdate(txt(v, "DATE")), "vtype": vt, "parent": parent,
            "number": txt(v, "VOUCHERNUMBER"), "reference": txt(v, "REFERENCE"), "ref_date": _tdate(txt(v, "REFERENCEDATE")),
            "party": txt(v, "PARTYLEDGERNAME"), "party_gstin": txt(v, "PARTYGSTIN"), "narration": txt(v, "NARRATION"),
            "entered_by": txt(v, "ENTEREDBY"), "irn": txt(v, "IRN") or txt(v, "IRNACKNO"), "eway": eway,
            "in_books": books, "excluded": excluded, "lines": lines, "stock": stock}


# ---------------------------------------------------------------------------- load into CAE
def _duty_kind(name: str) -> str | None:
    n = name.upper()
    for key, kind in (("IGST", "igst"), ("CGST", "cgst"), ("SGST", "sgst"), ("UTGST", "sgst"), ("CESS", "cess"),
                      ("TDS", "tds"), ("TCS", "tcs")):
        if key in n:
            return kind
    return None


def _mode(line: dict, cls: str | None, narration: str) -> str:
    if cls == "Cash-in-Hand":
        return "cash"
    text = " ".join([*(b.get("type", "") for b in line["bank"]), narration or ""]).lower()
    for key, mode in _MODE:
        if key in text:
            return mode
    return "bank"


def load(db, company_id: uuid.UUID, data: dict) -> dict:
    """Replace this company's Tally-sourced rows for the period and load the pulled books."""
    from app.models.master import Customer, GLAccount, Vendor
    from app.models.transaction import (BankTransaction, InventoryMovement, JournalEntry, JournalEntryLine,
                                        PurchaseInvoice, SalesInvoice)

    frm, to = data["from"], data["to"]
    groups, ledgers, bills = data["groups"], data["ledgers"], data["bills"]
    cls = {name: _group_class(info["parent"], groups) for name, info in ledgers.items()}

    # idempotent re-import: drop earlier Tally rows of the same window
    jes = db.query(JournalEntry.id).filter(JournalEntry.company_id == company_id, JournalEntry.erp_source == "tally",
                                           JournalEntry.entry_date.between(frm, to))
    old_ids = [r[0] for r in jes.all()]
    for i in range(0, len(old_ids), 1000):
        db.query(JournalEntryLine).filter(JournalEntryLine.journal_entry_id.in_(old_ids[i:i + 1000])).delete(
            synchronize_session=False)
    for model, col in ((JournalEntry, JournalEntry.entry_date), (SalesInvoice, SalesInvoice.invoice_date),
                       (PurchaseInvoice, PurchaseInvoice.invoice_date), (BankTransaction, BankTransaction.transaction_date),
                       (InventoryMovement, InventoryMovement.movement_date)):
        db.query(model).filter(model.company_id == company_id, model.erp_source == "tally",
                               col.between(frm, to)).delete(synchronize_session=False)
    db.flush()

    # masters (upsert by name)
    stats = defaultdict(int)
    existing_gl = {g.account_name: g for g in db.query(GLAccount).filter(GLAccount.company_id == company_id).all()}
    gl_ids = {}
    for name, info in ledgers.items():
        c = cls[name]
        acct_type, normal = KEY_GROUPS.get(c, ("Asset", "debit")) if c else ("Asset", "debit")
        g = existing_gl.get(name[:200])
        if g is None:
            g = GLAccount(id=uuid.uuid4(), company_id=company_id, account_code=_code("TL", name), account_name=name[:200],
                          account_type=acct_type, normal_balance=normal)
            db.add(g)
            stats["gl_accounts_added"] += 1
        g.account_subtype = (c or info["parent"] or "")[:100]
        g.is_bank_account = c in ("Bank Accounts", "Bank OD A/c")
        g.is_cash_account = c == "Cash-in-Hand"
        g.is_control_account = c in ("Sundry Debtors", "Sundry Creditors")
        gl_ids[name] = (g.id, g.account_code)
    # customers and vendors are separate masters: a debtor can appear on a purchase voucher (a customer
    # who also supplies) and a creditor on a sales voucher, so each side keeps its own name -> id map
    masters = {"customer": (Customer, "customer_code"), "vendor": (Vendor, "vendor_code")}
    party_ids = {kind: {p.name: p for p in db.query(model).filter(model.company_id == company_id).all()}
                 for kind, (model, _) in masters.items()}

    def party_id(kind: str, name: str | None):
        """Master id for a party on the given side, creating the master if the ledger is not there yet."""
        if not name:
            return None
        p = party_ids[kind].get(name[:300])
        if p is None:
            model, code_field = masters[kind]
            p = model(id=uuid.uuid4(), company_id=company_id, name=name[:300], **{code_field: _code("TL", name)})
            db.add(p)
            party_ids[kind][name[:300]] = p
            stats[f"{kind}s_added"] += 1
        info = ledgers.get(name)
        if info:
            p.gstin = (info["gstin"] or None) and info["gstin"][:15]
            p.pan = (info["pan"] or None) and info["pan"][:10]
            p.state = info["state"] or None
            if kind == "vendor" and info["msme"]:
                p.msme_status = info["msme"].title()[:20]
        return p.id

    for name in ledgers:
        if cls[name] == "Sundry Debtors":
            party_id("customer", name)
        elif cls[name] == "Sundry Creditors":
            party_id("vendor", name)
    db.flush()

    # settlement dates: the last Agst Ref allocation against each bill
    settled_on: dict[tuple, date] = {}
    for v in data["vouchers"]:
        if not v["in_books"]:
            continue
        for ln in v["lines"]:
            for b in ln["bills"]:
                if b["type"].lower().startswith("agst"):
                    key = (ln["ledger"], b["ref"])
                    settled_on[key] = max(settled_on.get(key, v["date"]), v["date"])

    avg = {}   # item -> [qty, value] running weighted average
    for name, it in data["items"].items():
        if it["qty"] > 0:
            avg[name] = [it["qty"], it["value"] or it["qty"] * it["rate"]]
            db.add(InventoryMovement(id=uuid.uuid4(), company_id=company_id, movement_date=frm, movement_type="opening",
                                     item_code=name[:100], item_name=name[:300], item_category=(it["group"] or None),
                                     hsn_sac_code=(it["hsn"] or None) and it["hsn"][:8], unit_of_measure=(it["unit"] or "NOS")[:20],
                                     quantity=Decimal(str(it["qty"])), unit_cost=Decimal(str(round(avg[name][1] / it["qty"], 4))),
                                     total_value=Decimal(str(round(avg[name][1], 2))), erp_source="tally",
                                     remarks="Opening stock from the Tally item master"))
            stats["inventory_movements"] += 1

    D = lambda x: Decimal(str(round(x, 2)))  # noqa: E731
    # Tally restarts numbering per voucher type and per year (Payment 1, Receipt 1 ...) and allows
    # manual duplicates; CAE keys journals on (company, voucher_number), so key on type / number / FY
    used_nos = {n for (n,) in db.query(JournalEntry.voucher_number).filter(JournalEntry.company_id == company_id).all()}

    def voucher_key(v) -> str:
        d = v["date"] or frm
        fy = d.year if d.month >= 4 else d.year - 1
        base = f"{v['vtype'][:40]}/{v['number'] or v['guid'][:12]}/FY{str(fy)[-2:]}-{str(fy + 1)[-2:]}"[:95]
        key, n = base, 2
        while key in used_nos:
            key, n = f"{base}#{n}", n + 1
        used_nos.add(key)
        return key

    for v in sorted(data["vouchers"], key=lambda x: (x["date"] or frm, x["number"])):
        if v["in_books"] and any(abs(ln["amount"]) >= 0.005 for ln in v["lines"]):
            dr = sum(-ln["amount"] for ln in v["lines"] if ln["amount"] < 0)
            cr = sum(ln["amount"] for ln in v["lines"] if ln["amount"] > 0)
            je = JournalEntry(id=uuid.uuid4(), company_id=company_id, voucher_number=voucher_key(v),
                              entry_date=v["date"], voucher_type=v["parent"].lower()[:30], reference_number=(v["reference"] or None) and v["reference"][:100],
                              narration=v["narration"] or None, total_debit=D(dr), total_credit=D(cr), is_posted=True,
                              is_reversed=False, status="posted", erp_source="tally", erp_internal_id=v["guid"][:100] or None,
                              raw_data={"entered_by": v["entered_by"] or None, "voucher_type": v["vtype"], "party": v["party"]})
            db.add(je)
            for i, ln in enumerate(v["lines"], 1):
                gid, gcode = gl_ids.get(ln["ledger"], (None, None))
                db.add(JournalEntryLine(id=uuid.uuid4(), journal_entry_id=je.id, line_number=i, account_id=gid,
                                        account_code=gcode, account_name=ln["ledger"][:200],
                                        debit_amount=D(-ln["amount"]) if ln["amount"] < 0 else D(0),
                                        credit_amount=D(ln["amount"]) if ln["amount"] > 0 else D(0)))
            stats["journal_entries"] += 1
            if v["parent"] in ("Sales", "Purchase"):
                _invoice(db, company_id, v, cls, party_id, ledgers, bills, settled_on, stats)
            for ln in v["lines"]:
                c = cls.get(ln["ledger"])
                if c not in ("Bank Accounts", "Bank OD A/c", "Cash-in-Hand") or not ln["amount"]:
                    continue
                others = [o for o in v["lines"] if o is not ln and cls.get(o["ledger"]) not in ("Bank Accounts", "Bank OD A/c")
                          and (o["amount"] > 0) == (ln["amount"] < 0)]
                party = v["party"] if v["party"] and v["party"] != ln["ledger"] else \
                    (max(others, key=lambda o: abs(o["amount"]))["ledger"] if others else None)
                bank_ref = next((b for b in ln["bank"] if b.get("instrument") or b.get("utr")), {})
                db.add(BankTransaction(id=uuid.uuid4(), company_id=company_id, transaction_date=v["date"],
                                       transaction_type="credit" if ln["amount"] < 0 else "debit", amount=D(abs(ln["amount"])),
                                       description=(v["narration"] or f"{v['vtype']} {v['number']}")[:1000],
                                       reference_number=(bank_ref.get("instrument") or v["number"] or None),
                                       utr_number=(bank_ref.get("utr") or None) and bank_ref["utr"][:22], transaction_mode=_mode(ln, c, v["narration"]),
                                       counterparty_name=(party or None) and party[:300], erp_source="tally",
                                       raw_data={"ledger": ln["ledger"], "voucher_type": v["vtype"], "voucher_number": v["number"]}))
                stats["bank_transactions"] += 1
        if v["stock"] and (v["in_books"] or v["parent"] in STOCK_ONLY - STOCK_SKIP) and v["parent"] not in STOCK_SKIP:
            for s in v["stock"]:
                q, val = avg.setdefault(s["item"], [0.0, 0.0])
                if s["inward"]:
                    value = s["amount"] or s["qty"] * s["rate"]
                    avg[s["item"]] = [q + s["qty"], val + value]
                    mtype = "goods_receipt" if v["parent"] in ("Purchase", "Credit Note") else "adjustment"
                else:
                    unit_cost = (val / q) if q > 0 else s["rate"]
                    value = s["qty"] * unit_cost
                    avg[s["item"]] = [q - s["qty"], val - value]
                    mtype = "goods_issue"
                db.add(InventoryMovement(id=uuid.uuid4(), company_id=company_id, movement_date=v["date"], movement_type=mtype,
                                         item_code=s["item"][:100], item_name=s["item"][:300], unit_of_measure=s["unit"][:20],
                                         quantity=Decimal(str(s["qty"])),
                                         unit_cost=Decimal(str(round(value / s["qty"], 4))) if s["qty"] else Decimal("0"),
                                         total_value=D(value), warehouse_from=(s["godown"] or None),
                                         reference_document_type=v["parent"].lower()[:50],
                                         reference_document_number=(v["number"] or None), erp_source="tally"))
                stats["inventory_movements"] += 1
    db.commit()
    stats["vouchers_read"] = len(data["vouchers"])
    stats["vouchers_in_books"] = sum(1 for v in data["vouchers"] if v["in_books"])
    # zero-value vouchers carry no ledger amount, so they are not loaded — but nullifying an invoice
    # instead of cancelling it is itself worth a look, so say which ones
    for label in ("cancelled", "optional", "deleted"):
        out = [v for v in data["vouchers"] if v.get("excluded") == label]
        if out:
            stats[f"{label}_vouchers"] = len(out)
            listed = ", ".join(f"{v['vtype']} {v['number']}" for v in out[:15])
            data["warnings"].append(f"{len(out)} {label} voucher(s) kept out of the books: {listed}"
                                    f"{' …' if len(out) > 15 else ''}")
    zero = [v for v in data["vouchers"] if v["in_books"] and not any(abs(ln["amount"]) >= 0.005 for ln in v["lines"])]
    if zero:
        stats["zero_value_vouchers"] = len(zero)
        listed = ", ".join(f"{v['vtype']} {v['number']} ({v['date']:%d-%m-%Y})" for v in zero[:15] if v["date"])
        data["warnings"].append(f"{len(zero)} zero-value voucher(s) in the books were not loaded — review them: "
                                f"{listed}{' …' if len(zero) > 15 else ''}")
    return dict(stats)


def _invoice(db, company_id, v, cls, party_id, ledgers, bills, settled_on, stats):
    from app.models.transaction import PurchaseInvoice, SalesInvoice

    sales = v["parent"] == "Sales"
    party_line = next((ln for ln in v["lines"] if ln["is_party"] or ln["ledger"] == v["party"]), None)
    tax = defaultdict(float)
    taxable = discount = 0.0
    for ln in v["lines"]:
        if ln is party_line:
            continue
        signed = ln["amount"] if sales else -ln["amount"]      # sales: credits add; purchases: debits add
        kind = _duty_kind(ln["ledger"]) if cls.get(ln["ledger"]) == "Duties & Taxes" else None
        if kind:
            tax[kind] += signed if kind not in ("tds", "tcs") else abs(ln["amount"])
        elif "round" in ln["ledger"].lower():
            continue
        else:
            taxable += signed
            if signed < 0:
                discount += -signed
    total = abs(party_line["amount"]) if party_line else taxable + tax["cgst"] + tax["sgst"] + tax["igst"] + tax["cess"]
    party = party_line["ledger"] if party_line else v["party"]
    ref = next((b["ref"] for b in (party_line or {"bills": []})["bills"] if b["type"].lower().startswith("new")), None) \
        or (v["number"] if sales else v["reference"] or v["number"])
    bill = (bills or {}).get((party, ref)) if party else None
    known = bills is not None and party in ledgers and ledgers[party]["billwise"]
    outstanding = abs(bill["closing"]) if bill else 0.0
    credit = (bill or {}).get("credit_days") or next((b["credit_days"] for b in (party_line or {"bills": []})["bills"]
                                                      if b["credit_days"]), None)
    due = (v["date"] + timedelta(days=credit)) if credit else None
    paid_on = settled_on.get((party, ref)) if known and outstanding < 0.5 else None
    common = dict(id=uuid.uuid4(), company_id=company_id, invoice_date=v["ref_date"] if (not sales and v["ref_date"]) else v["date"],
                  due_date=due, gross_amount=Decimal(str(round(taxable + discount, 2))),
                  discount_amount=Decimal(str(round(discount, 2))), taxable_amount=Decimal(str(round(taxable, 2))),
                  cgst_amount=Decimal(str(round(tax["cgst"], 2))), sgst_amount=Decimal(str(round(tax["sgst"], 2))),
                  igst_amount=Decimal(str(round(tax["igst"], 2))), cess_amount=Decimal(str(round(tax["cess"], 2))),
                  total_amount=Decimal(str(round(total, 2))), outstanding_amount=Decimal(str(round(outstanding, 2))),
                  paid_amount=Decimal(str(round(max(total - outstanding, 0), 2))) if known else Decimal("0"),
                  payment_date=paid_on, status=("paid" if paid_on else "pending") if known else "confirmed",
                  erp_source="tally", erp_internal_id=v["guid"][:100] or None,
                  raw_data={"voucher_type": v["vtype"], "voucher_number": v["number"], "bill_ref": ref,
                            "outstanding_known": known, "has_inventory": bool(v["stock"]),
                            "entered_by": v["entered_by"] or None})
    if sales:
        db.add(SalesInvoice(invoice_number=(v["number"] or v["guid"][:30])[:50], customer_id=party_id("customer", party),
                            e_invoice_irn=(v["irn"] or None) and v["irn"][:64],
                            e_way_bill_number=(v["eway"] or None) and v["eway"][:12],
                            tds_amount=Decimal(str(round(tax["tds"], 2))), **common))
        stats["sales_invoices"] += 1
    else:
        db.add(PurchaseInvoice(invoice_number=(v["reference"] or v["number"] or v["guid"][:30])[:50],
                               our_po_number=None, vendor_id=party_id("vendor", party), receipt_date=v["date"],
                               vendor_gstin=(v["party_gstin"] or ledgers.get(party, {}).get("gstin") or "")[:15] or None,
                               itc_eligible=(tax["cgst"] + tax["sgst"] + tax["igst"]) > 0,
                               tds_amount=Decimal(str(round(tax["tds"], 2))),
                               e_way_bill_number=(v["eway"] or None) and v["eway"][:12],
                               **common))
        stats["purchase_invoices"] += 1


# ---------------------------------------------------------------------------- job entry point
def run_import_job(job_id: str, cae_company_id: str, tally_company: str, from_date: str, to_date: str,
                   extended: bool = False) -> dict:
    from app.database import SessionLocal
    from app.models.ingestion import SyncJob

    db = SessionLocal()
    job = db.query(SyncJob).filter(SyncJob.id == uuid.UUID(str(job_id))).first()
    steps: list[str] = []

    def progress(msg):
        steps.append(msg)
        if job:
            job.result_json = {"stage": msg, "steps": steps[-50:]}
            db.commit()

    try:
        if job:
            job.status, job.started_at = "running", datetime.utcnow()
            db.commit()
        frm, to = date.fromisoformat(from_date), date.fromisoformat(to_date)
        data = pull(Gateway(), tally_company, frm, to, extended, progress)
        progress("loading into CAE")
        stats = load(db, uuid.UUID(cae_company_id), data)
        result = {"tally_company": tally_company, "from": from_date, "to": to_date, **stats,
                  "warnings": data["warnings"], "steps": steps[-50:]}
        if job:
            job.status, job.completed_at = "completed", datetime.utcnow()
            job.records_processed = stats.get("vouchers_in_books", 0)
            job.result_json = result
            db.commit()
        return result
    except Exception as e:
        db.rollback()
        if job:
            job = db.query(SyncJob).filter(SyncJob.id == uuid.UUID(str(job_id))).first()
            job.status, job.completed_at, job.error_message = "failed", datetime.utcnow(), str(e)[:500]
            job.result_json = {"steps": steps[-50:]}
            db.commit()
        log.exception("Tally import failed")
        return {"error": str(e)}
    finally:
        db.close()
