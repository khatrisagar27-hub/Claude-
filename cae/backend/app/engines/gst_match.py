"""
Deterministic GSTR-2B vs books matching — ported from the gstr2b-recon skill's
recon_engine.py. No LLM, no fuzzy auto-match.

Key = (normalised supplier GSTIN, normalised invoice number). Buckets:
  matched           key on both sides, taxable and tax within tolerance, same date
  mismatch          key on both sides, taxable / tax / date differ
  missing_in_2b     in books only  -> ITC at risk (supplier has not reported it)
  missing_in_books  in 2B only     -> ITC available but not booked
  review_probable   2B row whose GSTIN + tax match a books row with a different
                    invoice number; a person decides, the engine never pairs them

Changes from the skill version: duplicate keys are paired one-to-one instead of all
books rows being compared with the first 2B row, and dates are compared as dates.
"""
from __future__ import annotations

import csv
import io
import re
from collections import defaultdict
from datetime import date, datetime

GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$")

HEADER_HINTS = {
    "gstin": ["gstin of supplier", "supplier gstin", "gstin/uin", "gstin"],
    "inv_no": ["invoice number", "invoice no", "inv no", "bill no", "document number", "doc number"],
    "inv_date": ["invoice date", "inv date", "document date", "date"],
    "taxable": ["taxable value", "taxable amount", "taxable"],
    "igst": ["integrated tax", "igst"],
    "cgst": ["central tax", "cgst"],
    "sgst": ["state/ut tax", "state tax", "sgst", "utgst"],
    "cess": ["cess"],
    "supplier": ["trade/legal name", "supplier name", "legal name", "party", "name"],
}


def norm_gstin(v) -> str:
    return re.sub(r"\s+", "", str(v or "")).upper()


def norm_inv(v) -> str:
    """Uppercase, alphanumerics only, leading zeros of the trailing number dropped."""
    s = re.sub(r"[^0-9A-Za-z]", "", str(v or "")).upper()
    m = re.match(r"^(.*?)(0*)(\d+)$", s)
    if m and m.group(3):
        s = m.group(1) + str(int(m.group(3)))
    return s


def to_num(v) -> float:
    if v is None or v == "":
        return 0.0
    try:
        return float(re.sub(r"[,\s₹]", "", str(v)))
    except ValueError:
        return 0.0


def to_date(v) -> date | None:
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    s = str(v).strip()
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%b-%Y", "%d-%b-%y", "%d.%m.%Y"):
        try:
            return datetime.strptime(s[:11].strip(), fmt).date()
        except ValueError:
            continue
    return None


def record(gstin, inv_no, inv_date, taxable, tax, supplier="", ref=None) -> dict:
    return {
        "gstin": norm_gstin(gstin), "inv_no_raw": str(inv_no or "").strip(), "inv_no": norm_inv(inv_no),
        "inv_date": to_date(inv_date), "taxable": round(to_num(taxable), 2), "tax": round(to_num(tax), 2),
        "supplier": str(supplier or "").strip(), "ref": ref,
    }


def _find_header(rows):
    for i, row in enumerate(rows[:40]):
        cells = [str(c).strip().lower() if c is not None else "" for c in row]
        if any("gstin" in c for c in cells) and any("invoice" in c or "taxable" in c for c in cells):
            return i, cells
    return None, None


def _map_columns(header):
    colmap = {}
    for field, hints in HEADER_HINTS.items():
        colmap[field] = next((j for hint in hints for j, c in enumerate(header) if hint in c), None)
    return colmap


