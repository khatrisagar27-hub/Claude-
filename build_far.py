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
ws_in.merge_cells(f"B{hdr_row-1}:H{hdr_row-1}")
style_cell(ws_in, f"B{hdr_row-1}",
           "B.  ASSET MASTER – SCHEDULE II USEFUL LIVES + INCOME-TAX BLOCK MAPPING",
           fnt=font(11, True, WHITE), fl=fill(GREEN), al=align("center"))

sched_headers = ["Sr.", "Asset Category", "Description / Notes",
                 "Useful Life (Years)", "Indicative WDV Rate*",
                 "Income-Tax Block", "IT Dep Rate"]
for i, h in enumerate(sched_headers):
    col = get_column_letter(2 + i)
    style_cell(ws_in, f"{col}{hdr_row}", h, fnt=font(9, True, WHITE),
               fl=fill(GREEN), al=align("center", wrap=True))
ws_in.row_dimensions[hdr_row].height = 28

# Companies Act useful life (Schedule II Part C) + mapped Income-Tax block & rate
#   (category, description, life_yrs, IT block, IT WDV rate)
schedule_ii = [
    ("Buildings - RCC Frame",                 "Buildings other than factory (RCC frame)",   60, "Building (General/Non-residential)",  0.10),
    ("Buildings - Other than RCC",            "Buildings other than factory (non-RCC)",     30, "Building (General/Non-residential)",  0.10),
    ("Factory Building",                      "Factory buildings",                          30, "Building (General/Non-residential)",  0.10),
    ("Plant & Machinery - General",           "General rate plant & machinery",             15, "Plant & Machinery (General)",         0.15),
    ("Plant & Machinery - Continuous Process","Continuous process plant",                   25, "Plant & Machinery (General)",         0.15),
    ("Furniture & Fittings",                  "General furniture and fittings",             10, "Furniture & Fittings",                0.10),
    ("Office Equipment",                      "General office equipment",                    5, "Plant & Machinery (General)",         0.15),
    ("Computers - End User Devices",          "Laptops, desktops, printers",                 3, "Computers & Software",                0.40),
    ("Computers - Servers & Networks",        "Servers and network equipment",               6, "Computers & Software",                0.40),
    ("Electrical Installations",              "Electrical installations & equipment",       10, "Plant & Machinery (General)",         0.15),
    ("Motor Vehicles - Motor Cars",           "Cars (other than used in hire business)",     8, "Motor Vehicles (Non-hire)",           0.15),
    ("Motor Vehicles - Commercial",           "Buses/lorries used in business of hire",      6, "Motor Vehicles (Hire/Commercial)",    0.30),
    ("Motor Vehicles - Two Wheelers",         "Motor cycles, scooters",                     10, "Motor Vehicles (Non-hire)",           0.15),
    ("Laboratory Equipment - General",        "General laboratory equipment",               10, "Plant & Machinery (General)",         0.15),
    ("Plant & Machinery - Moulds/Dies",       "Moulds, jigs, dies and tooling",              8, "Plant & Machinery (General)",         0.15),
    ("Air Conditioning Plant",                "AC plant (treated as P&M)",                   5, "Plant & Machinery (General)",         0.15),
    ("Intangible Assets - Software",          "Computer software (computers block)",         5, "Computers & Software",                0.40),
    ("Leasehold Improvements",                "Over primary lease period (illustrative)",   10, "Building (General/Non-residential)",  0.10),
]
first_data = hdr_row + 1
for j, (cat, desc, life, itblk, itrate) in enumerate(schedule_ii):
    rr = first_data + j
    band = LGREEN if j % 2 == 0 else WHITE
    style_cell(ws_in, f"B{rr}", j + 1, fnt=font(9), fl=fill(band), al=align("center"))
    style_cell(ws_in, f"C{rr}", cat, fnt=font(9, True, NAVY), fl=fill(band), al=align("left"))
    style_cell(ws_in, f"D{rr}", desc, fnt=font(8, color=GREY), fl=fill(band), al=align("left"))
    style_cell(ws_in, f"E{rr}", life, fnt=font(9, True), fl=fill(band),
               al=align("center"), numfmt=YRS_FMT)
    style_cell(ws_in, f"F{rr}",
               f"=IF(E{rr}=0,0,1-(DefaultResidual)^(1/E{rr}))",
               fnt=font(9, color=ORANGE), fl=fill(band),
               al=align("center"), numfmt=PCT_FMT)
    style_cell(ws_in, f"G{rr}", itblk, fnt=font(8, True, color=ORANGE),
               fl=fill(band), al=align("left"))
    style_cell(ws_in, f"H{rr}", itrate, fnt=font(9, True, color=RED),
               fl=fill(band), al=align("center"), numfmt=PCT_FMT)
