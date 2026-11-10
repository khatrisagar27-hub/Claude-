"""Tally Prime Day Book XML → ledger entry records.

Tally stores a debit as a negative AMOUNT (ISDEEMEDPOSITIVE = Yes) and a credit
as a positive one. Ledger groups are not part of a voucher export, so
ledger_group stays blank unless a tabular day book supplies it.
"""
import re
import xml.etree.ElementTree as ET

VOUCHER_TYPES = {"sales": "sales", "purchase": "purchase", "payment": "payment", "receipt": "receipt",
                 "journal": "journal", "contra": "contra", "credit note": "credit_note", "debit note": "debit_note"}


def parse_tally_xml(content: bytes) -> list[dict]:
    text = content.decode("utf-8", errors="replace") if not content.startswith(b"\xff\xfe") else content.decode("utf-16")
    if "<!DOCTYPE" in text or "<!ENTITY" in text:
        raise ValueError("XML with a DOCTYPE or entity declaration is not accepted")
    # Tally emits control-character references (e.g. &#4;) that are illegal in XML 1.0.
    text = re.sub(r"&#(?:x[0-9a-fA-F]+|\d+);", lambda mt: mt.group(0) if _legal(mt.group(0)) else "", text)
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise ValueError(f"Not a valid Tally XML export: {exc}")
    records = []
    for voucher in root.iter("VOUCHER"):
        raw_type = (voucher.get("VCHTYPE") or voucher.findtext("VOUCHERTYPENAME") or "").strip().lower()
        common = {
            "voucher_no": (voucher.findtext("VOUCHERNUMBER") or "").strip(),
            "voucher_date": (voucher.findtext("DATE") or "").strip(),
            "voucher_type": VOUCHER_TYPES.get(raw_type, raw_type),
            "narration": (voucher.findtext("NARRATION") or "").strip(),
            "entered_by": (voucher.findtext("ENTEREDBY") or "").strip(),
        }
        lines = voucher.findall("ALLLEDGERENTRIES.LIST") + voucher.findall("LEDGERENTRIES.LIST")
        for line in lines:
            amount_text = (line.findtext("AMOUNT") or "0").strip() or "0"
            try:
                amount = float(amount_text.replace(",", ""))
            except ValueError:
                amount = amount_text  # left for row validation to reject with a reason
            record = dict(common, ledger=(line.findtext("LEDGERNAME") or "").strip())
            if isinstance(amount, float):
                record["debit"], record["credit"] = (-amount, 0.0) if amount < 0 else (0.0, amount)
            else:
                record["debit"] = amount
            records.append(record)
    if not records:
        raise ValueError("No vouchers found in the XML. Export the Day Book from Tally in XML format.")
    return records


def _legal(ref: str) -> bool:
    code = int(ref[3:-1], 16) if ref[2] in "xX" else int(ref[2:-1])
    return code in (9, 10, 13) or code >= 32
