"""Prints the rule catalogue as Markdown:  python -m app.catalogue > ../docs/rules.md"""
from app.audit.registry import AREAS, load_rules


def catalogue_markdown() -> str:
    rules = load_rules()
    out = ["# Rule catalogue", "",
           f"{len(rules)} rules. Generated from the code by `python -m app.catalogue` — do not edit by hand.", "",
           "Severity is the rule's inherent level; the amount involved can raise or lower it "
           "(see README, *How severity is set*). Thresholds shown are defaults and can be changed per engagement.", ""]
    for area in AREAS:
        out += [f"## {area}", ""]
        for code, r in sorted(rules.items()):
            if r.area != area:
                continue
            out += [f"### {code} — {r.name}", "", r.description, ""]
            out.append(f"- Severity: {r.severity}" + ("; fraud indicator" if r.fraud else ""))
            if r.law:
                out.append(f"- Provision: {r.law}")
            out.append(f"- Needs: {', '.join(r.needs)}")
            for name, (default, label) in r.params.items():
                shown = f"{default:,}" if isinstance(default, int) else str(default)
                out.append(f"- Threshold `{name}`: {label} — default {shown}")
            out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    print(catalogue_markdown(), end="")
