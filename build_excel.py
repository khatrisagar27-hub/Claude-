"""
build_excel.py — Creates the LexComply India styled Excel workbook.
Run once: python3 build_excel.py  → produces LexComply_India.xlsm
The .bas VBA module is imported separately via Alt+F11 > File > Import File.
"""

import openpyxl
from openpyxl import Workbook
from openpyxl.styles import (
    PatternFill, Font, Alignment, Border, Side, GradientFill
)
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.dimensions import ColumnDimension
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.utils import quote_sheetname
import os

OUT_FILE = "LexComply_India.xlsm"

# ── Colour palette ──
NAVY        = "0D1B2E"
GOLD        = "C8A951"
WHITE       = "FFFFFF"
LTGRAY      = "F2F2F2"
DGRAY       = "828282"
INPUT_BG    = "EFF6FF"   # light blue input cell
LABEL_BG    = "1E3A5F"   # dark blue label
SEC_HDR_BG  = "1D4ED8"   # section header (bright blue)
CRIT_BG     = "FEE2E2"
HIGH_BG     = "FEF3C7"
MED_BG      = "E0F2FE"
LOW_BG      = "D1FAE5"

def fill(hex_color):
    return PatternFill("solid", fgColor=hex_color)

def font(bold=False, color=NAVY, size=10, italic=False):
    return Font(bold=bold, color=color, size=size, italic=italic,
                name="Calibri")

def align(h="left", v="center", wrap=False):
    return Alignment(horizontal=h, vertical=v, wrap_text=wrap)

def border(style="thin", color="D0D0D0"):
    s = Side(style=style, color=color)
    return Border(left=s, right=s, top=s, bottom=s)

def thin_border():
    return border("thin", "BBBBBB")

def define_name(wb, name, sheet_name, cell_ref):
    """Add a workbook-scoped named range pointing to a single cell."""
    ref = f"{quote_sheetname(sheet_name)}!${cell_ref}"
    defn = DefinedName(name=name, attr_text=ref)
    wb.defined_names[name] = defn


# ── Helpers for writing styled cells ──
def hdr_cell(ws, row, col, text, bg=NAVY, fg=WHITE, size=11, bold=True,
             h_align="center", span_to=None):
    c = ws.cell(row=row, column=col, value=text)
    c.fill = fill(bg)
    c.font = font(bold=bold, color=fg, size=size)
    c.alignment = align(h_align, "center")
    if span_to:
        ws.merge_cells(
            start_row=row, start_column=col,
            end_row=row, end_column=span_to
        )
    return c

def label_cell(ws, row, col, text, bg=LABEL_BG, fg=GOLD):
    c = ws.cell(row=row, column=col, value=text)
    c.fill = fill(bg)
    c.font = font(bold=True, color=fg, size=9)
    c.alignment = align("left", "center")
    return c

def input_cell(ws, row, col, default=""):
    c = ws.cell(row=row, column=col, value=default)
    c.fill = fill(INPUT_BG)
    c.font = font(color=NAVY, size=10)
    c.alignment = align("left", "center")
    c.border = thin_border()
    return c

def note_cell(ws, row, col, text):
    c = ws.cell(row=row, column=col, value=text)
    c.fill = fill(LTGRAY)
    c.font = font(italic=True, color=DGRAY, size=8)
    c.alignment = align("left", "center")
    return c

def section_hdr(ws, row, col_start, col_end, text):
    c = ws.cell(row=row, column=col_start, value=text)
    c.fill = fill(SEC_HDR_BG)
    c.font = font(bold=True, color=WHITE, size=10)
    c.alignment = align("left", "center")
    ws.merge_cells(start_row=row, start_column=col_start,
                   end_row=row, end_column=col_end)
    ws.row_dimensions[row].height = 22

def output_placeholder(ws, text="(Run 'Analyze Compliance' to populate)",
                       row=3, col=1, span=10):
    c = ws.cell(row=row, column=col, value=text)
    c.fill = fill(LTGRAY)
    c.font = font(italic=True, color=DGRAY, size=10)
    c.alignment = align("center", "center")
    if span > 1:
        ws.merge_cells(start_row=row, start_column=col,
                       end_row=row+2, end_column=span)
    ws.row_dimensions[row].height = 60


