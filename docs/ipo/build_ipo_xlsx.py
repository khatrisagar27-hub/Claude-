# -*- coding: utf-8 -*-
"""Build the ESDS Software Solution IPO due-diligence workbook."""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.comments import Comment

OUT = "/home/user/Claude-/docs/ipo/ESDS-Software-Solution-IPO-2026.xlsx"

# ---------------------------------------------------------------- style kit
F = "Arial"
BLUE  = "FF0000FF"   # hardcoded input
BLACK = "FF000000"   # formula
GREEN = "FF008000"   # link to another sheet
GREY  = "FF6B7280"
WHITE = "FFFFFFFF"
NAVY  = "FF0F3D3E"   # header band
ACC   = "FF0F5F62"

fill_hdr   = PatternFill("solid", fgColor=NAVY)
fill_sub   = PatternFill("solid", fgColor="FFE4EDEC")
fill_key   = PatternFill("solid", fgColor="FFFFFF00")   # key assumption / fill-in
fill_band  = PatternFill("solid", fgColor="FFF2F4F5")
fill_warn  = PatternFill("solid", fgColor="FFFDECEA")
fill_ok    = PatternFill("solid", fgColor="FFE8F4EC")
fill_caut  = PatternFill("solid", fgColor="FFFDF4E1")

thin = Side(style="thin", color="FFD0D5D9")
box  = Border(left=thin, right=thin, top=thin, bottom=thin)
bot  = Border(bottom=Side(style="thin", color="FF9AA5AD"))

def title(ws, row, text, span=8):
    c = ws.cell(row=row, column=1, value=text)
    c.font = Font(name=F, size=14, bold=True, color=WHITE)
    c.fill = fill_hdr
    c.alignment = Alignment(vertical="center", indent=1)
    ws.row_dimensions[row].height = 26
    for i in range(2, span + 1):
        ws.cell(row=row, column=i).fill = fill_hdr

def sub(ws, row, text, span=8):
    c = ws.cell(row=row, column=1, value=text)
    c.font = Font(name=F, size=10, bold=True, color=ACC)
    c.fill = fill_sub
    c.alignment = Alignment(vertical="center", indent=1)
    for i in range(2, span + 1):
        ws.cell(row=row, column=i).fill = fill_sub

def hdr(ws, row, labels, start=1):
    for i, t in enumerate(labels):
        c = ws.cell(row=row, column=start + i, value=t)
        c.font = Font(name=F, size=9, bold=True, color="FF303840")
        c.fill = fill_band
        c.border = box
        c.alignment = Alignment(wrap_text=True, vertical="bottom")
    ws.row_dimensions[row].height = 30

def put(ws, row, col, val, *, bold=False, color=BLACK, fmt=None, wrap=False,
        fill=None, size=10, italic=False, border=True, align=None):
    c = ws.cell(row=row, column=col, value=val)
    c.font = Font(name=F, size=size, bold=bold, color=color, italic=italic)
    if fmt: c.number_format = fmt
    if fill: c.fill = fill
    if border: c.border = box
    c.alignment = Alignment(wrap_text=wrap, vertical="top",
                            horizontal=align or ("right" if fmt else "left"))
    return c

def note(ws, row, text, span=8, size=9):
    c = ws.cell(row=row, column=1, value=text)
    c.font = Font(name=F, size=size, italic=True, color=GREY)
    c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=span)
    ws.row_dimensions[row].height = max(14, 12 * (len(text) // (span * 16) + 1))

def widths(ws, spec):
    for col, w in spec.items():
        ws.column_dimensions[col].width = w

# number formats
RS   = '₹#,##0.00;(₹#,##0.00);-'
RS0  = '₹#,##0;(₹#,##0);-'
CR   = '#,##0.00;(#,##0.00);-'
PCT  = '0.0%;(0.0%);-'
PCT2 = '0.00%;(0.00%);-'
MULT = '0.0"x"'
MULT2= '0.00"x"'
NUM  = '#,##0.00'

wb = Workbook()

# ================================================================ 1. READ ME
ws = wb.active; ws.title = "Read Me"
widths(ws, {"A":22,"B":18,"C":16,"D":16,"E":16,"F":16,"G":16,"H":16})
title(ws, 1, "ESDS Software Solution Limited — IPO Due Diligence", 8)
put(ws, 2, 1, "Analysis date", bold=True, border=False)
put(ws, 2, 2, "28 August 2026 (Day 1 of the book)", border=False)
put(ws, 3, 1, "Issue", bold=True, border=False)
put(ws, 3, 2, "₹720 crore · 100% fresh issue · no OFS · band ₹408–₹429 · 28 Aug – 1 Sep 2026 · lists 4 Sep 2026", border=False)
put(ws, 4, 1, "Prepared for", bold=True, border=False)
put(ws, 4, 2, "Investment assessment — listing gains, 3–5 year hold, and risk-adjusted return", border=False)

r = 6
sub(ws, r, "READ THIS BEFORE ANY NUMBER IN THIS WORKBOOK"); r += 1
for t in [
 "Outbound network access in the environment where this was prepared was restricted to a web-search index. Every primary-source domain returned EGRESS_BLOCKED: sebi.gov.in, nseindia.com, bseindia.com, esds.co.in and every IPO-data host attempted.",
 "I could NOT open the RHP, the abridged prospectus, the audited financial statements, or any exchange filing. Every figure in this workbook comes from secondary sources quoting the RHP, retrieved on 28 August 2026.",
 "The CASH FLOW STATEMENT is unavailable in its entirety — CFO, capex and free cash flow for every year. For a capital-intensive data-centre business that is the most important gap in this analysis. It has been left empty rather than estimated.",
 "To compensate, the 'Consistency Audit' tab re-computes nine figures that ought to reconcile. All nine pass. That is why the income statement can be relied on despite second-hand provenance — but it is not a substitute for reading the RHP.",
]:
    c = put(ws, r, 1, t, wrap=True, border=False, size=10)
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=8)
    ws.row_dimensions[r].height = 30 if len(t) < 210 else 44
    r += 1

r += 1
sub(ws, r, "TAG KEY — every figure in this workbook carries one"); r += 1
hdr(ws, r, ["Tag", "Meaning", "", "", "", "", "", ""]); r += 1
for tag, mean in [
    ("[R]",  "Reported by a secondary source citing the RHP"),
    ("[C]",  "My calculation, derived from [R] inputs — the formula is live in the cell"),
    ("[NA]", "Not available — I could not obtain it. Left blank, never estimated"),
    ("[!]",  "Sources conflict, or the figure failed a cross-check. See the note beside it"),
]:
    put(ws, r, 1, tag, bold=True); put(ws, r, 2, mean, wrap=True)
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=8); r += 1

r += 1
sub(ws, r, "CELL COLOUR CONVENTION (standard financial-model convention)"); r += 1
hdr(ws, r, ["Colour", "Means", "", "", "", "", "", ""]); r += 1
for col, mean, fl in [
    (BLUE,  "Blue text — a hardcoded input. Every one is sourced on the 'Inputs' tab.", None),
    (BLACK, "Black text — a live formula. Change an input and this recalculates.", None),
    (GREEN, "Green text — a link to another sheet in this workbook.", None),
    (BLACK, "Yellow fill — a key assumption you are meant to challenge or change.", fill_key),
]:
    put(ws, r, 1, "sample", color=col, bold=True, fill=fl)
    put(ws, r, 2, mean, wrap=True)
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=8); r += 1

r += 1
sub(ws, r, "HOW TO USE THIS MODEL"); r += 1
for t in [
 "1.  'Inputs' is the single source of truth. Every hardcoded number lives there, in blue, with its source. Nothing else in the workbook hardcodes a figure.",
 "2.  Change the price on 'Valuation' cell C6 and every multiple, fair value and margin-of-safety number in the workbook updates.",
 "3.  Change the growth, margin and exit-multiple assumptions on 'Scenarios' (yellow cells) and the fair value range and verdict inputs update.",
 "4.  'Consistency Audit' will show FAIL if you change an input in a way that breaks reconciliation with the reported figures. That is intentional.",
]:
    put(ws, r, 1, t, wrap=True, border=False)
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=8)
    ws.row_dimensions[r].height = 26; r += 1

r += 1
c = put(ws, r, 1, "Analytical work product, not investment advice. Verify against the RHP before acting. IPO sentiment data cited here is timestamped and perishable.",
        wrap=True, italic=True, color=GREY, border=False)
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=8)

# ================================================================ 2. INPUTS
ws = wb.create_sheet("Inputs")
widths(ws, {"A":34,"B":10,"C":16,"D":8,"E":62})
title(ws, 1, "Inputs — every hardcoded figure in this workbook, with its source", 5)
note(ws, 2, "Blue = hardcoded. Nothing else in this workbook hardcodes a number; every other sheet links here. Change a value and the whole model recalculates.", 5)
hdr(ws, 3, ["Item", "Unit", "Value", "Tag", "Source / note"])

ROW = {}
r = 4
def inp(key, label, unit, value, tag, source, fmt=CR, section=False, fill=None):
    global r
    if section:
        sub(ws, r, label, 5); r += 1; return
    put(ws, r, 1, label, wrap=True)
    put(ws, r, 2, unit, size=9, color=GREY)
    put(ws, r, 3, value, color=BLUE, fmt=fmt, fill=fill)
    put(ws, r, 4, tag, size=9, bold=True,
        color=("FFB0392B" if tag == "[!]" else GREY), align="center")
    put(ws, r, 5, source, wrap=True, size=9, color=GREY)
    ROW[key] = r; r += 1

inp(None, "ISSUE TERMS", None, None, None, None, section=True)
inp("price_lo",  "Price band — lower",              "₹/sh", 408,    "[R]", "Groww / Bajaj Broking / Upstox IPO pages, 28 Aug 2026", RS0)
inp("price_hi",  "Price band — upper",              "₹/sh", 429,    "[R]", "Groww / Bajaj Broking / Upstox IPO pages, 28 Aug 2026", RS0)
inp("issue",     "Issue size (gross)",              "₹ cr", 720.00, "[R]", "IPOWatch / Chittorgarh / Zerodha. 100% fresh issue, no OFS")
inp("ofs",       "Offer for sale",                  "₹ cr", 0.00,   "[R]", "Nil — every rupee goes to the company")
inp("fresh_sh",  "Fresh shares issued (at ₹429)",   "cr",   1.68,   "[R]", "Reported as 1.68 crore shares for ₹720 cr")
inp("mcap_hi_r", "Post-issue market cap @ ₹429",    "₹ cr", 5028,   "[R]", "Reported. Used to back out the pre-issue share count")
inp("lot",       "Lot size",                        "sh",   34,     "[R]", "Angel One / Chittorgarh", '#,##0')
inp("fv",        "Face value",                      "₹/sh", 1,      "[R]", "₹1 per equity share", RS0)

inp(None, "PROFIT & LOSS  (₹ crore)", None, None, None, None, section=True)
inp("rev23", "FY23 revenue from operations", "₹ cr", 212.20, "[R]", "UnlistedZone FY25 review, citing RHP restated accounts")
inp("rev24", "FY24 revenue from operations", "₹ cr", 286.50, "[C]", "Derived: top-10 clients ₹107.10 cr = 37.38% of revenue from ops")
inp("rev25", "FY25 revenue from operations", "₹ cr", 361.30, "[R]", "Tradebrains: 'operational revenue rose 30.7% to ₹472.2 cr from ₹361.3 cr'")
inp("rev26", "FY26 revenue from operations", "₹ cr", 472.20, "[R]", "Tradebrains, Aug 2026")
inp("ti24",  "FY24 total income",            "₹ cr", 292.14, "[R]", "Tradebrains / Paytm Money IPO review")
inp("ti25",  "FY25 total income",            "₹ cr", 376.64, "[R]", "Tradebrains / Paytm Money IPO review")
inp("ti26",  "FY26 total income",            "₹ cr", 480.65, "[R]", "Tradebrains / Paytm Money IPO review")
inp("eb23",  "FY23 EBITDA",                  "₹ cr", 26.20,  "[R]", "UnlistedZone: 'up from ₹26.2 cr in the previous year'")
inp("eb24",  "FY24 EBITDA",                  "₹ cr", 76.10,  "[R]", "UnlistedZone: 'EBITDA surged to ₹76.1 cr, margin ~26%'")
inp("eb25",  "FY25 EBITDA",                  "₹ cr", 154.89, "[R]", "Tradebrains: 'EBITDA increased from ₹154.89 cr in FY25'")
inp("eb26",  "FY26 EBITDA",                  "₹ cr", 234.23, "[R]", "Tradebrains: '...to ₹234.23 cr in FY26'")
inp("pat23", "FY23 PAT",                     "₹ cr", -22.50, "[R]", "UnlistedZone: loss of ₹22.5 cr in FY23")
inp("pat24", "FY24 PAT",                     "₹ cr", 13.61,  "[R]", "Tradebrains / Chittorgarh")
inp("pat25", "FY25 PAT",                     "₹ cr", 55.61,  "[R]", "Tradebrains / Chittorgarh")
inp("pat26", "FY26 PAT",                     "₹ cr", 120.82, "[R]", "Tradebrains / Chittorgarh / Groww")
inp("oth26", "FY26 other income",            "₹ cr", 8.45,   "[C]", "Derived: total income ₹480.65 cr less revenue from ops ₹472.20 cr")

inp(None, "RATIOS & BALANCE SHEET", None, None, None, None, section=True)
inp("roe",    "FY26 Return on equity",             "%",    0.2512, "[R]", "INDmoney IPO review, citing RHP", PCT2)
inp("roce",   "FY26 Return on capital employed",   "%",    0.3278, "[R]", "INDmoney IPO review, citing RHP", PCT2)
inp("de26",   "FY26 Debt / equity",                "x",    0.08,   "[R]", "INDmoney: 'D/E declined from 0.66 to 0.08'", MULT2)
inp("de24",   "FY24 Debt / equity",                "x",    0.66,   "[R]", "INDmoney IPO review", MULT2)
inp("bor24",  "FY24 secured borrowings",           "₹ cr", 115.44, "[R]", "INDmoney IPO review, citing RHP")
inp("bor25",  "FY25 secured borrowings",           "₹ cr", 62.71,  "[R]", "INDmoney IPO review, citing RHP")
inp("bor26",  "FY26 secured borrowings",           "₹ cr", 42.92,  "[R]", "INDmoney IPO review, citing RHP")
inp("debt26", "FY26 total financial indebtedness", "₹ cr", 102.92, "[R]", "INDmoney IPO review, citing RHP")
inp("cl_nw",  "Contingent liabilities / net worth","%",    0.1043, "[R]", "FY26; was 30.50% two years prior", PCT2)
inp("unbill", "FY26 unbilled revenue",             "₹ cr", 63.39,  "[R]", "INDmoney IPO review, citing RHP")
inp("dso",    "FY26 receivable days",              "days", 79,     "[R]", "INDmoney: 'about 79 days to collect sales'", '#,##0')
inp("hypo",   "Current assets hypothecated",       "%",    0.9672, "[R]", "As at 31 Mar 2026", PCT2)
inp("tax_st", "Statutory corporate tax rate",      "%",    0.2517, "[R]", "India s.115BAA concessional rate, 22% + surcharge + cess", PCT2)
inp("int_rt", "Assumed interest rate on borrowings","%",   0.10,   "[C]", "My assumption for the tax-rate derivation. Challenge it.", PCT2, fill=fill_key)

