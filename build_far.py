#!/usr/bin/env python3
"""
Premium Fixed Asset Register (FAR) generator – Companies Act, 2013 (Schedule II).

Creates an Excel workbook with four sheets:
  1. Input    – global parameters (SLM/WDV switch, residual %, FY anchor) +
                Schedule II useful-life master table.
  2. FAR      – the single Register of Fixed Assets with year-wise, pro-rata
                depreciation that recalculates the moment the method/residual
                or any asset detail changes on the Input/FAR sheets.
  3. Reports  – year-wise depreciation schedule + category x year matrix.
  4. Summary  – category-wise gross block / accumulated depreciation /
                net block as on the selected reporting year.

Every number on FAR/Reports/Summary is a formula. Nothing is hard-coded
except the sample asset rows and the Schedule II master data.
"""

from openpyxl import Workbook
from openpyxl.styles import (
    Font, PatternFill, Border, Side, Alignment, NamedStyle, Protection
)
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import FormulaRule
from openpyxl.workbook.defined_name import DefinedName
import datetime

# --------------------------------------------------------------------------- #
#  Configuration
# --------------------------------------------------------------------------- #
N_YEARS = 16                       # number of year-wise depreciation columns
FIRST_FY_END = datetime.date(2021, 3, 31)
REPORTING_FY_END = datetime.date(2025, 3, 31)
OUT_FILE = "FAR_Schedule_II.xlsx"

# --------------------------------------------------------------------------- #
#  Palette / styles
# --------------------------------------------------------------------------- #
NAVY      = "1F3864"
BLUE      = "2E5496"
LBLUE     = "D6E0F0"
LLBLUE    = "EAF0FA"
GOLD      = "BF9000"
LGOLD     = "FFF2CC"
GREEN     = "548235"
LGREEN    = "E2EFDA"
GREY      = "808080"
LGREY     = "F2F2F2"
WHITE     = "FFFFFF"
ORANGE    = "C55A11"
LORANGE   = "FCE4D6"
RED       = "C00000"

thin   = Side(style="thin",   color="B0B7C3")
medium = Side(style="medium", color=NAVY)

BORDER_ALL  = Border(left=thin, right=thin, top=thin, bottom=thin)
BORDER_BOX  = Border(left=medium, right=medium, top=medium, bottom=medium)

INR_FMT  = '#,##0;[Red](#,##0)'
INR_DEC  = '#,##0.00;[Red](#,##0.00)'
PCT_FMT  = '0.00%'
DATE_FMT = 'dd-mmm-yyyy'
YRS_FMT  = '0'


def font(size=10, bold=False, color="000000", italic=False, name="Calibri"):
    return Font(name=name, size=size, bold=bold, color=color, italic=italic)


def fill(color):
    return PatternFill("solid", fgColor=color)


def align(h="left", v="center", wrap=False):
    return Alignment(horizontal=h, vertical=v, wrap_text=wrap)


def style_cell(ws, coord, value=None, *, fnt=None, fl=None, al=None,
               border=BORDER_ALL, numfmt=None):
    c = ws[coord]
    if value is not None:
        c.value = value
    if fnt:
        c.font = fnt
    if fl:
        c.fill = fl
    if al:
        c.alignment = al
    if border:
        c.border = border
    if numfmt:
        c.number_format = numfmt
    return c


wb = Workbook()

# =========================================================================== #
#  SHEET 1 : INPUT
# =========================================================================== #
ws_in = wb.active
ws_in.title = "Input"
ws_in.sheet_view.showGridLines = False

# ---- title ---------------------------------------------------------------- #
ws_in.merge_cells("B2:F2")
style_cell(ws_in, "B2", "FIXED ASSET REGISTER  |  CONTROL PANEL",
           fnt=font(16, True, WHITE), fl=fill(NAVY),
           al=align("center"), border=BORDER_BOX)
ws_in.merge_cells("B3:F3")
style_cell(ws_in, "B3",
           "Companies Act, 2013 – Schedule II  •  Single switch drives the whole register",
           fnt=font(9, italic=True, color=WHITE), fl=fill(BLUE),
           al=align("center"), border=None)
ws_in.row_dimensions[2].height = 26
ws_in.row_dimensions[3].height = 16

# ---- global parameters block --------------------------------------------- #
ws_in.merge_cells("B5:F5")
style_cell(ws_in, "B5", "A.  GLOBAL PARAMETERS  (edit the yellow cells)",
           fnt=font(11, True, WHITE), fl=fill(BLUE), al=align("center"))