last_data = first_data + len(schedule_ii) - 1

ws_in.merge_cells(f"B{last_data+1}:H{last_data+1}")
style_cell(ws_in, f"B{last_data+1}",
           "*Companies Act indicative WDV rate = 1 − (Residual)^(1/Useful Life). The Income-Tax block & rate "
           "(Sec. 32 / Appendix I, WDV) drive the Income-Tax Depreciation Chart. Edit rows freely – FAR & charts follow.",
           fnt=font(8, italic=True, color=GREY), fl=fill(LGREY), al=align("left", wrap=True))
ws_in.row_dimensions[last_data+1].height = 28

# defined names for the master table & category list (now C..H)
wb.defined_names.add(DefinedName(
    "ScheduleIITable", attr_text=f"Input!$C${first_data}:$H${last_data}"))
wb.defined_names.add(DefinedName(
    "AssetCategories", attr_text=f"Input!$C${first_data}:$C${last_data}"))

# --------------------------------------------------------------------------- #
#  Income-Tax block master (Section 32 / Appendix I, WDV rates)
# --------------------------------------------------------------------------- #
IT_BLOCKS = [
    ("Building (Residential)",                        0.05),
    ("Building (General/Non-residential)",            0.10),
    ("Building (Temporary Structures)",               0.40),
    ("Furniture & Fittings",                          0.10),
    ("Plant & Machinery (General)",                   0.15),
    ("Plant & Machinery (Energy-saving/Pollution)",   0.40),
    ("Motor Vehicles (Non-hire)",                     0.15),
    ("Motor Vehicles (Hire/Commercial)",              0.30),
    ("Computers & Software",                          0.40),
    ("Intangible Assets",                             0.25),
    ("Ships",                                         0.20),
    ("Books (annual publications / lending library)", 0.40),
]
itm_hdr = last_data + 3
ws_in.merge_cells(f"B{itm_hdr-1}:H{itm_hdr-1}")
style_cell(ws_in, f"B{itm_hdr-1}",
           "C.  INCOME-TAX BLOCK OF ASSETS – WDV RATES (Sec. 32, Appendix I)",
           fnt=font(11, True, WHITE), fl=fill(RED), al=align("center"))
style_cell(ws_in, f"B{itm_hdr}", "Block of Assets", fnt=font(9, True, WHITE),
           fl=fill(NAVY), al=align("center"))
ws_in.merge_cells(f"B{itm_hdr}:E{itm_hdr}")
style_cell(ws_in, f"F{itm_hdr}", "WDV Rate", fnt=font(9, True, WHITE),
           fl=fill(NAVY), al=align("center"))
for j, (blk, rate) in enumerate(IT_BLOCKS):
    rr = itm_hdr + 1 + j
    band = LORANGE if j % 2 == 0 else WHITE
    ws_in.merge_cells(f"B{rr}:E{rr}")
    style_cell(ws_in, f"B{rr}", blk, fnt=font(9, True, NAVY), fl=fill(band), al=align("left"))
    style_cell(ws_in, f"F{rr}", rate, fnt=font(9, True, RED), fl=fill(band),
               al=align("center"), numfmt=PCT_FMT)