# ================================================================
#  SHEET 1 — Company Profile (INPUT FORM)
# ================================================================
def build_profile_sheet(wb):
    ws = wb["Company Profile"]
    ws.sheet_view.showGridLines = False
    ws.sheet_properties.tabColor = "1D4ED8"

    # Column widths
    col_w = {1: 3, 2: 28, 3: 32, 4: 6, 5: 28, 6: 32, 7: 3}
    for col, w in col_w.items():
        ws.column_dimensions[get_column_letter(col)].width = w

    # ── Title banner ──
    ws.row_dimensions[1].height = 14
    ws.row_dimensions[2].height = 48
    ws.row_dimensions[3].height = 22
    ws.row_dimensions[4].height = 8

    hdr_cell(ws, 2, 1, "⚖  LexComply India — Company Compliance Profile",
             bg=NAVY, fg=GOLD, size=16, bold=True, h_align="center", span_to=6)
    hdr_cell(ws, 3, 1,
             "Fill in all fields below, then click the  ▶ Analyze Compliance  button",
             bg=SEC_HDR_BG, fg=WHITE, size=9, bold=False,
             h_align="center", span_to=6)

    # ── Validation lists ──
    YES_NO = '"Yes,No"'
    ENTITY_TYPES = ('"Private Limited Company,Public Limited Company,'
                    'LLP,Partnership Firm,Sole Proprietorship,'
                    'OPC (One Person Company),Section 8 Company,'
                    'Trust / Society,Government / PSU"')
    SECTORS = ('"Manufacturing,Trading / Distribution,IT / Software / BPO,'
               'Financial Services / NBFC,Banking,Insurance,'
               'E-Commerce / Online Marketplace,Food & Beverages,'
               'Pharmaceuticals / Healthcare,Real Estate / Construction,'
               'Mining / Quarrying,Hospitality / Hotels,'
               'Education / EdTech,Logistics / Transport,'
               'Agriculture / Agro-Processing,Media / Entertainment,'
               'Telecom,Energy / Power / Utilities,Other"')
    STATES = ('"Andhra Pradesh,Arunachal Pradesh,Assam,Bihar,Chhattisgarh,'
              'Goa,Gujarat,Haryana,Himachal Pradesh,Jharkhand,Karnataka,'
              'Kerala,Madhya Pradesh,Maharashtra,Manipur,Meghalaya,'
              'Mizoram,Nagaland,Odisha,Punjab,Rajasthan,Sikkim,'
              'Tamil Nadu,Telangana,Tripura,Uttar Pradesh,Uttarakhand,'
              'West Bengal,Delhi (NCT),Jammu & Kashmir,Ladakh,'
              'Puducherry,Chandigarh,Dadra & Nagar Haveli,'
              'Lakshadweep,Andaman & Nicobar"')
    TURNOVER_RANGES = ('"Below 20 Lakhs,20 - 40 Lakhs,40 Lakhs - 1 Crore,'
                       '1 - 5 Crores,5 - 10 Crores,10 - 40 Crores,'
                       '40 - 100 Crores,100 - 250 Crores,'
                       '250 - 500 Crores,Above 500 Crores"')

    def dv(formula1, prompt="Select from list"):
        v = DataValidation(type="list", formula1=formula1,
                           allow_blank=True, showDropDown=False)
        v.prompt = prompt
        v.showInputMessage = True
        v.showErrorMessage = True
        v.error = "Please select a valid option from the dropdown."
        v.errorTitle = "Invalid Input"
        return v

    dv_yesno    = dv(YES_NO, "Select Yes or No")
    dv_entity   = dv(ENTITY_TYPES, "Select entity type")
    dv_sector   = dv(SECTORS, "Select primary sector")
    dv_state    = dv(STATES, "Select state")
    dv_turnover = dv(TURNOVER_RANGES, "Select turnover range")

    for d in [dv_yesno, dv_entity, dv_sector, dv_state, dv_turnover]:
        ws.add_data_validation(d)

    # ── Named-range registry  {named_range: (row, col)} ──
    NR = {}  # filled as we place each input cell

    # ── Helper: place one label+input row ──
    def row_pair(row, col_l, col_i, label, named_range,
                 default="", dv_obj=None, note=None, span=1):
        label_cell(ws, row, col_l, label)
        c = input_cell(ws, row, col_i, default)
        if dv_obj:
            dv_obj.add(c)
        if note:
            # place note in next col after input span
            note_cell(ws, row, col_i + span, note)
        NR[named_range] = (row, col_i)
        ws.row_dimensions[row].height = 18
        return c

    # ── Section A: Company Identity ──
    section_hdr(ws, 5, 2, 6, "  A.  COMPANY IDENTITY")

    row_pair(6,  2, 3, "Company Name",         "inp_CompanyName")
    row_pair(7,  2, 3, "Entity Type",          "inp_EntityType",   dv_obj=dv_entity)
    row_pair(8,  2, 3, "State of Registration","inp_StateOfReg",   dv_obj=dv_state)
    row_pair(9,  2, 3, "States of Operation",  "inp_StatesOp",
             note="Separate multiple states with commas")
    row_pair(10, 2, 3, "Listed Company?",       "inp_IsListed",    default="No", dv_obj=dv_yesno)

    ws.row_dimensions[11].height = 8

    # ── Section B: Business Activity ──
    section_hdr(ws, 12, 2, 6, "  B.  BUSINESS ACTIVITY")

    row_pair(13, 2, 3, "Primary Business Sector", "inp_Sector",      dv_obj=dv_sector)
    row_pair(14, 2, 3, "Manufacturing Activity?",  "inp_IsManuf",     default="No", dv_obj=dv_yesno)
    row_pair(15, 2, 3, "Trading / Distribution?",  "inp_IsTrading",   default="No", dv_obj=dv_yesno)
    row_pair(16, 2, 3, "E-Commerce / Online Sales?","inp_IsEComm",    default="No", dv_obj=dv_yesno)
    row_pair(17, 2, 3, "Food & Beverages Business?","inp_FoodBev",    default="No", dv_obj=dv_yesno)
    row_pair(18, 2, 3, "Pharmaceuticals / Healthcare?","inp_Pharma",  default="No", dv_obj=dv_yesno)
    row_pair(19, 2, 3, "Petroleum / LPG / Fuel?",  "inp_Petroleum",   default="No", dv_obj=dv_yesno)
    row_pair(20, 2, 3, "Explosives / Fireworks?",  "inp_Explosives",  default="No", dv_obj=dv_yesno)
    row_pair(21, 2, 3, "Hazardous Chemicals?",     "inp_Chemicals",   default="No", dv_obj=dv_yesno)
    row_pair(22, 2, 3, "Uses Boilers?",             "inp_Boilers",    default="No", dv_obj=dv_yesno)
    row_pair(23, 2, 3, "Mining Operations?",        "inp_Mines",      default="No", dv_obj=dv_yesno)
    row_pair(24, 2, 3, "Construction Activity?",   "inp_Construct",   default="No", dv_obj=dv_yesno)
    row_pair(25, 2, 3, "Real Estate / RERA?",       "inp_RealEstate", default="No", dv_obj=dv_yesno)
    row_pair(26, 2, 3, "NBFC (Non-Banking Finance)?","inp_NBFC",      default="No", dv_obj=dv_yesno)
    row_pair(27, 2, 3, "Insurance Business?",       "inp_Insurance",  default="No", dv_obj=dv_yesno)
    row_pair(28, 2, 3, "Banking Business?",         "inp_Banking",    default="No", dv_obj=dv_yesno)

    ws.row_dimensions[29].height = 8

    # ── Section C: Financial Details ──
    section_hdr(ws, 30, 2, 6, "  C.  FINANCIAL DETAILS")

    row_pair(31, 2, 3, "Annual Turnover Range",     "inp_Turnover",
             dv_obj=dv_turnover,
             note="Enter number in Lakhs in column F for precise matching")
    row_pair(32, 2, 3, "Annual Turnover (₹ Lakhs)", "inp_TurnoverNum",
             note="Numeric — used for GST / MSME threshold checks")
    row_pair(33, 2, 3, "Net Worth (₹ Crores)",      "inp_NetWorth",  default=0)
    row_pair(34, 2, 3, "Net Profit (₹ Crores)",     "inp_NetProfit", default=0)
    row_pair(35, 2, 3, "Paid-Up Capital (₹ Crores)","inp_PaidUpCap", default=0)
    row_pair(36, 2, 3, "Registered as MSME?",        "inp_IsMSME",   default="No", dv_obj=dv_yesno)
    row_pair(37, 2, 3, "Has FDI (Foreign Investment)?","inp_HasFDI",  default="No", dv_obj=dv_yesno)
    row_pair(38, 2, 3, "Does Import / Export?",      "inp_ImportExp", default="No", dv_obj=dv_yesno)
    row_pair(39, 2, 3, "Has Foreign Exchange / FEMA?","inp_HasForex", default="No", dv_obj=dv_yesno)

    ws.row_dimensions[40].height = 8

    # ── Section D: Workforce ──
    section_hdr(ws, 41, 2, 6, "  D.  WORKFORCE")

    row_pair(42, 2, 3, "Total Employees",             "inp_TotalEmp",   default=0)
    row_pair(43, 2, 3, "Permanent Employees",         "inp_PermEmp",    default=0)
    row_pair(44, 2, 3, "Contract / Casual Workers",   "inp_ContractW",  default=0)
    row_pair(45, 2, 3, "Women Employees",             "inp_WomenEmp",   default=0)
    row_pair(46, 2, 3, "Migrant Workers",             "inp_MigrantW",   default=0)
    row_pair(47, 2, 3, "Persons with Disabilities",   "inp_PWDEmp",     default=0)
    row_pair(48, 2, 3, "Employees in Factory / Plant","inp_FactoryW",   default=0)
    row_pair(49, 2, 3, "Employs Apprentices?",        "inp_Apprentices",default="No", dv_obj=dv_yesno)

    ws.row_dimensions[50].height = 8

    # ── Section E: Premises & Environment ──
    section_hdr(ws, 51, 2, 6, "  E.  PREMISES & ENVIRONMENT")

    row_pair(52, 2, 3, "Has Factory / Manufacturing Unit?","inp_HasFactory", default="No", dv_obj=dv_yesno)
    row_pair(53, 2, 3, "Factory Uses Power / Electricity?","inp_FactPower",  default="No", dv_obj=dv_yesno)
    row_pair(54, 2, 3, "Has Shop / Retail Outlet?",        "inp_HasShop",    default="No", dv_obj=dv_yesno)
    row_pair(55, 2, 3, "Generates Hazardous Waste?",       "inp_HazWaste",   default="No", dv_obj=dv_yesno)
    row_pair(56, 2, 3, "Generates E-Waste?",               "inp_EWaste",     default="No", dv_obj=dv_yesno)
    row_pair(57, 2, 3, "Uses / Sells Plastic?",            "inp_Plastic",    default="No", dv_obj=dv_yesno)
    row_pair(58, 2, 3, "Discharges Wastewater / Effluents?","inp_WaterDisc", default="No", dv_obj=dv_yesno)
    row_pair(59, 2, 3, "Emits Air Pollutants?",            "inp_AirEmit",    default="No", dv_obj=dv_yesno)
    row_pair(60, 2, 3, "Large Electrical Installations?",  "inp_LargeElec",  default="No", dv_obj=dv_yesno)

    ws.row_dimensions[61].height = 8

    # ── Section F: Technology & Data ──
    section_hdr(ws, 62, 2, 6, "  F.  TECHNOLOGY & DATA")

    row_pair(63, 2, 3, "Has Website / App?",           "inp_HasWeb",    default="No", dv_obj=dv_yesno)
    row_pair(64, 2, 3, "Collects Personal Data?",      "inp_CollData",  default="No", dv_obj=dv_yesno)
    row_pair(65, 2, 3, "Has Online Payment Gateway?",  "inp_HasPayment",default="No", dv_obj=dv_yesno)
    row_pair(66, 2, 3, "IT / Software Services Company?","inp_IsIT",    default="No", dv_obj=dv_yesno)
    row_pair(67, 2, 3, "Subject to PMLA / AML Rules?", "inp_IsPMLA",   default="No", dv_obj=dv_yesno)
    row_pair(68, 2, 3, "Has IP / Trademarks / Patents?","inp_HasIP",    default="No", dv_obj=dv_yesno)

    ws.row_dimensions[69].height = 12

    # ── Analyze button instruction row ──
    btn_row = 70
    ws.row_dimensions[btn_row].height = 40
    c = ws.cell(row=btn_row, column=2,
                value="▶  CLICK THE 'ANALYZE COMPLIANCE' BUTTON ON THE TOOLBAR  ◀")
    c.fill = fill(GOLD)
    c.font = Font(bold=True, color=NAVY, size=12, name="Calibri")
    c.alignment = align("center", "center")
    ws.merge_cells(start_row=btn_row, start_column=2,
                   end_row=btn_row, end_column=6)

    ws.row_dimensions[71].height = 8
    note_cell(ws, 72, 2,
              "⚠  Save the file as .xlsm (macro-enabled) and import LexComply.bas "
              "before clicking Analyze.")
    ws.merge_cells(start_row=72, start_column=2, end_row=72, end_column=6)

    # ── Freeze panes ──
    ws.freeze_panes = "B5"

    return NR


