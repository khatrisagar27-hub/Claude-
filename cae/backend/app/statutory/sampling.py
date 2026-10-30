"""
Deterministic audit sampling (SA 530), ported from the tally-audit skill.

Same population + same seed => same sample, so the working paper is re-performable.
  1. Key items: every item with |amount| >= high_value_threshold, 100%.
  2. Residual: a seeded random sample of size n from the rest, drawn from a list sorted
     on (amount, id) so input order does not change the result.
The LLM never chooses or edits a sample.
"""
from __future__ import annotations

import random


def select(population: list[dict], seed: int, n: int = 25, high_value_threshold: float = 0.0,
           amount_key: str = "amount", id_key: str = "id") -> dict:
    items = [dict(p, _amt=float(p.get(amount_key) or 0)) for p in population]
    key_items = [p for p in items if high_value_threshold > 0 and abs(p["_amt"]) >= high_value_threshold]
    residual = [p for p in items if not (high_value_threshold > 0 and abs(p["_amt"]) >= high_value_threshold)]
    residual.sort(key=lambda p: (p["_amt"], str(p.get(id_key))))
    take = min(n, len(residual))
    random_items = random.Random(seed).sample(residual, take) if take else []

    for p in key_items:
        p["stratum"] = "key_item"
    for p in random_items:
        p["stratum"] = "random"
    selected = key_items + random_items

    pop_value = sum(abs(p["_amt"]) for p in items)
    sel_value = sum(abs(p["_amt"]) for p in selected)
    for p in selected:
        p.pop("_amt", None)
    return {
        "method": "SA 530 — key items 100% + seeded random residual",
        "seed": seed,
        "high_value_threshold": high_value_threshold,
        "population_count": len(items),
        "population_value": round(pop_value, 2),
        "key_items": len(key_items),
        "random_items": len(random_items),
        "selected_value": round(sel_value, 2),
        "value_coverage_pct": round(sel_value / pop_value * 100, 2) if pop_value else 0.0,
        "sample": selected,
    }