inp(None, "BUSINESS & CONCENTRATION", None, None, None, None, section=True)
inp("t10_24", "Top-10 clients as % of revenue, FY24", "%", 0.3738, "[R]", "INDmoney, citing RHP (₹107.10 cr)", PCT2)
inp("t10_25", "Top-10 clients as % of revenue, FY25", "%", 0.4934, "[R]", "INDmoney, citing RHP (₹178.27 cr)", PCT2)
inp("t10_26", "Top-10 clients as % of revenue, FY26", "%", 0.4536, "[R]", "INDmoney, citing RHP (₹214.17 cr)", PCT2)
inp("t10v26", "Top-10 client revenue, FY26",          "₹ cr", 214.17,"[R]", "Used in consistency check #8", CR)
inp("t1_26",  "Largest single client, FY26",          "%", 0.1593, "[R]", "INDmoney, citing RHP", PCT2)
inp("seg_ent","Enterprise share of FY26 revenue",     "%", 0.5509, "[R]", "Tradebrains, citing RHP", PCT2)
inp("seg_gov","Government share of FY26 revenue",     "%", 0.2737, "[R]", "Tradebrains, citing RHP", PCT2)
inp("seg_bfsi","BFSI share of FY26 revenue",          "%", 0.1753, "[R]", "Tradebrains, citing RHP", PCT2)
inp("mw_now", "Current IT load",                      "MW", 7,     "[R]", "Entrepreneur India, Aug 2026", '#,##0')
inp("mw_tgt", "Target IT load, 1–2 years",            "MW", 14,    "[R]", "Guidance 14–20 MW. Lower end used.", '#,##0')
inp("dcs",    "Data centres",                         "no.", 5,    "[R]", "Nashik, Navi Mumbai, Bengaluru, Mohali, Noida", '#,##0')

inp(None, "USE OF PROCEEDS & OWNERSHIP", None, None, None, None, section=True)
inp("capex",  "Cloud / DC equipment capex from proceeds","₹ cr", 576.00,"[R]", "Objects of the issue. See the [!] note below.")
inp("prom_pre","Promoter holding, pre-issue",           "%", 0.4606,"[R]", "Piyush & Komal Somani, P.O. Somani Family Trust", PCT2)
inp("pub_pre", "Public holding, pre-issue",             "%", 0.5265,"[!]", "Reported. 46.06% + 52.65% = 98.71% — residual 1.29% unexplained", PCT2)
inp("srv_life","Server / cloud hardware useful life",   "yrs", 5.5, "[C]", "Industry norm 5–6 years. My assumption for the D&A wave.", '#,##0.0', fill=fill_key)
inp("claim",   "Ex-employee litigation claim (cash alt.)","₹ cr", 18.48,"[R]", "R.S. Papneja: 1% of shares OR ₹18.48 cr compensation")

inp(None, "SENTIMENT  (timestamped 27–28 Aug 2026 — perishable)", None, None, None, None, section=True)
inp("gmp",     "Grey market premium",             "₹/sh", 330, "[!]", "Sahi.com, 28 Aug 2026. Implies +77% — see 'Sentiment' tab.", RS0)
inp("sub_all", "Day 1 subscription, overall",     "x", 0.40, "[R]", "Goodreturns, 28 Aug 2026 intra-day", MULT2)
inp("sub_ret", "Day 1 subscription, retail",      "x", 0.54, "[R]", "Goodreturns, 28 Aug 2026 intra-day", MULT2)
inp("sub_nii", "Day 1 subscription, NII/HNI",     "x", 0.60, "[R]", "Goodreturns, 28 Aug 2026 intra-day", MULT2)
inp("sub_qib", "Day 1 subscription, QIB ex-anchor","x", 0.00,"[R]", "Nil. Mainboard QIB books are back-loaded to the final day.", MULT2)
inp("anchor",  "Anchor book raised",              "₹ cr", 216.00,"[R]", "Inc42, 27 Aug 2026 — 19 investors at ₹429")
inp("anch_mf", "Anchor allocation to mutual funds","%", 0.8194,"[R]", "6 fund houses across 13 schemes", PCT2)

inp(None, "PEER — E2E NETWORKS  (the only listed peer named in the RHP)", None, None, None, None, section=True)
inp("e2e_px",  "Share price, 27 Aug 2026",        "₹", 617,    "[R]", "Trendlyne / Value Research", RS0)
inp("e2e_mc",  "Market capitalisation",           "₹ cr", 12602.16,"[R]","Smart-investing.in, 27 Aug 2026")
inp("e2e_pe",  "P/E (trailing twelve months)",    "x", 404.24, "[R]", "GuruFocus / Smart-investing.in, 27 Aug 2026", '#,##0.0"x"')
inp("e2e_ev",  "EV / EBITDA",                     "x", 53.60,  "[R]", "Trendlyne. 3-year average 35.11x", MULT)
inp("e2e_pb",  "Price / book",                    "x", 7.50,   "[R]", "Smart-investing.in, 27 Aug 2026", MULT)
inp("e2e_roe", "Return on equity",                "%", -0.0095,"[R]", "Per the RHP's own peer-comparison table", PCT2)
inp("e2e_roce","Return on capital employed",      "%", -0.0052,"[R]", "Per the RHP's own peer-comparison table", PCT2)
inp("e2e_de",  "Debt / equity",                   "x", 0.06,   "[R]", "Per the RHP's own peer-comparison table", MULT2)
inp("e2e_dso", "Receivable days",                 "days", 25,  "[R]", "INDmoney comparison", '#,##0')
inp("e2e_qr",  "Q1 FY27 revenue",                 "₹ cr", 156.80,"[R]", "Q1 FY27 earnings call: ₹1,568 million")
inp("e2e_qe",  "Q1 FY27 EBITDA",                  "₹ cr", 117.90,"[R]", "Q1 FY27 earnings call: ₹1,179 million")
inp("e2e_qp",  "Q1 FY27 PAT",                     "₹ cr", 43.90, "[R]", "Q1 FY27 earnings call: ₹439 million")

inp(None, "MY VALUATION ASSUMPTIONS  (yellow = challenge these)", None, None, None, None, section=True)
inp("disc",   "Discount rate",                    "%", 0.14, "[C]", "My assumption — equity cost of capital for an Indian mid-cap", PCT2, fill=fill_key)
inp("horizon","Valuation horizon",                "yrs", 3,  "[C]", "FY26 base to FY29", '#,##0', fill=fill_key)
inp("p_bear", "Probability weight — bear",        "%", 0.25,"[C]", "My judgment", PCT, fill=fill_key)
inp("p_base", "Probability weight — base",        "%", 0.50,"[C]", "My judgment", PCT, fill=fill_key)
inp("p_bull", "Probability weight — bull",        "%", 0.25,"[C]", "My judgment", PCT, fill=fill_key)

r += 1
c = put(ws, r, 1, "[!]  FAILED CROSS-CHECK — objects of the issue", bold=True, color="FFB0392B", border=False)
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5); r += 1
put(ws, r, 1, "One source listed uses of ₹576 cr (equipment) + ₹93.50 cr (working capital) + ₹90.00 cr (debt repayment) = ₹759.5 cr, which EXCEEDS the ₹720 cr gross raise — impossible, since net proceeds are gross less issue expenses. A ₹90 cr repayment is also implausible against total indebtedness of ₹102.92 cr and D/E of 0.08. I have adopted the ₹576 cr + general corporate purposes version, which reconciles and which other sources give, and flag the residual ~₹100–140 cr of net proceeds as unallocated in my sources. Verify against the RHP's Objects chapter.",
    wrap=True, border=False, size=9, color=GREY)
ws.merge_cells(start_row=r, start_column=1, end_row=r+3, end_column=5)

def I(key):
    return f"Inputs!$C${ROW[key]}"

# ================================================================ 3. SNAPSHOT
ws = wb.create_sheet("IPO Snapshot")
widths(ws, {"A":36,"B":22,"C":22,"D":8,"E":52})
title(ws, 1, "IPO Snapshot", 5)
hdr(ws, 3, ["Item", "At ₹408 (lower)", "At ₹429 (upper)", "Tag", "Note"])
r = 4
def snap(label, lo, hi, tag, nt, fmt=None, colr=BLACK, merge=False, bold=False):
    global r
    put(ws, r, 1, label, wrap=True, bold=bold)
    if merge:
        put(ws, r, 2, lo, color=colr, fmt=fmt, wrap=True, bold=bold)
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=3)
        ws.cell(row=r, column=3).border = box
    else:
        put(ws, r, 2, lo, color=colr, fmt=fmt, bold=bold)
        put(ws, r, 3, hi, color=colr, fmt=fmt, bold=bold)
    put(ws, r, 4, tag, size=9, bold=True, color=GREY, align="center")
    put(ws, r, 5, nt, wrap=True, size=9, color=GREY)
    r += 1

snap("Company", "ESDS Software Solution Limited", None, "[R]", "Incorporated 2005, headquartered Nashik", merge=True, colr=BLUE)
snap("Sector", "Data centres · cloud (IaaS) · managed services · SaaS", None, "[R]", "", merge=True, colr=BLUE)
snap("IPO type", "100% FRESH ISSUE — NO OFS", None, "[R]", "Every rupee goes to the company", merge=True, colr=BLUE, bold=True)
snap("Issue size (gross)", f"={I('issue')}", None, "[R]", "₹ crore", merge=True, colr=GREEN, fmt=CR)
snap("Offer for sale", f"={I('ofs')}", None, "[R]", "Nil", merge=True, colr=GREEN, fmt=CR)
snap("Price", f"={I('price_lo')}", f"={I('price_hi')}", "[R]", "₹ per share", fmt=RS0, colr=GREEN)
snap("Face value", f"={I('fv')}", None, "[R]", "₹ per share", merge=True, colr=GREEN, fmt=RS0)
snap("Lot size", f"={I('lot')}", None, "[R]", "shares", merge=True, colr=GREEN, fmt='#,##0')
R_MININV = r
snap("Minimum investment (retail)", f"={I('lot')}*{I('price_lo')}", f"={I('lot')}*{I('price_hi')}", "[C]", "Lot size x price", fmt=RS0)
snap("Anchor book date", "27 Aug 2026", None, "[R]", "", merge=True, colr=BLUE)
snap("Issue opens", "Friday 28 August 2026", None, "[R]", "", merge=True, colr=BLUE)
snap("Issue closes", "Tuesday 1 September 2026", None, "[R]", "", merge=True, colr=BLUE)
snap("Basis of allotment", "2 September 2026", None, "[R]", "", merge=True, colr=BLUE)
snap("Listing", "4 September 2026 — BSE and NSE", None, "[R]", "", merge=True, colr=BLUE)

r += 1
sub(ws, r, "SHARE COUNT AND MARKET CAPITALISATION — derived, shown in full", 5); r += 1
hdr(ws, r, ["Item", "At ₹408 (lower)", "At ₹429 (upper)", "Tag", "Working"]); r += 1
R_PRE = r
snap("Pre-issue shares outstanding", f"={I('mcap_hi_r')}/{I('price_hi')}-{I('fresh_sh')}", None, "[C]",
     "Reported m-cap ₹5,028 cr / ₹429 = 11.72 cr post-issue, less 1.68 cr fresh", merge=True, fmt='#,##0.00')
R_FRESH = r
snap("Fresh shares issued", f"={I('issue')}/{I('price_lo')}", f"={I('issue')}/{I('price_hi')}", "[C]",
     "₹720 cr / price. Assumes the raise is fixed in rupees and share count flexes.", fmt='#,##0.00')
R_POST = r
snap("Post-issue shares outstanding", f"=$B${R_PRE}+B{R_FRESH}", f"=$B${R_PRE}+C{R_FRESH}", "[C]", "crore shares", fmt='#,##0.00', bold=True)
R_MCAP = r
snap("Implied market capitalisation", f"=B{R_POST}*{I('price_lo')}", f"=C{R_POST}*{I('price_hi')}", "[C]",
     "₹ crore. The ₹429 figure reproduces the reported ₹5,028 cr exactly — see Consistency Audit.", fmt='#,##0', bold=True)
R_EPS = r
snap("FY26 EPS on post-issue base", f"={I('pat26')}/B{R_POST}", f"={I('pat26')}/C{R_POST}", "[C]", "₹ per share", fmt=RS)

r += 1
sub(ws, r, "OWNERSHIP", 5); r += 1
hdr(ws, r, ["Item", "Pre-issue", "Post-issue", "Tag", "Note"]); r += 1
snap("Promoter holding", f"={I('prom_pre')}", f"={I('prom_pre')}*$B${R_PRE}/$C${R_POST}", "[R] [C]",
     "Post = pre-issue promoter shares / post-issue total. Promoters sell nothing.", fmt=PCT)
snap("Public holding", f"={I('pub_pre')}", None, "[!]",
     "46.06% + 52.65% = 98.71%. The residual 1.29% is unexplained in my sources.", merge=True, colr=GREEN, fmt=PCT)
snap("Promoters", "Piyush Prakashchandra Somani (CMD) · Komal Piyush Somani (WTD) · P.O. Somani Family Trust", None, "[R]", "", merge=True, colr=BLUE)
snap("Anchor investors", f"={I('anchor')}", None, "[R]", "₹ crore from 19 investors at ₹429; 81.94% to domestic mutual funds", merge=True, colr=GREEN, fmt=CR)
snap("Anchor mutual funds", "Motilal Oswal · Bandhan · Quant · ITI · JM Financial · Samco", None, "[R]", "6 houses, 13 schemes", merge=True, colr=BLUE)
snap("Lead managers", "DAM Capital Advisors · Systematix Corporate Services", None, "[R]", "", merge=True, colr=BLUE)
snap("Registrar", "MUFG Intime India (formerly Link Intime India)", None, "[R]", "", merge=True, colr=BLUE)
snap("Reservation", "QIB 50% · NII 15% · Retail 35%", None, "[R]", "Standard book-built structure", merge=True, colr=BLUE)

r += 1
note(ws, r, "LOCK-IN: promoters hold under 50% pre-IPO, reflecting years of pre-listing fundraising and an active unlisted market in the shares. Under SEBI ICDR, pre-issue capital other than promoter contribution is generally locked in for six months from allotment — so that overhang surfaces around March 2027, not at listing. This is the general regulatory rule applied by me; the RHP's specific lock-in disclosures were not verifiable.", 5)

SNAP = {"pre": R_PRE, "post": R_POST, "mcap": R_MCAP, "eps": R_EPS, "fresh": R_FRESH}

# ================================================================ 4. AUDIT
ws = wb.create_sheet("Consistency Audit")
widths(ws, {"A":5,"B":34,"C":15,"D":15,"E":11,"F":46})
title(ws, 1, "Consistency Audit — can these second-hand numbers be trusted?", 6)
note(ws, 2, "Because the RHP could not be opened, I tested whether independently-sourced figures reconcile. Each row below RE-COMPUTES a figure from other inputs and compares it to what was reported. All nine pass. Change an input on the Inputs tab and any broken reconciliation will show FAIL.", 6)
hdr(ws, 3, ["#", "Check", "Computed", "Reported", "Result", "Why it matters"])
r = 4
def chk(n, label, comp, rep, tol, why, fmt=NUM):
    global r
    put(ws, r, 1, n, align="center", size=9)
    put(ws, r, 2, label, wrap=True)
    put(ws, r, 3, comp, fmt=fmt)
    put(ws, r, 4, rep, fmt=fmt, color=GREEN)
    put(ws, r, 5, f'=IF(ABS(C{r}-D{r})<={tol},"PASS","FAIL")', bold=True, align="center",
        fill=fill_ok)
    put(ws, r, 6, why, wrap=True, size=9, color=GREY)
    r += 1

