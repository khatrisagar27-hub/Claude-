"""
Where each rule's findings land in a Statutory audit and in an Internal audit.

Statutory audit (Companies Act 2013 s.143): findings are mapped to the reporting they feed —
CARO 2020 para 3 clauses, the tax audit report (Form 3CD, Income-tax Act 1961, for FY up to
2025-26), IFC over financial reporting (s.143(3)(i)) and the Standards on Auditing / law the
auditor must consider. A rule is in statutory scope when it bears on a financial-statement
assertion or a statutory report; control-only rules come in when IFC reporting applies;
purely operational tests stay internal.

Internal audit (ICAI Standards on Internal Audit): every active rule is in scope and findings
are grouped by business process.

Sources: CARO 2020 (G.S.R. 849(E), 25-02-2020) para 3; Form 3CD (Rule 6G, Income-tax Rules
1962) as amended; ICAI GN on Audit of IFC over Financial Reporting; SA 240, 250, 320, 501,
520, 550. Mapping written 31-10-2026 — the auditor confirms each clause before reporting. A
change in a form or Order is a dated edit here plus a test.
"""
from __future__ import annotations

from datetime import date

CARO_2020 = {
    "3(ii)(a)": "Inventory — physical verification; discrepancies of 10% or more in aggregate per class",
    "3(iii)": "Investments, guarantees, security, loans or advances granted",
    "3(iv)": "Compliance with ss.185 and 186 for loans, investments, guarantees",
    "3(v)": "Deposits / deemed deposits accepted (ss.73-76)",
    "3(vii)(a)": "Regularity in depositing undisputed statutory dues (GST, PF, ESI, income tax, cess...)",
    "3(xi)(a)": "Fraud by the company or on the company noticed or reported",
    "3(xiii)": "Related-party transactions — compliance with ss.177 and 188, disclosure",
}

FORM_3CD = {  # Income-tax Act, 1961 — applies to tax audits of FY up to 2025-26
    "20(b)": "Employees' contribution to PF/ESI received and paid — s.36(1)(va)",
    "21(b)": "Amounts inadmissible u/s 40(a) (incl. 40(a)(ia) — TDS not deducted/paid)",
    "21(d)": "Expenditure in cash above the s.40A(3) limit",
    "22": "Interest inadmissible u/s 23 of the MSMED Act",
    "26": "Sums referred to in s.43B (incl. 43B(h) — MSE dues beyond the s.15 time limit)",
    "31(a)/(c)": "Loans / deposits taken or repaid otherwise than by account-payee cheque or bank (ss.269SS / 269T)",
    "31(ba)": "Receipts of Rs.2 lakh or more otherwise than by banking channels (s.269ST)",
    "34(a)": "TDS/TCS — deduction/collection and payment as required",
}
LAST_3CD_FY = 2025   # FY 2025-26 is the last year audited under the 1961 Act

IFC_REF = "s.143(3)(i) — IFC over financial reporting (ICAI GN): evaluate as a control deficiency"

PROCESSES = ("Order to Cash", "Procure to Pay", "Record to Report", "Hire to Retire (Payroll)",
             "Inventory", "Treasury & Cash", "Tax & Statutory Compliance")

