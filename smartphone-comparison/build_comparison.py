#!/usr/bin/env python3
"""
Build Smartphone_Comparison_Aug2026.xlsx -- a side-by-side comparison of the
Galaxy Z Fold 7/6/5, Galaxy S26/S25/S24/S23 Ultra and iPhone 17/16/15 with
India street pricing, a weighted scorecard and a buying recommendation.

Run:  python build_comparison.py
Then: python /root/.claude/skills/synced/xlsx/scripts/recalc.py <output>
"""

import os

from openpyxl import Workbook
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

import data

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "Smartphone_Comparison_Aug2026.xlsx")

PRICE_SHEET = "Price and Value"

# --------------------------------------------------------------------- styling
FONT = "Arial"
INK = "1F2933"
ACCENT = "1F4E79"          # headers
ACCENT_LIGHT = "DDEBF7"    # section bands
INPUT_FILL = "FFF2CC"      # cells the reader is meant to edit
BAND = "F5F7FA"

INR = '[>=10000000]"₹"##\\,##\\,##\\,##0;[>=100000]"₹"##\\,##\\,##0;"₹"##,##0'
PCT = '0.0%'
NUM1 = '0.0'

BLUE = Font(name=FONT, size=10, color="0000FF")           # hardcoded input
BLACK = Font(name=FONT, size=10, color=INK)               # formula / text
GREEN = Font(name=FONT, size=10, color="008000")          # link to another sheet
BOLD = Font(name=FONT, size=10, bold=True, color=INK)
HEAD = Font(name=FONT, size=10, bold=True, color="FFFFFF")
TITLE = Font(name=FONT, size=16, bold=True, color=ACCENT)
SUB = Font(name=FONT, size=10, italic=True, color="5A6570")
SECTION = Font(name=FONT, size=10, bold=True, color=ACCENT)

thin = Side(style="thin", color="BFC7D1")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)

WRAP = Alignment(wrap_text=True, vertical="top")
WRAP_C = Alignment(wrap_text=True, vertical="center", horizontal="center")
CTR = Alignment(horizontal="center", vertical="center")


def title_block(ws, title, subtitle, width):
    ws["A1"] = title
    ws["A1"].font = TITLE
    ws["A2"] = subtitle
    ws["A2"].font = SUB
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=width)
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=width)
    ws.row_dimensions[1].height = 24
    ws.row_dimensions[2].height = 15


def header_row(ws, row, values, start_col=1, height=32):
    for i, v in enumerate(values):
        c = ws.cell(row=row, column=start_col + i, value=v)
        c.font = HEAD
        c.fill = PatternFill("solid", fgColor=ACCENT)
        c.alignment = WRAP_C
        c.border = BOX
    ws.row_dimensions[row].height = height


