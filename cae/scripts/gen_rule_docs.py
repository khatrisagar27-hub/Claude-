"""
Write cae/docs/rules.md from the rule catalogue and each rule's docstring, so the
document cannot drift from the code.
Run: python scripts/gen_rule_docs.py
"""
import inspect
import os
import sys
from collections import defaultdict

_backend = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, _backend)

from app.rules import get_rule_fn  # noqa: E402
from app.rules.catalogue import RULE_CATALOGUE  # noqa: E402

AREA_TITLES = {
    "revenue": "Revenue", "expenditure": "Expenditure", "gst": "GST", "statutory": "Statutory (income tax, MSME, PF/ESI)",
    "related_party": "Related party", "inventory": "Inventory", "financial_reporting": "Journals and financial reporting",
    "payroll": "Payroll", "bank_reconciliation": "Bank and treasury",
}

by_area = defaultdict(list)
for row in RULE_CATALOGUE:
    by_area[row[2]].append(row)

lines = [
    "# CAE rule catalogue",
    "",
    "Generated from `app/rules/catalogue.py` and the rule docstrings by `scripts/gen_rule_docs.py` — do not edit by hand.",
    "",
    f"{len(RULE_CATALOGUE)} rules. Parameters are defaults; override per company with `PUT /rules/{{id}}/parameters`. "
    "Every ageing rule also accepts `as_on` (YYYY-MM-DD); without it the latest date in the data is used.",
    "",
    "Statutory references switch by transaction date: before 01-04-2026 the Income-tax Act, 1961 section is cited; "
    "from that date the Income-tax Act, 2025 section, with the 1961 equivalent alongside (`GET /statutory/section-map`).",
    "",
]
for area in AREA_TITLES:
    if area not in by_area:
        continue
    lines += [f"## {AREA_TITLES[area]}", "", "| Code | Rule | Severity | Runs | What it checks | Default parameters |",
              "|---|---|---|---|---|---|"]
    for code, name, _, _, severity, frequency, params in by_area[area]:
        doc = " ".join((inspect.getdoc(get_rule_fn(code)) or "").split())
        p = ", ".join(f"`{k}={v}`" for k, v in params.items()) or "—"
        lines.append(f"| {code} | {name} | {severity} | {frequency} | {doc.replace('|', '/')} | {p} |")
    lines.append("")

out = os.path.join(os.path.dirname(__file__), "..", "docs", "rules.md")
with open(out, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lines))
print(f"wrote {os.path.normpath(out)} ({len(RULE_CATALOGUE)} rules)")