chk(1, "Post-issue share count (crore)", f"='IPO Snapshot'!C{SNAP['post']}", f"={I('mcap_hi_r')}/{I('price_hi')}", 0.01,
    "Reported market cap divided by the upper band must give the post-issue share count.")
chk(2, "Pre-issue share count (crore)", f"='IPO Snapshot'!B{SNAP['pre']}", f"={I('mcap_hi_r')}/{I('price_hi')}-{I('fresh_sh')}", 0.01,
    "Post-issue count less the fresh shares.")
chk(3, "P/E at the upper band", f"={I('price_hi')}/('IPO Snapshot'!C{SNAP['eps']})", 41.61, 0.10,
    "STRONGEST CHECK. My derived EPS of ₹10.31 x reported P/E must reproduce ₹429. It does, to two decimals.", MULT2)
chk(4, "EBITDA margin, FY26", f"={I('eb26')}/{I('rev26')}", 0.4960, 0.0005,
    "EXACT. Confirms EBITDA is struck on revenue from operations, not total income.", PCT2)
chk(5, "PAT margin, FY26", f"={I('pat26')}/{I('rev26')}", 0.2559, 0.0005,
    "EXACT. Same denominator convention.", PCT2)
chk(6, "Revenue growth, FY25 to FY26", f"={I('ti26')}/{I('ti25')}-1", 0.28, 0.005,
    "Reported as '+28%' on total income. Computes to 27.6%.", PCT2)
chk(7, "PAT growth, FY25 to FY26", f"={I('pat26')}/{I('pat25')}-1", 1.17, 0.005,
    "Reported as '+117%'. Computes to 117.3%.", PCT2)
chk(8, "Top-10 client concentration, FY26", f"={I('t10v26')}/{I('rev26')}", f"={I('t10_26')}", 0.0005,
    "The source listed the three years out of order. This check identifies which year is which.", PCT2)
chk(9, "Debt / equity, FY26", f"={I('bor26')}/({I('pat26')}/{I('roe')})", 0.08, 0.02,
    "Uses net worth backed out of ROE. Confirms the ~₹481-536 cr equity base.", MULT2)

r += 1
put(ws, r, 2, "Checks passed", bold=True)
put(ws, r, 3, f'=COUNTIF(E4:E{r-2},"PASS")&" of "&COUNTA(E4:E{r-2})', bold=True, fill=fill_ok, align="center")
ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=4)
put(ws, r, 6, "Nine of nine reconcile, three of them exactly. The income statement and per-share data can be relied on.", wrap=True, size=9, color=GREY)
r += 2
c = put(ws, r, 2, "WHAT THIS DOES NOT PROVE", bold=True, color="FFB0392B", border=False)
r += 1
put(ws, r, 2, "A green audit proves the reported figures are internally coherent. It cannot prove they match the RHP, and it says nothing about the balance sheet or cash flow, where far fewer figures were available to cross-check. Confidence: HIGH on the income statement, MODERATE on the balance sheet, NONE on cash flow.",
    wrap=True, border=False, size=9, color=GREY)
ws.merge_cells(start_row=r, start_column=2, end_row=r+2, end_column=6)

# ================================================================ 6. DERIVATIONS
ws = wb.create_sheet("Derivations")
widths(ws, {"A":6,"B":40,"C":16,"D":10,"E":60})
title(ws, 1, "Derivations — the depreciation problem", 5)
note(ws, 2, "The most important non-obvious finding in this analysis. Reported D&A was not available, so it is backed out of the reported ROCE. Moderate confidence — every step is shown so it can be challenged.", 5)
hdr(ws, 3, ["", "Step", "Value", "Unit", "Working / comment"])
r = 4
def drv(label, val, unit, work, fmt=CR, bold=False, fill=None, tag=""):
    global r
    put(ws, r, 1, tag, align="center", size=9, color=GREY)
    put(ws, r, 2, label, wrap=True, bold=bold)
    put(ws, r, 3, val, fmt=fmt, bold=bold, fill=fill)
    put(ws, r, 4, unit, size=9, color=GREY, align="center")
    put(ws, r, 5, work, wrap=True, size=9, color=GREY)
    rr = r; r += 1; return rr

sub(ws, r, "STEP 1 — back out the capital base and EBIT", 5); r += 1
R_AVGE = drv("Average equity", f"={I('pat26')}/{I('roe')}", "₹ cr", "PAT ₹120.82 cr / ROE 25.12%")
R_CLSE = drv("Closing equity", f"={I('bor26')}/{I('de26')}", "₹ cr", "Secured borrowings ₹42.92 cr / D/E 0.08")
R_AVGD = drv("Average debt", f"=({I('bor25')}+{I('bor26')})/2", "₹ cr", "Mean of FY25 ₹62.71 cr and FY26 ₹42.92 cr")
R_CE   = drv("Average capital employed", f"=C{R_AVGE}+C{R_AVGD}", "₹ cr", "Equity plus debt")
R_EBITD= drv("EBIT", f"={I('roce')}*C{R_CE}", "₹ cr", "ROCE 32.78% x capital employed", bold=True)
R_DAD  = drv("Depreciation & amortisation", f"={I('eb26')}-C{R_EBITD}", "₹ cr", "EBITDA less EBIT", bold=True, fill=fill_caut)
R_DAP  = drv("D&A as % of revenue", f"=C{R_DAD}/{I('rev26')}", "%", "Comparable colocation operators typically run 20–30%", fmt=PCT, bold=True, fill=fill_caut)
r += 1
put(ws, r, 2, "₹59 crore of depreciation across five Tier-3 data centres is low — strikingly so. Three explanations are possible:  (1) LEGACY ASSETS ARE LARGELY WRITTEN DOWN. ESDS has operated since 2005; the Nashik facility is old. Assets past their depreciable life carry revenue but no charge. Most likely, and it fits the margin curve exactly.  (2) LEASED rather than owned capacity, shifting cost from D&A into operating expense.  (3) LONG ASSUMED USEFUL LIVES — which would be an accounting-aggressiveness flag.  I cannot distinguish between these without the RHP's fixed-asset schedule. [NA] — and it is the single most valuable thing an investor could check before applying.",
    wrap=True, border=False, size=9, color=GREY)
ws.merge_cells(start_row=r, start_column=2, end_row=r+4, end_column=5); r += 6

sub(ws, r, "STEP 2 — does the profit surge survive a tax check?", 5); r += 1
drv("EBITDA", f"={I('eb26')}", "₹ cr", "Reported")
drv("less D&A (derived)", f"=-C{R_DAD}", "₹ cr", "From step 1")
drv("less interest", f"=-{I('int_rt')}*C{R_AVGD}", "₹ cr", "Assumed 10% on average debt — a yellow input on the Inputs tab")
drv("plus other income", f"={I('oth26')}", "₹ cr", "Total income less revenue from operations")
R_PBTD = drv("= PBT", f"={I('eb26')}-C{R_DAD}-{I('int_rt')}*C{R_AVGD}+{I('oth26')}", "₹ cr", "", bold=True)
drv("less PAT (reported)", f"=-{I('pat26')}", "₹ cr", "Reported")
R_TAXD = drv("= Implied tax charge", f"=C{R_PBTD}-{I('pat26')}", "₹ cr", "", bold=True)
R_ETR  = drv("Implied effective tax rate", f"=C{R_TAXD}/C{R_PBTD}", "%", "", fmt=PCT, bold=True, fill=fill_ok)
drv("Statutory rate for comparison", f"={I('tax_st')}", "%", "s.115BAA concessional regime", fmt=PCT, )
R_VERD = r
put(ws, r, 2, "Verdict", bold=True)
put(ws, r, 3, f'=IF(C{R_ETR}>{I("tax_st")},"ABOVE statutory","BELOW statutory")', bold=True, fill=fill_ok, align="center")
put(ws, r, 5, "An effective rate ABOVE statutory is the opposite of a tax-flattered result. The obvious suspicion — that PAT rose 117% while EBITDA rose 51% because of deferred-tax-asset recognition against the FY23 loss — does not survive this check.",
    wrap=True, size=9, color=GREY)
ws.merge_cells(start_row=r, start_column=5, end_row=r+2, end_column=5); r += 4
put(ws, r, 2, "Caveat: this chain rests on a derived D&A figure. If actual D&A is LOWER, the implied tax rate rises further, strengthening the conclusion. If D&A is materially HIGHER, PBT falls and the implied rate drops. The conclusion is robust in one direction and sensitive in the other.",
    wrap=True, border=False, size=9, italic=True, color=GREY)
ws.merge_cells(start_row=r, start_column=2, end_row=r+1, end_column=5); r += 3

sub(ws, r, "STEP 3 — the forward consequence: the depreciation wave", 5); r += 1
R_NEWDA = drv("New annual D&A from the ₹576 cr capex", f"={I('capex')}/{I('srv_life')}", "₹ cr",
              "₹576 cr over an assumed 5.5-year server life. Yellow input — change it on the Inputs tab.", bold=True, fill=fill_warn)
drv("Current D&A for comparison", f"=C{R_DAD}", "₹ cr", "From step 1")
R_TOTDA = drv("Total D&A once deployed", f"=C{R_DAD}+C{R_NEWDA}", "₹ cr", "Roughly three times current", bold=True)
R_VSPAT = drv("New D&A as % of FY26 PAT", f"=C{R_NEWDA}/{I('pat26')}", "%",
              "The increment alone is comparable to the whole of FY26 profit", fmt=PCT, bold=True, fill=fill_warn)
r += 1
sub(ws, r, "Sizing the offset if the capacity actually fills", 5); r += 1
R_REVCAP = drv("Revenue capacity at target MW", f"={I('rev26')}*{I('mw_tgt')}/{I('mw_now')}", "₹ cr",
               "Assumes revenue scales linearly with IT load — a simplification", fill=fill_key)
R_INCREV = drv("Incremental revenue at full utilisation", f"=C{R_REVCAP}-{I('rev26')}", "₹ cr", "")
R_INCEB  = drv("x incremental EBITDA margin (50%)", f"=C{R_INCREV}*0.5", "₹ cr", "Near the current 49.6% margin")
R_INCEBIT= drv("less incremental D&A", f"=C{R_INCEB}-C{R_NEWDA}", "₹ cr",
               "INCREMENTAL EBIT at full utilisation", bold=True, fill=fill_ok)
r += 1
put(ws, r, 2, "THE CENTRAL CONCLUSION:  the capex is strongly accretive at full utilisation and strongly dilutive at low utilisation. The entire equity story reduces to one number — capacity utilisation — which ESDS does not publish. That is why the long-term verdict is Neutral rather than Positive: not a judgment about quality, but an admission that the decisive variable is unobservable from outside.",
    wrap=True, border=False, size=10, bold=True)
ws.merge_cells(start_row=r, start_column=2, end_row=r+3, end_column=5)

DRV = {"da": R_DAD, "ebit": R_EBITD, "pbt": R_PBTD, "etr": R_ETR, "newda": R_NEWDA}

# ================================================================ 5. FINANCIALS
ws = wb.create_sheet("Financials")
widths(ws, {"A":34,"B":14,"C":14,"D":14,"E":14,"F":8,"G":44})
title(ws, 1, "Financials — four years (FY22 is not available)", 7)
note(ws, 2, "All ₹ crore unless stated. Black = live formula off the Inputs tab. FY22 could not be obtained, so the brief's five-year study is delivered as a four-year study — flagged rather than filled.", 7)
hdr(ws, 3, ["₹ crore", "FY23", "FY24", "FY25", "FY26", "Tag", "Note"])
r = 4
def fin(label, cells, tag, nt, fmt=CR, bold=False, colr=BLACK, fill=None):
    global r
    put(ws, r, 1, label, wrap=True, bold=bold)
    for i, v in enumerate(cells):
        put(ws, r, 2 + i, v, fmt=fmt, bold=bold, color=(GREY if v is None else colr), fill=fill)
        if v is None:
            ws.cell(row=r, column=2+i).value = "n/a"
            ws.cell(row=r, column=2+i).alignment = Alignment(horizontal="center")
    put(ws, r, 6, tag, size=9, bold=True, color=GREY, align="center")
    put(ws, r, 7, nt, wrap=True, size=9, color=GREY)
    rr = r; r += 1; return rr

sub(ws, r, "INCOME STATEMENT", 7); r += 1
R_REV = fin("Revenue from operations", [f"={I('rev23')}", f"={I('rev24')}", f"={I('rev25')}", f"={I('rev26')}"],
            "[R] [C]", "FY24 derived: top-10 ₹107.10 cr / 37.38%", colr=GREEN, bold=True)
R_TI  = fin("Total income", [None, f"={I('ti24')}", f"={I('ti25')}", f"={I('ti26')}"], "[R]", "", colr=GREEN)
R_RG  = fin("Revenue growth, y/y", [None, f"=C{R_REV}/B{R_REV}-1", f"=D{R_REV}/C{R_REV}-1", f"=E{R_REV}/D{R_REV}-1"],
            "[C]", "On revenue from operations", fmt=PCT)
R_EB  = fin("EBITDA", [f"={I('eb23')}", f"={I('eb24')}", f"={I('eb25')}", f"={I('eb26')}"], "[R]", "", colr=GREEN, bold=True)
R_EBM = fin("EBITDA margin", [f"=B{R_EB}/B{R_REV}", f"=C{R_EB}/C{R_REV}", f"=D{R_EB}/D{R_REV}", f"=E{R_EB}/E{R_REV}"],
            "[C]", "THE CENTRAL FACT: 12.3% to 49.6% in three years", fmt=PCT, bold=True, fill=fill_caut)
R_DA  = fin("Depreciation & amortisation", [None, None, None, f"=Derivations!C{R_DAD}"],
            "[C]", "Derived from ROCE — see the Derivations tab", colr=GREEN)
R_EBIT= fin("EBIT", [None, None, None, f"=Derivations!C{R_EBITD}"], "[C]", "Derived", colr=GREEN)
R_PBT = fin("PBT", [None, None, None, f"=Derivations!C{R_PBTD}"], "[C]", "Derived", colr=GREEN)
R_PAT = fin("PAT", [f"={I('pat23')}", f"={I('pat24')}", f"={I('pat25')}", f"={I('pat26')}"], "[R]", "", colr=GREEN, bold=True)
R_PATM= fin("PAT margin", [None, f"=C{R_PAT}/C{R_REV}", f"=D{R_PAT}/D{R_REV}", f"=E{R_PAT}/E{R_REV}"],
            "[C]", "FY23 was a loss", fmt=PCT, bold=True)
R_EPSY= fin("EPS on post-issue base (₹)", [None, f"=C{R_PAT}/'IPO Snapshot'!$C${SNAP['post']}",
            f"=D{R_PAT}/'IPO Snapshot'!$C${SNAP['post']}", f"=E{R_PAT}/'IPO Snapshot'!$C${SNAP['post']}"],
            "[C]", "Post-issue share count held constant to show the earnings trajectory", fmt=RS)

r += 1
sub(ws, r, "COMPOUND GROWTH — the most important table in this workbook", 7); r += 1
hdr(ws, r, ["Metric", "From", "To", "Years", "CAGR", "Tag", "Note"]); r += 1
def cagr(label, frm, to, yrs, nt, tag="[C]"):
    global r
    put(ws, r, 1, label, wrap=True, bold=True)
    put(ws, r, 2, frm, fmt=CR); put(ws, r, 3, to, fmt=CR)
    put(ws, r, 4, yrs, fmt='#,##0', align="center")
    put(ws, r, 5, f"=(C{r}/B{r})^(1/D{r})-1", fmt=PCT, bold=True, fill=fill_caut)
    put(ws, r, 6, tag, size=9, bold=True, color=GREY, align="center")
    put(ws, r, 7, nt, wrap=True, size=9, color=GREY); r += 1

