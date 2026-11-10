"""Risk score — deliberately simple enough to recompute by hand.

Area score = sum of weights of findings still needing attention, capped at 100.
Overall    = the highest area score (an engagement is as risky as its worst area).
"""
WEIGHTS = {"critical": 25, "high": 10, "medium": 4, "low": 1}
ACTIVE = ("open", "queried", "confirmed")
BANDS = ((75, "critical"), (50, "high"), (25, "medium"), (0, "low"))


def band(score: int) -> str:
    return next(name for floor, name in BANDS if score >= floor)


def score(findings) -> dict:
    """findings: iterable of objects with .area, .severity, .status, .impact"""
    areas = {}
    for f in findings:
        if f.status not in ACTIVE:
            continue
        a = areas.setdefault(f.area, {"score": 0, "impact": 0.0, "critical": 0, "high": 0, "medium": 0, "low": 0})
        a["score"] += WEIGHTS[f.severity]
        a["impact"] += float(f.impact or 0)
        a[f.severity] += 1
    for a in areas.values():
        a["score"] = min(100, a["score"])
        a["impact"] = round(a["impact"], 2)
        a["band"] = band(a["score"])
    overall = max((a["score"] for a in areas.values()), default=0)
    return {"overall": overall, "band": band(overall), "areas": areas}