# scope: "statutory" = always in a statutory audit; "ifc" = only when IFC reporting applies;
# "internal" = internal audit only. refs: (frame, reference, note).
_O2C, _P2P, _R2R, _H2R, _INV, _TRE, _TAX = PROCESSES
RULE_MAP: dict[str, dict] = {
    "SAL-001": {"process": _O2C, "scope": "statutory", "refs": [("SA", "SA 240 / SA 250", "Rule 46(b) CGST — serial number unique in a FY; revenue occurrence")]},
    "SAL-002": {"process": _O2C, "scope": "internal", "refs": []},
    "SAL-003": {"process": _O2C, "scope": "statutory", "refs": [("SA", "SA 520", "Analytical procedure — revenue occurrence / cut-off")]},
    "SAL-004": {"process": _O2C, "scope": "statutory", "refs": [("SA", "SA 240 / AS 9 / Ind AS 115", "Revenue cut-off")]},
    "SAL-005": {"process": _O2C, "scope": "internal", "refs": []},
    "SAL-007": {"process": _TAX, "scope": "statutory", "refs": [("SA", "SA 250", "Rule 138 CGST — e-way bill")]},
    "SAL-009": {"process": _O2C, "scope": "ifc", "refs": [("IFC", "s.143(3)(i)", "Manual invoice outside ERP controls")]},
    "SAL-010": {"process": _O2C, "scope": "internal", "refs": []},
    "SAL-016": {"process": _O2C, "scope": "internal", "refs": []},
    "SAL-019": {"process": _O2C, "scope": "internal", "refs": []},
    "SAL-021": {"process": _TAX, "scope": "statutory", "refs": [("SA", "SA 250", "Rule 48(4) CGST — e-invoice IRN")]},
    "SAL-022": {"process": _TAX, "scope": "statutory", "refs": [("3CD", "31(ba)", "s.269ST (2025 Act s.186) — penalty s.271DA"), ("SA", "SA 250", "")]},
    "SAL-034": {"process": _O2C, "scope": "statutory", "refs": [("SA", "SA 240", "Duplicate sale — revenue occurrence")]},
    "PUR-001": {"process": _P2P, "scope": "statutory", "refs": [("SA", "SA 240", "Duplicate booking — expense occurrence, double ITC"), ("CARO", "3(xi)(a)", "if fraud is confirmed"), ("IFC", "s.143(3)(i)", "")]},
    "PUR-002": {"process": _P2P, "scope": "ifc", "refs": [("IFC", "s.143(3)(i)", "Three-way match control")]},
    "PUR-004": {"process": _P2P, "scope": "ifc", "refs": [("IFC", "s.143(3)(i)", "Purchase authorisation control")]},
    "PUR-006": {"process": _P2P, "scope": "ifc", "refs": [("IFC", "s.143(3)(i)", "Delegation-of-authority control")]},
    "PUR-010": {"process": _P2P, "scope": "statutory", "refs": [("SA", "SA 240", "Payment diversion"), ("CARO", "3(xi)(a)", "if fraud is confirmed")]},
    "PUR-013": {"process": _P2P, "scope": "ifc", "refs": [("IFC", "s.143(3)(i)", "Approval control")]},
    "PUR-016": {"process": _P2P, "scope": "statutory", "refs": [("SA", "SA 240", "Duplicate payment"), ("CARO", "3(xi)(a)", "if fraud is confirmed")]},
    "PUR-021": {"process": _P2P, "scope": "statutory", "refs": [("SA", "SA 501 / SA 330", "Purchase and inventory cut-off")]},
    "PUR-022": {"process": _P2P, "scope": "statutory", "refs": [("SA", "SA 550 / SA 240", "Undisclosed related party / ghost vendor"), ("CARO", "3(xiii)", ""), ("CARO", "3(xi)(a)", "if fraud is confirmed")]},
    "PUR-031": {"process": _TAX, "scope": "statutory", "refs": [("3CD", "22", "s.23 MSMED — interest not deductible"), ("3CD", "26", "s.43B(h) — MSE dues beyond the s.15 limit"), ("SA", "SA 250", "Sch III / s.22 MSMED disclosure of dues and interest")]},
    "GST-001": {"process": _TAX, "scope": "statutory", "refs": [("CARO", "3(vii)(a)", "possible short payment of GST"), ("SA", "SA 250", "Notf 9/2025-CT(Rate)")]},
    "GST-002": {"process": _TAX, "scope": "statutory", "refs": [("CARO", "3(vii)(a)", "ITC reversal due under Rule 37"), ("SA", "SA 250", "")]},
    "GST-003": {"process": _TAX, "scope": "statutory", "refs": [("CARO", "3(vii)(a)", "ITC availed after the s.16(4) limit"), ("SA", "SA 250", "")]},
    "TDS-001": {"process": _TAX, "scope": "statutory", "refs": [("3CD", "34(a)", "s.194Q (2025 Act s.393 Table Sl.8(ii))"), ("3CD", "21(b)", "s.40(a)(ia) disallowance"), ("CARO", "3(vii)(a)", "")]},
    "TDS-002": {"process": _TAX, "scope": "statutory", "refs": [("3CD", "34(a)", "short deduction"), ("CARO", "3(vii)(a)", "")]},
    "INV-001": {"process": _INV, "scope": "statutory", "refs": [("CARO", "3(ii)(a)", "book records unreliable — extend physical verification"), ("SA", "SA 501", "")]},
    "INV-002": {"process": _INV, "scope": "statutory", "refs": [("CARO", "3(ii)(a)", "report discrepancies of 10% or more per class"), ("SA", "SA 501", "")]},
    "INV-005": {"process": _INV, "scope": "statutory", "refs": [("SA", "SA 501 / AS 2 / Ind AS 2", "Net realisable value")]},
    "INV-007": {"process": _INV, "scope": "statutory", "refs": [("CARO", "3(ii)(a)", ""), ("SA", "SA 501 / SA 240", "Existence")]},
    "INV-010": {"process": _INV, "scope": "internal", "refs": []},
    "INV-015": {"process": _INV, "scope": "statutory", "refs": [("SA", "SA 501", "Over-receipt — existence of inventory / purchases")]},
    "JE-001": {"process": _R2R, "scope": "statutory", "refs": [("SA", "SA 240 para 32", "Journal-entry testing"), ("IFC", "s.143(3)(i)", "")]},
    "JE-002": {"process": _R2R, "scope": "ifc", "refs": [("IFC", "s.143(3)(i)", "Timely posting / period close control")]},
    "JE-003": {"process": _R2R, "scope": "statutory", "refs": [("SA", "SA 240 para 32", "Journal-entry testing"), ("IFC", "s.143(3)(i)", "")]},
    "JE-005": {"process": _R2R, "scope": "statutory", "refs": [("SA", "SA 330", "Unreconciled suspense — classification / existence")]},
    "JE-006": {"process": _R2R, "scope": "statutory", "refs": [("SA", "SA 240 para 32", "Unsupported reversal")]},
    "JE-009": {"process": _R2R, "scope": "statutory", "refs": [("SA", "SA 240 para 32", "Ledger integrity")]},
    "JE-011": {"process": _R2R, "scope": "ifc", "refs": [("IFC", "s.143(3)(i)", "Segregation of duties")]},
    "JE-015": {"process": _R2R, "scope": "statutory", "refs": [("SA", "AS 5 / Ind AS 8", "Prior-period items")]},
    "PAY-001": {"process": _H2R, "scope": "statutory", "refs": [("SA", "SA 240", "Ghost employee"), ("CARO", "3(xi)(a)", "if fraud is confirmed")]},
    "PAY-002": {"process": _H2R, "scope": "internal", "refs": []},
    "PAY-003": {"process": _H2R, "scope": "statutory", "refs": [("SA", "SA 240", "Shared salary account"), ("CARO", "3(xi)(a)", "if fraud is confirmed")]},
    "PAY-004": {"process": _H2R, "scope": "statutory", "refs": [("SA", "SA 240", "Post-exit pay"), ("CARO", "3(xi)(a)", "if fraud is confirmed")]},
    "PAY-005": {"process": _TAX, "scope": "statutory", "refs": [("3CD", "20(b)", "s.36(1)(va) employee contribution"), ("CARO", "3(vii)(a)", "PF / ESI")]},
    "PAY-009": {"process": _H2R, "scope": "internal", "refs": []},
    "TRE-001": {"process": _TAX, "scope": "statutory", "refs": [("3CD", "21(d)", "s.40A(3) (2025 Act s.36(4))")]},
    "TRE-002": {"process": _TRE, "scope": "statutory", "refs": [("SA", "SA 240", "Fund rotation / window dressing"), ("CARO", "3(xi)(a)", "if fraud is confirmed")]},
    "TRE-003": {"process": _TAX, "scope": "statutory", "refs": [("3CD", "31(a)/(c)", "ss.269SS / 269T (2025 Act ss.185 / 188)"), ("CARO", "3(v)", "if the receipt is a deposit")]},
    "TRE-004": {"process": _TRE, "scope": "ifc", "refs": [("IFC", "s.143(3)(i)", "Payment authorisation trail")]},
    "TRE-005": {"process": _TRE, "scope": "internal", "refs": []},
    "TRE-006": {"process": _TRE, "scope": "statutory", "refs": [("CARO", "3(iii)", ""), ("CARO", "3(iv)", "ss.185 / 186"), ("CARO", "3(xiii)", "s.188"), ("SA", "SA 550", "")]},
    "TRE-010": {"process": _TRE, "scope": "statutory", "refs": [("SA", "SA 240", "Structured cash"), ("CARO", "3(xi)(a)", "if fraud is confirmed")]},
}