# ============================================================== 1. Read Me ====
def sheet_readme(wb):
    ws = wb.create_sheet("Read Me")
    ws.sheet_view.showGridLines = False
    title_block(ws, "Smartphone Comparison - Fold vs Ultra vs iPhone",
                f"Ten phones, compared for an India purchase decision. All data as of {data.AS_OF}.", 6)

    rows = [
        ("", ""),
        ("What is in this workbook", ""),
        ("Spec Comparison", "Every phone as a column, ~55 attributes as rows, grouped by section. This is the main table."),
        (PRICE_SHEET, "Launch MRP against the best street price found today, the usual bank offer, and how far each phone has fallen."),
        ("Scorecard", "A weighted decision model. Change the weights in row 4 to match what YOU care about and the ranking re-sorts itself."),
        ("Best and Unique", "The three things each phone does best, the one thing only it does, and what is wrong with it."),
        ("Recommendation", "The actual answer: what to buy, at what budget, and why waiting two weeks may save you money."),
        ("", ""),
        ("How to use it", ""),
        ("1.", "Read the Recommendation sheet first if you just want an answer."),
        ("2.", "Open the Scorecard and change the seven weights in row 4 (yellow cells) so they total 100%. The ranking updates."),
        ("3.", "If you have a live quote, overwrite the price in column D of the " + PRICE_SHEET + " sheet. Everything downstream follows."),
        ("", ""),
        ("Colour legend", ""),
        ("Blue text", "A hardcoded number or judgement typed in by hand -- an input you may change."),
        ("Black text", "A formula. Do not overwrite these; they recalculate from the inputs."),
        ("Green text", "A link pulling a value in from another sheet."),
        ("Yellow fill", "A cell you are expected to edit -- the scorecard weights."),
        ("", ""),
        ("Where the numbers came from", ""),
        ("Prices", "Public retail and price-tracker listings on 26 Aug 2026: Flipkart, Amazon India, Croma, Samsung India, Smartprix, 91mobiles, MySmartPrice, PriceHistory, SamMobile, Cashify."),
        ("Specifications", "Manufacturer spec sheets (Samsung India, Apple India) cross-checked against GSMArena, PhoneArena, TechRadar and 91mobiles."),
        ("Ratings", "The 1-10 category ratings on the Scorecard are MY judgement, not a measurement. They are typed in blue so you can disagree and overwrite them."),
        ("", ""),
        ("Read this before you spend money", ""),
        ("Prices move daily", "Indian smartphone street prices swing by Rs 5,000-15,000 on bank offers, exchange bonuses and sale events. Every price here is a snapshot, not a quote. Re-check on the day you buy."),
        ("Festive season is coming", "Flipkart Big Billion Days and Amazon Great Indian Festival typically land late September / early October. Several phones here will be cheaper then."),
        ("Two launches are pending", "The Galaxy Z Fold 8 already launched (22 Jul 2026), which is why the Fold 7 is discounted. Apple's next event is expected around 9 Sep 2026 -- roughly two weeks from this workbook's date."),
        ("Variant matters", "Every price here is the base variant listed in the " + PRICE_SHEET + " sheet. A 512 GB model typically costs Rs 10,000-20,000 more."),
    ]

    r = 4
    for label, text in rows:
        if label and not text:
            ws.cell(row=r, column=1, value=label).font = SECTION
            ws.cell(row=r, column=1).fill = PatternFill("solid", fgColor=ACCENT_LIGHT)
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
        elif label:
            a = ws.cell(row=r, column=1, value=label)
            a.font = BOLD
            a.alignment = WRAP
            b = ws.cell(row=r, column=2, value=text)
            b.font = BLACK
            b.alignment = WRAP
            ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)
            ws.row_dimensions[r].height = max(14, 13 * (len(text) // 95 + 1))
        r += 1

    ws.column_dimensions["A"].width = 24
    for col in "BCDEF":
        ws.column_dimensions[col].width = 22
    return ws


# ================================================== 2. Price and Value ========
def sheet_prices(wb):
    ws = wb.create_sheet(PRICE_SHEET)
    ws.sheet_view.showGridLines = False
    title_block(ws, "Price and Value - India, " + data.AS_OF,
                "Best mainstream online price found for the base variant. Bank offer is the typical card discount running at that store; "
                "exchange bonuses are excluded because they depend on your old phone.", 9)

    header_row(ws, 3, ["Phone", "Base variant", "Launch MRP", "Best street price today",
                       "Typical bank offer", "Effective price", "Fall from launch MRP",
                       "Where", "What is going on with this price"])

    for i, dev in enumerate(data.DEVICES):
        r = 4 + i
        variant, mrp, best, store, offer, note = data.PRICING[dev]
        ws.cell(row=r, column=1, value=dev).font = BOLD
        ws.cell(row=r, column=2, value=variant).font = BLACK
        ws.cell(row=r, column=3, value=mrp).font = BLUE
        ws.cell(row=r, column=4, value=best).font = BLUE
        ws.cell(row=r, column=5, value=offer).font = BLUE
        ws.cell(row=r, column=6, value=f"=D{r}-E{r}").font = BLACK
        ws.cell(row=r, column=7, value=f"=IF(C{r}=0,\"\",(C{r}-D{r})/C{r})").font = BLACK
        ws.cell(row=r, column=8, value=store).font = BLACK
        ws.cell(row=r, column=9, value=note).font = BLACK

        for col in (3, 4, 5, 6):
            ws.cell(row=r, column=col).number_format = INR
        ws.cell(row=r, column=7).number_format = PCT
        for col in range(1, 10):
            c = ws.cell(row=r, column=col)
            c.border = BOX
            c.alignment = WRAP if col in (1, 2, 8, 9) else CTR
            if i % 2:
                c.fill = PatternFill("solid", fgColor=BAND)
        ws.row_dimensions[r].height = 42

    last = 3 + len(data.DEVICES)
    ws.cell(row=last + 2, column=1, value="Cheapest today").font = BOLD
    ws.cell(row=last + 2, column=3, value=f"=MIN(F4:F{last})").font = BLACK
    ws.cell(row=last + 2, column=3).number_format = INR
    ws.cell(row=last + 3, column=1, value="Dearest today").font = BOLD
    ws.cell(row=last + 3, column=3, value=f"=MAX(F4:F{last})").font = BLACK
    ws.cell(row=last + 3, column=3).number_format = INR
    ws.cell(row=last + 4, column=1, value="Spread").font = BOLD
    ws.cell(row=last + 4, column=3, value=f"=C{last + 3}-C{last + 2}").font = BLACK
    ws.cell(row=last + 4, column=3).number_format = INR
    ws.cell(row=last + 6, column=1,
            value="Prices are a snapshot taken on " + data.AS_OF + " from public retail and price-tracker listings "
                  "(Flipkart, Amazon India, Croma, Samsung India, Smartprix, 91mobiles, MySmartPrice, PriceHistory, SamMobile). "
                  "Overwrite column D with a live quote and every dependent figure in this workbook updates.").font = SUB
    ws.merge_cells(start_row=last + 6, start_column=1, end_row=last + 6, end_column=9)
    ws.row_dimensions[last + 6].height = 40
    ws.cell(row=last + 6, column=1).alignment = WRAP

    ws.conditional_formatting.add(
        f"F4:F{last}",
        ColorScaleRule(start_type="min", start_color="C6EFCE",
                       end_type="max", end_color="F8CBAD"))

    widths = {"A": 20, "B": 14, "C": 15, "D": 17, "E": 15, "F": 15, "G": 14, "H": 20, "I": 60}
    for col, w in widths.items():
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "B4"
    return ws


# ==================================================== 3. Spec Comparison ======
def sheet_specs(wb):
    ws = wb.create_sheet("Spec Comparison")
    ws.sheet_view.showGridLines = False
    ncols = 2 + len(data.DEVICES)
    title_block(ws, "Full Specification Comparison",
                "Read across a row to compare one attribute; read down a column for one phone. "
                "Pricing rows are pulled live from the " + PRICE_SHEET + " sheet.", ncols)

    header_row(ws, 3, ["Section", "Attribute"] + data.DEVICES, height=34)

    r = 4
    last_section = None
    price_row_of = {d: 4 + i for i, d in enumerate(data.DEVICES)}

    for section, attr, values in data.SPEC_ROWS:
        if section != last_section:
            band = ws.cell(row=r, column=1, value=section)
            band.font = SECTION
            for col in range(1, ncols + 1):
                ws.cell(row=r, column=col).fill = PatternFill("solid", fgColor=ACCENT_LIGHT)
                ws.cell(row=r, column=col).border = BOX
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=ncols)
            ws.row_dimensions[r].height = 18
            last_section = section
            r += 1

        ws.cell(row=r, column=1, value="").font = BLACK
        a = ws.cell(row=r, column=2, value=attr)
        a.font = BOLD
        a.alignment = WRAP

        is_link = isinstance(values, str) and values.startswith("LINK:")
        for i, dev in enumerate(data.DEVICES):
            c = ws.cell(row=r, column=3 + i)
            if is_link:
                col_letter = values.split(":")[1]
                c.value = f"='{PRICE_SHEET}'!{col_letter}{price_row_of[dev]}"
                c.font = GREEN
                c.number_format = PCT if col_letter == "G" else INR
                c.alignment = CTR
            else:
                c.value = values[i]
                c.font = BLACK
                c.alignment = WRAP
        for col in range(1, ncols + 1):
            cell = ws.cell(row=r, column=col)
            cell.border = BOX
            if (r % 2) == 0:
                if not cell.fill or cell.fill.fgColor.rgb in (None, "00000000"):
                    cell.fill = PatternFill("solid", fgColor=BAND)
        ws.row_dimensions[r].height = 30
        r += 1

    ws.column_dimensions["A"].width = 3
    ws.column_dimensions["B"].width = 32
    for i in range(len(data.DEVICES)):
        ws.column_dimensions[get_column_letter(3 + i)].width = 26
    ws.freeze_panes = "C4"
    return ws


# ========================================================= 4. Scorecard =======
def sheet_scorecard(wb):
    ws = wb.create_sheet("Scorecard")
    ws.sheet_view.showGridLines = False
    cats = [c for c, _ in data.RATING_CATEGORIES]
    ncols = 1 + len(cats) + 5
    title_block(ws, "Weighted Scorecard - make it your decision, not mine",
                "The 1-10 ratings are my judgement (blue). The weights in row 4 are yours to change (yellow). "
                "Everything in black is a formula and re-ranks the moment you edit a weight.", ncols)

    ws.cell(row=4, column=1, value="Weights (edit - must total 100%)").font = BOLD
    for i, (cat, w) in enumerate(data.RATING_CATEGORIES):
        c = ws.cell(row=4, column=2 + i, value=w)
        c.font = BLUE
        c.number_format = PCT
        c.fill = PatternFill("solid", fgColor=INPUT_FILL)
        c.border = BOX
        c.alignment = CTR
    wcol_first = get_column_letter(2)
    wcol_last = get_column_letter(1 + len(cats))
    chk = ws.cell(row=4, column=2 + len(cats), value=f"=SUM({wcol_first}4:{wcol_last}4)")
    chk.font = BOLD
    chk.number_format = PCT
    chk.alignment = CTR
    chk.border = BOX
    ws.cell(row=4, column=3 + len(cats),
            value='=IF(ROUND(SUM(' + wcol_first + '4:' + wcol_last + '4),4)=1,"Weights OK","FIX: weights must total 100%")').font = BOLD

    hdr = ["Phone"] + cats + ["Weighted score (0-10)", "Rank on score",
                              "Effective price", "Score per Rs 10,000", "Rank on value"]
    header_row(ws, 6, hdr, height=44)

    first, last = 7, 6 + len(data.DEVICES)
    score_col = get_column_letter(2 + len(cats))          # I
    price_col = get_column_letter(4 + len(cats))          # K
    value_col = get_column_letter(5 + len(cats))          # L

    for i, dev in enumerate(data.DEVICES):
        r = first + i
        ws.cell(row=r, column=1, value=dev).font = BOLD
        for j, rating in enumerate(data.RATINGS[dev]):
            c = ws.cell(row=r, column=2 + j, value=rating)
            c.font = BLUE
            c.number_format = NUM1
            c.alignment = CTR

        s = ws.cell(row=r, column=2 + len(cats),
                    value=f"=SUMPRODUCT(${wcol_first}$4:${wcol_last}$4,{wcol_first}{r}:{wcol_last}{r})")
        s.font = BOLD
        s.number_format = NUM1

        rk = ws.cell(row=r, column=3 + len(cats),
                     value=f"=RANK({score_col}{r},${score_col}${first}:${score_col}${last})")
        rk.font = BLACK

        p = ws.cell(row=r, column=4 + len(cats),
                    value=f"=INDEX('{PRICE_SHEET}'!$F$4:$F$13,MATCH($A{r},'{PRICE_SHEET}'!$A$4:$A$13,0))")
        p.font = GREEN
        p.number_format = INR

        v = ws.cell(row=r, column=5 + len(cats),
                    value=f"=IF({price_col}{r}=0,\"\",{score_col}{r}/({price_col}{r}/10000))")
        v.font = BOLD
        v.number_format = '0.00'

        vr = ws.cell(row=r, column=6 + len(cats),
                     value=f"=RANK({value_col}{r},${value_col}${first}:${value_col}${last})")
        vr.font = BLACK

        for col in range(1, ncols + 1):
            cell = ws.cell(row=r, column=col)
            cell.border = BOX
            if col > 1:
                cell.alignment = CTR
            if i % 2:
                cell.fill = PatternFill("solid", fgColor=BAND)
        ws.row_dimensions[r].height = 20

    ws.conditional_formatting.add(
        f"{score_col}{first}:{score_col}{last}",
        ColorScaleRule(start_type="min", start_color="F8CBAD",
                       end_type="max", end_color="C6EFCE"))
    ws.conditional_formatting.add(
        f"{value_col}{first}:{value_col}{last}",
        ColorScaleRule(start_type="min", start_color="F8CBAD",
                       end_type="max", end_color="C6EFCE"))

    notes = [
        "",
        "How to read this",
        "Weighted score is the quality of the phone alone, ignoring price -- SUMPRODUCT of the seven ratings against your weights.",
        "Score per Rs 10,000 divides that score by the effective price. Higher is better -- but read it knowing what it rewards: dividing by price "
        "structurally favours the cheapest phone, which is why the iPhone 15 tops it. Use it to spot phones that are over-priced for what they are, "
        "not as a shopping list.",
        "Effective price is pulled from the " + PRICE_SHEET + " sheet (best street price minus the typical bank offer).",
        "",
        "What the ratings mean",
        "Performance: chipset generation, sustained load behaviour, RAM headroom.",
        "Display: size, resolution, refresh rate, brightness, and for the folds the value of the second screen.",
        "Camera: the whole system -- main sensor, ultra-wide, optical zoom reach, video, processing.",
        "Battery and charging: capacity, real screen-on time, wired and wireless charging speed.",
        "Software support life: how many years of OS and security updates remain from today, not from launch.",
        "Design and portability: weight, thickness, ingress protection, one-handed use, materials.",
        "Features and ecosystem: stylus, DeX or Continuity, multitasking, AI features, accessory ecosystem.",
        "",
        "These ratings are judgement, not measurement. Every one of them is a blue input you can overwrite -- if you never use a stylus, "
        "drop 'Features and ecosystem' to 5% and watch the order change.",
    ]
    r = last + 2
    for n in notes:
        if not n:
            r += 1
            continue
        c = ws.cell(row=r, column=1, value=n)
        if n in ("How to read this", "What the ratings mean"):
            c.font = SECTION
        else:
            c.font = SUB
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=ncols)
            c.alignment = WRAP
            ws.row_dimensions[r].height = max(14, 13 * (len(n) // 130 + 1))
        r += 1

    ws.column_dimensions["A"].width = 20
    for i in range(len(cats)):
        ws.column_dimensions[get_column_letter(2 + i)].width = 12
    ws.column_dimensions[score_col].width = 14
    ws.column_dimensions[get_column_letter(3 + len(cats))].width = 11
    ws.column_dimensions[price_col].width = 15
    ws.column_dimensions[value_col].width = 15
    ws.column_dimensions[get_column_letter(6 + len(cats))].width = 11
    ws.freeze_panes = "B7"
    return ws


# ==================================================== 5. Best and Unique ======
def sheet_features(wb):
    ws = wb.create_sheet("Best and Unique")
    ws.sheet_view.showGridLines = False
    title_block(ws, "Best Features, Unique Features and the Catch",
                "What each phone genuinely does well, the one thing only it does, and what you give up by choosing it.", 5)

    header_row(ws, 3, ["Phone", "Three things it does best", "Only on this phone",
                       "What you give up", "Who it actually suits"], height=34)

    for i, dev in enumerate(data.DEVICES):
        r = 4 + i
        best, unique, cons, suits = data.FEATURES[dev]
        ws.cell(row=r, column=1, value=dev).font = BOLD
        ws.cell(row=r, column=2, value="\n".join("• " + b for b in best)).font = BLACK
        u = ws.cell(row=r, column=3, value=unique)
        u.font = Font(name=FONT, size=10, bold=True, color="1F4E79")
        ws.cell(row=r, column=4, value="\n".join("• " + c for c in cons)).font = BLACK
        ws.cell(row=r, column=5, value=suits).font = BLACK
        for col in range(1, 6):
            c = ws.cell(row=r, column=col)
            c.border = BOX
            c.alignment = WRAP
            if i % 2:
                c.fill = PatternFill("solid", fgColor=BAND)
        ws.row_dimensions[r].height = 76

    for col, w in {"A": 20, "B": 52, "C": 40, "D": 44, "E": 38}.items():
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "B4"
    return ws


# ==================================================== 6. Recommendation =======
def sheet_reco(wb):
    ws = wb.create_sheet("Recommendation")
    ws.sheet_view.showGridLines = False
    title_block(ws, "Recommendation",
                "One buyer's view as of " + data.AS_OF + ", for a phone bought in India. "
                "The Scorecard exists so you can disagree with it.", 5)

    r = 4

    def band(text):
        nonlocal r
        c = ws.cell(row=r, column=1, value=text)
        c.font = SECTION
        for col in range(1, 6):
            ws.cell(row=r, column=col).fill = PatternFill("solid", fgColor=ACCENT_LIGHT)
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
        ws.row_dimensions[r].height = 20
        r += 1

    def para(text, bold=False):
        nonlocal r
        c = ws.cell(row=r, column=1, value=text)
        c.font = BOLD if bold else BLACK
        c.alignment = WRAP
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
        ws.row_dimensions[r].height = max(15, 13 * (len(text) // 120 + 1))
        r += 1

    def table(headers, rows, widths_note=None):
        nonlocal r
        header_row(ws, r, headers, height=28)
        r += 1
        for i, row in enumerate(rows):
            for j, v in enumerate(row):
                c = ws.cell(row=r, column=1 + j, value=v)
                c.font = BOLD if j == 0 else BLACK
                c.alignment = WRAP
                c.border = BOX
                if i % 2:
                    c.fill = PatternFill("solid", fgColor=BAND)
            ws.row_dimensions[r].height = 44
            r += 1
        r += 1

    band("The short answer")
    para("Buy the Galaxy S25 Ultra at roughly Rs 88,000 effective. It carries the full Ultra camera stack -- 200 MP main, "
         "50 MP autofocus ultra-wide, 3x and 5x optical -- a titanium body, a built-in S Pen and updates running to February 2032, "
         "for about Rs 32,000 less than the S26 Ultra that improves on it mainly in main-sensor aperture and charging speed. "
         "It ranks second on raw quality on the Scorecard and is the highest-scoring phone available below Rs 90,000.", bold=True)
    para("If you are set on iOS: wait until mid-September. Apple's next event is expected around 9 September 2026, and the iPhone 17 "
         "has already traded as low as Rs 75,900. Buying it on 26 August is the single most avoidable mistake in this workbook.")
    para("If you want the foldable: the Galaxy Z Fold 7 at roughly Rs 155,000 effective is the one worth owning, but it is a want, not a value buy. "
         "It ranks near the bottom of the value column and its 4,400 mAh / 25 W battery is the weakest here.")
    r += 1

    band("Pick by budget")
    table(["Budget (effective)", "Buy this", "Why", "Runner-up", "Skip"],
          [["Under Rs 50,000", "iPhone 15 (Rs 51,999, ~Rs 49,000 after card offer)",
            "Cheapest route to a current iOS build with a 48 MP main camera. Accept that Apple Intelligence will never run on it.",
            "A used or refurbished S23 Ultra at around Rs 53,000", "Nothing new from Samsung's flagship line lands here"],
           ["Rs 60,000 - 75,000", "Galaxy S24 Ultra (Rs 78,999, ~Rs 75,000 after card offer)",
            "Titanium, 200 MP main, a real 5x periscope, Bluetooth S Pen and updates to January 2031. Nothing else at this price has that camera reach.",
            "iPhone 16 at ~Rs 62,000 if you need iOS", "Galaxy S23 Ultra -- same money, a year older, updates end Feb 2028"],
           ["Rs 75,000 - 95,000", "Galaxy S25 Ultra (Rs 92,990, ~Rs 88,000 after card offer)",
            "The value winner of this entire comparison. Near-flagship in every column at a two-generations-old price.",
            "iPhone 17 -- but only after the September event", "Do not stretch to the Fold 5 at Rs 108,990 -- cheaper phones here beat it on every axis"],
           ["Rs 95,000 - 130,000", "Galaxy S26 Ultra (Rs 124,999, ~Rs 120,000 after card offer)",
            "Best Android phone you can buy today: f/1.4 main, 60 W charging, Privacy Display, updates to Feb 2033.",
            "Galaxy Z Fold 6 at ~Rs 105,000 if you specifically want a foldable",
            "Paying full MRP -- it launched at Rs 139,999 and has fallen Rs 15,000 in six months"],
           ["Above Rs 150,000", "Galaxy Z Fold 7 (Rs 161,855, ~Rs 155,000 after card offer)",
            "The only foldable here with a flagship 200 MP camera and a cover screen you can actually type on.",
            "Galaxy Z Fold 8 at Rs 179,999 if you want current-generation",
            "Buying a Fold for the camera or the battery -- an S26 Ultra beats it on both for about Rs 35,000 less"]])

    band("Pick by what you actually care about")
    table(["If this matters most", "Buy", "Because"],
          [["Camera, no compromise", "Galaxy S26 Ultra",
            "f/1.4 main takes in roughly 47% more light than the S24 Ultra, plus a 50 MP autofocus ultra-wide and 5x periscope. Nothing else here is close in low light."],
           ["Zoom reach specifically", "Galaxy S23 Ultra (used or discounted)",
            "The only phone in this list with a true 10x optical periscope. Samsung has not shipped one since. Buy it knowing security updates end Feb 2028."],
           ["Battery that survives a long day", "Galaxy S26 Ultra",
            "5,000 mAh with 60 W wired and 25 W wireless. Real screen-on time of 8-9 hours -- the folds manage 5-6."],
           ["Screen real estate / multitasking", "Galaxy Z Fold 7",
            "An 8-inch 120 Hz tablet in your pocket, plus Samsung DeX. If you read contracts, review spreadsheets or run two apps side by side, nothing else competes."],
           ["Lightest phone that still feels premium", "iPhone 16 (170 g) or iPhone 17 (177 g)",
            "Every Samsung in this list is 214 g or heavier; the Fold 5 is 253 g."],
           ["Longest useful life", "Galaxy S26 Ultra",
            "Security updates to Feb 2033 -- about 6.5 years from today. The iPhone 17 is close behind at roughly 5.5."],
           ["Resale value", "iPhone 17",
            "iPhones hold roughly 60-65% of MRP at two years against 40-50% for Samsung flagships. Factor that in before comparing sticker prices."],
           ["Stylus / handwritten notes", "Galaxy S25 Ultra or S24 Ultra",
            "Both have an S Pen in the body. The Fold 7 dropped stylus support entirely, and the S24 Ultra is the last one with Bluetooth Air Actions."],
           ["Lowest total spend on iOS", "iPhone 15",
            "Under Rs 52,000 for a Dynamic Island iPhone with USB-C. The catch is permanent: no Apple Intelligence, 60 Hz, and Apple India has discontinued it."]])

    band("Do not buy these right now")
    table(["Phone", "Why not", "What to do instead"],
          [["Galaxy Z Fold 5 (Rs 108,990)", "Costs almost the same as a Fold 6 that is a generation newer, with worse ingress protection (IPX8, no dust rating), 253 g, and updates ending Aug 2028.", "Pay Rs 1,000 more for the Fold 6, or wait for it to fall below Rs 85,000."],
           ["Galaxy S23 Ultra (Rs 74,999)", "Priced level with the S24 Ultra but a year older, with under 18 months of security updates left.", "Buy the S24 Ultra, unless you specifically want the 10x periscope -- then buy refurbished at around Rs 53,000."],
           ["iPhone 17 at Rs 81,900 today", "Apple's next event is expected around 9 September 2026, roughly two weeks away. This phone has already traded at Rs 75,900.", "Wait two weeks. If you cannot, at least wait for the festive sale in late September."],
           ["Galaxy Z Fold 7 if you want value", "Ranks last or near-last on score-per-rupee. You are paying roughly Rs 35,000 more than an S26 Ultra for the hinge.", "Buy it because you want a foldable, not because it is the better phone. Otherwise buy the S26 Ultra."]])

    band("Timing - what is about to happen")
    for t in [
        "22 July 2026: the Galaxy Z Fold 8 and Fold 8 Ultra launched in India at Rs 179,999 and Rs 199,999, on sale from 8 August. "
        "That is exactly why the Fold 7 fell about Rs 13,000 at Croma with another Rs 7,000 off on HDFC cards.",
        "~9 September 2026: Apple's autumn event is expected. Reports point to the iPhone 18 Pro, iPhone 18 Pro Max and a foldable iPhone; "
        "the standard iPhone 18 is expected to slip to spring 2027. Note the consequence -- if you want a non-Pro iPhone, the iPhone 17 stays "
        "Apple's current base model for another six months, so its price will drop but it will not be superseded.",
        "Late September / early October 2026: Flipkart Big Billion Days and Amazon Great Indian Festival. Historically the deepest cuts of the year "
        "on last-generation flagships -- which is most of this list.",
        "Roughly February 2027: the Galaxy S27 Ultra cycle. If you are buying an S26 Ultra and can wait, its price will fall meaningfully then. "
        "If you are buying an S25 Ultra it is already at that stage of the curve, which is the whole argument for it.",
    ]:
        para("• " + t)
    r += 1

    band("How to actually pay less in India")
    for t in [
        "Stack the offers: card discount (Rs 3,000-7,000 depending on bank and store), exchange bonus, and no-cost EMI are usually combinable. "
        "The listed price is rarely the price you pay.",
        "Exchange bonuses are the biggest lever on Samsung phones -- Flipkart has advertised up to Rs 63,300 total savings on the Fold 7 with a trade-in. "
        "They are excluded from this workbook because the number depends entirely on your old phone.",
        "Check Croma and Samsung's own store, not just Flipkart and Amazon. The best Fold 7 price today is at Croma, not either marketplace.",
        "Apple discounts differently: Apple India rarely cuts its own price, but Flipkart and Amazon do, and Apple cuts MRP on older models when a new one launches "
        "(as it did for the iPhone 16 after the 17).",
        "Refurbished is a real option at the bottom of this list -- a certified S23 Ultra runs around Rs 53,000 against Rs 74,999 new. Check the warranty terms before you commit.",
        "Buy the base storage variant unless you know you need more. A 512 GB step-up costs Rs 10,000-20,000; a cloud subscription costs far less.",
    ]:
        para("• " + t)
    r += 1

    band("What this recommendation is not")
    para("These are my judgements on a snapshot of prices taken on " + data.AS_OF + ". Indian street prices move daily on bank offers and sale events, "
         "and the ratings feeding the Scorecard are opinions, not benchmarks. Re-check the price on the day you buy, and if you weigh things differently "
         "from me, change the weights in row 4 of the Scorecard -- the ranking is a formula, not a verdict.")

    for col, w in {"A": 30, "B": 34, "C": 52, "D": 34, "E": 34}.items():
        ws.column_dimensions[col].width = w
    return ws


def main():
    wb = Workbook()
    wb.remove(wb.active)
    sheet_readme(wb)
    sheet_reco(wb)
    sheet_specs(wb)
    sheet_prices(wb)
    sheet_scorecard(wb)
    sheet_features(wb)
    # Reading order: overview, answer, evidence, price, model, detail.
    order = ["Read Me", "Recommendation", "Spec Comparison", PRICE_SHEET,
             "Scorecard", "Best and Unique"]
    wb._sheets = [wb[name] for name in order]
    for ws in wb.worksheets:
        ws.sheet_properties.tabColor = ACCENT
    wb.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