params = [
    ("Company Name",                 "ABC Manufacturing Pvt. Ltd.", None,      "GlobalCompany"),
    ("Reporting Currency",           "INR (Rs.)",                   None,      None),
    ("Depreciation Method (Global)", "WDV",                         None,      "GlobalMethod"),
    ("Default Residual Value %",     0.05,                          PCT_FMT,   "DefaultResidual"),
    ("First Financial Year End",     FIRST_FY_END,                  DATE_FMT,  "FirstFYEnd"),
    ("Reporting Financial Year End", REPORTING_FY_END,              DATE_FMT,  "ReportingFYEnd"),
    ("No. of Year Columns in FAR",   N_YEARS,                       "0",       None),
]
r = 6
for label, val, nf, name in params:
    style_cell(ws_in, f"B{r}", label, fnt=font(10, True, NAVY),
               fl=fill(LLBLUE), al=align("left"))
    ws_in.merge_cells(f"C{r}:D{r}")
    cell = style_cell(ws_in, f"C{r}", val, fnt=font(10, True, color=GOLD),
                      fl=fill(LGOLD), al=align("center"),
                      numfmt=nf if nf else None)
    if isinstance(val, datetime.date):
        cell.number_format = DATE_FMT
    if name:
        wb.defined_names.add(DefinedName(name, attr_text=f"Input!$C${r}"))
    # helper note
    notes = {
        6: "↳ free text", 7: "display only",
        8: "↳ pick SLM or WDV — recalculates everything",
        9: "↳ 5% per Schedule II guidance",
        10: "↳ anchor for the year columns",
        11: "↳ must equal one of the FY columns",
        12: "↳ informational",
    }
    ws_in.merge_cells(f"E{r}:F{r}")
    style_cell(ws_in, f"E{r}", notes.get(r, ""), fnt=font(8, italic=True, color=GREY),
               fl=fill(LGREY), al=align("left"), border=None)
    r += 1

# method validation dropdown
dv_method = DataValidation(type="list", formula1='"SLM,WDV"', allow_blank=False)
dv_method.error = "Choose SLM (Straight Line) or WDV (Written Down Value)."
dv_method.prompt = "Select depreciation method"
ws_in.add_data_validation(dv_method)
dv_method.add("C8")

# =========================================================================== #
#  Schedule II master table
# =========================================================================== #
hdr_row = r + 1
ws_in.merge_cells(f"B{hdr_row-1}:F{hdr_row-1}")
style_cell(ws_in, f"B{hdr_row-1}",
           "B.  SCHEDULE II – USEFUL LIVES OF ASSETS  (master lookup)",
           fnt=font(11, True, WHITE), fl=fill(GREEN), al=align("center"))

sched_headers = ["Sr.", "Asset Category", "Description / Notes",
                 "Useful Life (Years)", "Indicative WDV Rate*"]
for i, h in enumerate(sched_headers):
    col = get_column_letter(2 + i)
    style_cell(ws_in, f"{col}{hdr_row}", h, fnt=font(10, True, WHITE),
               fl=fill(GREEN), al=align("center", wrap=True))

schedule_ii = [
    ("Buildings - RCC Frame",                 "Buildings other than factory (RCC frame)", 60),
    ("Buildings - Other than RCC",            "Buildings other than factory (non-RCC)",   30),
    ("Factory Building",                      "Factory buildings",                        30),
    ("Plant & Machinery - General",           "General rate plant & machinery",           15),
    ("Plant & Machinery - Continuous Process","Continuous process plant",                 25),
    ("Furniture & Fittings",                  "General furniture and fittings",           10),
    ("Office Equipment",                      "General office equipment",                  5),
    ("Computers - End User Devices",          "Laptops, desktops, printers",               3),
    ("Computers - Servers & Networks",        "Servers and network equipment",             6),
    ("Electrical Installations",              "Electrical installations & equipment",     10),
    ("Motor Vehicles - Motor Cars",           "Cars (other than used in hire business)",   8),
    ("Motor Vehicles - Commercial",           "Buses, lorries, motor lorries (commercial)",6),
    ("Motor Vehicles - Two Wheelers",         "Motor cycles, scooters",                   10),
    ("Laboratory Equipment - General",        "General laboratory equipment",             10),
    ("Plant & Machinery - Moulds/Dies",       "Moulds, jigs, dies and tooling",            8),
    ("Air Conditioning Plant",                "AC plant (treated as P&M / office eqp.)",   5),
    ("Intangible Assets - Software",          "Computer software (per AS/Ind AS)",         5),
    ("Leasehold Improvements",                "Over primary lease period (illustrative)", 10),
]
first_data = hdr_row + 1
for j, (cat, desc, life) in enumerate(schedule_ii):
    rr = first_data + j
    band = LGREEN if j % 2 == 0 else WHITE
    style_cell(ws_in, f"B{rr}", j + 1, fnt=font(9), fl=fill(band), al=align("center"))
    style_cell(ws_in, f"C{rr}", cat, fnt=font(9, True, NAVY), fl=fill(band), al=align("left"))
    style_cell(ws_in, f"D{rr}", desc, fnt=font(9, color=GREY), fl=fill(band), al=align("left"))
    style_cell(ws_in, f"E{rr}", life, fnt=font(9, True), fl=fill(band),
               al=align("center"), numfmt=YRS_FMT)
    # indicative WDV rate at default residual = 1 - (residual)^(1/life)
    style_cell(ws_in, f"F{rr}",
               f"=IF(E{rr}=0,0,1-(DefaultResidual)^(1/E{rr}))",
               fnt=font(9, color=ORANGE), fl=fill(band),
               al=align("center"), numfmt=PCT_FMT)