# ================================================================
#  OUTPUT SHEETS — styled placeholder
# ================================================================
def build_output_sheet(wb, name, tab_color, col_headers, col_widths,
                       placeholder_text):
    ws = wb[name]
    ws.sheet_view.showGridLines = False
    ws.sheet_properties.tabColor = tab_color

    # Title row
    ws.row_dimensions[1].height = 36
    hdr_cell(ws, 1, 1, f"⚖  LexComply India — {name}",
             bg=NAVY, fg=GOLD, size=13, h_align="center", span_to=len(col_headers))

    # Column header row
    ws.row_dimensions[2].height = 20
    for i, (hdr, w) in enumerate(zip(col_headers, col_widths), start=1):
        c = ws.cell(row=2, column=i, value=hdr)
        c.fill = fill(SEC_HDR_BG)
        c.font = font(bold=True, color=WHITE, size=9)
        c.alignment = align("center", "center")
        ws.column_dimensions[get_column_letter(i)].width = w

    output_placeholder(ws, placeholder_text, row=3, col=1,
                       span=len(col_headers))


# ================================================================
#  DASHBOARD SHEET
# ================================================================
def build_dashboard_sheet(wb):
    ws = wb["Dashboard"]
    ws.sheet_view.showGridLines = False
    ws.sheet_properties.tabColor = "C8A951"

    ws.column_dimensions["A"].width = 4
    ws.column_dimensions["B"].width = 30
    ws.column_dimensions["C"].width = 24
    ws.column_dimensions["D"].width = 24
    ws.column_dimensions["E"].width = 24
    ws.column_dimensions["F"].width = 24
    ws.column_dimensions["G"].width = 4

    ws.row_dimensions[1].height = 12
    ws.row_dimensions[2].height = 56
    ws.row_dimensions[3].height = 24
    ws.row_dimensions[4].height = 12

    hdr_cell(ws, 2, 1, "⚖  LexComply India — Compliance Dashboard",
             bg=NAVY, fg=GOLD, size=16, h_align="center", span_to=6)
    hdr_cell(ws, 3, 1,
             "Summary of applicable Indian laws for your company — generated automatically",
             bg=SEC_HDR_BG, fg=WHITE, size=9, bold=False,
             h_align="center", span_to=6)

    # KPI boxes row 5
    kpi_row = 5
    ws.row_dimensions[kpi_row].height = 60
    kpi_labels = [
        ("TOTAL LAWS", "0", NAVY, "BBBBFF"),
        ("CRITICAL",   "0", "DC2626", CRIT_BG),
        ("HIGH",       "0", "D97706", HIGH_BG),
        ("MEDIUM",     "0", "0284C7", MED_BG),
        ("LOW",        "0", "059669", LOW_BG),
    ]
    for i, (lbl, val, fg_col, bg_col) in enumerate(kpi_labels, start=2):
        c_num = ws.cell(row=kpi_row, column=i, value=val)
        c_num.fill = fill(bg_col)
        c_num.font = Font(bold=True, color=fg_col, size=22, name="Calibri")
        c_num.alignment = align("center", "center")

        c_lbl = ws.cell(row=kpi_row + 1, column=i, value=lbl)
        c_lbl.fill = fill(bg_col)
        c_lbl.font = font(bold=True, color=fg_col, size=9)
        c_lbl.alignment = align("center", "center")
        ws.row_dimensions[kpi_row + 1].height = 20

    ws.row_dimensions[7].height = 16
    output_placeholder(ws,
                       "(Run 'Analyze Compliance' to populate the dashboard)",
                       row=8, col=1, span=6)