it_first = itm_hdr + 1
it_last = itm_hdr + len(IT_BLOCKS)
wb.defined_names.add(DefinedName("ITBlockTable", attr_text=f"Input!$B${it_first}:$F${it_last}"))
wb.defined_names.add(DefinedName("ITBlockList", attr_text=f"Input!$B${it_first}:$B${it_last}"))

# column widths
for col, w in {"A": 2.5, "B": 26, "C": 26, "D": 30, "E": 15,
               "F": 14, "G": 30, "H": 11}.items():
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
    # --- Schedule II extra-shift + CARO 2020 compliance ---
    ("Shift Basis",               12, "shift"),
    ("Shift Factor",              10, "num"),
    ("Date of Physical Verif.",   15, "date"),
    ("Title Deed in Co. Name?",   13, "deed"),
    ("Remarks / Components",      26, "text"),
]
N_FIXED = len(fixed_cols)              # 26
YEAR_START_COL = N_FIXED + 1           # 27 -> 'AA'
SHIFT_FACTOR_COL = get_column_letter(23)   # 'W' – multiplies the annual charge

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
           '"   |   Companies Act, 2013 – Schedule II  (see Income-Tax Chart sheet for Sec. 32)"',
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
group_header(get_column_letter(22), get_column_letter(26), "EXTRA-SHIFT (SCH. II) & CARO 2020 COMPLIANCE", ORANGE)

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
        # Schedule II extra-shift: charge x shift factor (1.0 / 1.5 / 2.0)
        uncapped = f'IF($O{r}="WDV",{wdvm},{slm})*${SHIFT_FACTOR_COL}{r}'
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

    # --- Schedule II extra-shift + CARO 2020 compliance (V..Z) ------------- #
    # V: shift basis (Single / Double / Triple / NESD) – default Single
    style_cell(ws, f"V{r}", ("Single" if s else None), fnt=font(9, color=BLUE),
               fl=fill(band), al=align("center"))
    # W: shift factor derived from basis (double +50%, triple +100%)
    style_cell(ws, f"W{r}",
               f'=IF($V{r}="Double",1.5,IF($V{r}="Triple",2,1))',
               fnt=font(9, True), fl=fill(band), al=align("center"), numfmt='0.0')
    # X: date of physical verification (CARO 3(i)(b)) – user fills
    style_cell(ws, f"X{r}", None, fnt=font(9), fl=fill(band),
               al=align("center"), numfmt=DATE_FMT)
    # Y: title deed in company's name (CARO 3(i)(c)) – auto-flag immovables
    style_cell(ws, f"Y{r}",
               f'=IF($K{r}="","",IF(OR(ISNUMBER(SEARCH("Build",$C{r})),'
               f'ISNUMBER(SEARCH("Lease",$C{r}))),"Yes","NA"))',
               fnt=font(9, True), fl=fill(band), al=align("center"))
    # Z: remarks / significant components (Schedule II componentisation)
    style_cell(ws, f"Z{r}", None, fnt=font(8, color=GREY), fl=fill(band), al=align("left"))

# Totals row
TOT = DATA_END + 1
style_cell(ws, f"A{TOT}", "TOTAL", fnt=font(10, True, WHITE), fl=fill(NAVY), al=align("center"))
for c in "BCDEFGHIJ":
    style_cell(ws, f"{c}{TOT}", "", fl=fill(NAVY))
for col in ["J", "K", "M", "Q", "R", "S", "T"]:
    style_cell(ws, f"{col}{TOT}",
               f"=SUM({col}{DATA_START}:{col}{DATA_END})",
               fnt=font(10, True, WHITE), fl=fill(NAVY), al=align("right"), numfmt=INR_FMT)
for c in ["L", "N", "O", "P", "U", "V", "W", "X", "Y", "Z"]:
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

# Shift-basis dropdown (Schedule II extra-shift)
dv_shift = DataValidation(type="list", formula1='"Single,Double,Triple,NESD"',
                          allow_blank=True)
