"""Inventory audit rules INV-001 to INV-015."""
from app.rules import register

# Signed stock ledger: one row per movement leg at the warehouse it affects.
# Receipts/openings land in warehouse_to (falling back to warehouse_from for ERPs
# that record a single location); issues and transfers leave warehouse_from; a
# transfer's inbound leg is added separately. Adjustments carry their own sign
# (negative = write-down), consistent with INV-002.
_STOCK_LEDGER = """
    SELECT item_code,
           CASE WHEN movement_type IN ('goods_receipt', 'opening') THEN COALESCE(warehouse_to, warehouse_from)
                ELSE COALESCE(warehouse_from, warehouse_to) END AS warehouse,
           CASE WHEN movement_type IN ('goods_receipt', 'opening', 'adjustment') THEN quantity
                ELSE -quantity END AS qty,
           CASE WHEN movement_type IN ('goods_receipt', 'opening', 'adjustment') THEN COALESCE(total_value, 0)
                ELSE -COALESCE(total_value, 0) END AS value,
           movement_date
    FROM inventory_movements
    WHERE company_id = ?
    UNION ALL
    SELECT item_code, warehouse_to, quantity, COALESCE(total_value, 0), movement_date
    FROM inventory_movements
    WHERE company_id = ? AND movement_type = 'transfer' AND warehouse_to IS NOT NULL
"""


@register("INV-001")
def inv_001(conn, company_id, rule):
    """Negative Stock Balance."""
    rows = conn.execute(f"""
        SELECT item_code, warehouse, SUM(qty) as balance
        FROM ({_STOCK_LEDGER}) l
        GROUP BY item_code, warehouse
        HAVING SUM(qty) < 0
    """, [company_id, company_id]).fetchall()
    return [
        {
            "title": f"Negative Stock: {r[0]} at {r[1]}",
            "description": f"Item {r[0]} at warehouse {r[1]} has negative balance of {float(r[2]):.2f} units. Data integrity issue.",
            "severity": "critical",
            "financial_impact": 0,
            "evidence": {"item_code": r[0], "warehouse": r[1], "balance": float(r[2])},
            "key": f"item_code={r[0]}|warehouse={r[1]}",
        }
        for r in rows
    ]


@register("INV-002")
def inv_002(conn, company_id, rule):
    """Inventory Shrinkage >2%."""
    rows = conn.execute("""
        SELECT item_code,
               SUM(CASE WHEN movement_type = 'goods_receipt' THEN quantity ELSE 0 END) as receipts,
               SUM(CASE WHEN movement_type = 'adjustment' AND quantity < 0 THEN ABS(quantity) ELSE 0 END) as shrinkage
        FROM inventory_movements
        WHERE company_id = ?
        GROUP BY item_code
        HAVING receipts > 0 AND shrinkage / receipts > 0.02
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Inventory Shrinkage >2%: {r[0]}",
            "description": f"Item {r[0]} has shrinkage of {float(r[2])/float(r[1])*100:.1f}% ({float(r[2]):.0f} units). Normal threshold is 2%.",
            "severity": "high",
            "financial_impact": 0,
            "evidence": {"item_code": r[0], "receipts": float(r[1]), "shrinkage": float(r[2])},
            "key": f"item_code={r[0]}",
        }
        for r in rows
    ]


@register("INV-005")
def inv_005(conn, company_id, rule):
    """Slow Moving Stock — stock on hand with >180 days no movement."""
    rows = conn.execute(f"""
        SELECT item_code, warehouse, last_movement,
               DATEDIFF('day', last_movement, CURRENT_DATE) as days_idle,
               inventory_value
        FROM (
            SELECT item_code, warehouse,
                   MAX(movement_date) as last_movement,
                   SUM(qty) as qty_on_hand,
                   SUM(value) as inventory_value
            FROM ({_STOCK_LEDGER}) l
            GROUP BY item_code, warehouse
        ) t
        WHERE last_movement < CURRENT_DATE - INTERVAL '180' DAY
          AND qty_on_hand > 0
          AND inventory_value > 0
    """, [company_id, company_id]).fetchall()
    return [
        {
            "title": f"Slow Moving Stock: {r[0]} at {r[1]}",
            "description": f"Item {r[0]} at {r[1]} has had no movement for {r[3]} days. Last movement: {r[2]}. Value: ₹{float(r[4]):,.0f}.",
            "severity": "medium",
            "financial_impact": float(r[4]),
            "evidence": {"item_code": r[0], "warehouse": r[1], "days_idle": r[3], "value": float(r[4])},
            "key": f"item_code={r[0]}|warehouse={r[1]}",
        }
        for r in rows
    ]


@register("INV-007")
def inv_007(conn, company_id, rule):
    """Ghost Inventory — high book value with very few movements."""
    rows = conn.execute(f"""
        SELECT item_code, warehouse, SUM(value) as book_value, COUNT(*) as total_movements
        FROM ({_STOCK_LEDGER}) l
        GROUP BY item_code, warehouse
        HAVING SUM(value) > 500000 AND COUNT(*) < 3
    """, [company_id, company_id]).fetchall()
    return [
        {
            "title": f"Ghost Inventory Indicator: {r[0]} at {r[1]}",
            "description": f"Item {r[0]} shows book value ₹{float(r[2]):,.0f} with only {r[3]} movements. Physical verification required.",
            "severity": "critical",
            "financial_impact": float(r[2]),
            "evidence": {"item_code": r[0], "warehouse": r[1], "book_value": float(r[2]), "movements": r[3]},
            "key": f"item_code={r[0]}|warehouse={r[1]}",
        }
        for r in rows
    ]


@register("INV-010")
def inv_010(conn, company_id, rule):
    """Weekend Inventory Movements (high-value)."""
    # ISODOW: Saturday=6, Sunday=7. (DuckDB's DAYOFWEEK is Sunday=0.)
    rows = conn.execute("""
        SELECT id, item_code, movement_date, movement_type, quantity, total_value
        FROM inventory_movements
        WHERE company_id = ? AND total_value > 200000
          AND ISODOW(movement_date) IN (6, 7)
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Weekend Inventory Movement: {r[1]} on {r[2]}",
            "description": f"{r[3]} of {float(r[4]):.0f} units of item {r[1]} valued ₹{float(r[5]):,.0f} occurred on weekend {r[2]}.",
            "severity": "high",
            "financial_impact": float(r[5]),
            "evidence": {"item_code": r[1], "movement_date": str(r[2]), "type": r[3], "value": float(r[5])},
            "key": f"movement_id={r[0]}",
        }
        for r in rows
    ]


@register("INV-015")
def inv_015(conn, company_id, rule):
    """Multiple GRNs for same reference document beyond expected quantity."""
    rows = conn.execute("""
        SELECT reference_document_number, item_code,
               COUNT(*) as grn_count,
               SUM(quantity) as total_received
        FROM inventory_movements
        WHERE company_id = ? AND movement_type = 'goods_receipt'
          AND reference_document_number IS NOT NULL
        GROUP BY reference_document_number, item_code
        HAVING COUNT(*) > 2 AND SUM(quantity) > 0
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Multiple GRNs on Reference: {r[0]} ({r[1]})",
            "description": f"Reference {r[0]} for item {r[1]} has {r[2]} GRN entries totaling {float(r[3]):.0f} units. Possible over-receipt.",
            "severity": "high",
            "financial_impact": 0,
            "evidence": {"reference_doc": r[0], "item_code": r[1], "grn_count": r[2], "total_received": float(r[3])},
            "key": f"reference={r[0]}|item_code={r[1]}",
        }
        for r in rows
    ]