# ================================================================
#  MAIN
# ================================================================
def main():
    wb = Workbook()

    # Remove default sheet and add named sheets in order
    default = wb.active
    sheet_names = [
        "Company Profile",
        "Laws Overview",
        "Compliance Checklist",
        "Compliance Calendar",
        "Urgent Actions",
        "Dashboard",
    ]
    wb.remove(default)
    for name in sheet_names:
        wb.create_sheet(name)

    # ── Company Profile ──
    named_ranges = build_profile_sheet(wb)

    # ── Register named ranges ──
    sheet_name = "Company Profile"
    for nr_name, (row, col) in named_ranges.items():
        col_letter = get_column_letter(col)
        define_name(wb, nr_name, sheet_name, f"{col_letter}{row}")

    # ── Laws Overview ──
    build_output_sheet(
        wb, "Laws Overview", "DC2626",
        col_headers=["#", "Law / Act", "Category", "Priority",
                     "Why Applicable", "No. Actions", "Authority"],
        col_widths=[5, 38, 22, 12, 42, 12, 28],
        placeholder_text="Run 'Analyze Compliance' to see all applicable laws here."
    )

    # ── Compliance Checklist ──
    build_output_sheet(
        wb, "Compliance Checklist", "D97706",
        col_headers=["#", "Law / Act", "Compliance Action", "Frequency",
                     "Next Deadline", "Authority", "Penalty for Non-compliance"],
        col_widths=[5, 30, 40, 14, 18, 28, 32],
        placeholder_text="Run 'Analyze Compliance' to generate your full compliance checklist."
    )

    # ── Compliance Calendar ──
    build_output_sheet(
        wb, "Compliance Calendar", "0284C7",
        col_headers=["Frequency Bucket", "Priority", "Law / Act",
                     "Action", "Deadline", "Authority", "Penalty"],
        col_widths=[18, 12, 30, 40, 18, 28, 32],
        placeholder_text="Run 'Analyze Compliance' to generate your compliance calendar."
    )

    # ── Urgent Actions ──
    build_output_sheet(
        wb, "Urgent Actions", "DC2626",
        col_headers=["#", "Priority", "Law / Act", "Action Required",
                     "Deadline", "Authority", "Penalty"],
        col_widths=[5, 12, 30, 40, 18, 28, 32],
        placeholder_text="Run 'Analyze Compliance' to see Critical and High priority actions."
    )

    # ── Dashboard ──
    build_dashboard_sheet(wb)

    # ── Active sheet on open ──
    wb.active = wb["Company Profile"]

    # Save
    wb.save(OUT_FILE)
    print(f"✓  Created: {OUT_FILE}")
    print(f"   Sheets : {', '.join(sheet_names)}")
    print(f"   Named ranges defined: {len(named_ranges)}")
    print()
    print("NEXT STEPS:")
    print("  1. Open LexComply_India.xlsm in Excel (Enable Macros when prompted)")
    print("  2. Press Alt+F11 to open VBA Editor")
    print("  3. File → Import File → select  LexComply.bas")
    print("  4. Close VBA Editor")
    print("  5. Fill in the 'Company Profile' sheet")
    print("  6. Press Alt+F8 → 'AnalyzeCompliance' → Run")
    print("     (or assign the macro to a button/shape on the profile sheet)")


if __name__ == "__main__":
    main()
