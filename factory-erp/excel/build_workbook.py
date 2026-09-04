"""Generates FactoryERP.xlsx — the macro-free, formula-only Excel edition of
the factory-erp scaffold. Mirrors the analytics formulas in
factory-erp/backend/app/analytics/*.py exactly, so both editions agree on
what OEE, stock ageing, downtime Pareto, and material yield mean. Data rows
are pre-seeded with the same demo scenario as backend/scripts/seed_data.py.

Run: python build_workbook.py   (writes ./FactoryERP.xlsx)
Then: python <xlsx-skill>/scripts/recalc.py FactoryERP.xlsx
"""

from datetime import datetime

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table, TableStyleInfo

FONT_NAME = "Arial"
HEADER_FILL = PatternFill("solid", fgColor="1F2937")
HEADER_FONT = Font(name=FONT_NAME, bold=True, color="FFFFFF", size=10)
INPUT_FONT = Font(name=FONT_NAME, color="0000FF", size=10)  # blue = hardcoded input
FORMULA_FONT = Font(name=FONT_NAME, color="000000", size=10)  # black = formula
TITLE_FONT = Font(name=FONT_NAME, bold=True, size=14)
SECTION_FONT = Font(name=FONT_NAME, bold=True, size=11, color="1F2937")
NOTE_FONT = Font(name=FONT_NAME, italic=True, size=9, color="6B7280")
THIN = Side(style="thin", color="D1D5DB")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

MAX_ROW = 60  # formula ranges go this far; extend (fill down the last row) if you outgrow it

wb = Workbook()
wb.remove(wb.active)