cagr("Revenue from operations", f"=B{R_REV}", f"=E{R_REV}", 3, "FY23 to FY26. Good, but ordinary.")
cagr("EBITDA", f"=B{R_EB}", f"=E{R_EB}", 3, "FY23 to FY26. 3.5x FASTER THAN REVENUE — the whole story.")
cagr("PAT", f"=C{R_PAT}", f"=E{R_PAT}", 2, "FY24 to FY26 only. FY23 was a loss, so a CAGR from it is undefined.")
r += 1
put(ws, r, 1, "EBITDA CAGR / Revenue CAGR", bold=True)
put(ws, r, 5, f"=E{r-3}/E{r-4}", fmt='0.0"x"', bold=True, fill=fill_caut)
put(ws, r, 7, "Profit growth here is overwhelmingly a MARGIN story, and margin stories are finite by construction. Margin cannot expand from 49.6% to 150%.", wrap=True, size=9, color=GREY)
ws.merge_cells(start_row=r, start_column=7, end_row=r+1, end_column=7)
r += 3

sub(ws, r, "BALANCE SHEET", 7); r += 1
hdr(ws, r, ["₹ crore", "FY24", "FY25", "FY26", "", "Tag", "Note"]); r += 1
def bs(label, vals, tag, nt, fmt=CR, bold=False, colr=GREEN):
    global r
    put(ws, r, 1, label, wrap=True, bold=bold)
    for i, v in enumerate(vals):
        if v is None:
            put(ws, r, 2+i, "n/a", color=GREY, align="center")
        else:
            put(ws, r, 2+i, v, fmt=fmt, color=colr, bold=bold)
    put(ws, r, 5, "")
    put(ws, r, 6, tag, size=9, bold=True, color=GREY, align="center")
    put(ws, r, 7, nt, wrap=True, size=9, color=GREY)
    rr = r; r += 1; return rr

R_BOR = bs("Secured borrowings", [f"={I('bor24')}", f"={I('bor25')}", f"={I('bor26')}"], "[R]", "Down 63% in two years while the business grew 30% p.a.", bold=True)
bs("Total financial indebtedness", [None, None, f"={I('debt26')}"], "[R]", "")
R_NW = bs("Net worth (closing, derived)", [None, None, f"={I('bor26')}/{I('de26')}"], "[C]", "Secured borrowings / reported D/E of 0.08", colr=BLACK)
R_NWA = bs("Net worth (average, derived)", [None, None, f"={I('pat26')}/{I('roe')}"], "[C]", "PAT / reported ROE of 25.12%", colr=BLACK)
bs("Debt / equity", [f"={I('de24')}", None, f"={I('de26')}"], "[R]", "0.66 to 0.08", fmt=MULT2)
bs("Contingent liabilities (% of net worth)", [None, None, f"={I('cl_nw')}"], "[R]", "Was 30.50% two years prior — improving", fmt=PCT2)
bs("Contingent liabilities (₹ cr, derived)", [None, None, f"={I('cl_nw')}*D{R_NW}"], "[C]", "", colr=BLACK)
bs("Unbilled revenue", [None, None, f"={I('unbill')}"], "[R]", "13.4% of FY26 revenue — the earnings-quality flag")
bs("Current assets hypothecated", [None, None, f"={I('hypo')}"], "[R]", "Normal for working-capital facilities, but little unpledged collateral remains", fmt=PCT2)
bs("Total assets / cash / inventory", [None, None, None], "[NA]", "NOT AVAILABLE — could not be obtained")

r += 1
sub(ws, r, "POST-IPO BALANCE SHEET — the dilution nobody mentions", 7); r += 1
R_NWP = r
put(ws, r, 1, "Net worth post-IPO (before issue expenses)", bold=True)
put(ws, r, 2, f"=D{R_NW}+{I('issue')}", fmt=CR, bold=True)
put(ws, r, 6, "[C]", size=9, bold=True, color=GREY, align="center")
put(ws, r, 7, "₹536 cr existing plus the ₹720 cr raise", wrap=True, size=9, color=GREY); r += 1
put(ws, r, 1, "ROE, pre-IPO (reported)", bold=True)
put(ws, r, 2, f"={I('roe')}", fmt=PCT, color=GREEN, bold=True)
put(ws, r, 6, "[R]", size=9, bold=True, color=GREY, align="center"); r += 1
R_ROEP = r
put(ws, r, 1, "ROE, post-IPO pro forma", bold=True, )
put(ws, r, 2, f"={I('pat26')}/B{R_NWP}", fmt=PCT, bold=True, fill=fill_warn)
put(ws, r, 6, "[C]", size=9, bold=True, color=GREY, align="center")
put(ws, r, 7, "The headline 25% ROE will not exist by the December 2026 quarter. It falls to under 10% the moment the money lands, and stays there until the ₹576 cr earns a return.",
    wrap=True, size=9, color=GREY)
ws.merge_cells(start_row=r, start_column=7, end_row=r+1, end_column=7); r += 3

sub(ws, r, "CASH FLOW", 7); r += 1
hdr(ws, r, ["₹ crore", "FY24", "FY25", "FY26", "", "Tag", "Note"]); r += 1
for lab in ["Cash flow from operations (CFO)", "Capital expenditure", "Free cash flow", "CFO / PAT", "FCF / PAT"]:
    put(ws, r, 1, lab, bold=True)
    for cc in range(2, 5):
        put(ws, r, cc, "NOT AVAILABLE", color=GREY, align="center", size=9, fill=fill_warn)
    put(ws, r, 6, "[NA]", size=9, bold=True, color="FFB0392B", align="center")
    r += 1
r += 1
put(ws, r, 1, "The entire cash flow statement is unavailable. I will not estimate it — this is exactly where fabrication would be most tempting and most harmful. What can be said indirectly:  SUPPORTIVE — borrowings fell ₹72.52 cr over two years while the business grew; debt reduction of that size funded internally implies real operating cash generation.  CAUTIONARY — 79-day DSO plus ₹63.39 cr unbilled means roughly ₹165 cr tied up, about 1.4x FY26 PAT; growth here consumes cash before it returns any.  STRUCTURAL — with capex funded from the IPO, FCF will almost certainly be deeply negative in FY27–FY28 by design. That is appropriate for the strategy, not a defect, but expect no FCF support for the valuation during the build.",
    wrap=True, border=False, size=9, color=GREY)
ws.merge_cells(start_row=r, start_column=1, end_row=r+4, end_column=7)

FIN = {"rev": R_REV, "eb": R_EB, "pat": R_PAT, "nw": R_NW, "nwp": R_NWP, "bor": R_BOR, "nwa": R_NWA}

# ================================================================ 7. VALUATION
ws = wb.create_sheet("Valuation")
widths(ws, {"A":34,"B":16,"C":16,"D":16,"E":8,"F":48})
title(ws, 1, "Valuation", 6)
note(ws, 2, "Change the price in the yellow cell below and every multiple on this sheet, plus the margin-of-safety grid on 'Fair Value', recalculates.", 6)
r = 4
sub(ws, r, "PRICE DRIVER", 6); r += 1
put(ws, r, 1, "Price under test (₹ per share)", bold=True)
R_PXT = r
put(ws, r, 2, f"={I('price_hi')}", fmt=RS0, bold=True, fill=fill_key, size=12)
put(ws, r, 3, "<- change this", size=9, italic=True, color=GREY, border=False)
put(ws, r, 6, "Defaults to the upper band. Try ₹408 for the lower band, or any secondary-market price.", wrap=True, size=9, color=GREY)
r += 2

hdr(ws, r, ["Metric", "At ₹408 (lower)", "At ₹429 (upper)", "At price under test", "Tag", "Note"]); r += 1
def val(label, lo, hi, tst, tag, nt, fmt=MULT, bold=False, fill=None):
    global r
    put(ws, r, 1, label, wrap=True, bold=bold)
    put(ws, r, 2, lo, fmt=fmt, bold=bold)
    put(ws, r, 3, hi, fmt=fmt, bold=bold)
    put(ws, r, 4, tst, fmt=fmt, bold=bold, fill=fill or fill_band)
    put(ws, r, 5, tag, size=9, bold=True, color=GREY, align="center")
    put(ws, r, 6, nt, wrap=True, size=9, color=GREY)
    rr = r; r += 1; return rr

SP = "'IPO Snapshot'!"
R_VSH = val("Post-issue shares (crore)",
    f"={SP}B{SNAP['post']}", f"={SP}C{SNAP['post']}",
    f"={SP}$B${SNAP['pre']}+{I('issue')}/$B${R_PXT}", "[C]", "Pre-issue count plus ₹720 cr / price", fmt='#,##0.00')
R_VMC = val("Market capitalisation (₹ cr)",
    f"={SP}B{SNAP['mcap']}", f"={SP}C{SNAP['mcap']}", f"=D{R_VSH}*$B${R_PXT}",
    "[C]", "The ₹429 figure reproduces the reported ₹5,028 cr", fmt='#,##0', bold=True)
R_VEV = val("Enterprise value (₹ cr)",
    f"=B{R_VMC}+{I('debt26')}", f"=C{R_VMC}+{I('debt26')}", f"=D{R_VMC}+{I('debt26')}",
    "[C]", "Understates by the cash balance, which is [NA]", fmt='#,##0')
R_VEPS= val("FY26 EPS (₹)",
    f"={I('pat26')}/B{R_VSH}", f"={I('pat26')}/C{R_VSH}", f"={I('pat26')}/D{R_VSH}", "[C]", "", fmt=RS)
r += 1
sub(ws, r, "MULTIPLES", 6); r += 1
R_VPE = val("P / E (FY26)", f"={I('price_lo')}/B{R_VEPS}", f"={I('price_hi')}/C{R_VEPS}", f"=$B${R_PXT}/D{R_VEPS}",
    "[C]", "Reported as 41.61x at the upper band — reproduced exactly", bold=True, fill=fill_caut)
R_VEVE= val("EV / EBITDA (FY26)", f"=B{R_VEV}/{I('eb26')}", f"=C{R_VEV}/{I('eb26')}", f"=D{R_VEV}/{I('eb26')}",
    "[C]", "THE MORE RELIABLE ANCHOR — sits above the depreciation line, so it is not contaminated by the timing of asset deployment", bold=True, fill=fill_caut)
val("EV / Sales (FY26)", f"=B{R_VEV}/{I('rev26')}", f"=C{R_VEV}/{I('rev26')}", f"=D{R_VEV}/{I('rev26')}", "[C]", "")
val("P / Sales (FY26)", f"=B{R_VMC}/{I('rev26')}", f"=C{R_VMC}/{I('rev26')}", f"=D{R_VMC}/{I('rev26')}", "[C]", "")
val("P / B (post-money)", f"=B{R_VMC}/Financials!$B${FIN['nwp']}", f"=C{R_VMC}/Financials!$B${FIN['nwp']}",
    f"=D{R_VMC}/Financials!$B${FIN['nwp']}", "[C]", "Post-money book = ₹536 cr existing + ₹720 cr raise")
val("PEG (vs revenue CAGR)", f"=B{R_VPE}/(Financials!$E$19*100)", f"=C{R_VPE}/(Financials!$E$19*100)",
    f"=D{R_VPE}/(Financials!$E$19*100)", "[C]",
    "Against REVENUE growth of 30.6%. Against FY26 earnings growth of 117% the PEG looks trivially cheap — but that growth is arithmetically unrepeatable, so that PEG is a mirage.", fmt=NUM)
val("FCF yield", "n/a", "n/a", "n/a", "[NA]", "Free cash flow unavailable, and negative through the build", fmt=None)

r += 1
sub(ws, r, "AGAINST THE PEER — E2E Networks, the only listed comparable", 6); r += 1
hdr(ws, r, ["Metric", "ESDS at ₹429", "E2E Networks", "ESDS as % of peer", "Tag", "Note"]); r += 1
def pcmp(label, esds, e2e, nt, fmt=MULT, better=""):
    global r
    put(ws, r, 1, label, wrap=True)
    put(ws, r, 2, esds, fmt=fmt, bold=True)
    put(ws, r, 3, e2e, fmt=fmt, color=GREEN)
    put(ws, r, 4, f"=IFERROR(B{r}/C{r},\"n/a\")", fmt=PCT)
    put(ws, r, 5, better, size=9, bold=True, color=GREY, align="center")
    put(ws, r, 6, nt, wrap=True, size=9, color=GREY); r += 1

R_E2EEV = r
put(ws, r, 1, "E2E annualised revenue (₹ cr)"); put(ws, r, 2, f"={I('e2e_qr')}*4", fmt=CR)
put(ws, r, 3, "E2E annualised EBITDA"); put(ws, r, 4, f"={I('e2e_qe')}*4", fmt=CR)
put(ws, r, 5, "PAT"); put(ws, r, 6, f"={I('e2e_qp')}*4", fmt=CR)
r += 1
note(ws, r, "Annualising Q1 FY27 is mine [C] and assumes the run-rate holds — a simplification given E2E's trajectory. It is used only to show that even on a forward basis the gap does not close.", 6); r += 1
hdr(ws, r, ["Metric", "ESDS at ₹429", "E2E Networks", "ESDS as % of peer", "Tag", "Note"]); r += 1
pcmp("P / E", f"=C{R_VPE}", f"={I('e2e_pe')}", "E2E on trailing earnings. Forward is ~72x.")
pcmp("P / E, forward (annualised)", f"=C{R_VPE}", f"={I('e2e_mc')}/({I('e2e_qp')}*4)", "The fairer comparison")
pcmp("EV / EBITDA", f"=C{R_VEVE}", f"={I('e2e_ev')}", "")
pcmp("EV / EBITDA, forward", f"=C{R_VEVE}", f"={I('e2e_mc')}/({I('e2e_qe')}*4)", "The gap narrows but does not close")
pcmp("P / B", f"=C{R_VMC}/Financials!$B${FIN['nwp']}", f"={I('e2e_pb')}", "")
pcmp("EBITDA margin", f"=Financials!E{R_EBM}", f"={I('e2e_qe')}/{I('e2e_qr')}", "E2E structurally higher on GPU mix", fmt=PCT)
pcmp("Return on equity", f"={I('roe')}", f"={I('e2e_roe')}", "ESDS DECISIVELY BETTER", fmt=PCT, better="ESDS")
pcmp("Return on capital employed", f"={I('roce')}", f"={I('e2e_roce')}", "ESDS DECISIVELY BETTER", fmt=PCT, better="ESDS")
pcmp("Debt / equity", f"={I('de26')}", f"={I('e2e_de')}", "Both near debt-free", fmt=MULT2)
pcmp("Receivable days", f"={I('dso')}", f"={I('e2e_dso')}", "ESDS MATERIALLY WORSE", fmt='#,##0', better="E2E")
pcmp("Market capitalisation (₹ cr)", f"=C{R_VMC}", f"={I('e2e_mc')}", "", fmt='#,##0')

r += 1
put(ws, r, 1, "WHY I DECLINE TO CONCLUDE 'UNDERVALUED' FROM THIS", bold=True, color="FFB0392B", border=False); r += 1
put(ws, r, 1, "E2E trades at 404x trailing earnings. A comparison against a stock priced on an AI narrative sets a SENTIMENT ceiling, not a fair value. The brief specifically warns against using a convenient peer to make a valuation look attractive, and anchoring fair value to E2E would do exactly that. E2E is also a genuinely different business — it has pivoted hard into GPU/AI compute, which carries 75% EBITDA margins and a different multiple entirely. The honest reading: relative valuation is supportive of listing-day sentiment, and close to uninformative about intrinsic value. ON ABSOLUTE MERIT, 41.6x trailing earnings, 21.9x EV/EBITDA and 10.6x sales for a ₹472 crore capital-intensive business is A FULL PRICE.",
    wrap=True, border=False, size=9, color=GREY)