dv_shift.prompt = ("Single shift = normal. Double shift = +50% dep, Triple = +100% "
                   "(Schedule II). NESD = no extra-shift depreciation.")
ws.add_data_validation(dv_shift)
dv_shift.add(f"V{DATA_START}:V{DATA_END}")

# Title-deed dropdown (CARO 3(i)(c))
dv_deed = DataValidation(type="list", formula1='"Yes,No,NA"', allow_blank=True)
dv_deed.prompt = "Is the title deed of this immovable property held in the company's name?"
ws.add_data_validation(dv_deed)
dv_deed.add(f"Y{DATA_START}:Y{DATA_END}")

# Freeze panes so master columns + headers stay visible
ws.freeze_panes = f"D{DATA_START}"

# Conditional formatting: shade Disposed rows, flag #N/A category
disp_rule = FormulaRule(formula=[f'$U{DATA_START}="Disposed"'],
                        fill=fill(LORANGE), font=font(9, italic=True, color=ORANGE))
ws.conditional_formatting.add(f"A{DATA_START}:Z{DATA_END}", disp_rule)
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

for j, (cat, _d, _l, _b, _rt) in enumerate(schedule_ii):
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

for j, (cat, _d, _l, _b, _rt) in enumerate(schedule_ii):
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
#  SHEET 5 : INCOME-TAX DEPRECIATION CHART  (Block of Assets, Sec. 32)
# =========================================================================== #
it = wb.create_sheet("Income-Tax Dep Chart")
it.sheet_view.showGridLines = False
it.sheet_properties.tabColor = RED

it.merge_cells("B2:N2")
style_cell(it, "B2", "INCOME-TAX DEPRECIATION CHART – BLOCK OF ASSETS",
           fnt=font(16, True, WHITE), fl=fill(RED), al=align("center"), border=BORDER_BOX)
it.row_dimensions[2].height = 26
it.merge_cells("B3:N3")
style_cell(it, "B3",
           "Section 32, Income-Tax Act  •  WDV method on block of assets (Appendix I rates)  •  "
           "180-day half-rate rule applied automatically from 'Date Put to Use' on FAR",
           fnt=font(9, italic=True, color=WHITE), fl=fill(NAVY), al=align("center"))

# IT computation FY selector
style_cell(it, "B5", "Income-Tax Computation FY (year ending):",
           fnt=font(10, True, NAVY), fl=fill(LLBLUE), al=align("left"))
it.merge_cells("B5:D5")
cell = style_cell(it, "E5", FIRST_FY_END, fnt=font(10, True, GOLD),
                  fl=fill(LGOLD), al=align("center"), numfmt=DATE_FMT)
wb.defined_names.add(DefinedName("ITFYEnd", attr_text="'Income-Tax Dep Chart'!$E$5"))
it.merge_cells("F5:N5")
style_cell(it, "F5",
           "↳ Additions of THIS year auto-flow from FAR (≥180 / <180 days). Enter Opening WDV "
           "(closing WDV of prior year) and any Additional Depreciation u/s 32(1)(iia) in the yellow cells.",
           fnt=font(8, italic=True, color=GREY), fl=fill(LGREY), al=align("left", wrap=True))
it.row_dimensions[5].height = 26

ITFYSTART = "(EDATE(ITFYEnd,-12)+1)"

# ---- Section B layout is computed first so Section A can SUM over it ------- #
secA_hdr = 7
secA_first = secA_hdr + 1
secA_last = secA_first + len(IT_BLOCKS) - 1
secA_tot = secA_last + 1

secB_title = secA_tot + 3
secB_hdr = secB_title + 1
secB_first = secB_hdr + 1
secB_last = secB_first + N_ROWS - 1

# convenient Section-B ranges (for SUMIF in Section A)
sb_block = f"$C${secB_first}:$C${secB_last}"
sb_180 = f"$G${secB_first}:$G${secB_last}"
sb_less = f"$H${secB_first}:$H${secB_last}"
sb_sale = f"$J${secB_first}:$J${secB_last}"