last_data = first_data + len(schedule_ii) - 1

ws_in.merge_cells(f"B{last_data+1}:F{last_data+1}")
style_cell(ws_in, f"B{last_data+1}",
           "*Indicative WDV rate = 1 − (Residual Value)^(1/Useful Life), using the default residual % above. "
           "Add or edit rows freely – the FAR dropdown & lookups follow this table.",
           fnt=font(8, italic=True, color=GREY), fl=fill(LGREY), al=align("left", wrap=True))
ws_in.row_dimensions[last_data+1].height = 26

# defined names for the master table & category list
wb.defined_names.add(DefinedName(
    "ScheduleIITable", attr_text=f"Input!$C${first_data}:$E${last_data}"))
wb.defined_names.add(DefinedName(
    "AssetCategories", attr_text=f"Input!$C${first_data}:$C${last_data}"))

# column widths
for col, w in {"A": 2.5, "B": 26, "C": 26, "D": 34, "E": 16, "F": 16}.items():
    ws_in.column_dimensions[col].width = w
ws_in.sheet_properties.tabColor = NAVY

# =========================================================================== #
#  SHEET 2 : FAR  (Register of Fixed Assets)
# =========================================================================== #
ws = wb.create_sheet("FAR")
ws.sheet_view.showGridLines = False
ws.sheet_properties.tabColor = BLUE

# Fixed columns 1..21 (A..U)
fixed_cols = [
    ("Asset ID",                 10, "text"),
    ("Asset Description",         28, "text"),
    ("Asset Category",            26, "cat"),
    ("Location / Cost Centre",    20, "text"),
    ("Supplier / Vendor",         20, "text"),
    ("Invoice No.",               14, "text"),
    ("Date of Purchase",          15, "date"),
    ("Date Put to Use",           15, "date"),
    ("Date of Sale / Disposal",   16, "date"),
    ("Sale Proceeds (Rs.)",       15, "num"),
    ("Gross Cost (Rs.)",          16, "num"),
    ("Residual %",                11, "pct"),
    ("Residual Value (Rs.)",      15, "num"),
    ("Useful Life (Yrs)",         12, "yrs"),
    ("Method",                    9,  "text"),
    ("WDV Rate",                  10, "pct"),
    ("Depreciable Amt (Rs.)",     16, "num"),
    ("Dep – Reporting FY (Rs.)",  16, "num"),
    ("Acc. Dep – Rep. FY (Rs.)",  16, "num"),
    ("WDV – Reporting FY (Rs.)",  16, "num"),
    ("Status",                    13, "text"),
]
N_FIXED = len(fixed_cols)              # 21
YEAR_START_COL = N_FIXED + 1           # 22 -> 'V'

# Title rows
last_col_idx = N_FIXED + 2 * N_YEARS
last_col = get_column_letter(last_col_idx)
ws.merge_cells(f"A1:{last_col}1")
style_cell(ws, "A1", "REGISTER OF FIXED ASSETS  (FAR)",
           fnt=font(18, True, WHITE), fl=fill(NAVY), al=align("center"), border=BORDER_BOX)
ws.row_dimensions[1].height = 30
ws.merge_cells(f"A2:{last_col}2")
style_cell(ws, "A2",
           '=Input!C6&"   |   Depreciation Method: "&GlobalMethod&'
           '"   |   Reporting FY ending: "&TEXT(ReportingFYEnd,"dd-mmm-yyyy")&'
           '"   |   Default Residual: "&TEXT(DefaultResidual,"0%")&'
           '"   |   Prepared per Companies Act, 2013 – Schedule II"',
           fnt=font(9, True, color=NAVY), fl=fill(LGOLD), al=align("center"))
ws.row_dimensions[2].height = 18

# Group header row (row 3): fixed area split into logical groups,
# year area carries the FY-end DATE on the Dep column (used by lookups).
def group_header(c1, c2, text, color):
    ws.merge_cells(f"{c1}3:{c2}3")
    style_cell(ws, f"{c1}3", text, fnt=font(9, True, WHITE),
               fl=fill(color), al=align("center"))

group_header(get_column_letter(1),  get_column_letter(9),  "ASSET MASTER DETAILS", BLUE)
group_header(get_column_letter(10), get_column_letter(10), "DISPOSAL", ORANGE)
group_header(get_column_letter(11), get_column_letter(17), "COST & DEPRECIATION BASIS", GREEN)
group_header(get_column_letter(18), get_column_letter(21), "POSITION AS ON REPORTING FY", GOLD)

# Year group: row-3 dep cell holds the FY-end date (formula off FirstFYEnd)
for k in range(N_YEARS):
    dep_idx = YEAR_START_COL + 2 * k
    wdv_idx = dep_idx + 1
    dep_col = get_column_letter(dep_idx)
    wdv_col = get_column_letter(wdv_idx)
    # FY end date in the Dep column header (row 3) – drives all year formulas
    style_cell(ws, f"{dep_col}3", f"=EDATE(FirstFYEnd,12*{k})",
               fnt=font(8, True, WHITE), fl=fill(NAVY),
               al=align("center"), numfmt=DATE_FMT)
    style_cell(ws, f"{wdv_col}3", "", fnt=font(8, True, WHITE),
               fl=fill(NAVY), al=align("center"))

