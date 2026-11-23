"""
Recompute DSO / DIO / DPO / CCC straight from the database, without the engine.

An independent check on app/engines/wc_engine.py: plain SQL over the invoice and
inventory tables, the same definitions written out longhand. Prints both sets of
figures and exits 1 if they differ by more than 0.1 day.

    DATABASE_URL=postgresql://... python scripts/check_wc_metrics.py [company_id]
"""
import os
import sys
from datetime import timedelta
from pathlib import Path

from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

WINDOW = 365


def recompute(conn, cid: str) -> dict:
    one = lambda sql, **kw: conn.execute(text(sql), {"cid": cid, **kw}).scalar()  # noqa: E731

    ref = one("""SELECT MAX(invoice_date) FROM sales_invoices
                 WHERE company_id = :cid AND total_amount > 0 AND status <> 'cancelled'""")
    start = ref - timedelta(days=WINDOW - 1)
    first = one("""SELECT MIN(d) FROM (SELECT MIN(invoice_date) d FROM sales_invoices WHERE company_id = :cid
                   UNION ALL SELECT MIN(invoice_date) FROM purchase_invoices WHERE company_id = :cid) x""")
    days = WINDOW if first <= start else (ref - first).days + 1

    sales = float(one("""SELECT COALESCE(SUM(total_amount), 0) FROM sales_invoices WHERE company_id = :cid
                         AND status <> 'cancelled' AND invoice_date BETWEEN :s AND :r""", s=start, r=ref))
    purchases = float(one("""SELECT COALESCE(SUM(total_amount), 0) FROM purchase_invoices WHERE company_id = :cid
                             AND status <> 'cancelled' AND invoice_date BETWEEN :s AND :r""", s=start, r=ref))
    # Open bills only: a bill marked paid is settled even if outstanding_amount was never cleared.
    ar = float(one("""SELECT COALESCE(SUM(outstanding_amount), 0) FROM sales_invoices WHERE company_id = :cid
                      AND outstanding_amount > 0 AND status NOT IN ('cancelled', 'paid') AND invoice_date <= :r""", r=ref))
    ap = float(one("""SELECT COALESCE(SUM(outstanding_amount), 0) FROM purchase_invoices WHERE company_id = :cid
                      AND outstanding_amount > 0 AND status NOT IN ('cancelled', 'paid') AND invoice_date <= :r""", r=ref))
    # Gross movements -> signed net per item, floored at zero.
    inventory = float(one("""SELECT COALESCE(SUM(GREATEST(net, 0)), 0) FROM (
                               SELECT item_code, SUM(CASE movement_type WHEN 'goods_issue' THEN -total_value
                                                      WHEN 'transfer' THEN 0 ELSE total_value END) net
                               FROM inventory_movements WHERE company_id = :cid AND movement_date <= :r
                               GROUP BY item_code) x""", r=ref))
    cogs = float(one("""SELECT COALESCE(SUM(total_value), 0) FROM inventory_movements WHERE company_id = :cid
                        AND movement_type = 'goods_issue' AND movement_date BETWEEN :s AND :r""", s=start, r=ref))

    dso = ar / (sales / days) if sales else 0
    dpo = ap / (purchases / days) if purchases else 0
    dio = inventory / (cogs / days) if cogs else 0
    return {"as_of": ref.isoformat(), "days_in_period": days, "dso": round(dso, 1), "dio": round(dio, 1),
            "dpo": round(dpo, 1), "ccc": round(dso + dio - dpo, 1)}


def main() -> int:
    eng = create_engine(os.environ["DATABASE_URL"])
    with eng.connect() as conn:
        cid = sys.argv[1] if len(sys.argv) > 1 else str(conn.execute(text("SELECT id FROM companies LIMIT 1")).scalar())
        mine = recompute(conn, cid)

    from app.database import SessionLocal
    from app.engines.wc_engine import WorkingCapitalEngine
    db = SessionLocal()
    try:
        theirs = WorkingCapitalEngine(db, cid).compute_full()
    finally:
        db.close()

    bad = False
    print(f"{'metric':<10}{'independent':>14}{'engine':>12}   (days)")
    for k in ("dso", "dio", "dpo", "ccc"):
        flag = abs(mine[k] - theirs[k]) > 0.1
        bad |= flag
        print(f"{k:<10}{mine[k]:>14}{theirs[k]:>12}{'   MISMATCH' if flag else ''}")
    print(f"as of {mine['as_of']}, {mine['days_in_period']} days in period")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