ws.merge_cells(start_row=r, start_column=1, end_row=r+4, end_column=6)

VAL = {"px": R_PXT, "sh": R_VSH, "mc": R_VMC, "pe": R_VPE, "eve": R_VEVE, "eps": R_VEPS}

# ================================================================ 8. SCENARIOS
ws = wb.create_sheet("Scenarios")
widths(ws, {"A":38,"B":16,"C":16,"D":16,"E":8,"F":46})
title(ws, 1, "Scenario valuation — FY29", 6)
note(ws, 2, "All three are MY models [C]. Yellow cells are assumptions — change them and the fair value, returns and probability-weighted value all update. These are not forecasts. Common assumption: no further equity dilution, which is itself optimistic since a second capacity doubling would need more capital.", 6)
hdr(ws, 3, ["Assumption / output", "Bear", "Base", "Bull", "Unit", "Rationale"])
r = 4
def sc(label, b, m, u, unit, rat, fmt=CR, key=False, bold=False, fill=None):
    global r
    put(ws, r, 1, label, wrap=True, bold=bold)
    fl = fill_key if key else fill
    for i, v in enumerate([b, m, u]):
        put(ws, r, 2 + i, v, fmt=fmt, fill=fl, bold=bold,
            color=(BLUE if key else BLACK))
    put(ws, r, 5, unit, size=9, color=GREY, align="center")
    put(ws, r, 6, rat, wrap=True, size=9, color=GREY)
    rr = r; r += 1; return rr

sub(ws, r, "ASSUMPTIONS — challenge these", 6); r += 1
R_SG = sc("Revenue CAGR, FY26 to FY29", 0.12, 0.22, 0.32, "%", "Bear: new capacity fills slowly, enterprise price war, a top-3 account lost.  Base: capacity doubles and fills over ~3 years, tracking the ~20% industry rate.  Bull: fills fast, AI/GPU and sovereign-cloud mandates accelerate.", fmt=PCT, key=True)
R_SM = sc("EBITDA margin, FY29", 0.40, 0.47, 0.52, "%", "Bear: ~₹105 cr of fresh D&A lands on a half-empty build.  Base: slight compression from 49.6% as new assets carry a full charge.  Bull: utilisation offsets depreciation; mix shifts to managed services and SaaS.", fmt=PCT, key=True)
R_SP = sc("PAT margin, FY29", 0.14, 0.20, 0.24, "%", "Follows the EBITDA margin, net of the new depreciation wave and a normal tax charge.", fmt=PCT, key=True)
R_SX = sc("Exit P/E multiple", 22, 30, 40, "x", "Bear: de-rated to an infrastructure multiple.  Base: a quality-growth infrastructure multiple.  Bull: re-rated toward the AI/cloud cohort.", fmt=MULT, key=True)
r += 1
sub(ws, r, "OUTPUTS — all formulas", 6); r += 1
R_SREV = sc("FY29 revenue (₹ cr)", f"={I('rev26')}*(1+B{R_SG})^{I('horizon')}", f"={I('rev26')}*(1+C{R_SG})^{I('horizon')}",
            f"={I('rev26')}*(1+D{R_SG})^{I('horizon')}", "₹ cr", "FY26 revenue compounded at the scenario CAGR", fmt='#,##0')
R_SEB  = sc("FY29 EBITDA (₹ cr)", f"=B{R_SREV}*B{R_SM}", f"=C{R_SREV}*C{R_SM}", f"=D{R_SREV}*D{R_SM}", "₹ cr", "", fmt='#,##0')
R_SPAT = sc("FY29 PAT (₹ cr)", f"=B{R_SREV}*B{R_SP}", f"=C{R_SREV}*C{R_SP}", f"=D{R_SREV}*D{R_SP}", "₹ cr", "", fmt='#,##0')
R_SEPS = sc("FY29 EPS (₹)", f"=B{R_SPAT}/'IPO Snapshot'!$C${SNAP['post']}", f"=C{R_SPAT}/'IPO Snapshot'!$C${SNAP['post']}",
            f"=D{R_SPAT}/'IPO Snapshot'!$C${SNAP['post']}", "₹", "Post-issue share count held constant", fmt=RS)
R_SMC  = sc("FY29 market cap (₹ cr)", f"=B{R_SPAT}*B{R_SX}", f"=C{R_SPAT}*C{R_SX}", f"=D{R_SPAT}*D{R_SX}", "₹ cr", "", fmt='#,##0')
R_SVAL = sc("FY29 value per share (₹)", f"=B{R_SEPS}*B{R_SX}", f"=C{R_SEPS}*C{R_SX}", f"=D{R_SEPS}*D{R_SX}", "₹",
            "", fmt=RS0, bold=True, fill=fill_band)
R_SPV  = sc("Present value today (₹)", f"=B{R_SVAL}/(1+{I('disc')})^{I('horizon')}", f"=C{R_SVAL}/(1+{I('disc')})^{I('horizon')}",
            f"=D{R_SVAL}/(1+{I('disc')})^{I('horizon')}", "₹", "Discounted at 14%", fmt=RS0, bold=True, fill=fill_band)
r += 1
sub(ws, r, "RETURNS FROM THE PRICE UNDER TEST", 6); r += 1
R_SRET = sc("Total return over 3 years", f"=B{R_SVAL}/Valuation!$B${VAL['px']}-1", f"=C{R_SVAL}/Valuation!$B${VAL['px']}-1",
            f"=D{R_SVAL}/Valuation!$B${VAL['px']}-1", "%", "Against the price on the Valuation tab", fmt=PCT, bold=True)
R_SANN = sc("Annualised return", f"=(1+B{R_SRET})^(1/{I('horizon')})-1", f"=(1+C{R_SRET})^(1/{I('horizon')})-1",
            f"=(1+D{R_SRET})^(1/{I('horizon')})-1", "%", "", fmt=PCT, bold=True, fill=fill_caut)
r += 1
put(ws, r, 1, "Probability weight", bold=True)
for i, k in enumerate(["p_bear", "p_base", "p_bull"]):
    put(ws, r, 2 + i, f"={I(k)}", fmt=PCT, color=GREEN, fill=fill_key)
put(ws, r, 5, "%", size=9, color=GREY, align="center")
put(ws, r, 6, "My judgment. Change on the Inputs tab.", wrap=True, size=9, color=GREY)
R_SW = r; r += 1
R_SPW = r
put(ws, r, 1, "PROBABILITY-WEIGHTED VALUE (₹/share)", bold=True, size=11)
put(ws, r, 2, f"=SUMPRODUCT(B{R_SPV}:D{R_SPV},B{R_SW}:D{R_SW})", fmt=RS0, bold=True, size=12, fill=fill_caut)
put(ws, r, 6, "Feeds the Fair Value tab", wrap=True, size=9, color=GREY)
r += 2
put(ws, r, 1, "READ THE BASE CASE CAREFULLY. It returns under 1% per annum over three years from ₹429. That is not a prediction — it is what the arithmetic says when reasonable, industry-consistent assumptions are plugged in. The IPO price already discounts the base case. The bull case pays well; the bear case is brutal. This is a wide, right-skewed distribution priced near the middle.",
    wrap=True, border=False, size=10, bold=True)
ws.merge_cells(start_row=r, start_column=1, end_row=r+2, end_column=6)

SC = {"pw": R_SPW, "pv": R_SPV, "ann": R_SANN}

# ================================================================ 9. FAIR VALUE
ws = wb.create_sheet("Fair Value")
widths(ws, {"A":38,"B":18,"C":18,"D":18,"E":8,"F":46})
title(ws, 1, "Fair value and margin of safety", 6)
r = 3
sub(ws, r, "METHODS — used and rejected", 6); r += 1
hdr(ws, r, ["Method", "Used?", "", "", "", "Rationale"]); r += 1
for m, u, why in [
    ("EV / EBITDA", "PRIMARY", "Sits above the depreciation line — essential when a capex wave is about to distort reported earnings"),
    ("Scenario model", "PRIMARY", "Explicit assumptions, discounted at 14%. See the Scenarios tab."),
    ("P / E", "Secondary", "Standard, but the FY26 base is flattered by low legacy depreciation"),
    ("P / Sales", "Cross-check", "Useful given margin uncertainty"),
    ("P / B", "Limited", "Post-money book is distorted by the raise itself"),
    ("Full DCF", "REJECTED", "Requires CFO and capex, both [NA]. Building one would mean inventing the inputs."),
]:
    put(ws, r, 1, m, bold=True)
    put(ws, r, 2, u, align="center", bold=True,
        fill=(fill_warn if u == "REJECTED" else fill_ok if u == "PRIMARY" else None))
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
    for cc in range(3, 6): ws.cell(row=r, column=cc).border = box
    put(ws, r, 6, why, wrap=True, size=9, color=GREY); r += 1

r += 1
sub(ws, r, "TRIANGULATION", 6); r += 1
hdr(ws, r, ["Method", "Assumption", "Fair value (₹/sh)", "", "Tag", "Note"]); r += 1
R_T0 = r
def tri(label, assump, formula, nt):
    global r
    put(ws, r, 1, label, wrap=True)
    put(ws, r, 2, assump, wrap=True, size=9)
    put(ws, r, 3, formula, fmt=RS0, bold=True)
    put(ws, r, 4, "")
    put(ws, r, 5, "[C]", size=9, bold=True, color=GREY, align="center")
    put(ws, r, 6, nt, wrap=True, size=9, color=GREY); r += 1

tri("Scenario model, weighted", "25 / 50 / 25", f"=Scenarios!B{SC['pw']}", "From the Scenarios tab")
tri("P/E on FY26 earnings", "35x fair multiple", f"=35*Valuation!C{VAL['eps']}", "A fair multiple for a 25–30% grower with these risks")
tri("P/E on FY27 estimate", "35x, PAT ~₹150 cr", f"=35*150/'IPO Snapshot'!$C${SNAP['post']}", "FY27 PAT estimate is mine and unverified")
tri("EV/EBITDA on FY27 estimate", "18x, EBITDA ~₹300 cr", f"=(18*300-{I('debt26')})/'IPO Snapshot'!$C${SNAP['post']}", "Less net debt")
tri("P/Sales cross-check", "8x FY26 revenue", f"=8*{I('rev26')}/'IPO Snapshot'!$C${SNAP['post']}", "")
R_T1 = r - 1

r += 1
R_FLO = r
put(ws, r, 1, "Fair value — low end", bold=True)
put(ws, r, 3, f"=MIN(C{R_T0}:C{R_T1})", fmt=RS0, bold=True, fill=fill_band)
put(ws, r, 6, "The width of this range is honest, not evasive — it reflects genuine uncertainty about the FY27 depreciation charge and the utilisation ramp, neither of which is disclosed.", wrap=True, size=9, color=GREY)
ws.merge_cells(start_row=r, start_column=6, end_row=r+2, end_column=6); r += 1
R_FHI = r
put(ws, r, 1, "Fair value — high end", bold=True)
put(ws, r, 3, f"=MAX(C{R_T0}:C{R_T1})", fmt=RS0, bold=True, fill=fill_band); r += 1
R_FMID = r
put(ws, r, 1, "FAIR VALUE — MIDPOINT", bold=True, size=11)
put(ws, r, 3, f"=AVERAGE(C{R_FLO},C{R_FHI})", fmt=RS0, bold=True, size=12, fill=fill_caut); r += 2

sub(ws, r, "MARGIN OF SAFETY  =  (Fair value − IPO price) / Fair value", 6); r += 1
hdr(ws, r, ["Against", "At ₹408 (lower)", "At ₹429 (upper)", "At price under test", "Tag", "Note"]); r += 1
for lab, ref in [("Low end", f"C{R_FLO}"), ("MIDPOINT", f"C{R_FMID}"), ("High end", f"C{R_FHI}")]:
    bold = lab == "MIDPOINT"
    put(ws, r, 1, lab, bold=bold)
    put(ws, r, 2, f"=(${ref}-{I('price_lo')})/${ref}", fmt=PCT, bold=bold,
        fill=(fill_caut if bold else None))
    put(ws, r, 3, f"=(${ref}-{I('price_hi')})/${ref}", fmt=PCT, bold=bold,
        fill=(fill_caut if bold else None))
    put(ws, r, 4, f"=(${ref}-Valuation!$B${VAL['px']})/${ref}", fmt=PCT, bold=bold,
        fill=(fill_caut if bold else None))
    put(ws, r, 5, "[C]", size=9, bold=True, color=GREY, align="center")
    if bold:
        put(ws, r, 6, "NEGATIVE AT BOTH ENDS OF THE BAND. There is no meaningful margin of safety.", wrap=True, size=9, color="FFB0392B", bold=True)
    r += 1

r += 1
put(ws, r, 1, "This is the central finding of the valuation work, and it is what separates the listing verdict from the investment verdict. The IPO may well list at a premium — sentiment, anchor support and the absence of an OFS all point that way. But a listing pop is a transfer from the next buyer, not a return generated by the business. For a three-to-five year holder, the entry price leaves nothing in reserve.",
    wrap=True, border=False, size=10, bold=True)
ws.merge_cells(start_row=r, start_column=1, end_row=r+2, end_column=6)
FV = {"mid": R_FMID, "lo": R_FLO, "hi": R_FHI, "mos_mid": R_FMID}
R_MOS_MID = r - 4  # midpoint MoS row

# ================================================================ 10. SCORES
ws = wb.create_sheet("Scores")
widths(ws, {"A":34,"B":10,"C":10,"D":10,"E":8,"F":60})
title(ws, 1, "Scores — moat, management, business quality, and the IPO scorecard", 6)
note(ws, 2, "Scores out of 10, with the evidence beside each. Totals are AVERAGE formulas — change a score and the total updates.", 6)
r = 3
def scoreblock(heading, rows, note_text=None, weighted=False):
    global r
    sub(ws, r, heading, 6); r += 1
    hdr(ws, r, ["Factor", "Score /10", "", "", "", "Evidence"]); r += 1
    first = r
    for lab, sc_, ev in rows:
        put(ws, r, 1, lab, wrap=True)
        c = put(ws, r, 2, sc_, fmt='0.0', color=BLUE, align="center", bold=True)
        c.fill = (fill_warn if sc_ <= 4 else fill_ok if sc_ >= 7 else fill_caut)
        for cc in range(3, 6): ws.cell(row=r, column=cc).border = box
        put(ws, r, 6, ev, wrap=True, size=9, color=GREY); r += 1
    last = r - 1
    put(ws, r, 1, "OVERALL", bold=True)
    put(ws, r, 2, f"=AVERAGE(B{first}:B{last})", fmt='0.0', bold=True, align="center", size=11, fill=fill_caut)
    for cc in range(3, 6): ws.cell(row=r, column=cc).border = box
    if note_text:
        put(ws, r, 6, note_text, wrap=True, size=9, color=GREY)
    r += 2
    return first, last