# ---- Section A : block-of-assets depreciation chart ----------------------- #
it.merge_cells(f"B{secA_hdr-1}:N{secA_hdr-1}")
style_cell(it, f"B{secA_hdr-1}",
           "A.  BLOCK-OF-ASSETS DEPRECIATION CHART  (yellow = your input)",
           fnt=font(11, True, WHITE), fl=fill(RED), al=align("center"))

a_heads = ["Block of Assets", "Rate", "Opening WDV", "Additions ≥180 days",
           "Additions <180 days", "Deletions (Sale)", "Normal Dep (full rate)",
           "Dep on <180 (½ rate)", "Additional Dep", "Total Depreciation",
           "Closing WDV", "Remarks"]
for i, h in enumerate(a_heads):
    col = get_column_letter(2 + i)
    style_cell(it, f"{col}{secA_hdr}", h, fnt=font(8, True, WHITE),
               fl=fill(NAVY), al=align("center", wrap=True))
it.row_dimensions[secA_hdr].height = 40

for j, (blk, rate) in enumerate(IT_BLOCKS):
    rr = secA_first + j
    band = LORANGE if j % 2 == 0 else WHITE
    yin = LGOLD                                   # input cells
    style_cell(it, f"B{rr}", f"=Input!B{it_first+j}", fnt=font(8, True, NAVY),
               fl=fill(band), al=align("left"))
    style_cell(it, f"C{rr}", f"=VLOOKUP($B{rr},ITBlockTable,5,FALSE)",
               fnt=font(8, True, RED), fl=fill(band), al=align("center"), numfmt=PCT_FMT)
    # Opening WDV – input
    style_cell(it, f"D{rr}", 0, fnt=font(8, True, GOLD), fl=fill(yin),
               al=align("right"), numfmt=INR_FMT)
    # Additions / deletions from Section B
    style_cell(it, f"E{rr}", f"=SUMIF({sb_block},$B{rr},{sb_180})",
               fnt=font(8), fl=fill(band), al=align("right"), numfmt=INR_FMT)
    style_cell(it, f"F{rr}", f"=SUMIF({sb_block},$B{rr},{sb_less})",
               fnt=font(8), fl=fill(band), al=align("right"), numfmt=INR_FMT)
    style_cell(it, f"G{rr}", f"=SUMIF({sb_block},$B{rr},{sb_sale})",
               fnt=font(8, color=ORANGE), fl=fill(band), al=align("right"), numfmt=INR_FMT)
    # net full base = Opening + Add>=180 - Deletions
    netfull = f"($D{rr}+$E{rr}-$G{rr})"
    fullbase = f"MAX(0,{netfull})"
    halfbase = f"MAX(0,$F{rr}+MIN(0,{netfull}))"
    style_cell(it, f"H{rr}", f"={fullbase}*$C{rr}", fnt=font(8, True),
               fl=fill(band), al=align("right"), numfmt=INR_FMT)
    style_cell(it, f"I{rr}", f"={halfbase}*$C{rr}*0.5", fnt=font(8, True),
               fl=fill(band), al=align("right"), numfmt=INR_FMT)
    # Additional dep – input
    style_cell(it, f"J{rr}", 0, fnt=font(8, True, GOLD), fl=fill(yin),
               al=align("right"), numfmt=INR_FMT)
    blockwdv = f"($D{rr}+$E{rr}+$F{rr}-$G{rr})"
    style_cell(it, f"K{rr}",
               f"=IF({blockwdv}<=0,0,MIN($H{rr}+$I{rr}+$J{rr},{blockwdv}))",
               fnt=font(8, True, RED), fl=fill(band), al=align("right"), numfmt=INR_FMT)
    style_cell(it, f"L{rr}", f"=IF({blockwdv}<=0,0,{blockwdv}-$K{rr})",
               fnt=font(8, True, NAVY), fl=fill(band), al=align("right"), numfmt=INR_FMT)
    style_cell(it, f"M{rr}",
               f'=IF({netfull}<0,"Block negative – examine STCG (Sec.50)",'
               f'IF(AND(($D{rr}+$E{rr}+$F{rr})=0,$G{rr}>0),"Block ceased",""))',
               fnt=font(7, italic=True, color=ORANGE), fl=fill(band), al=align("left"))