def parse_2b_file(content: bytes, filename: str) -> tuple[list[dict], dict]:
    """Read a GSTR-2B Excel (portal download) or CSV. Returns (records, stats); rows with an
    amount but no valid GSTIN are counted, never silently dropped."""
    if filename.lower().endswith((".xlsx", ".xlsm")):
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        sheets = [[list(r) for r in ws.iter_rows(values_only=True)] for ws in wb.worksheets]
    else:
        sheets = [list(csv.reader(io.StringIO(content.decode("utf-8-sig"))))]

    best, best_stats = [], {"data_rows": 0, "invalid_gstin": 0}
    for rows in sheets:
        hi, header = _find_header(rows)
        if hi is None:
            continue
        cm = _map_columns(header)
        if cm["taxable"] is None or cm["gstin"] is None:
            continue
        recs, stats = [], {"data_rows": 0, "invalid_gstin": 0}
        for row in rows[hi + 1:]:
            def cell(f):
                k = cm.get(f)
                return row[k] if k is not None and k < len(row) else None
            tax = sum(to_num(cell(k)) for k in ("igst", "cgst", "sgst", "cess"))
            taxable = to_num(cell("taxable"))
            if tax == 0 and taxable == 0:
                continue
            stats["data_rows"] += 1
            r = record(cell("gstin"), cell("inv_no"), cell("inv_date"), taxable, tax, cell("supplier"))
            if not GSTIN_RE.match(r["gstin"]):
                stats["invalid_gstin"] += 1
                continue
            recs.append(r)
        # most valid rows wins; ties go to the sheet with more data rows so the
        # invalid-GSTIN count still explains an empty result
        if (len(recs), stats["data_rows"]) > (len(best), best_stats["data_rows"]):
            best, best_stats = recs, stats
    return best, best_stats


def reconcile(b2: list[dict], books: list[dict], tolerance: float = 1.0) -> dict:
    i2, ib = defaultdict(list), defaultdict(list)
    for r in b2:
        i2[(r["gstin"], r["inv_no"])].append(r)
    for r in books:
        ib[(r["gstin"], r["inv_no"])].append(r)

    out = {k: [] for k in ("matched", "mismatch", "missing_in_2b", "missing_in_books", "review_probable")}
    leftover_2b = []
    for key in set(i2) | set(ib):
        brecs, recs2 = ib.get(key, []), i2.get(key, [])
        for br, r2 in zip(brecs, recs2):
            flags = []
            d_tax, d_txbl = round(br["tax"] - r2["tax"], 2), round(br["taxable"] - r2["taxable"], 2)
            if abs(d_tax) > tolerance:
                flags.append("tax")
            if abs(d_txbl) > tolerance:
                flags.append("taxable")
            if br["inv_date"] and r2["inv_date"] and br["inv_date"] != r2["inv_date"]:
                flags.append("date")
            row = {**br, "b2_inv_date": r2["inv_date"], "b2_taxable": r2["taxable"], "b2_tax": r2["tax"],
                   "diff_taxable": d_txbl, "diff_tax": d_tax, "mismatch_on": ",".join(flags)}
            out["mismatch" if flags else "matched"].append(row)
        for br in brecs[len(recs2):]:
            out["missing_in_2b"].append(dict(br, reason="In books, not in GSTR-2B: ITC at risk"))
        leftover_2b.extend(recs2[len(brecs):])

    by_amount = defaultdict(list)
    for r in out["missing_in_2b"]:
        by_amount[(r["gstin"], round(r["tax"]))].append(r)
    for r in leftover_2b:
        probable = by_amount.get((r["gstin"], round(r["tax"])))
        if probable:
            out["review_probable"].append(dict(r, books_inv_no=probable[0]["inv_no_raw"],
                                               note="GSTIN and tax match a books invoice with a different number"))
        else:
            out["missing_in_books"].append(dict(r, reason="In GSTR-2B, not in books"))

    itc_at_risk = sum(r["tax"] for r in out["missing_in_2b"]) + sum(max(r["diff_tax"], 0) for r in out["mismatch"])
    out["summary"] = {
        **{f"{k}_count": len(v) for k, v in out.items() if isinstance(v, list)},
        "books_itc": round(sum(r["tax"] for r in books), 2),
        "gstr2b_itc": round(sum(r["tax"] for r in b2), 2),
        "itc_at_risk": round(itc_at_risk, 2),
        "itc_not_booked": round(sum(r["tax"] for r in out["missing_in_books"]), 2),
        "tolerance": tolerance,
    }
    return out