scoreblock("MOAT — classification: WEAK-TO-MODERATE, narrow but real", [
 ("Regulatory barriers", 7, "THE STRONGEST PILLAR. Data-localisation and sovereign-cloud rules structurally exclude offshore hyperscalers from government/BFSI workloads = 44.9% of revenue. Compliance credentials take years to build."),
 ("Switching costs", 7, "Migrating a production BFSI or government workload is expensive, risky and requires re-certification. Genuinely sticky once embedded."),
 ("Customer relationships", 6, "1,300+ clients over 21 years; 99.995% uptime is a real, evidenced credential in a trust-driven purchase."),
 ("Intellectual property", 5, "Patents granted in India AND the United States for vertical auto-scaling. Real and verifiable — but a feature, not a platform."),
 ("Technology", 5, "SWARAJ/eNlight is differentiated; not decisively ahead of well-funded rivals."),
 ("Brand", 4, "Recognised in the Indian mid-market and government; negligible outside it."),
 ("Distribution", 4, "Direct enterprise sales, five-city footprint. No structural distribution edge."),
 ("Access to capital", 4, "Improves materially post-IPO, but remains far below CtrlS / Nxtra / Yotta."),
 ("Cost advantage", 3, "No purchasing scale; USD-imported hardware; higher unit costs than larger rivals."),
 ("Scale", 2, "THE CRITICAL WEAKNESS. ~7 MW against competitors deploying hundreds. Sub-scale in procurement, power negotiation and financing."),
 ("Network effects", 2, "Essentially none — cloud infrastructure has weak network effects."),
], "Narrow but genuine regulatory and switching-cost moat around sovereign/BFSI. Outside that perimeter — the 55.09% of revenue that is general enterprise — ESDS has essentially no moat and is a price-taker.")

scoreblock("MANAGEMENT QUALITY", [
 ("Financial discipline", 8, "D/E from 0.66 to 0.08 while growing 30% p.a. The single most impressive verifiable fact about this management team."),
 ("Shareholder treatment", 8, "ZERO OFS. Promoters sell nothing. 100% of proceeds to the company. In the Indian IPO market this is genuinely uncommon."),
 ("Capital allocation", 7, "Turned a loss-making business into 32.78% ROCE; deleveraged 63% in two years; declined to IPO in 2021–22 at a weak valuation and waited until PAT was 5.4x higher."),
 ("Execution", 7, "Revenue 30.6% CAGR; EBITDA margin 12.3% to 49.6%; uptime at least 99.995%; 21 years of continuous operation."),
 ("Track record", 7, "Piyush Somani has run this since 2005; built a patented platform from Nashik."),
 ("Transparency", 5, "Standard RHP disclosure. CAPACITY UTILISATION — the key metric — is not disclosed. Guidance cites the top of the industry growth range (20.70% vs a 13.6–20.1% third-party spread)."),
 ("Corporate governance", 5, "No adverse findings, but my verification is FY22-vintage and incomplete. Scored as UNVERIFIED, not as clean."),
], "Above average. Genuinely strong on capital discipline and alignment; unverified on governance; opaque on the one metric that matters most.")

scoreblock("BUSINESS QUALITY", [
 ("Balance sheet", 9, "D/E 0.08; interest coverage ~35x; net-cash post-IPO."),
 ("Growth", 8, "30.6% revenue CAGR; secular, legislation-backed demand."),
 ("Profitability", 8, "49.6% EBITDA, 25.6% PAT, 32.78% ROCE — genuinely strong."),
 ("Industry attractiveness", 8, "Secular growth with a legislated demand floor — but consolidating around capital."),
 ("Management quality", 7, "Strong capital discipline and alignment."),
 ("Governance", 5, "No adverse findings; verification absent."),
 ("Cash generation", 4, "[NA] AND HEAVILY PENALISED FOR IT. DSO 79 days; unbilled 13.4%; FCF negative by design during the build."),
 ("Competitive advantage", 4, "Narrow regulatory/switching moat; structurally sub-scale."),
], "A good business with two real structural constraints: scale and working capital. The cash-generation score is the one most likely to be wrong in either direction — if the RHP shows CFO/PAT above 1.0x it rises to 7 and the overall to ~7.0; if CFO is below PAT it falls to 3.")

scoreblock("IPO INVESTMENT SCORECARD", [
 ("Profit growth", 9, "+788% over two years — exceptional, though unrepeatable."),
 ("Balance sheet", 9, "D/E 0.08, ~35x coverage, net-cash post-issue."),
 ("IPO structure", 9, "ZERO OFS, 100% fresh, promoters selling nothing — excellent."),
 ("Industry growth", 8, "Secular, legislation-backed; 13.6–20.1% forward CAGR estimates."),
 ("Revenue growth", 8, "30.6% CAGR over three years, verified and consistent."),
 ("Business quality", 7, "Good economics, real returns on capital, structurally sub-scale."),
 ("Management", 7, "Strong capital discipline; 21-year record; declined a cheap 2021 IPO."),
 ("Growth prospects", 7, "Capacity doubling funded; utilisation unproven."),
 ("Governance", 5, "No adverse findings; verification unavailable."),
 ("Valuation", 5, "Fair, not cheap; negative margin of safety. 'Correctly priced' — which, for an IPO, is not a compliment."),
 ("Risk", 5, "Concentrated in execution and working capital, not solvency."),
 ("Cash flow", 4, "[NA]; DSO 79 days; unbilled 13.4%; FCF negative during the build."),
 ("Competitive moat", 4, "Narrow regulatory/switching moat; scale is a structural weakness."),
], "A good business, honestly structured, at a full price.")

# ================================================================ 11. RISK
ws = wb.create_sheet("Risk Matrix")
widths(ws, {"A":34,"B":14,"C":12,"D":14,"E":58})
title(ws, 1, "Risk matrix", 5)
hdr(ws, 3, ["Risk", "Probability", "Impact", "Severity", "Evidence"])
r = 4
for rk, p, im, sev, ev in [
 ("Business — new capacity underutilised","Medium-High","High","CRITICAL","₹576 cr capex doubling 7 MW to 14–20 MW; ~₹96–115 cr of new annual D&A; utilisation [NA]"),
 ("Valuation — 41.6x embeds execution","High","High","CRITICAL","Base-case scenario returns +0.9% p.a. from ₹429; margin of safety −10%"),
 ("Competitive — structurally sub-scale","High","High","CRITICAL","~7 MW against India's multi-GW base; CtrlS/Nxtra/Yotta deploy in hundreds of MW"),
 ("Customer concentration","Medium","High","HIGH","Top client 15.93%; top 10 45.36% of FY26 revenue"),
 ("Financial — working capital","High","Medium","HIGH","DSO 79 days vs peer 25; unbilled revenue ₹63.39 cr = 13.4% of revenue"),
 ("Margin normalisation","High","Medium","HIGH","12.3% to 49.6% in three years; partly a legacy-asset artefact the IPO itself unwinds"),
 ("Technology obsolescence","Medium","High","HIGH","5–6 year server lives; GPU generations turn faster; ₹576 cr at risk of stranding"),
 ("Cybersecurity / data breach","Medium","Very High","HIGH","Explicitly disclosed. Hosts BFSI and government data — reputational loss would be terminal for the niche"),
 ("Supplier concentration","Medium","Medium","MEDIUM","Dependent on major equipment suppliers; no purchasing scale; USD-priced"),
 ("Regulatory","Low","Medium","MEDIUM","Net-positive today (localisation aids ESDS); a policy reversal would remove the moat"),
 ("Promoter / governance","Low","Medium","MEDIUM","No adverse findings, but verification [NA]; one ex-employee equity claim"),
 ("Macro / interest rates","Medium","Medium","MEDIUM","High-multiple growth stock; duration-sensitive to rate moves"),
 ("Debt","Low","Low","LOW","D/E 0.08; interest coverage ~35x; net-cash post-IPO"),
 ("Cyclicality","Low","Low","LOW","Secular, legislation-backed demand"),
]:
    fl = {"CRITICAL": fill_warn, "HIGH": fill_caut, "MEDIUM": None, "LOW": fill_ok}[sev]
    put(ws, r, 1, rk, wrap=True, bold=(sev == "CRITICAL"))
    put(ws, r, 2, p, align="center"); put(ws, r, 3, im, align="center")
    put(ws, r, 4, sev, align="center", bold=True, fill=fl)
    put(ws, r, 5, ev, wrap=True, size=9, color=GREY); r += 1

r += 1
sub(ws, r, "THE FIVE RISKS THAT ACTUALLY DECIDE THE OUTCOME", 5); r += 1
for i, t in enumerate([
 "1.  UTILISATION OF THE NEW BUILD. Everything else is secondary. ₹576 cr of equipment carrying ~₹105 cr of annual depreciation is transformative if filled and value-destructive if not. It is not disclosed and cannot be verified before applying.",
 "2.  THE VALUATION ALREADY ASSUMES SUCCESS. At 41.6x, my base case returns under 1% a year. You are not being paid to take the execution risk — you are paying for the execution to work.",
 "3.  STRUCTURAL SUB-SCALE. After spending the entire IPO, ESDS remains a sub-1% player against competitors with vastly deeper capital. Its defence is regulatory, and regulation can change.",
 "4.  WORKING CAPITAL CONSUMES GROWTH. ~₹165 cr tied in receivables and unbilled revenue — 1.4x FY26 PAT — with no cash-flow statement to size the drag.",
 "5.  THE MARGIN RAMP IS PARTLY A LEGACY-ASSET ARTEFACT. Some of the 49.6% EBITDA margin exists BECAUSE the old assets are written down. The IPO buys new assets that are not. Investors extrapolating current margins onto a doubled asset base are double-counting.",
]):
    put(ws, r, 1, t, wrap=True, border=False, size=10)
    ws.merge_cells(start_row=r, start_column=1, end_row=r+1, end_column=5)
    ws.row_dimensions[r].height = 26; r += 2

# ================================================================ 12. RED FLAGS
ws = wb.create_sheet("Red Flags")
widths(ws, {"A":36,"B":20,"C":66})
title(ws, 1, "Red-flag investigation — actively searched, not summarised from the prospectus", 3)
note(ws, 2, "Including, explicitly, what could NOT be checked. Absence of evidence is weak evidence when the primary documents were unreachable.", 3)
hdr(ws, 3, ["Flag", "Status", "Detail"])
r = 4
for fg, st, dt in [
 ("Large OFS","CLEAR — POSITIVE","ZERO OFS. 100% fresh issue."),
 ("Promoter selling","CLEAR — POSITIVE","Promoters sell nothing. They dilute from 46.06% to ~39.5% to fund capacity."),
 ("Debt defaults","None found","Borrowings fell 63% in two years."),
 ("Contingent liabilities","Improving","10.43% of net worth, down from 30.50% two years prior."),
 ("Regulatory investigations","None found","No adverse search results against the company or promoters."),
 ("Negative industry developments","None","Sector tailwind intact."),
 ("Sudden profit growth","INVESTIGATED","+788% over two years — BUT the derived effective tax rate of ~32% argues against accounting manipulation. See the Derivations tab."),
 ("Tax disputes","Disclosed, unquantified","'Ongoing legal and tax disputes' referenced in the risk factors; amounts [NA]."),
 ("Excessive IPO valuation","Full, not egregious","41.6x P/E; cheaper than the only listed peer; margin of safety negative."),
 ("Frequent equity dilution","Historically yes","Promoter under 50% pre-IPO implies extensive prior raises. Further capital likely for the next expansion."),
 ("Related-party transactions","STALE EVIDENCE","FY22 annual report: 'no materially significant related party transactions'. FY26 position [NA] — four years stale."),
 ("Asset hypothecation","CONFIRMED","96.72% of current assets pledged to lenders as at 31 Mar 2026. Normal for working-capital facilities, but little unpledged collateral remains."),
 ("Material litigation","CONFIRMED","Ex-employee R.S. Papneja claims 1% of shares (~₹50 cr at the issue m-cap) OR ₹18.48 cr cash. Status, merits and provisioning [NA]."),
 ("Customer concentration","CONFIRMED","Top 10 = 45.36% of FY26 revenue; largest single client 15.93%."),
 ("Supplier concentration","CONFIRMED","Explicitly disclosed as a risk. No purchasing scale; USD-priced hardware."),
 ("Receivables","CONFIRMED","79 days vs 25 for the listed peer."),
 ("Unbilled revenue","CONFIRMED","₹63.39 cr = 13.4% of FY26 revenue. Recognised but not yet invoiced. The trend is [NA] — check the ageing schedule in the RHP."),
 ("Unusual margin expansion","PARTLY EXPLAINED","12.3% to 49.6% in three years. ~70–80% attributable to genuine operating leverage; ~10–15% to falling interest; ~10–15% to low legacy depreciation."),
 ("Declining cash flow","CANNOT CHECK","CASH FLOW STATEMENT ENTIRELY UNAVAILABLE."),
 ("Auditor qualifications","UNVERIFIED","No s.143(12) fraud reporting in FY22. FY23–FY26 [NA]. Auditor identity and rotation history [NA]."),
 ("Promoter pledges","CANNOT CHECK","Not disclosed in any accessible source."),
 ("Subsidiary problems","CANNOT CHECK","[NA]"),
 ("Corporate governance","UNVERIFIED","No adverse findings; documentary verification absent. Board composition and compensation [NA]."),
 ("Inventory problems","Not applicable","Services business."),
]:
    fl = None
    if "POSITIVE" in st or st in ("None found", "None", "Improving", "Not applicable"): fl = fill_ok
    elif st in ("CONFIRMED", "CANNOT CHECK"): fl = fill_warn
    elif st in ("UNVERIFIED", "STALE EVIDENCE", "INVESTIGATED", "Historically yes",
                "Full, not egregious", "Disclosed, unquantified", "PARTLY EXPLAINED"): fl = fill_caut
    put(ws, r, 1, fg, wrap=True, bold=True)
    put(ws, r, 2, st, align="center", bold=True, fill=fl, size=9)
    put(ws, r, 3, dt, wrap=True, size=9, color=GREY); r += 1

r += 1
put(ws, r, 1, "NET ASSESSMENT:  no red flag rises to disqualifying. The cluster that matters is WORKING CAPITAL and STRUCTURAL SCALE, not fraud or governance. The structural positives — zero OFS, no promoter selling, genuine deleveraging, an above-statutory effective tax rate — are unusually strong for an Indian mid-cap IPO and deserve weight.",
    wrap=True, border=False, size=10, bold=True)
ws.merge_cells(start_row=r, start_column=1, end_row=r+2, end_column=3)

# ================================================================ 13. SENTIMENT
ws = wb.create_sheet("Sentiment")
widths(ws, {"A":34,"B":18,"C":18,"D":8,"E":56})
title(ws, 1, "Grey market and subscription — sentiment only, never valuation evidence", 5)
note(ws, 2, "All figures timestamped 27–28 August 2026 and highly perishable. Treat GMP and subscription as sentiment indicators, not fundamental evidence.", 5)
hdr(ws, 3, ["Indicator", "Value", "Derived", "Tag", "As at / note"])
r = 4
def sent(label, val, drv_, tag, nt, fmt=None, dfmt=None, fill=None, bold=False):
    global r
    put(ws, r, 1, label, wrap=True, bold=bold)
    put(ws, r, 2, val, fmt=fmt, bold=bold, fill=fill, color=(GREEN if isinstance(val, str) and val.startswith("=") else BLACK))
    put(ws, r, 3, drv_, fmt=dfmt, bold=bold, fill=fill)
    put(ws, r, 4, tag, size=9, bold=True, color=GREY, align="center")
    put(ws, r, 5, nt, wrap=True, size=9, color=GREY)
    rr = r; r += 1; return rr