# Column header row (row 4)
HEAD_ROW = 4
for i, (name, width, _kind) in enumerate(fixed_cols):
    col = get_column_letter(i + 1)
    ws.column_dimensions[col].width = width
    style_cell(ws, f"{col}{HEAD_ROW}", name, fnt=font(9, True, WHITE),
               fl=fill(NAVY), al=align("center", wrap=True))
ws.row_dimensions[HEAD_ROW].height = 38

for k in range(N_YEARS):
    dep_idx = YEAR_START_COL + 2 * k
    wdv_idx = dep_idx + 1
    dep_col = get_column_letter(dep_idx)
    wdv_col = get_column_letter(wdv_idx)
    ws.column_dimensions[dep_col].width = 14
    ws.column_dimensions[wdv_col].width = 14
    style_cell(ws, f"{dep_col}{HEAD_ROW}",
               f'="Dep "&TEXT(EDATE(FirstFYEnd,12*{k}),"yyyy")',
               fnt=font(8, True, WHITE), fl=fill(GREEN), al=align("center", wrap=True))
    style_cell(ws, f"{wdv_col}{HEAD_ROW}",
               f'="WDV "&TEXT(EDATE(FirstFYEnd,12*{k}),"yyyy")',
               fnt=font(8, True, WHITE), fl=fill(GOLD), al=align("center", wrap=True))

# --------------------------------------------------------------------------- #
#  Sample asset data
# --------------------------------------------------------------------------- #
DATA_START = HEAD_ROW + 1            # row 5
sample = [
    ("FA-001", "Head Office Building",       "Buildings - RCC Frame",        "Mumbai HO",   "Skyline Constructions", "INV-HO-001",  datetime.date(2020,4,1),  datetime.date(2020,4,1),  None, None, 50000000),
    ("FA-002", "Factory Shed - Unit 1",      "Factory Building",             "Pune Plant",  "BuildWell Ltd",         "INV-FB-014",  datetime.date(2020,7,15), datetime.date(2020,8,1),  None, None, 18000000),
    ("FA-003", "CNC Machine",                "Plant & Machinery - General", "Pune Plant",  "TechMach India",        "INV-PM-203",  datetime.date(2021,5,10), datetime.date(2021,6,1),  None, None, 6500000),
    ("FA-004", "Office Furniture (lot)",     "Furniture & Fittings",        "Mumbai HO",   "Featherlite",           "INV-FF-099",  datetime.date(2021,4,20), datetime.date(2021,4,20), None, None, 850000),
    ("FA-005", "Laptops (25 nos.)",          "Computers - End User Devices","Mumbai HO",   "Dell India",            "INV-IT-451",  datetime.date(2022,6,1),  datetime.date(2022,6,5),  None, None, 1750000),
    ("FA-006", "Application Server",         "Computers - Servers & Networks","Mumbai HO", "HPE",                   "INV-IT-460",  datetime.date(2022,9,12), datetime.date(2022,9,20), None, None, 1200000),
    ("FA-007", "Director's Car",             "Motor Vehicles - Motor Cars", "Mumbai HO",   "Toyota",                "INV-MV-011",  datetime.date(2023,1,15), datetime.date(2023,1,15), None, None, 2800000),
    ("FA-008", "Central AC Plant",           "Air Conditioning Plant",      "Mumbai HO",   "Blue Star",             "INV-AC-007",  datetime.date(2021,3,1),  datetime.date(2021,3,10), None, None, 1500000),
    ("FA-009", "Electrical Installation",    "Electrical Installations",    "Pune Plant",  "Schneider",             "INV-EL-033",  datetime.date(2020,8,1),  datetime.date(2020,9,1),  None, None, 2200000),
    ("FA-010", "Delivery Van (disposed)",    "Motor Vehicles - Commercial", "Pune Plant",  "Tata Motors",           "INV-MV-020",  datetime.date(2020,6,1),  datetime.date(2020,6,10), datetime.date(2024,9,30), 350000, 1400000),
]
N_ROWS = 60                                   # provision blank rows for growth
DATA_END = DATA_START + N_ROWS - 1

def yc(idx):    # year column letter helper
    return get_column_letter(idx)