# totals
style_cell(it, f"B{secA_tot}", "TOTAL", fnt=font(9, True, WHITE), fl=fill(NAVY), al=align("center"))
style_cell(it, f"C{secA_tot}", "", fl=fill(NAVY))
for col in ["D", "E", "F", "G", "H", "I", "J", "K", "L"]:
    style_cell(it, f"{col}{secA_tot}", f"=SUM({col}{secA_first}:{col}{secA_last})",
               fnt=font(9, True, WHITE), fl=fill(NAVY), al=align("right"), numfmt=INR_FMT)
style_cell(it, f"M{secA_tot}", "", fl=fill(NAVY))

# ---- Section B : asset-wise detail feeding the chart ---------------------- #
it.merge_cells(f"B{secB_title}:N{secB_title}")
style_cell(it, f"B{secB_title}",
           "B.  ASSET-WISE WORKING (auto-linked to FAR; classifies each addition by the 180-day rule)",
           fnt=font(11, True, WHITE), fl=fill(NAVY), al=align("center"))
b_heads = ["Asset", "(hidden block key)", "IT Block", "Gross Cost", "Date Put to Use",
           "Days Used in FY", "Addition ≥180", "Addition <180", "Disposal Date",
           "Sale Proceeds (FY)"]
# map: B=Asset, C=block key, D=cost, E=put, F=days, G=add>=180, H=add<180, I=disp, J=sale
hdr_map = {"B": "Asset", "C": "IT Block", "D": "Gross Cost", "E": "Date Put to Use",
           "F": "Days Used in FY", "G": "Addition ≥180", "H": "Addition <180",
           "I": "Disposal Date", "J": "Sale Proceeds (FY)"}
for col, h in hdr_map.items():
    style_cell(it, f"{col}{secB_hdr}", h, fnt=font(8, True, WHITE),
               fl=fill(GREEN), al=align("center", wrap=True))
it.row_dimensions[secB_hdr].height = 28

for idx in range(N_ROWS):
    fr = DATA_START + idx                # corresponding FAR row
    rr = secB_first + idx
    band = LGREEN if idx % 2 == 0 else WHITE
    style_cell(it, f"B{rr}", f'=IF(FAR!K{fr}="","",FAR!B{fr})', fnt=font(8, NAVY),
               fl=fill(band), al=align("left"))
    style_cell(it, f"C{rr}",
               f'=IF(FAR!C{fr}="","",IFERROR(VLOOKUP(FAR!C{fr},ScheduleIITable,5,FALSE),""))',
               fnt=font(8, color=ORANGE), fl=fill(band), al=align("left"))
    style_cell(it, f"D{rr}", f'=IF(FAR!K{fr}="","",FAR!K{fr})', fnt=font(8),
               fl=fill(band), al=align("right"), numfmt=INR_FMT)
    style_cell(it, f"E{rr}", f'=IF(FAR!H{fr}="","",FAR!H{fr})', fnt=font(8),
               fl=fill(band), al=align("center"), numfmt=DATE_FMT)
    in_fy = f'AND(FAR!H{fr}<>"",FAR!H{fr}>={ITFYSTART},FAR!H{fr}<=ITFYEnd)'
    style_cell(it, f"F{rr}",
               f'=IF({in_fy},ITFYEnd-FAR!H{fr}+1,"")', fnt=font(8, GREY),
               fl=fill(band), al=align("center"), numfmt="0")
    style_cell(it, f"G{rr}",
               f'=IF(AND(FAR!K{fr}<>"",{in_fy},(ITFYEnd-FAR!H{fr}+1)>=180),FAR!K{fr},0)',
               fnt=font(8), fl=fill(band), al=align("right"), numfmt=INR_FMT)
    style_cell(it, f"H{rr}",
               f'=IF(AND(FAR!K{fr}<>"",{in_fy},(ITFYEnd-FAR!H{fr}+1)<180),FAR!K{fr},0)',
               fnt=font(8), fl=fill(band), al=align("right"), numfmt=INR_FMT)
    style_cell(it, f"I{rr}", f'=IF(FAR!I{fr}="","",FAR!I{fr})', fnt=font(8, ORANGE),
               fl=fill(band), al=align("center"), numfmt=DATE_FMT)
    in_disp = f'AND(FAR!I{fr}<>"",FAR!I{fr}>={ITFYSTART},FAR!I{fr}<=ITFYEnd)'
    style_cell(it, f"J{rr}", f'=IF({in_disp},FAR!J{fr},0)', fnt=font(8, ORANGE),
               fl=fill(band), al=align("right"), numfmt=INR_FMT)