R_GMP = sent("Grey market premium (₹/share)", f"={I('gmp')}", None, "[!]", "Sahi.com, 28 Aug 2026", fmt=RS0, fill=fill_warn, bold=True)
sent("Implied listing price", f"={I('price_hi')}+{I('gmp')}", None, "[C]", "Upper band plus GMP", fmt=RS0)
R_GMPP = sent("Implied listing gain", f"={I('gmp')}/{I('price_hi')}", None, "[C]", "NOT CREDIBLE — see the analysis below", fmt=PCT, fill=fill_warn, bold=True)
sent("Implied listing P/E", f"=({I('price_hi')}+{I('gmp')})/Valuation!C{VAL['eps']}", None, "[C]",
     "The GMP asks the market to believe ESDS should list at this multiple of FY26 earnings", fmt=MULT, fill=fill_warn)
r += 1
sent("Day 1 subscription — overall", f"={I('sub_all')}", None, "[R]", "Goodreturns, 28 Aug 2026 intra-day", fmt=MULT2)
sent("Day 1 subscription — retail", f"={I('sub_ret')}", None, "[R]", "28 Aug 2026 intra-day", fmt=MULT2)
sent("Day 1 subscription — NII / HNI", f"={I('sub_nii')}", None, "[R]", "28 Aug 2026 intra-day", fmt=MULT2)
sent("Day 1 subscription — QIB ex-anchor", f"={I('sub_qib')}", None, "[R]", "Nil. Mainboard QIB books are back-loaded to the final day, so this is uninformative rather than bearish.", fmt=MULT2)
sent("Earlier Day 1 reading", 0.12, None, "[R]", "HDFC Sky, earlier on 28 Aug — different timestamp, same day", fmt=MULT2)
r += 1
R_ANC = sent("Anchor book raised (₹ cr)", f"={I('anchor')}", None, "[R]", "Inc42, 27 Aug 2026", fmt=CR, bold=True, fill=fill_ok)
sent("Anchor as % of issue", f"={I('anchor')}/{I('issue')}", None, "[C]",
     "The full 30% permitted (60% of the 50% QIB portion) was taken — the anchor book was fully placed at the top of the band.", fmt=PCT, fill=fill_ok)
sent("Anchor allocation to mutual funds", f"={I('anch_mf')}", None, "[R]",
     "6 fund houses across 13 schemes: Motilal Oswal, Bandhan, Quant, ITI, JM Financial, Samco", fmt=PCT, fill=fill_ok)
sent("Employee quota", "n/a", None, "[NA]", "Not obtainable")

r += 1
sub(ws, r, "THE CONTRADICTION, AND HOW TO READ IT", 5); r += 1
put(ws, r, 1, "A GMP implying +77% is not consistent with a 0.40x Day-1 book. One of these signals is wrong, and it is almost certainly the GMP.",
    wrap=True, border=False, size=11, bold=True)
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5); r += 2
for t in [
 "1.  A 0.40x DAY-1 BOOK IS UNREMARKABLE. Mainboard books build back-loaded — institutions almost always bid on the final day, which is why the QIB column reads nil. Day 1 at 0.40x is not a bearish signal; it is simply an uninformative one.",
 "2.  A +77% GMP IS EXTRAORDINARY. For a ₹720 crore issue at 41.6x earnings in a sector whose only listed comparable is already at 404x, a grey market pricing 77% of instant upside asks the market to believe ESDS should list at roughly 72x FY26 earnings.",
 "3.  THE GREY MARKET FOR A MID-SIZE ISSUE IS THIN AND CHEAPLY MOVED. Small notional volumes set the quoted premium. It is not a regulated, transparent or deep market. If a genuine +77% pop were broadly expected, retail would not be at 0.54x on Day 1 — that money would already be in. The inconsistency is itself the tell.",
 "THE ANCHOR BOOK IS THE SIGNAL WORTH WEIGHTING. ₹216 crore is the full 30% permitted, placed at the top of the band, with 81.94% going to domestic mutual funds — institutions doing genuine diligence and accepting a lock-in. Six fund houses committing at ₹429 is meaningfully more informative than an anonymous grey-market quote.",
 "PRACTICAL CONCLUSION: expect a positive listing, size expectations far below +77%, and do not let the GMP influence position sizing.",
]:
    put(ws, r, 1, t, wrap=True, border=False, size=10)
    ws.merge_cells(start_row=r, start_column=1, end_row=r+1, end_column=5)
    ws.row_dimensions[r].height = 26; r += 2

sub(ws, r, "WHAT TO WATCH WHEN THE BOOK CLOSES ON 1 SEPTEMBER", 5); r += 1
hdr(ws, r, ["Pattern", "Interpretation", "", "", ""]); r += 1
for p, i2 in [
 ("QIB above 20x","Institutional conviction at ₹429 — the most meaningful confirmation available. Would support an upgrade."),
 ("QIB 3x to 10x","Adequate; consistent with a modest listing gain."),
 ("QIB below 3x","Institutions are unconvinced by the valuation. WEIGHT THIS HEAVILY AGAINST THE GMP. Would support a downgrade to Avoid at IPO price."),
 ("NII above 30x","Largely leveraged funding demand chasing the GMP — noise, not conviction."),
 ("Retail above 5x","Retail is following the GMP, which raises listing-day volatility in both directions."),
]:
    put(ws, r, 1, p, bold=True)
    put(ws, r, 2, i2, wrap=True, size=9, color=GREY)
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
    for cc in range(3, 6): ws.cell(row=r, column=cc).border = box
    r += 1
r += 1
put(ws, r, 1, "Do NOT read high subscription as evidence of good fundamentals. Subscription measures how many people want to flip an allotment, not what the business is worth. In issues with an inflated GMP the two are often inversely related — the GMP itself manufactures the oversubscription that appears to validate it.",
    wrap=True, border=False, size=10, bold=True)
ws.merge_cells(start_row=r, start_column=1, end_row=r+1, end_column=5)

SENT = {"gmp_pct": R_GMPP}

# ================================================================ 14. OTHER IPOs
ws = wb.create_sheet("Other Open IPOs")
widths(ws, {"A":30,"B":20,"C":20,"D":18,"E":20,"F":20})
title(ws, 1, "The other IPOs open in this window — comparative screen, not full diligence", 6)
note(ws, 2, "ESDS received the full treatment as the flagship opening today. This is a screen of the rest of the window. It is NOT due diligence and is not a substitute for it.", 6)
hdr(ws, 3, ["", "ESDS Software", "Lumino Industries", "Priority Jewels", "Annu Projects", "Symbiotec Pharmalab"])
r = 4
for lab, vals, fmt, bold in [
 ("Business", ["Data centres / cloud","Electrical & power infra","Jewellery","EPC — telecom, sewerage, gas","API / pharma"], None, False),
 ("Issue size (₹ cr)", [720.00, 700.00, 91.50, 175.06, 1757.00], '#,##0.00', True),
 ("Structure", ["100% FRESH — no OFS","₹500 cr fresh + ₹200 cr OFS","n/a","100% fresh","₹150 cr fresh + ₹1,607 cr OFS"], None, False),
 ("OFS as % of issue", [0.0, 200/700, None, 0.0, 1607/1757], PCT, True),
 ("Price band (₹)", ["408 – 429","78 – 82","190 – 200","94 – 99","938 – 988"], None, False),
 ("Lot size", [34, 182, 75, 151, None], '#,##0', False),
 ("Minimum investment (₹)", [14586, 14196, 15000, 14949, None], '#,##0', False),
 ("Open – close", ["28 Aug – 1 Sep","27 – 31 Aug","28 Aug – 1 Sep","25 – 28 Aug (CLOSES TODAY)","24 – 27 Aug (CLOSED)"], None, False),
 ("Listing date", ["4 Sep","3 Sep","4 Sep","2 Sep","1 Sep"], None, False),
 ("FY26 revenue (₹ cr)", [472.20, 2089.31, None, 244.59, None], '#,##0.00', False),
 ("FY25 revenue (₹ cr)", [361.30, 1946.68, None, 182.35, None], '#,##0.00', False),
 ("Revenue growth", [472.20/361.30-1, 2089.31/1946.68-1, None, 244.59/182.35-1, None], PCT, True),
 ("FY26 PAT (₹ cr)", [120.82, 160.00, None, 33.03, None], '#,##0.00', False),
 ("FY25 PAT (₹ cr)", [55.61, 124.59, None, 21.10, None], '#,##0.00', False),
 ("PAT growth", [120.82/55.61-1, 160.00/124.59-1, None, 33.03/21.10-1, None], PCT, True),
 ("PAT margin, FY26", [120.82/472.20, 160.00/2089.31, None, 33.03/244.59, None], PCT, True),
 ("Reported GMP", ["+76.9%  [!]","₹56  [!]","+18.5%","+6.4%","n/a"], None, False),
 ("Latest subscription", ["0.40x (Day 1)","n/a","n/a","2.95x (Day 2)","n/a"], None, False),
 ("Anchor book (₹ cr)", [216.00, None, None, None, 526.20], '#,##0.00', False),
]:
    put(ws, r, 1, lab, bold=True, wrap=True)
    for i, v in enumerate(vals):
        if v is None:
            put(ws, r, 2+i, "n/a", color=GREY, align="center", size=9)
        else:
            put(ws, r, 2+i, v, fmt=fmt, bold=bold, wrap=(fmt is None), size=(9 if fmt is None else 10),
                fill=(fill_ok if i == 0 and bold else None))
    r += 1
r += 1
sub(ws, r, "OBSERVATIONS", 6); r += 1
for t in [
 "LUMINO INDUSTRIES has by far the largest revenue base (₹2,089 cr) but grew only ~7.3% at a 7.7% PAT margin — a low-margin infrastructure contractor, a fundamentally different proposition from ESDS. It also carries a ₹200 cr OFS (29% of the issue), so nearly a third of subscriber money goes to selling shareholders rather than the business. Its reported GMP of ₹56 against an ₹82 upper band implies +68% and an ~₹138 listing price — I regard this as unreliable, for the same reasons as the ESDS GMP.",
 "ANNU PROJECTS shows the best growth-to-size ratio (+34.1% revenue, +56.5% PAT, 13.5% margin) on a small ₹175 cr all-fresh issue, and is the only one with a meaningful subscription reading (2.95x on Day 2). It CLOSES TODAY — no time for the diligence it would deserve.",
 "PRIORITY JEWELS — financials [NA] entirely. I will not comment on an issue whose income statement I have not seen.",
 "SYMBIOTEC PHARMALAB closed on 27 August and lists 1 September. ₹1,607 cr of its ₹1,757 cr — 91% — was OFS, the structural opposite of ESDS.",
 "ON ISSUE STRUCTURE ALONE, ESDS IS THE MOST SHAREHOLDER-ALIGNED ISSUE IN THIS WINDOW. That is one input among many, but in a month where 91%-OFS issues are being sold, it deserves saying.",
]:
    put(ws, r, 1, t, wrap=True, border=False, size=10)
    ws.merge_cells(start_row=r, start_column=1, end_row=r+1, end_column=6)
    ws.row_dimensions[r].height = 26; r += 2

# ================================================================ 15. VERDICT
ws = wb.create_sheet("Verdict")
widths(ws, {"A":30,"B":26,"C":18,"D":8,"E":58})
title(ws, 1, "Verdict and investor decision table", 5)
r = 3
sub(ws, r, "FOUR SEPARATE QUESTIONS, FOUR SEPARATE ANSWERS", 5); r += 1
hdr(ws, r, ["Question", "Verdict", "Key number", "", "Reasoning"]); r += 1
for q, v, kn, why, fl in [
 ("For listing gains", "APPLY WITH CAUTION", f"=Sentiment!B{SENT['gmp_pct']}",
  "Zero OFS, a fully-placed MF-heavy anchor book, a modest float and a defensible relative valuation support a positive debut. The +77% GMP does not. Apply for one lot; treat any premium as a windfall.", fill_caut),
 ("For a 3–5 year hold", "NEUTRAL", f"=Scenarios!C{SC['ann']}",
  "Genuine quality at a full price, with no cash-flow statement available and the decisive operating variable undisclosed. Better approached on the secondary market after two or three quarters of listed results. (Key number = base-case annualised return.)", fill_caut),
 ("At ₹408 (lower band)", "APPLY WITH CAUTION", f"=Valuation!B{VAL['pe']}",
  "About 39.8x FY26 earnings — roughly at my fair-value midpoint of ₹390. Marginally acceptable.", fill_caut),
 ("At ₹429 (upper band)", "LISTING GAINS ONLY", f"=Valuation!C{VAL['pe']}",
  "41.6x, about 10% above my midpoint. Adequate for a flip; insufficient for a hold.", fill_warn),
]:
    put(ws, r, 1, q, bold=True)
    put(ws, r, 2, v, bold=True, align="center", fill=fl)
    put(ws, r, 3, kn, fmt=('0.0"x"' if "Valuation" in kn else PCT), bold=True, align="center")
    put(ws, r, 4, "")
    put(ws, r, 5, why, wrap=True, size=9, color=GREY)
    ws.row_dimensions[r].height = 46; r += 1

r += 1
sub(ws, r, "HEADLINE NUMBERS — all live", 5); r += 1
hdr(ws, r, ["Metric", "Value", "", "Tag", "Note"]); r += 1
for lab, f, fmt, nt in [
 ("Market cap at ₹429 (₹ cr)", f"=Valuation!C{VAL['mc']}", '#,##0', "Reproduces the reported ₹5,028 cr"),
 ("P/E at ₹429", f"=Valuation!C{VAL['pe']}", MULT, "Against a peer at 404x trailing / ~72x forward"),
 ("EV/EBITDA at ₹429", f"=Valuation!C{VAL['eve']}", MULT, "The more reliable anchor — above the depreciation line"),
 ("Fair value — midpoint (₹)", f"='Fair Value'!C{FV['mid']}", RS0, "Triangulated across five methods"),
 ("Margin of safety at ₹408", f"=('Fair Value'!$C${FV['mid']}-{I('price_lo')})/'Fair Value'!$C${FV['mid']}", PCT, "NEGATIVE"),
 ("Margin of safety at ₹429", f"=('Fair Value'!$C${FV['mid']}-{I('price_hi')})/'Fair Value'!$C${FV['mid']}", PCT, "NEGATIVE"),
 ("Base-case annualised return", f"=Scenarios!C{SC['ann']}", PCT, "Over three years from the price under test"),
 ("ROE post-IPO pro forma", f"=Financials!B{FIN['nwp']+2}", PCT, "Falls from 25.1% the moment the money lands"),
 ("Derived D&A as % of revenue", f"=Derivations!C{DRV['da']+1}", PCT, "Low for five data centres — see Derivations"),
 ("New annual D&A from the capex (₹ cr)", f"=Derivations!C{DRV['newda']}", CR, "About twice the current charge"),
 ("Implied effective tax rate", f"=Derivations!C{DRV['etr']}", PCT, "ABOVE statutory — argues against accounting flattery"),
]:
    put(ws, r, 1, lab, wrap=True, bold=True)
    put(ws, r, 2, f, fmt=fmt, bold=True, align="center", fill=fill_band)
    put(ws, r, 3, ""); put(ws, r, 4, "[C]", size=9, bold=True, color=GREY, align="center")
    put(ws, r, 5, nt, wrap=True, size=9, color=GREY); r += 1