for ridx in range(N_ROWS):
    r = DATA_START + ridx
    band = LLBLUE if ridx % 2 == 0 else WHITE
    s = sample[ridx] if ridx < len(sample) else None

    def put(col_letter, value=None, *, nf=None, al_=align("center"),
            f=font(9), seed=None):
        v = value
        if value is None and seed is not None:
            v = seed
        style_cell(ws, f"{col_letter}{r}", v, fnt=f, fl=fill(band), al=al_, numfmt=nf)

    # --- master detail (A..J) ---
    put("A", seed=(s[0] if s else None), f=font(9, True, NAVY))
    put("B", seed=(s[1] if s else None), al_=align("left"))
    put("C", seed=(s[2] if s else None), al_=align("left"))
    put("D", seed=(s[3] if s else None), al_=align("left"))
    put("E", seed=(s[4] if s else None), al_=align("left"), f=font(9, color=GREY))
    put("F", seed=(s[5] if s else None), f=font(9, color=GREY))
    put("G", seed=(s[6] if s else None), nf=DATE_FMT)
    put("H", seed=(s[7] if s else None), nf=DATE_FMT)
    put("I", seed=(s[8] if s else None), nf=DATE_FMT, f=font(9, color=ORANGE))
    put("J", seed=(s[9] if s else None), nf=INR_FMT, al_=align("right"), f=font(9, color=ORANGE))
    put("K", seed=(s[10] if s else None), nf=INR_FMT, al_=align("right"), f=font(9, True))

    # --- derived basis (L..Q) ---
    # Residual % = global default (single switch); user may overwrite a cell.
    style_cell(ws, f"L{r}", "=DefaultResidual", fnt=font(9), fl=fill(band),
               al=align("center"), numfmt=PCT_FMT)
    # Residual value
    style_cell(ws, f"M{r}", f'=IF($K{r}="","",$K{r}*$L{r})', fnt=font(9),
               fl=fill(band), al=align("right"), numfmt=INR_FMT)
    # Useful life via Schedule II lookup
    style_cell(ws, f"N{r}",
               f'=IF($C{r}="","",IFERROR(VLOOKUP($C{r},ScheduleIITable,3,FALSE),"#N/A"))',
               fnt=font(9, True), fl=fill(band), al=align("center"), numfmt=YRS_FMT)
    # Method (global switch)
    style_cell(ws, f"O{r}", f'=IF($K{r}="","",GlobalMethod)', fnt=font(9, True, color=BLUE),
               fl=fill(band), al=align("center"))
    # WDV rate
    style_cell(ws, f"P{r}",
               f'=IF(OR($K{r}="",$N{r}="",$N{r}=0,$M{r}=0),0,1-($M{r}/$K{r})^(1/$N{r}))',
               fnt=font(9, color=ORANGE), fl=fill(band), al=align("center"), numfmt=PCT_FMT)
    # Depreciable amount
    style_cell(ws, f"Q{r}", f'=IF($K{r}="","",$K{r}-$M{r})', fnt=font(9),
               fl=fill(band), al=align("right"), numfmt=INR_FMT)

    # --- year-wise depreciation block (V.. ) -------------------------------- #
    for k in range(N_YEARS):
        dep_idx = YEAR_START_COL + 2 * k
        wdv_idx = dep_idx + 1
        dep_col = yc(dep_idx)
        wdv_col = yc(wdv_idx)
        hdr = f"{dep_col}$3"                      # FY-end date in row 3
        fystart = f"(EDATE({hdr},-12)+1)"
        fulldays = f"({hdr}-{fystart}+1)"
        # previous closing WDV (cost for first FY)
        prev = f"$K{r}" if k == 0 else f"{yc(dep_idx-1)}{r}"
        startuse = f"MAX($H{r},{fystart})"
        effend = f'IF($I{r}="",{hdr},MIN($I{r},{hdr}))'
        days = f"MAX(0,({effend})-({startuse})+1)"
        remaining = f"MAX(0,{prev}-$M{r})"
        slm = f'IF($N{r}=0,0,$Q{r}/$N{r}*{days}/{fulldays})'
        wdvm = f'{prev}*$P{r}*{days}/{fulldays}'
        uncapped = f'IF($O{r}="WDV",{wdvm},{slm})'
        dep_formula = (
            f'=IF(OR($K{r}="",$H{r}=""),"",'
            f'MIN(MAX(0,{uncapped}),{remaining}))'
        )
        style_cell(ws, f"{dep_col}{r}", dep_formula, fnt=font(8),
                   fl=fill(LGREEN if ridx % 2 == 0 else WHITE),
                   al=align("right"), numfmt=INR_FMT)
        # closing WDV: 0 if disposed on/before FY end, else prev - dep
        disposed = f'AND($I{r}<>"",$I{r}<={hdr})'
        wdv_formula = (
            f'=IF($K{r}="","",IF({disposed},0,{prev}-{dep_col}{r}))'
        )
        style_cell(ws, f"{wdv_col}{r}", wdv_formula, fnt=font(8),
                   fl=fill(LGOLD if ridx % 2 == 0 else WHITE),
                   al=align("right"), numfmt=INR_FMT)

    # --- reporting-FY position (R..U) using INDEX/MATCH on the year block --- #
    first_year_col = yc(YEAR_START_COL)
    last_year_col = yc(last_col_idx)
    row_range = f"${first_year_col}{r}:${last_year_col}{r}"
    hdr_range = f"${first_year_col}$3:${last_year_col}$3"
    match = f"MATCH(ReportingFYEnd,{hdr_range},0)"
    style_cell(ws, f"R{r}", f'=IF($K{r}="","",INDEX({row_range},1,{match}))',
               fnt=font(9, True, GREEN), fl=fill(band), al=align("right"), numfmt=INR_FMT)
    style_cell(ws, f"T{r}", f'=IF($K{r}="","",INDEX({row_range},1,{match}+1))',
               fnt=font(9, True, GOLD), fl=fill(band), al=align("right"), numfmt=INR_FMT)
    # status
    status = (
        f'=IF($K{r}="","",'
        f'IF(AND($I{r}<>"",$I{r}<=ReportingFYEnd),"Disposed",'
        f'IF(OR($H{r}="",$H{r}>ReportingFYEnd),"Not Yet in Use","Active")))'
    )
    style_cell(ws, f"U{r}", status, fnt=font(9, True), fl=fill(band), al=align("center"))
    # accumulated dep at reporting FY
    style_cell(ws, f"S{r}",
               f'=IF($K{r}="","",IF($U{r}="Disposed",0,$K{r}-$T{r}))',
               fnt=font(9), fl=fill(band), al=align("right"), numfmt=INR_FMT)

