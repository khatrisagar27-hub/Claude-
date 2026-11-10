"""Rule catalogue. A rule is a plain function plus the facts a reviewer needs:
what it tests, under which provision, and which thresholds it uses."""
from dataclasses import dataclass, field

SEVERITIES = ("low", "medium", "high", "critical")
AREAS = ("Sales", "Purchases", "GST", "TDS", "Books", "Treasury", "Payroll", "Inventory")


@dataclass
class Hit:
    """One exception found by a rule.

    key identifies the underlying item (an invoice, a vendor, a month). It must be
    the same on every run for the same item — that is what stops duplicates.
    """
    key: str
    title: str
    detail: str
    impact: float = 0.0
    evidence: list = field(default_factory=list)
    severity: str | None = None  # overrides the rule's default when set


@dataclass
class Rule:
    code: str
    area: str
    name: str
    severity: str
    law: str
    needs: tuple
    params: dict          # name -> (default, label)
    fraud: bool
    fn: callable
    description: str

    def defaults(self) -> dict:
        return {k: v[0] for k, v in self.params.items()}


RULES: dict[str, Rule] = {}


def rule(code, area, name, severity, needs, law="", params=None, fraud=False):
    """needs: datasets that must hold data, optionally a column ("purchases.po_no")
    that must not be entirely blank. A rule whose needs are unmet is reported as
    "no data" instead of silently passing."""
    assert area in AREAS and severity in SEVERITIES and code not in RULES, code

    def register(fn):
        RULES[code] = Rule(code, area, name, severity, law, tuple(needs), params or {}, fraud, fn,
                           " ".join((fn.__doc__ or "").split()))
        return fn
    return register


def load_rules():
    from app.audit.rules import books, gst, inventory, payroll, purchases, sales, tds, treasury  # noqa: F401
    return RULES