r += 1
sub(ws, r, "INVESTOR DECISION TABLE", 5); r += 1
hdr(ws, r, ["Question", "Answer", "", "", ""]); r += 1
for q, a, fl in [
 ("Is the business fundamentally strong?","YES, with a structural caveat — 32.78% ROCE and 49.6% EBITDA margin, but sub-scale at ~7 MW", fill_caut),
 ("Is revenue growth attractive?","YES — 30.6% CAGR over three years, verified and internally consistent", fill_ok),
 ("Are profits high quality?","PROBABLY — the derived ~32% effective tax rate argues against manipulation; unbilled revenue at 13.4% is a flag", fill_caut),
 ("Is cash flow healthy?","UNKNOWN — [NA]. Debt falling 63% is supportive indirect evidence; 79-day DSO is not.", fill_warn),
 ("Is debt manageable?","YES, comfortably — D/E 0.08, interest coverage ~35x, net-cash post-IPO", fill_ok),
 ("Does the company have a moat?","NARROW BUT REAL — regulatory and switching costs in sovereign/BFSI; none in general enterprise", fill_caut),
 ("Is management trustworthy?","EVIDENCE FAVOURABLE — 21-year record, zero OFS, deleveraged, declined a cheap 2021 IPO", fill_ok),
 ("Is governance satisfactory?","UNVERIFIED — no adverse findings, but my documentary evidence is FY22-vintage", fill_warn),
 ("Is the industry attractive?","YES — secular and legislation-backed; but consolidating around capital", fill_ok),
 ("Is IPO valuation reasonable?","FAIR, NOT CHEAP — 41.6x P/E, 21.9x EV/EBITDA; cheaper than the only listed peer", fill_caut),
 ("Is there sufficient margin of safety?","NO. −4.6% at ₹408, −10.0% at ₹429 against my ₹390 midpoint.", fill_warn),
 ("Main upside catalyst","The new 7 MW filling faster than expected — it drives revenue, margin and multiple simultaneously", None),
 ("Biggest risk","The same capacity sitting empty while ~₹105 cr of fresh annual depreciation lands in full", None),
 ("Listing-gain view","POSITIVE — but far below the +77% GMP, which is not credible", fill_caut),
 ("Long-term view","NEUTRAL — good business, full price, decisive variable undisclosed", fill_caut),
 ("FINAL VERDICT","APPLY / BUY WITH CAUTION — one lot for listing; revisit for investment after two quarters of disclosed results", fill_caut),
]:
    put(ws, r, 1, q, wrap=True, bold=True)
    put(ws, r, 2, a, wrap=True, fill=fl, bold=(q == "FINAL VERDICT"))
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
    for cc in range(3, 6): ws.cell(row=r, column=cc).border = box
    ws.row_dimensions[r].height = 30; r += 1

r += 1
sub(ws, r, "WHAT WOULD CHANGE THIS CONCLUSION", 5); r += 1
hdr(ws, r, ["Direction", "Trigger", "", "", ""]); r += 1
for d, trg, fl in [
 ("UPGRADE to BUY","The RHP shows CFO/PAT above 1.0x for FY25 and FY26 — this single disclosure would move business quality from 6.6 to ~7.0 and remove my largest reservation", fill_ok),
 ("UPGRADE to BUY","QIB subscription exceeds 20x, confirming institutional conviction at ₹429", fill_ok),
 ("UPGRADE to BUY","Capacity utilisation is disclosed above 80%, indicating the new build addresses proven demand", fill_ok),
 ("UPGRADE to BUY","Contracted revenue or a committed order book for the new capacity is disclosed", fill_ok),
 ("UPGRADE to BUY","The price is available below ₹360 post-listing", fill_ok),
 ("DOWNGRADE to AVOID","QIB comes in under 3x, leaving the GMP institutionally unsupported", fill_warn),
 ("DOWNGRADE to AVOID","The RHP reveals CFO materially below PAT, or unbilled revenue growing faster than revenue", fill_warn),
 ("DOWNGRADE to AVOID","Depreciation policy shows useful lives longer than industry norms — meaning current margins are an accounting choice, not an operating achievement", fill_warn),
 ("DOWNGRADE to AVOID","Related-party transactions or auditor observations emerge that my FY22-vintage evidence could not surface", fill_warn),
 ("DOWNGRADE to AVOID","The ex-employee equity claim is shown to be materially provisioned or advanced", fill_warn),
]:
    put(ws, r, 1, d, bold=True, fill=fl, size=9)
    put(ws, r, 2, trg, wrap=True, size=9)
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
    for cc in range(3, 6): ws.cell(row=r, column=cc).border = box
    r += 1
r += 1
put(ws, r, 1, "THE HONEST SUMMARY:  high confidence in the income statement, moderate confidence in the balance sheet, and no visibility on cash flow. That distribution of confidence is what produces a Neutral long-term view on a business I otherwise like.",
    wrap=True, border=False, size=11, bold=True)
ws.merge_cells(start_row=r, start_column=1, end_row=r+1, end_column=5)

# ================================================================ 16. TEN THINGS
ws = wb.create_sheet("Ten Things")
widths(ws, {"A":5,"B":100})
title(ws, 1, "The ten things to know before applying", 2)
r = 3
TEN = [
 "It is a 100% FRESH ISSUE WITH ZERO OFS. Every rupee goes to the company; the promoters sell nothing and dilute from 46.06% to ~39.5%. In a month where a ₹1,757 cr peer issue was 91% OFS, this is a genuinely strong alignment signal.",
 "PROFIT GROWTH IS A MARGIN STORY, NOT A VOLUME STORY — AND MARGIN STORIES END. Revenue compounded at 30.6%; EBITDA at 107.6%. EBITDA margin went 12.3% to 49.6% in three years. It cannot go to 150%. Anyone extrapolating the +117% PAT growth is extrapolating an arithmetic impossibility.",
 "PART OF THAT MARGIN IS A LEGACY-ASSET ARTEFACT THIS VERY IPO WILL UNWIND. Derived D&A is only ~12.5% of revenue — low for five data centres, and consistent with assets built years ago and largely written down. The ₹576 cr of new equipment adds ~₹96–115 cr of fresh annual depreciation, roughly 80–95% of all of FY26 PAT.",
 "THE WHOLE INVESTMENT REDUCES TO ONE UNDISCLOSED NUMBER: CAPACITY UTILISATION. Doubling 7 MW to 14 MW is strongly accretive if filled and strongly dilutive if not. ESDS does not disclose it, and you cannot know it before applying.",
 "ROE DROPS FROM 25.1% TO ABOUT 9.7% THE DAY THE MONEY LANDS. The raise nearly triples book value. The headline return ratio in the marketing will not exist by the December 2026 quarter.",
 "THE CASH FLOW STATEMENT WAS UNAVAILABLE, AND THAT IS THE BIGGEST GAP IN THIS ANALYSIS. Receivables run at 79 days versus 25 for the listed peer, with ₹63.39 cr of unbilled revenue — roughly ₹165 cr, or 1.4x FY26 PAT, tied up in working capital. Debt falling 63% in two years is supportive indirect evidence, but it is not verification.",
 "THE +77% GMP IS NOT CREDIBLE, AND THE DAY-1 BOOK QUIETLY SAYS SO. A ₹330 premium implies listing at roughly 72x FY26 earnings. Retail sat at 0.54x on Day 1. A genuinely expected 77% pop does not produce that book. The grey market for a ₹720 cr issue is thin and easily moved.",
 "THE ANCHOR BOOK IS THE SIGNAL ACTUALLY WORTH WEIGHTING. ₹216 cr fully placed with 19 investors at the top of the band, 81.94% to domestic mutual funds across six fund houses — institutions that did real diligence and accepted a lock-in.",
 "ESDS IS STRUCTURALLY SUB-SCALE, AND THE IPO DOES NOT FIX IT. At ~7 MW it holds well under 1% of Indian data-centre capacity while CtrlS, Nxtra and Yotta deploy in the hundreds of megawatts. Its defence is regulatory — sovereign and BFSI workloads offshore hyperscalers legally cannot take — covering 44.9% of revenue. The other 55.09% has no moat.",
 "THERE IS NO MARGIN OF SAFETY AT EITHER END OF THE BAND. Fair value ₹330–450, midpoint ~₹390, against a band of ₹408–429 — −4.6% at the floor, −10.0% at the cap. My base case returns +0.9% per annum over three years. The business is good; the price already assumes it.",
]
for i, t in enumerate(TEN, 1):
    put(ws, r, 1, i, bold=True, align="center", color=ACC, size=12)
    put(ws, r, 2, t, wrap=True, size=10)
    ws.merge_cells(start_row=r, start_column=1, end_row=r+2, end_column=1)
    ws.merge_cells(start_row=r, start_column=2, end_row=r+2, end_column=2)
    for rr2 in range(r, r+3):
        ws.row_dimensions[rr2].height = 16
    r += 4

# ================================================================ 17. SOURCES
ws = wb.create_sheet("Sources")
widths(ws, {"A":40,"B":56,"C":26})
title(ws, 1, "Source appendix", 3)
put(ws, 2, 1, "Analysis date: 28 August 2026. All sources retrieved on that date unless otherwise stated.", border=False, italic=True, color=GREY)
r = 4
sub(ws, r, "PRIMARY SOURCES — REFERENCED BUT NOT ACCESSED", 3); r += 1
put(ws, r, 1, "These documents exist and are the correct authority. Network restrictions prevented opening any of them. Every figure attributed to them reached me via secondary reporting.",
    wrap=True, border=False, size=9, color=GREY)
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3); r += 1
hdr(ws, r, ["Document", "Location", "Status"]); r += 1
for d, l, s in [
 ("RHP — ESDS Software Solution Ltd","sebi.gov.in/filings/public-issues/aug-2026/esds-software-solution-limited-rhp_103893.html","EGRESS_BLOCKED"),
 ("Abridged Prospectus","sebi.gov.in/sebi_data/commondocs/aug-2026/","EGRESS_BLOCKED"),
 ("DRHP (filed 30 March 2025)","bseindia.com/corporates/download/330873/  ·  esds.co.in/investors/pdf/ESDS_DRHP.pdf","EGRESS_BLOCKED"),
 ("Annual Report FY22","esds.co.in/policies_document/Annual Reports/Annual Report-FY-22.pdf","EGRESS_BLOCKED"),
 ("Standalone financials FY2020-21","esds.co.in/investors/pdf/","EGRESS_BLOCKED"),
 ("Investor financial reports","esds.co.in/investors-financial-reports","EGRESS_BLOCKED"),
 ("NSE / BSE exchange filings","nseindia.com  ·  bseindia.com","EGRESS_BLOCKED"),
]:
    put(ws, r, 1, d, wrap=True); put(ws, r, 2, l, wrap=True, size=9, color=GREY)
    put(ws, r, 3, s, align="center", bold=True, fill=fill_warn, size=9); r += 1

r += 1
sub(ws, r, "SECONDARY SOURCES ACTUALLY USED", 3); r += 1
hdr(ws, r, ["Category", "Sources", "Used for"]); r += 1
for cat, src, use in [
 ("Issue terms, dates, structure","Groww — 'ESDS Software Solution IPO to Open on August 28, 2026' (28 Aug 2026) · Bajaj Broking · Upstox · Angel One · Zerodha · Orient Publication / Sujatawde — price-band release","Price band, dates, lot size, structure, lead managers, registrar"),
 ("Financials FY23–FY26","Tradebrains — 'Price band set at ₹408–₹429' (Aug 2026) · Tradebrains — 'From Issue Details to Financials' · Tradebrains — 'Data Centre IPO With 780% Profit Growth In 2 Years' · Paytm Money · Flattrade Kosh · IPOPlatform · UnlistedZone — 'FY2025 A Transformative Year'","Revenue, EBITDA, PAT by year. The Tradebrains piece is the source of the FY25/FY26 EBITDA bridge; UnlistedZone supplies FY23/FY24"),
 ("Ratios, risk factors, concentration","INDmoney — 'ESDS Software Solution IPO Review, GMP: Apply or Avoid?' · Chanakya Ni Pothi · Precize — 'ESDS IPO: SEBI Nod' · IPO360 · IPOMarket · Lemonn · Kotak Neo","ROE, ROCE, D/E, DSO, hypothecation, top-10 concentration, litigation, borrowings"),
 ("Anchor book, GMP, subscription","Inc42 — anchor allocation (27 Aug 2026) · Sahi.com — GMP and Day 1 subscription (28 Aug 2026) · Business Standard — 'booked over 50% in an hour' (28 Aug 2026) · Goodreturns — '0.40x subscribed on Day 1' · HDFC Sky","Sentiment data, all timestamped"),
 ("Business, capacity, technology","ESDS corporate site — data centre and about-us pages · Entrepreneur India — 'ESDS to Double Data Center Capacity' · Datacenters.com — Nashik facility profile","Five data centres, 7 MW, Tier-3, uptime, SWARAJ/eNlight patents, segment mix"),
 ("Peer — E2E Networks (27 Aug 2026)","Screener.in · Trendlyne · Value Research Online · GuruFocus — P/E (TTM) · Smart-investing.in — P/E (18 Aug 2026)","Price, market cap, P/E, EV/EBITDA, P/B, Q1 FY27 results"),
 ("Industry","Arizton / GlobeNewswire — 'India Data Center Colocation Report 2026' (30 Apr 2026) · Arizton — India Data Center Market 2026 · Mordor Intelligence — India Data Center Market to 2031 · Data Centre Magazine (Apr 2026)","Market size, CAGR estimates (which disagree — both shown)"),
 ("Other IPOs in the window","ICICI Direct, Sushil Finance, IPO Watch — Lumino Industries · Value Research, MNCL — Annu Projects · IPO Watch, StockGro, IPOGuru — Priority Jewels · Kotak Neo, MNCL, Sahi — Symbiotec Pharmalab","The comparative screen"),
]:
    put(ws, r, 1, cat, wrap=True, bold=True)
    put(ws, r, 2, src, wrap=True, size=9, color=GREY)
    put(ws, r, 3, use, wrap=True, size=9, color=GREY); r += 1

r += 1
sub(ws, r, "RELIABILITY HIERARCHY APPLIED", 3); r += 1
for t in [
 "1.  Figures reconciling across two or more independent sources AND passing an arithmetic cross-check → treated as reliable. This covers the entire income statement, the share count and every valuation multiple.",
 "2.  Figures from a single source, consistent with the rest → reported with the source named on the Inputs tab.",
 "3.  Figures failing a cross-check → flagged [!] and the conflict shown, never silently resolved. This covers the objects of the issue, the year-ordering of top-10 concentration, and the industry CAGR estimates.",
 "4.  Figures unobtainable → marked [NA] and left empty. This covers the entire cash flow statement, FY22, the auditor's identity, promoter pledges, and capacity utilisation.",
]:
    put(ws, r, 1, t, wrap=True, border=False, size=10)
    ws.merge_cells(start_row=r, start_column=1, end_row=r+1, end_column=3)
    ws.row_dimensions[r].height = 24; r += 2

put(ws, r, 1, "Prepared 28 August 2026. Analytical work product, not investment advice. Every figure is sourced from secondary reporting of the RHP because primary-document access was blocked — verify against the RHP before acting. Markets move, and the IPO sentiment data cited here is timestamped and perishable.",
    wrap=True, border=False, size=9, italic=True, color=GREY)
ws.merge_cells(start_row=r, start_column=1, end_row=r+2, end_column=3)

# ---------------------------------------------------------------- polish
for s in wb.worksheets:
    s.sheet_view.showGridLines = False
    s.freeze_panes = "A4"
wb["Read Me"].freeze_panes = None
wb["Ten Things"].freeze_panes = None
wb["Valuation"].freeze_panes = None
wb.calculation.fullCalcOnLoad = True
wb.active = 0

wb.move_sheet("Financials", offset=-1)
wb.save(OUT)
print("saved", OUT)