# Totals row
TOT = DATA_END + 1
style_cell(ws, f"A{TOT}", "TOTAL", fnt=font(10, True, WHITE), fl=fill(NAVY), al=align("center"))
for c in "BCDEFGHIJ":
    style_cell(ws, f"{c}{TOT}", "", fl=fill(NAVY))
for col in ["J", "K", "M", "Q", "R", "S", "T"]:
    style_cell(ws, f"{col}{TOT}",
               f"=SUM({col}{DATA_START}:{col}{DATA_END})",
               fnt=font(10, True, WHITE), fl=fill(NAVY), al=align("right"), numfmt=INR_FMT)
for c in ["L", "N", "O", "P", "U"]:
    style_cell(ws, f"{c}{TOT}", "", fl=fill(NAVY))
for k in range(N_YEARS):
    dep_idx = YEAR_START_COL + 2 * k
    wdv_idx = dep_idx + 1
    for ci in (dep_idx, wdv_idx):
        cl = yc(ci)
        style_cell(ws, f"{cl}{TOT}", f"=SUM({cl}{DATA_START}:{cl}{DATA_END})",
                   fnt=font(8, True, WHITE), fl=fill(NAVY), al=align("right"), numfmt=INR_FMT)

# Data validation: category dropdown + method override + date sanity
dv_cat = DataValidation(type="list", formula1="AssetCategories", allow_blank=True)
dv_cat.error = "Pick a category from the Schedule II master (Input sheet)."
dv_cat.prompt = "Select an asset category (drives useful life & rate)."
ws.add_data_validation(dv_cat)
dv_cat.add(f"C{DATA_START}:C{DATA_END}")

# Freeze panes so master columns + headers stay visible
ws.freeze_panes = f"D{DATA_START}"

# Conditional formatting: shade Disposed rows, flag #N/A category
disp_rule = FormulaRule(formula=[f'$U{DATA_START}="Disposed"'],
                        fill=fill(LORANGE), font=font(9, italic=True, color=ORANGE))
ws.conditional_formatting.add(f"A{DATA_START}:U{DATA_END}", disp_rule)
na_rule = FormulaRule(formula=[f'$N{DATA_START}="#N/A"'], fill=fill("FFC7CE"),
                      font=font(9, bold=True, color=RED))
ws.conditional_formatting.add(f"N{DATA_START}:N{DATA_END}", na_rule)

# Print setup
ws.print_title_rows = "1:4"
ws.sheet_view.zoomScale = 90

# =========================================================================== #
#  SHEET 3 : REPORTS  (year-wise depreciation)
# =========================================================================== #
rep = wb.create_sheet("Reports")
rep.sheet_view.showGridLines = False
rep.sheet_properties.tabColor = GREEN

rep.merge_cells("B2:H2")
style_cell(rep, "B2", "DEPRECIATION REPORTS – YEAR-WISE SCHEDULE",
           fnt=font(16, True, WHITE), fl=fill(GREEN), al=align("center"), border=BORDER_BOX)
rep.row_dimensions[2].height = 26
rep.merge_cells("B3:H3")
style_cell(rep, "B3",
           '="Method: "&GlobalMethod&"   |   All figures auto-link to the FAR sheet"',
           fnt=font(9, italic=True, color=WHITE), fl=fill(BLUE), al=align("center"))

# ---- 3A : total depreciation & block movement by year --------------------- #
style_cell(rep, "B5", "A.  YEAR-WISE DEPRECIATION & NET BLOCK MOVEMENT",
           fnt=font(11, True, WHITE), fl=fill(BLUE), al=align("center"))
rep.merge_cells("B5:H5")
rep_head = ["Financial Year", "Dep for the Year (Rs.)", "Cumulative Dep (Rs.)",
            "Closing Net Block / WDV (Rs.)"]
for i, h in enumerate(rep_head):
    col = get_column_letter(2 + i)
    style_cell(rep, f"{col}6", h, fnt=font(10, True, WHITE), fl=fill(NAVY),
               al=align("center", wrap=True))
rep.row_dimensions[6].height = 30