def style_header(ws, row, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER


def add_table(ws, name, ref, style="TableStyleMedium2"):
    tbl = Table(displayName=name, ref=ref)
    tbl.tableStyleInfo = TableStyleInfo(
        name=style, showRowStripes=True, showFirstColumn=False, showLastColumn=False
    )
    ws.add_table(tbl)


def autosize(ws, widths):
    for col, width in widths.items():
        ws.column_dimensions[col].width = width


# ---------------------------------------------------------------------------
# README / legend
# ---------------------------------------------------------------------------
readme = wb.create_sheet("README")
readme.sheet_view.showGridLines = False
readme["B2"] = "Factory ERP — Excel Edition"
readme["B2"].font = TITLE_FONT
readme["B4"] = (
    "Macro-free workbook: stock, machines, production logged as append-only tables; "
    "every analytics number (OEE, downtime Pareto, stock ageing/reorder/valuation, "
    "material yield) is a formula, computed the same way as "
    "factory-erp/backend/app/analytics/*.py — so this and the web app never disagree "
    "on what a number means."
)
readme["B4"].alignment = Alignment(wrap_text=True)
readme.merge_cells("B4:H6")

legend_rows = [
    ("Blue text", "Hardcoded input — the cells you actually type into."),
    ("Black text", "Formula — never overwrite; extend the pattern down instead."),
    ("Yellow fill", "Dropdown cell — pick from the list, don't free-type."),
    ("Red fill (Analytics/Stock)", "Reorder alert — on-hand qty is below reorder level."),
]
r = 9
readme.cell(row=r, column=2, value="Legend").font = SECTION_FONT
r += 1
for label, desc in legend_rows:
    readme.cell(row=r, column=2, value=label).font = Font(name=FONT_NAME, bold=True, size=10)
    readme.cell(row=r, column=3, value=desc).font = Font(name=FONT_NAME, size=10)
    readme.merge_cells(start_row=r, start_column=3, end_row=r, end_column=8)
    r += 1

r += 1
readme.cell(row=r, column=2, value="How to add data").font = SECTION_FONT
r += 1
howto = [
    "Master data (Machines, Products, BOM): add a row anywhere inside the table — it "
    "auto-expands and every dropdown/formula elsewhere already points at the full "
    f"table range (rows 2-{MAX_ROW}).",
    "Transactions (StockMovements, Downtime, WorkOrders, Rejections): one row per "
    "event, oldest first is not required — formulas are order-independent. Never "
    "edit or delete a posted row; if a movement was wrong, post a correcting entry "
    "(same discipline as the backend's ledger — see factory-erp/README.md).",
    "Analytics/Dashboard sheets recalculate automatically as you add rows — nothing "
    "to refresh by hand (this is plain formulas, not Power Query/Power Pivot).",
]
for line in howto:
    readme.cell(row=r, column=2, value=f"• {line}").font = Font(name=FONT_NAME, size=10)
    readme.cell(row=r, column=2).alignment = Alignment(wrap_text=True)
    readme.merge_cells(start_row=r, start_column=2, end_row=r, end_column=8)
    readme.row_dimensions[r].height = 30
    r += 2

r += 1
readme.cell(row=r, column=2, value="Multi-user editing — read this before relying on it").font = (
    SECTION_FONT
)
r += 1
caveat = (
    "This workbook is macro-free specifically so co-authoring works: put it on OneDrive or "
    "SharePoint and several people can add rows to the same table at the same time from Excel "
    "desktop or Excel Online. That is the ceiling of what Excel can offer, though — it is NOT "
    "a database. There is no row-level locking or transaction guarantee; near-simultaneous "
    "saves are usually merged cleanly but occasionally are not, formula recalculation lags a "
    "beat behind concurrent edits, and a large shared file gets slower to co-author as row "
    "counts grow into the thousands. If your factory needs guaranteed data integrity under "
    "real concurrent load, that is exactly the gap the FastAPI + Postgres edition in "
    "factory-erp/backend and factory-erp/frontend fills — this workbook is the tradeoff you "
    "chose in exchange for zero hosting and a format your team already knows."
)
readme.cell(row=r, column=2, value=caveat).font = Font(name=FONT_NAME, size=10)
readme.cell(row=r, column=2).alignment = Alignment(wrap_text=True)
readme.merge_cells(start_row=r, start_column=2, end_row=r + 4, end_column=8)
autosize(readme, {"A": 3, "B": 14})

# ---------------------------------------------------------------------------
# Machines
# ---------------------------------------------------------------------------
ws = wb.create_sheet("Machines")
headers = ["Code", "Name", "Category", "RatedCapacityPerHour", "Status"]
for i, h in enumerate(headers, start=1):
    ws.cell(row=1, column=i, value=h)
style_header(ws, 1, len(headers))
data = [
    ("PRESS-01", "Hydraulic Press 1", "press", 120, "running"),
    ("PRESS-02", "Hydraulic Press 2", "press", 100, "idle"),
]
for r, row in enumerate(data, start=2):
    for c, val in enumerate(row, start=1):
        cell = ws.cell(row=r, column=c, value=val)
        cell.font = INPUT_FONT
        cell.border = BORDER
add_table(ws, "TblMachines", f"A1:E{MAX_ROW}")
dv_status = DataValidation(
    type="list", formula1='"running,idle,breakdown,maintenance"', allow_blank=True
)
ws.add_data_validation(dv_status)
dv_status.add(f"E2:E{MAX_ROW}")
for row in ws[f"E2:E{MAX_ROW}"]:
    row[0].fill = PatternFill("solid", fgColor="FFFDE7")
autosize(ws, {"A": 12, "B": 20, "C": 12, "D": 20, "E": 14})

# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------
ws = wb.create_sheet("Products")
headers = ["SKU", "Name", "Category", "UOM", "StandardCost", "ReorderLevel", "ReorderQty"]
for i, h in enumerate(headers, start=1):
    ws.cell(row=1, column=i, value=h)
style_header(ws, 1, len(headers))
data = [
    ("RM-STEEL-COIL", "Steel Coil 2mm", "raw_material", "kg", 65, 500, 2000),
    ("FG-BRACKET-A", "Mounting Bracket A", "finished_good", "pcs", 180, 200, 500),
]
for r, row in enumerate(data, start=2):
    for c, val in enumerate(row, start=1):
        cell = ws.cell(row=r, column=c, value=val)
        cell.font = INPUT_FONT
        cell.border = BORDER
add_table(ws, "TblProducts", f"A1:G{MAX_ROW}")
dv_cat = DataValidation(
    type="list",
    formula1='"raw_material,wip,finished_good,consumable,spare_part"',
    allow_blank=True,
)
ws.add_data_validation(dv_cat)
dv_cat.add(f"C2:C{MAX_ROW}")
for row in ws[f"C2:C{MAX_ROW}"]:
    row[0].fill = PatternFill("solid", fgColor="FFFDE7")
autosize(ws, {"A": 16, "B": 22, "C": 14, "D": 8, "E": 13, "F": 13, "G": 13})

# ---------------------------------------------------------------------------
# BOM  (D: component standard cost lookup, E: line standard cost — helper cols)
# ---------------------------------------------------------------------------
ws = wb.create_sheet("BOM")
headers = ["ParentSKU", "ComponentSKU", "QtyPerUnit", "ComponentStdCost", "LineStdCost"]
for i, h in enumerate(headers, start=1):
    ws.cell(row=1, column=i, value=h)
style_header(ws, 1, len(headers))
ws.cell(row=2, column=1, value="FG-BRACKET-A").font = INPUT_FONT
ws.cell(row=2, column=2, value="RM-STEEL-COIL").font = INPUT_FONT
ws.cell(row=2, column=3, value=1.8).font = INPUT_FONT
for r in range(2, MAX_ROW + 1):
    ws.cell(row=r, column=4, value=f"=IFERROR(INDEX(Products!$E$2:$E${MAX_ROW},MATCH(B{r},Products!$A$2:$A${MAX_ROW},0)),\"\")").font = FORMULA_FONT
    ws.cell(row=r, column=5, value=f"=IFERROR(C{r}*D{r},\"\")").font = FORMULA_FONT
for row in ws[f"A1:E{MAX_ROW}"]:
    for cell in row:
        cell.border = BORDER
add_table(ws, "TblBOM", f"A1:E{MAX_ROW}")
autosize(ws, {"A": 16, "B": 16, "C": 12, "D": 16, "E": 13})

# ---------------------------------------------------------------------------
# StockMovements  (I: helper column, Value = Quantity * UnitCost)
# ---------------------------------------------------------------------------
ws = wb.create_sheet("StockMovements")
headers = ["Date", "ProductSKU", "Warehouse", "MovementType", "Quantity", "UnitCost", "Reference", "WorkOrderNo", "Value"]
for i, h in enumerate(headers, start=1):
    ws.cell(row=1, column=i, value=h)
style_header(ws, 1, len(headers))
data = [
    (datetime(2026, 8, 23, 9, 0), "RM-STEEL-COIL", "Raw Material Store", "receipt", 3000, 65, "PO-1001", None),
    (datetime(2026, 9, 1, 8, 0), "RM-STEEL-COIL", "Raw Material Store", "issue", 900, 65, "WO-2026-0001", "WO-2026-0001"),
    (datetime(2026, 9, 1, 12, 0), "FG-BRACKET-A", "Finished Goods Store", "production_in", 470, 180, "WO-2026-0001", "WO-2026-0001"),
]
for r, row in enumerate(data, start=2):
    for c, val in enumerate(row, start=1):
        cell = ws.cell(row=r, column=c, value=val)
        cell.font = INPUT_FONT
        cell.border = BORDER
    ws.cell(row=r, column=1).number_format = "yyyy-mm-dd hh:mm"
for r in range(2, MAX_ROW + 1):
    cell = ws.cell(row=r, column=9, value=f'=IFERROR(E{r}*F{r},"")')
    cell.font = FORMULA_FONT
    cell.border = BORDER
add_table(ws, "TblStockMoves", f"A1:I{MAX_ROW}")
dv_move = DataValidation(
    type="list",
    formula1='"receipt,issue,production_in,production_out,transfer,adjustment,scrap"',
    allow_blank=True,
)
ws.add_data_validation(dv_move)
dv_move.add(f"D2:D{MAX_ROW}")
for row in ws[f"D2:D{MAX_ROW}"]:
    row[0].fill = PatternFill("solid", fgColor="FFFDE7")
autosize(ws, {"A": 18, "B": 16, "C": 20, "D": 15, "E": 10, "F": 10, "G": 14, "H": 16, "I": 12})

# ---------------------------------------------------------------------------
# Downtime  (G: helper column, DurationMinutes)
# ---------------------------------------------------------------------------
ws = wb.create_sheet("Downtime")
headers = ["MachineCode", "WorkOrderNo", "StartTime", "EndTime", "ReasonCategory", "Remarks", "DurationMinutes"]
for i, h in enumerate(headers, start=1):
    ws.cell(row=1, column=i, value=h)
style_header(ws, 1, len(headers))
data = [
    ("PRESS-01", "WO-2026-0001", datetime(2026, 9, 1, 9, 0), datetime(2026, 9, 1, 9, 25), "breakdown", "Hydraulic seal leak"),
    ("PRESS-01", "WO-2026-0001", datetime(2026, 9, 1, 10, 30), datetime(2026, 9, 1, 10, 45), "changeover", "Die change"),
]
for r, row in enumerate(data, start=2):
    for c, val in enumerate(row, start=1):
        cell = ws.cell(row=r, column=c, value=val)
        cell.font = INPUT_FONT
        cell.border = BORDER
    ws.cell(row=r, column=3).number_format = "yyyy-mm-dd hh:mm"
    ws.cell(row=r, column=4).number_format = "yyyy-mm-dd hh:mm"
for r in range(2, MAX_ROW + 1):
    cell = ws.cell(row=r, column=7, value=f'=IFERROR((D{r}-C{r})*1440,"")')
    cell.font = FORMULA_FONT
    cell.border = BORDER
add_table(ws, "TblDowntime", f"A1:G{MAX_ROW}")
dv_reason = DataValidation(
    type="list",
    formula1='"breakdown,changeover,no_material,power,planned_maintenance,other"',
    allow_blank=True,
)
ws.add_data_validation(dv_reason)
dv_reason.add(f"E2:E{MAX_ROW}")
dv_machine = DataValidation(type="list", formula1=f"=Machines!$A$2:$A${MAX_ROW}", allow_blank=True)
ws.add_data_validation(dv_machine)
dv_machine.add(f"A2:A{MAX_ROW}")
for row in ws[f"E2:E{MAX_ROW}"]:
    row[0].fill = PatternFill("solid", fgColor="FFFDE7")
autosize(ws, {"A": 14, "B": 16, "C": 18, "D": 18, "E": 16, "F": 24, "G": 15})

# ---------------------------------------------------------------------------
# WorkOrders  (L: GoodQty, M: PlannedMinutes, N: OnTime helper cols)
# ---------------------------------------------------------------------------
ws = wb.create_sheet("WorkOrders")
headers = [
    "OrderNo", "ProductSKU", "MachineCode", "PlannedQty", "ProducedQty", "RejectedQty",
    "PlannedStart", "PlannedEnd", "ActualStart", "ActualEnd", "Status",
    "GoodQty", "PlannedMinutes", "OnTime",
]
for i, h in enumerate(headers, start=1):
    ws.cell(row=1, column=i, value=h)
style_header(ws, 1, len(headers))
row2 = (
    "WO-2026-0001", "FG-BRACKET-A", "PRESS-01", 500, 470, 12,
    datetime(2026, 9, 1, 8, 0), datetime(2026, 9, 1, 12, 0),
    datetime(2026, 9, 1, 8, 0), datetime(2026, 9, 1, 12, 0), "completed",
)
for c, val in enumerate(row2, start=1):
    cell = ws.cell(row=2, column=c, value=val)
    cell.font = INPUT_FONT
    cell.border = BORDER
for col_letter in ("G", "H", "I", "J"):
    ws[f"{col_letter}2"].number_format = "yyyy-mm-dd hh:mm"
for r in range(2, MAX_ROW + 1):
    ws.cell(row=r, column=12, value=f'=IFERROR(E{r}-F{r},"")').font = FORMULA_FONT
    ws.cell(row=r, column=13, value=f'=IFERROR((J{r}-I{r})*1440,"")').font = FORMULA_FONT
    ws.cell(
        row=r, column=14,
        value=f'=IF(K{r}="completed",IF(AND(J{r}<>"",H{r}<>""),IF(J{r}<=H{r},1,0),""),"")',
    ).font = FORMULA_FONT
    for c in (12, 13, 14):
        ws.cell(row=r, column=c).border = BORDER
add_table(ws, "TblWorkOrders", f"A1:N{MAX_ROW}")
dv_wstatus = DataValidation(
    type="list", formula1='"planned,in_progress,completed,cancelled"', allow_blank=True
)
ws.add_data_validation(dv_wstatus)
dv_wstatus.add(f"K2:K{MAX_ROW}")
for row in ws[f"K2:K{MAX_ROW}"]:
    row[0].fill = PatternFill("solid", fgColor="FFFDE7")
autosize(ws, {c: 16 for c in "ABCDEFGHIJKLMN"})

# ---------------------------------------------------------------------------
# Rejections
# ---------------------------------------------------------------------------
ws = wb.create_sheet("Rejections")
headers = ["WorkOrderNo", "DefectType", "Quantity", "Remarks"]
for i, h in enumerate(headers, start=1):
    ws.cell(row=1, column=i, value=h)
style_header(ws, 1, len(headers))
data = [("WO-2026-0001", "Burr / sharp edge", 12, "Die wear — flagged for PRESS-01 maintenance")]
for r, row in enumerate(data, start=2):
    for c, val in enumerate(row, start=1):
        cell = ws.cell(row=r, column=c, value=val)
        cell.font = INPUT_FONT
        cell.border = BORDER
add_table(ws, "TblRejections", f"A1:D{MAX_ROW}")
autosize(ws, {"A": 16, "B": 22, "C": 10, "D": 34})

# ---------------------------------------------------------------------------
# Analytics_Stock — mirrors Products row-for-row: on-hand, valuation, ageing,
# reorder status. Formula for OnHand matches app/analytics/stock.py's
# on_hand_qty exactly: INWARD_TYPES (receipt/production_in/adjustment) minus
# every other movement type.
# ---------------------------------------------------------------------------
ws = wb.create_sheet("Analytics_Stock")
headers = [
    "SKU", "Name", "Category", "OnHand", "StandardCost", "ValuationValue",
    "ReorderLevel", "ReorderStatus", "LastMovementDate", "DaysSinceMovement", "AgeingBucket",
]
for i, h in enumerate(headers, start=1):
    ws.cell(row=1, column=i, value=h)
style_header(ws, 1, len(headers))

MV = f"StockMovements!$E$2:$E${MAX_ROW}"
MV_SKU = f"StockMovements!$B$2:$B${MAX_ROW}"
MV_TYPE = f"StockMovements!$D$2:$D${MAX_ROW}"
MV_DATE = f"StockMovements!$A$2:$A${MAX_ROW}"

for r in range(2, MAX_ROW + 1):
    # Wrapped (not a bare `=Products!A{r}`) so a genuinely blank master row
    # propagates as the text "" rather than the 0 a bare reference to an
    # empty cell would return — every `IF(A{r}="",...)` guard below depends
    # on that to actually detect an unused row instead of falling through.
    ws.cell(row=r, column=1, value=f'=IF(Products!A{r}="","",Products!A{r})').font = FORMULA_FONT
    ws.cell(row=r, column=2, value=f'=IF(Products!A{r}="","",Products!B{r})').font = FORMULA_FONT
    ws.cell(row=r, column=3, value=f'=IF(Products!A{r}="","",Products!C{r})').font = FORMULA_FONT
    onhand = (
        f"=IF(A{r}=\"\",\"\","
        f"SUMIFS({MV},{MV_SKU},A{r},{MV_TYPE},\"receipt\")"
        f"+SUMIFS({MV},{MV_SKU},A{r},{MV_TYPE},\"production_in\")"
        f"+SUMIFS({MV},{MV_SKU},A{r},{MV_TYPE},\"adjustment\")"
        f"-SUMIFS({MV},{MV_SKU},A{r},{MV_TYPE},\"issue\")"
        f"-SUMIFS({MV},{MV_SKU},A{r},{MV_TYPE},\"production_out\")"
        f"-SUMIFS({MV},{MV_SKU},A{r},{MV_TYPE},\"transfer\")"
        f"-SUMIFS({MV},{MV_SKU},A{r},{MV_TYPE},\"scrap\"))"
    )
    ws.cell(row=r, column=4, value=onhand).font = FORMULA_FONT
    ws.cell(row=r, column=5, value=f'=IF(A{r}="","",Products!E{r})').font = FORMULA_FONT
    ws.cell(row=r, column=6, value=f'=IF(A{r}="","",D{r}*E{r})').font = FORMULA_FONT
    ws.cell(row=r, column=7, value=f'=IF(A{r}="","",Products!F{r})').font = FORMULA_FONT
    ws.cell(row=r, column=8, value=f'=IF(A{r}="","",IF(D{r}<G{r},"REORDER","OK"))').font = FORMULA_FONT
    ws.cell(
        row=r, column=9,
        value=f'=IF(A{r}="","",IFERROR(_xlfn.MAXIFS({MV_DATE},{MV_SKU},A{r}),0))',
    ).font = FORMULA_FONT
    ws.cell(row=r, column=9).number_format = "yyyy-mm-dd"
    ws.cell(
        row=r, column=10,
        value=f'=IF(OR(A{r}="",I{r}=0),"",TODAY()-I{r})',
    ).font = FORMULA_FONT
    ws.cell(
        row=r, column=11,
        value=(
            f'=IF(A{r}="","",IF(I{r}=0,"never moved",'
            f'IF(J{r}<=30,"0-30",IF(J{r}<=60,"31-60",IF(J{r}<=90,"61-90","90+")))))'
        ),
    ).font = FORMULA_FONT
    for c in range(1, 12):
        ws.cell(row=r, column=c).border = BORDER
add_table(ws, "TblAnalyticsStock", f"A1:K{MAX_ROW}")
ws.conditional_formatting.add(
    f"H2:H{MAX_ROW}",
    CellIsRule(operator="equal", formula=['"REORDER"'], fill=PatternFill("solid", fgColor="FECACA")),
)
autosize(ws, {c: 14 for c in "ABCDEFGHIJK"})
ws.column_dimensions["B"].width = 22

# ---------------------------------------------------------------------------
# Analytics_OEE — mirrors Machines row-for-row. Matches app/analytics/oee.py:
# Availability = RunTime/PlannedTime, Performance = Output/(RunHours*Rated),
# Quality = Good/Total, OEE = product of the three, each clamped to [0,1].
# ---------------------------------------------------------------------------
ws = wb.create_sheet("Analytics_OEE")
headers = [
    "Code", "Name", "RatedCapacityPerHour", "PlannedMinutes", "TotalOutput",
    "RejectedTotal", "GoodOutput", "DowntimeMinutes", "RunMinutes",
    "Availability", "Performance", "Quality", "OEE",
]
for i, h in enumerate(headers, start=1):
    ws.cell(row=1, column=i, value=h)
style_header(ws, 1, len(headers))

WO_PLANMIN = f"WorkOrders!$M$2:$M${MAX_ROW}"
WO_MACHINE = f"WorkOrders!$C$2:$C${MAX_ROW}"
WO_PRODUCED = f"WorkOrders!$E$2:$E${MAX_ROW}"
WO_REJECTED = f"WorkOrders!$F$2:$F${MAX_ROW}"
DT_MIN = f"Downtime!$G$2:$G${MAX_ROW}"
DT_MACHINE = f"Downtime!$A$2:$A${MAX_ROW}"

for r in range(2, MAX_ROW + 1):
    # See the Analytics_Stock note above: wrapped so a blank master row
    # propagates as "" (text) rather than the 0 a bare reference returns.
    ws.cell(row=r, column=1, value=f'=IF(Machines!A{r}="","",Machines!A{r})').font = FORMULA_FONT
    ws.cell(row=r, column=2, value=f'=IF(Machines!A{r}="","",Machines!B{r})').font = FORMULA_FONT
    ws.cell(row=r, column=3, value=f'=IF(A{r}="","",Machines!D{r})').font = FORMULA_FONT
    ws.cell(row=r, column=4, value=f"=SUMIFS({WO_PLANMIN},{WO_MACHINE},A{r})").font = FORMULA_FONT
    ws.cell(row=r, column=5, value=f"=SUMIFS({WO_PRODUCED},{WO_MACHINE},A{r})").font = FORMULA_FONT
    ws.cell(row=r, column=6, value=f"=SUMIFS({WO_REJECTED},{WO_MACHINE},A{r})").font = FORMULA_FONT
    ws.cell(row=r, column=7, value=f"=E{r}-F{r}").font = FORMULA_FONT
    ws.cell(row=r, column=8, value=f"=SUMIFS({DT_MIN},{DT_MACHINE},A{r})").font = FORMULA_FONT
    ws.cell(row=r, column=9, value=f"=MAX(0,D{r}-H{r})").font = FORMULA_FONT
    ws.cell(
        row=r, column=10, value=f'=IF(A{r}="","",IF(D{r}=0,0,MIN(1,I{r}/D{r})))'
    ).font = FORMULA_FONT
    ws.cell(
        row=r, column=11,
        value=f'=IF(A{r}="","",IF(OR(I{r}=0,C{r}=0),0,MIN(1,E{r}/((I{r}/60)*C{r}))))',
    ).font = FORMULA_FONT
    ws.cell(
        row=r, column=12, value=f'=IF(A{r}="","",IF(E{r}=0,0,MIN(1,MAX(0,G{r}/E{r}))))'
    ).font = FORMULA_FONT
    ws.cell(row=r, column=13, value=f'=IF(A{r}="","",J{r}*K{r}*L{r})').font = FORMULA_FONT
    for c in (10, 11, 12, 13):
        ws.cell(row=r, column=c).number_format = "0.0%"
    for c in range(1, 14):
        ws.cell(row=r, column=c).border = BORDER
add_table(ws, "TblAnalyticsOEE", f"A1:M{MAX_ROW}")
autosize(ws, {c: 14 for c in "ABCDEFGHIJKLM"})
ws.column_dimensions["B"].width = 20

# ---------------------------------------------------------------------------
# Analytics_Downtime — Pareto by reason category (matches
# app/analytics/downtime.py). Fixed list of the six reason categories used
# on the Downtime sheet's dropdown.
# ---------------------------------------------------------------------------
ws = wb.create_sheet("Analytics_Downtime")
headers = ["ReasonCategory", "TotalMinutes", "Occurrences"]
for i, h in enumerate(headers, start=1):
    ws.cell(row=1, column=i, value=h)
style_header(ws, 1, len(headers))
categories = ["breakdown", "changeover", "no_material", "power", "planned_maintenance", "other"]
DT_MIN_ALL = f"Downtime!$G$2:$G${MAX_ROW}"
DT_REASON = f"Downtime!$E$2:$E${MAX_ROW}"
for i, cat in enumerate(categories, start=2):
    ws.cell(row=i, column=1, value=cat).font = FORMULA_FONT
    ws.cell(row=i, column=2, value=f'=SUMIFS({DT_MIN_ALL},{DT_REASON},A{i})').font = FORMULA_FONT
    ws.cell(row=i, column=3, value=f'=COUNTIFS({DT_REASON},A{i})').font = FORMULA_FONT
    for c in (1, 2, 3):
        ws.cell(row=i, column=c).border = BORDER
add_table(ws, "TblAnalyticsDowntime", "A1:C7")
autosize(ws, {"A": 20, "B": 14, "C": 13})

# ---------------------------------------------------------------------------
# Analytics_Production — plant-wide summary (matches
# app/analytics/production.py's production_summary).
# ---------------------------------------------------------------------------
ws = wb.create_sheet("Analytics_Production")
ws["A1"] = "Production summary"
ws["A1"].font = SECTION_FONT
labels_formulas = [
    ("Total planned qty", f"=SUM(WorkOrders!$D$2:$D${MAX_ROW})", None),
    ("Total produced qty", f"=SUM(WorkOrders!$E$2:$E${MAX_ROW})", None),
    ("Total rejected qty", f"=SUM(WorkOrders!$F$2:$F${MAX_ROW})", None),
    ("Good qty", "=B3-B4", None),
    ("Rejection rate", "=IF(B3=0,0,B4/B3)", "0.00%"),
    ("Completed work orders", f'=COUNTIFS(WorkOrders!$K$2:$K${MAX_ROW},"completed")', None),
    ("Completed on/before planned end", f"=SUM(WorkOrders!$N$2:$N${MAX_ROW})", None),
    ("Schedule adherence", "=IF(B7=0,0,B8/B7)", "0.0%"),
]
for i, (label, formula, fmt) in enumerate(labels_formulas, start=2):
    ws.cell(row=i, column=1, value=label).font = Font(name=FONT_NAME, size=10)
    cell = ws.cell(row=i, column=2, value=formula)
    cell.font = FORMULA_FONT
    if fmt:
        cell.number_format = fmt
autosize(ws, {"A": 30, "B": 14})

# ---------------------------------------------------------------------------
# Analytics_Yield — mirrors WorkOrders row-for-row (matches
# app/analytics/production.py's material_yield / material_cost_per_unit).
# ---------------------------------------------------------------------------
ws = wb.create_sheet("Analytics_Yield")
headers = [
    "OrderNo", "ProductSKU", "StdUnitMaterialCost", "MaterialIssuedValue",
    "StandardOutputUnits", "GoodQty", "MaterialYieldPct", "MaterialCostPerUnit",
]
for i, h in enumerate(headers, start=1):
    ws.cell(row=1, column=i, value=h)
style_header(ws, 1, len(headers))
BOM_PARENT = f"BOM!$A$2:$A${MAX_ROW}"
BOM_LINECOST = f"BOM!$E$2:$E${MAX_ROW}"
SM_WO = f"StockMovements!$H$2:$H${MAX_ROW}"
SM_TYPE = f"StockMovements!$D$2:$D${MAX_ROW}"
SM_VALUE = f"StockMovements!$I$2:$I${MAX_ROW}"
for r in range(2, MAX_ROW + 1):
    # See the Analytics_Stock note above: wrapped so a blank master row
    # propagates as "" (text) rather than the 0 a bare reference returns.
    ws.cell(row=r, column=1, value=f'=IF(WorkOrders!A{r}="","",WorkOrders!A{r})').font = FORMULA_FONT
    ws.cell(row=r, column=2, value=f'=IF(A{r}="","",WorkOrders!B{r})').font = FORMULA_FONT
    ws.cell(
        row=r, column=3,
        value=f'=IF(A{r}="","",IFERROR(SUMIFS({BOM_LINECOST},{BOM_PARENT},B{r}),""))',
    ).font = FORMULA_FONT
    ws.cell(
        row=r, column=4,
        value=f'=IF(A{r}="","",SUMIFS({SM_VALUE},{SM_WO},A{r},{SM_TYPE},"issue"))',
    ).font = FORMULA_FONT
    ws.cell(
        row=r, column=5,
        value=f'=IF(OR(A{r}="",C{r}="",C{r}=0,D{r}=0),"",D{r}/C{r})',
    ).font = FORMULA_FONT
    ws.cell(row=r, column=6, value=f'=IF(A{r}="","",WorkOrders!L{r})').font = FORMULA_FONT
    ws.cell(
        row=r, column=7,
        value=f'=IF(OR(E{r}="",E{r}=0),"",F{r}/E{r})',
    ).font = FORMULA_FONT
    ws.cell(row=r, column=7).number_format = "0.0%"
    ws.cell(
        row=r, column=8,
        value=f'=IF(OR(C{r}="",F{r}="",F{r}=0),"",C{r}*WorkOrders!E{r}/F{r})',
    ).font = FORMULA_FONT
    for c in range(1, 9):
        ws.cell(row=r, column=c).border = BORDER
add_table(ws, "TblAnalyticsYield", f"A1:H{MAX_ROW}")
autosize(ws, {c: 16 for c in "ABCDEFGH"})

# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
ws = wb.create_sheet("Dashboard")
ws.sheet_view.showGridLines = False
ws["B2"] = "Plant Dashboard"
ws["B2"].font = TITLE_FONT

kpis = [
    ("Average OEE", '=IFERROR(AVERAGEIF(Analytics_OEE!$M$2:$M$11,"<>"),"")', "0.0%"),
    ("Total produced qty", "=Analytics_Production!B3", "#,##0"),
    ("Rejection rate", "=Analytics_Production!B6", "0.00%"),
    ("Reorder alerts", f'=COUNTIFS(Analytics_Stock!$H$2:$H${MAX_ROW},"REORDER")', "0"),
]
for i, (label, formula, fmt) in enumerate(kpis):
    col = 2 + i * 2
    letter = get_column_letter(col)
    ws.cell(row=4, column=col, value=label).font = Font(name=FONT_NAME, bold=True, size=10, color="6B7280")
    cell = ws.cell(row=5, column=col, value=formula)
    cell.font = Font(name=FONT_NAME, bold=True, size=18, color="1F2937")
    cell.number_format = fmt
    ws.merge_cells(start_row=4, start_column=col, end_row=4, end_column=col + 1)
    ws.merge_cells(start_row=5, start_column=col, end_row=5, end_column=col + 1)
    ws.column_dimensions[letter].width = 16

ws["B7"] = "OEE by machine"
ws["B7"].font = SECTION_FONT
oee_chart = BarChart()
oee_chart.type = "col"
oee_chart.title = None
oee_chart.y_axis.numFmt = "0%"
oee_chart.y_axis.title = "OEE"
data_ref = Reference(wb["Analytics_OEE"], min_col=13, min_row=1, max_row=11)
cats_ref = Reference(wb["Analytics_OEE"], min_col=2, min_row=2, max_row=11)
oee_chart.add_data(data_ref, titles_from_data=True)
oee_chart.set_categories(cats_ref)
oee_chart.width = 14
oee_chart.height = 8
ws.add_chart(oee_chart, "B8")

ws["J7"] = "Downtime by reason (Pareto)"
ws["J7"].font = SECTION_FONT
dt_chart = BarChart()
dt_chart.type = "col"
dt_chart.title = None
dt_chart.y_axis.title = "Minutes"
data_ref = Reference(wb["Analytics_Downtime"], min_col=2, min_row=1, max_row=7)
cats_ref = Reference(wb["Analytics_Downtime"], min_col=1, min_row=2, max_row=7)
dt_chart.add_data(data_ref, titles_from_data=True)
dt_chart.set_categories(cats_ref)
dt_chart.width = 14
dt_chart.height = 8
ws.add_chart(dt_chart, "J8")

ws["B24"] = "Stock — first 20 products (full list: Analytics_Stock)"
ws["B24"].font = SECTION_FONT
stock_headers = ["SKU", "Name", "OnHand", "ReorderLevel", "Status"]
for i, h in enumerate(stock_headers, start=2):
    ws.cell(row=25, column=i, value=h)
style_header(ws, 25, 0)
for c in range(2, 7):
    cell = ws.cell(row=25, column=c)
    cell.fill = HEADER_FILL
    cell.font = HEADER_FONT
    cell.border = BORDER
for i in range(20):
    src = i + 2
    dst = 26 + i
    ws.cell(row=dst, column=2, value=f"=Analytics_Stock!A{src}").font = FORMULA_FONT
    ws.cell(row=dst, column=3, value=f"=Analytics_Stock!B{src}").font = FORMULA_FONT
    ws.cell(row=dst, column=4, value=f"=Analytics_Stock!D{src}").font = FORMULA_FONT
    ws.cell(row=dst, column=5, value=f"=Analytics_Stock!G{src}").font = FORMULA_FONT
    ws.cell(row=dst, column=6, value=f"=Analytics_Stock!H{src}").font = FORMULA_FONT
    for c in range(2, 7):
        ws.cell(row=dst, column=c).border = BORDER
ws.conditional_formatting.add(
    f"F26:F45",
    CellIsRule(operator="equal", formula=['"REORDER"'], fill=PatternFill("solid", fgColor="FECACA")),
)
autosize(ws, {"B": 16, "C": 22, "D": 12, "E": 14, "F": 12})

wb.save("FactoryERP.xlsx")
print("Wrote FactoryERP.xlsx")
