"""Inventory audit rules INV-001 to INV-015.

On-hand is derived by netting signed movements per item — receipts, opening and
adjustments add, goods issues subtract, transfers move stock between warehouses and are
excluded at item level (same convention as the working-capital engine).
"""
from app.rules import register, param, as_on_date

_SIGNED_QTY = """CASE WHEN movement_type IN ('goods_receipt', 'opening', 'adjustment') THEN quantity
                     WHEN movement_type = 'goods_issue' THEN -quantity ELSE 0 END"""


@register("INV-001")
def inv_001(conn, company_id, rule):
    """Negative Stock Balance (item level)."""
    rows = conn.execute(f"""
        SELECT item_code, SUM({_SIGNED_QTY}) AS balance, MIN(movement_date), MAX(movement_date)
        FROM inventory_movements
        WHERE company_id = ?
        GROUP BY item_code
        HAVING SUM({_SIGNED_QTY}) < 0
        ORDER BY balance
        LIMIT 20
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Negative Stock: {r[0]}",
            "description": f"Item {r[0]} nets to {float(r[1]):,.2f} units on hand — more issued than received. "
                           "Issues booked without receipts, or a missing opening balance.",
            "severity": "critical",
            "financial_impact": 0,
            "evidence": {"item_code": r[0], "balance": float(r[1]), "first_movement": str(r[2]), "last_movement": str(r[3])},
        }
        for r in rows
    ]


@register("INV-002")
def inv_002(conn, company_id, rule):
    """Inventory shrinkage — negative adjustments above N% of receipts."""
    max_pct = float(param(rule, "max_shrinkage_pct", 2))
    rows = conn.execute("""
        SELECT item_code,
               SUM(CASE WHEN movement_type = 'goods_receipt' THEN quantity ELSE 0 END) AS receipts,
               SUM(CASE WHEN movement_type = 'adjustment' AND quantity < 0 THEN ABS(quantity) ELSE 0 END) AS shrinkage,
               SUM(CASE WHEN movement_type = 'adjustment' AND quantity < 0 THEN ABS(COALESCE(total_value, 0)) ELSE 0 END) AS value
        FROM inventory_movements
        WHERE company_id = ?
        GROUP BY item_code
        HAVING receipts > 0 AND shrinkage / receipts * 100 > ?
        LIMIT 20
    """, [company_id, max_pct]).fetchall()
    return [
        {
            "title": f"Inventory Shrinkage >{max_pct:g}%: {r[0]}",
            "description": f"Item {r[0]} has write-down adjustments of {float(r[2]):,.0f} units — {float(r[2]) / float(r[1]) * 100:.1f}% of receipts.",
            "severity": "high",
            "financial_impact": float(r[3]),
            "evidence": {"item_code": r[0], "receipts": float(r[1]), "shrinkage": float(r[2])},
        }
        for r in rows
    ]


@register("INV-005")
def inv_005(conn, company_id, rule):
    """Slow-moving stock — on-hand items with no movement for N days."""
    max_idle = int(param(rule, "max_idle_days", 180))
    as_on = as_on_date(conn, rule, "inventory_movements", "movement_date")
    rows = conn.execute(f"""
        WITH items AS (
            SELECT item_code, MAX(movement_date) AS last_movement, SUM({_SIGNED_QTY}) AS on_hand,
                   ARG_MAX(unit_cost, movement_date) AS last_cost
            FROM inventory_movements
            WHERE company_id = ? AND movement_date <= ?
            GROUP BY item_code
        )
        SELECT item_code, last_movement, DATEDIFF('day', last_movement, CAST(? AS DATE)) AS idle,
               on_hand, on_hand * COALESCE(last_cost, 0) AS value
        FROM items
        WHERE on_hand > 0 AND DATEDIFF('day', last_movement, CAST(? AS DATE)) > ?
        ORDER BY value DESC
        LIMIT 30
    """, [company_id, as_on, as_on, as_on, max_idle]).fetchall()
    return [
        {
            "title": f"Slow Moving Stock: {r[0]}",
            "description": f"Item {r[0]} has {float(r[3]):,.0f} units on hand (≈₹{float(r[4]):,.0f} at last cost) and no movement for {r[2]} days "
                           f"as on {as_on}. Consider NRV write-down (AS 2 / Ind AS 2).",
            "severity": "medium",
            "financial_impact": float(r[4]),
            "evidence": {"item_code": r[0], "last_movement": str(r[1]), "days_idle": r[2], "on_hand": float(r[3]),
                         "value_at_last_cost": float(r[4]), "as_on": str(as_on)},
        }
        for r in rows
    ]


@register("INV-007")
def inv_007(conn, company_id, rule):
    """Ghost inventory — high on-hand value carried by very few movements."""
    min_value = float(param(rule, "min_value", 500_000))
    max_movements = int(param(rule, "max_movements", 2))
    rows = conn.execute(f"""
        WITH items AS (
            SELECT item_code, COUNT(*) AS movements, SUM({_SIGNED_QTY}) AS on_hand,
                   ARG_MAX(unit_cost, movement_date) AS last_cost
            FROM inventory_movements
            WHERE company_id = ?
            GROUP BY item_code
        )
        SELECT item_code, on_hand * COALESCE(last_cost, 0) AS value, movements, on_hand
        FROM items
        WHERE on_hand > 0 AND on_hand * COALESCE(last_cost, 0) > ? AND movements <= ?
        ORDER BY value DESC
        LIMIT 20
    """, [company_id, min_value, max_movements]).fetchall()
    return [
        {
            "title": f"Ghost Inventory Indicator: {r[0]}",
            "description": f"Item {r[0]} carries ≈₹{float(r[1]):,.0f} on hand from only {r[2]} movement(s). Include in physical verification.",
            "severity": "critical",
            "financial_impact": float(r[1]),
            "evidence": {"item_code": r[0], "book_value": float(r[1]), "movements": r[2], "on_hand": float(r[3])},
        }
        for r in rows
    ]


@register("INV-010")
def inv_010(conn, company_id, rule):
    """High-value inventory movements dated Saturday or Sunday."""
    min_value = float(param(rule, "min_value", 200_000))
    rows = conn.execute("""
        SELECT id, item_code, movement_date, movement_type, quantity, total_value, DAYNAME(movement_date)
        FROM inventory_movements
        WHERE company_id = ? AND total_value > ? AND ISODOW(movement_date) IN (6, 7)
        ORDER BY total_value DESC
        LIMIT 20
    """, [company_id, min_value]).fetchall()
    return [
        {
            "title": f"Weekend Inventory Movement: {r[1]} on {r[2]}",
            "description": f"{r[3]} of {float(r[4]):,.0f} units of {r[1]} (₹{float(r[5]):,.0f}) is dated {r[2]}, a {r[6]}.",
            "severity": "high",
            "financial_impact": float(r[5]),
            "evidence": {"item_code": r[1], "movement_date": str(r[2]), "weekday": r[6], "type": r[3], "value": float(r[5])},
        }
        for r in rows
    ]


@register("INV-015")
def inv_015(conn, company_id, rule):
    """Several GRNs against the same reference document and item."""
    max_grns = int(param(rule, "max_grns", 2))
    rows = conn.execute("""
        SELECT reference_document_number, item_code, COUNT(*) AS grn_count, SUM(quantity) AS total_received,
               SUM(COALESCE(total_value, 0))
        FROM inventory_movements
        WHERE company_id = ? AND movement_type = 'goods_receipt'
          AND reference_document_number IS NOT NULL AND TRIM(reference_document_number) != ''
        GROUP BY reference_document_number, item_code
        HAVING COUNT(*) > ?
        LIMIT 20
    """, [company_id, max_grns]).fetchall()
    return [
        {
            "title": f"Multiple GRNs on Reference: {r[0]} ({r[1]})",
            "description": f"Reference {r[0]} for item {r[1]} has {r[2]} GRNs totalling {float(r[3]):,.0f} units. Check against the PO quantity for over-receipt.",
            "severity": "high",
            "financial_impact": float(r[4]),
            "evidence": {"reference_doc": r[0], "item_code": r[1], "grn_count": r[2], "total_received": float(r[3])},
        }
        for r in rows
    ]