for k in range(N_YEARS):
    rr = 7 + k
    dep_idx = YEAR_START_COL + 2 * k
    wdv_idx = dep_idx + 1
    dep_col = yc(dep_idx)
    wdv_col = yc(wdv_idx)
    band = LGREEN if k % 2 == 0 else WHITE
    style_cell(rep, f"B{rr}", f'="FY "&TEXT(FAR!{dep_col}$3,"yyyy")',
               fnt=font(9, True, NAVY), fl=fill(band), al=align("center"))
    style_cell(rep, f"C{rr}", f"=FAR!{dep_col}{TOT}", fnt=font(9), fl=fill(band),
               al=align("right"), numfmt=INR_FMT)
    style_cell(rep, f"D{rr}",
               (f"=C{rr}" if k == 0 else f"=D{rr-1}+C{rr}"),
               fnt=font(9), fl=fill(band), al=align("right"), numfmt=INR_FMT)
    style_cell(rep, f"E{rr}", f"=FAR!{wdv_col}{TOT}", fnt=font(9, True, GOLD),
               fl=fill(band), al=align("right"), numfmt=INR_FMT)

# ---- 3B : category x year depreciation matrix ----------------------------- #
mstart = 7 + N_YEARS + 2
style_cell(rep, f"B{mstart-1}", "B.  CATEGORY × YEAR DEPRECIATION MATRIX (Rs.)",
           fnt=font(11, True, WHITE), fl=fill(GREEN), al=align("center"))
rep.merge_cells(f"B{mstart-1}:{get_column_letter(2+N_YEARS)}{mstart-1}")

style_cell(rep, f"B{mstart}", "Asset Category", fnt=font(9, True, WHITE),
           fl=fill(NAVY), al=align("center", wrap=True))
for k in range(N_YEARS):
    col = get_column_letter(3 + k)
    style_cell(rep, f"{col}{mstart}", f'=TEXT(FAR!{yc(YEAR_START_COL+2*k)}$3,"yyyy")',
               fnt=font(8, True, WHITE), fl=fill(NAVY), al=align("center"))
rep.row_dimensions[mstart].height = 22

for j, (cat, _d, _l) in enumerate(schedule_ii):
    rr = mstart + 1 + j
    band = LGREEN if j % 2 == 0 else WHITE
    style_cell(rep, f"B{rr}",
               f"=Input!C{first_data+j}", fnt=font(8, True, NAVY),
               fl=fill(band), al=align("left"))
    for k in range(N_YEARS):
        col = get_column_letter(3 + k)
        dep_col = yc(YEAR_START_COL + 2 * k)
        style_cell(rep, f"{col}{rr}",
                   f'=SUMIF(FAR!$C${DATA_START}:$C${DATA_END},$B{rr},'
                   f'FAR!{dep_col}${DATA_START}:{dep_col}${DATA_END})',
                   fnt=font(8), fl=fill(band), al=align("right"), numfmt=INR_FMT)
mtot = mstart + 1 + len(schedule_ii)
style_cell(rep, f"B{mtot}", "TOTAL", fnt=font(9, True, WHITE), fl=fill(NAVY), al=align("center"))
for k in range(N_YEARS):
    col = get_column_letter(3 + k)
    style_cell(rep, f"{col}{mtot}", f"=SUM({col}{mstart+1}:{col}{mtot-1})",
               fnt=font(8, True, WHITE), fl=fill(NAVY), al=align("right"), numfmt=INR_FMT)

rep.column_dimensions["A"].width = 2.5
rep.column_dimensions["B"].width = 30
for k in range(max(4, N_YEARS)):
    rep.column_dimensions[get_column_letter(3 + k)].width = 13
rep.freeze_panes = "C7"

# =========================================================================== #
#  SHEET 4 : SUMMARY
# =========================================================================== #
sm = wb.create_sheet("Summary")
sm.sheet_view.showGridLines = False
sm.sheet_properties.tabColor = GOLD

sm.merge_cells("B2:H2")
style_cell(sm, "B2", "FIXED ASSETS – SUMMARY / SCHEDULE TO ACCOUNTS",
           fnt=font(16, True, WHITE), fl=fill(GOLD), al=align("center"), border=BORDER_BOX)
sm.row_dimensions[2].height = 26
sm.merge_cells("B3:H3")
style_cell(sm, "B3",
           '="As on "&TEXT(ReportingFYEnd,"dd-mmm-yyyy")&"   |   Method: "&GlobalMethod&'
           '"   |   "&Input!C6',
           fnt=font(9, italic=True, color=WHITE), fl=fill(NAVY), al=align("center"))

# category-wise block (Active assets only)
sm_head = ["Asset Category", "Gross Block (Rs.)", "Dep for the Year (Rs.)",
           "Accumulated Dep (Rs.)", "Net Block / WDV (Rs.)"]
hr = 5
for i, h in enumerate(sm_head):
    col = get_column_letter(2 + i)
    style_cell(sm, f"{col}{hr}", h, fnt=font(10, True, WHITE), fl=fill(BLUE),
               al=align("center", wrap=True))
sm.row_dimensions[hr].height = 30