def process_for(rule_code: str) -> str:
    return RULE_MAP.get(rule_code, {}).get("process", "Other")


def in_scope(rule_code: str, engagement) -> bool:
    """Does this rule run in the engagement? No engagement = continuous monitoring = all rules."""
    if engagement is None or engagement.audit_type == "internal":
        return True
    scope = RULE_MAP.get(rule_code, {}).get("scope", "internal")
    return scope == "statutory" or (scope == "ifc" and bool(engagement.ifc_applicable))


def tax_audit_frame(fy: int | None) -> str:
    if fy is not None and fy > LAST_3CD_FY:
        return "Tax audit report (Income-tax Act, 2025) — confirm clause against the notified form"
    return "Form 3CD (Income-tax Act, 1961)"


def refs_for(rule_code: str, engagement) -> list[dict]:
    """Reporting references for a finding, filtered to the frames that apply to the engagement."""
    if engagement is None:
        return []
    if engagement.audit_type == "internal":
        return [{"frame": "Process", "ref": process_for(rule_code), "note": ""}]
    out = []
    for frame, ref, note in RULE_MAP.get(rule_code, {}).get("refs", []):
        if frame == "CARO" and not engagement.caro_applicable:
            continue
        if frame == "3CD" and not engagement.tax_audit_applicable:
            continue
        if frame == "IFC" and not engagement.ifc_applicable:
            continue
        label = {"CARO": "CARO 2020", "3CD": tax_audit_frame(engagement.financial_year), "IFC": "IFC", "SA": "SA / law"}[frame]
        title = CARO_2020.get(ref) if frame == "CARO" else FORM_3CD.get(ref) if frame == "3CD" else ""
        out.append({"frame": label, "ref": f"cl. {ref}" if frame == "3CD" else ref, "title": title or "", "note": note})
    return out


def fy_bounds(fy: int) -> tuple[date, date]:
    return date(fy, 4, 1), date(fy + 1, 3, 31)