for col, w in {"A": 2.5, "B": 26, "C": 30, "D": 15, "E": 14, "F": 12,
               "G": 15, "H": 15, "I": 13, "J": 14, "K": 15, "L": 15,
               "M": 28, "N": 4}.items():
    it.column_dimensions[col].width = w
it.freeze_panes = f"B{secA_first}"

# =========================================================================== #
#  SHEET 6 : NOTES & COMPLIANCE
# =========================================================================== #
nt = wb.create_sheet("Notes & Compliance")
nt.sheet_view.showGridLines = False
nt.sheet_properties.tabColor = GREY
nt.column_dimensions["A"].width = 2.5
nt.column_dimensions["B"].width = 4
nt.column_dimensions["C"].width = 110

nt.merge_cells("B2:C2")
style_cell(nt, "B2", "NOTES, ASSUMPTIONS & STATUTORY COMPLIANCE",
           fnt=font(15, True, WHITE), fl=fill(NAVY), al=align("center"), border=BORDER_BOX)
nt.row_dimensions[2].height = 26

def note_section(row, title, color):
    nt.merge_cells(f"B{row}:C{row}")
    style_cell(nt, f"B{row}", title, fnt=font(11, True, WHITE), fl=fill(color),
               al=align("left"))
    return row + 1

def note_line(row, num, text, bold=False, color="000000"):
    if num:
        style_cell(nt, f"B{row}", num, fnt=font(9, True, color=GREY),
                   al=align("center", v="top"), border=None)
    style_cell(nt, f"C{row}", text, fnt=font(9, bold, color),
               al=align("left", wrap=True, v="top"), border=None)
    nt.row_dimensions[row].height = 14 * (1 + len(text) // 95)
    return row + 1

rN = 4
rN = note_section(rN, "A.  COMPANIES ACT, 2013 – SCHEDULE II (depreciation on PPE)", BLUE)
for n, t in [
    ("1", "Depreciation is based on the USEFUL LIFE of the asset (Part C of Schedule II), not on fixed rates. The FAR looks up each asset's useful life from the master table on the Input sheet."),
    ("2", "Residual / scrap value shall NOT exceed 5% of the original cost (default set to 5% on Input; editable per asset on FAR)."),
    ("3", "Method: SLM or WDV may be used (and disclosed). The global switch on Input drives the whole register; a single asset can be overridden in the 'Method' column on FAR."),
    ("4", "Pro-rata depreciation is charged from the date the asset is 'put to use' and up to the date of sale/disposal (day-count based)."),
    ("5", "EXTRA-SHIFT (Schedule II Note): for double shift, depreciation increases by 50%; for triple shift by 100%, for the period of such use. Assets marked NESD get no extra-shift depreciation. Set this per asset via the 'Shift Basis' column (Single/Double/Triple/NESD) on FAR."),
    ("6", "COMPONENTISATION: where the cost of a significant part of an asset has a useful life different from the asset, it must be depreciated separately. Record such parts as separate FAR rows and note linkage in 'Remarks / Components'."),
]:
    rN = note_line(rN, n, t)

rN += 1
rN = note_section(rN, "B.  INCOME-TAX ACT – DEPRECIATION (Sec. 32 / Appendix I)", RED)
for n, t in [
    ("1", "Income-tax depreciation is computed on the WRITTEN DOWN VALUE of a BLOCK OF ASSETS (assets of the same class with the same rate), not asset-by-asset. See the 'Income-Tax Dep Chart' sheet."),
    ("2", "Indicative WDV rates used: Buildings 10% (residential 5%, temporary structures 40%); Furniture & Fittings 10%; Plant & Machinery (general) 15%; Motor vehicles 15% (commercial/used in hire 30%); Computers & software 40%; Intangibles 25%; Books 40%; Ships 20%. (Verify against the latest Appendix I each year.)"),
    ("3", "180-DAY RULE: if an asset is acquired AND put to use for less than 180 days during the year of acquisition, depreciation for that year is restricted to 50% of the normal rate. The chart classifies each addition automatically from the FAR 'Date Put to Use'."),
    ("4", "ADDITIONAL DEPRECIATION u/s 32(1)(iia): new plant & machinery acquired by a manufacturing undertaking is eligible for 20% additional depreciation (10% if used <180 days, balance allowed next year). Enter the eligible amount in the 'Additional Dep' input column."),
    ("5", "Block computation: Closing WDV = Opening WDV + Additions − Moneys payable on sale − Depreciation. If sale proceeds exceed (Opening + Additions), the block value turns negative → short-term capital gain u/s 50 (flagged in 'Remarks')."),
    ("6", "No depreciation on individual asset is relevant for tax; gains/losses are computed at block level, except where the entire block ceases to exist."),
]:
    rN = note_line(rN, n, t)

rN += 1
rN = note_section(rN, "C.  CARO 2020 – CLAUSE 3(i): PPE & INTANGIBLE ASSETS (audit reporting)", GREEN)
for n, t in [
    ("a", "Proper records showing full particulars, including QUANTITATIVE DETAILS and SITUATION, of Property, Plant & Equipment and of intangible assets (this FAR captures ID, description, location/cost-centre, cost and movement)."),
    ("b", "Whether PPE have been PHYSICALLY VERIFIED by management at reasonable intervals and material discrepancies dealt with — record the date in 'Date of Physical Verif.' on FAR."),
    ("c", "Whether TITLE DEEDS of all immovable properties are held in the company's name — flagged via 'Title Deed in Co. Name?' on FAR (auto-set to apply for buildings/leasehold)."),
    ("d", "Whether the company has REVALUED its PPE/intangibles based on a Registered Valuer's report (note in 'Remarks' and adjust cost if applicable)."),
    ("e", "Whether any proceedings for holding BENAMI property are initiated/pending (disclose in 'Remarks')."),
]:
    rN = note_line(rN, n, t)

rN += 1
rN = note_section(rN, "D.  SOURCES & DISCLAIMER", GOLD)
for n, t in [
    ("", "Companies Act, 2013 – Schedule II (useful lives, residual value, extra-shift, componentisation)."),
    ("", "Income-Tax Act – Section 32 read with Rule 5 and Appendix I (block-of-assets WDV rates, 180-day rule, additional depreciation)."),
    ("", "CARO 2020 – Companies (Auditor's Report) Order, 2020, paragraph 3(i)(a)–(e)."),
    ("", "DISCLAIMER: This template is an illustrative working tool. Useful lives and tax rates change by Finance Act/MCA notification and by asset specifics. Verify the current Schedule II and Appendix I, and consult your auditor/tax advisor before filing."),
]:
    rN = note_line(rN, n, t, color=GREY)

# =========================================================================== #
#  Save
# =========================================================================== #
wb.save(OUT_FILE)
print(f"Saved {OUT_FILE}")
print(f"FAR data rows {DATA_START}..{DATA_END}, totals row {TOT}, "
      f"year cols {get_column_letter(YEAR_START_COL)}..{last_col}")