fa_C = f"FAR!$C${DATA_START}:$C${DATA_END}"
fa_K = f"FAR!$K${DATA_START}:$K${DATA_END}"
fa_R = f"FAR!$R${DATA_START}:$R${DATA_END}"
fa_S = f"FAR!$S${DATA_START}:$S${DATA_END}"
fa_T = f"FAR!$T${DATA_START}:$T${DATA_END}"
fa_U = f"FAR!$U${DATA_START}:$U${DATA_END}"

for j, (cat, _d, _l) in enumerate(schedule_ii):
    rr = hr + 1 + j
    band = LGOLD if j % 2 == 0 else WHITE
    style_cell(sm, f"B{rr}", f"=Input!C{first_data+j}", fnt=font(9, True, NAVY),
               fl=fill(band), al=align("left"))
    style_cell(sm, f"C{rr}", f'=SUMIFS({fa_K},{fa_C},$B{rr},{fa_U},"<>Disposed")',
               fnt=font(9), fl=fill(band), al=align("right"), numfmt=INR_FMT)
    style_cell(sm, f"D{rr}", f'=SUMIFS({fa_R},{fa_C},$B{rr},{fa_U},"<>Disposed")',
               fnt=font(9), fl=fill(band), al=align("right"), numfmt=INR_FMT)
    style_cell(sm, f"E{rr}", f'=SUMIFS({fa_S},{fa_C},$B{rr},{fa_U},"<>Disposed")',
               fnt=font(9), fl=fill(band), al=align("right"), numfmt=INR_FMT)
    style_cell(sm, f"F{rr}", f'=SUMIFS({fa_T},{fa_C},$B{rr},{fa_U},"<>Disposed")',
               fnt=font(9, True, GOLD), fl=fill(band), al=align("right"), numfmt=INR_FMT)
sm_tot = hr + 1 + len(schedule_ii)
style_cell(sm, f"B{sm_tot}", "TOTAL", fnt=font(10, True, WHITE), fl=fill(NAVY), al=align("center"))
for col in ["C", "D", "E", "F"]:
    style_cell(sm, f"{col}{sm_tot}", f"=SUM({col}{hr+1}:{col}{sm_tot-1})",
               fnt=font(10, True, WHITE), fl=fill(NAVY), al=align("right"), numfmt=INR_FMT)

# reconciliation check
chk = sm_tot + 2
style_cell(sm, f"B{chk}", "Check: Gross − Acc. Dep = Net Block",
           fnt=font(9, italic=True, color=GREY), al=align("left"), border=None)
sm.merge_cells(f"B{chk}:D{chk}")
style_cell(sm, f"E{chk}", f"=C{sm_tot}-E{sm_tot}", fnt=font(9, True),
           fl=fill(LGREY), al=align("right"), numfmt=INR_FMT)
style_cell(sm, f"F{chk}", f'=IF(ROUND(E{chk}-F{sm_tot},0)=0,"OK ✓","CHECK")',
           fnt=font(9, True, GREEN), fl=fill(LGREEN), al=align("center"))

# disposals section
ds = chk + 3
style_cell(sm, f"B{ds-1}", "DISPOSALS DURING / UP TO REPORTING FY",
           fnt=font(11, True, WHITE), fl=fill(ORANGE), al=align("center"))
sm.merge_cells(f"B{ds-1}:F{ds-1}")
dheads = ["Asset", "Category", "Disposal Date", "Gross Cost (Rs.)", "Sale Proceeds (Rs.)"]
for i, h in enumerate(dheads):
    col = get_column_letter(2 + i)
    style_cell(sm, f"{col}{ds}", h, fnt=font(9, True, WHITE), fl=fill(NAVY),
               al=align("center", wrap=True))
# pull disposed rows from FAR via simple links (sample row 10 = FA-010)
disp_rows = [DATA_START + i for i, srow in enumerate(sample) if srow[8] is not None]
for n, far_r in enumerate(disp_rows):
    rr = ds + 1 + n
    band = LORANGE if n % 2 == 0 else WHITE
    style_cell(sm, f"B{rr}", f"=FAR!B{far_r}", fnt=font(9, True, NAVY), fl=fill(band), al=align("left"))
    style_cell(sm, f"C{rr}", f"=FAR!C{far_r}", fnt=font(9), fl=fill(band), al=align("left"))
    style_cell(sm, f"D{rr}", f"=FAR!I{far_r}", fnt=font(9), fl=fill(band), al=align("center"), numfmt=DATE_FMT)
    style_cell(sm, f"E{rr}", f"=FAR!K{far_r}", fnt=font(9), fl=fill(band), al=align("right"), numfmt=INR_FMT)
    style_cell(sm, f"F{rr}", f"=FAR!J{far_r}", fnt=font(9), fl=fill(band), al=align("right"), numfmt=INR_FMT)

for col, w in {"A": 2.5, "B": 30, "C": 22, "D": 20, "E": 20, "F": 20}.items():
    sm.column_dimensions[col].width = w

# =========================================================================== #
#  Save
# =========================================================================== #
wb.save(OUT_FILE)
print(f"Saved {OUT_FILE}")
print(f"FAR data rows {DATA_START}..{DATA_END}, totals row {TOT}, "
      f"year cols {get_column_letter(YEAR_START_COL)}..{last_col}")
