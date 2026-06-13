"""
India Bluechip Equity Watchlist — Board-Ready Excel Report
16% CAGR Target | 2-Year Horizon | Nifty 50 / Large-Cap Focus
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, Reference
import datetime

# ── Premium colour palette (Midnight Blue × Saffron × Emerald) ─────────────
MIDNIGHT   = "0D1B2A"
SAFFRON    = "D45B10"
EMERALD    = "1A5C40"
ROYAL      = "1D3F6B"
STEEL      = "4A6FA5"
CREAM      = "FFFAF2"
LIGHT_STEEL= "EBF3FB"
LIGHT_CREAM= "FFF3E5"
WHITE      = "FFFFFF"
DARK_TXT   = "1C1C2E"
GREEN_OK   = "1E7E34"
AMBER_MID  = "C87D00"
RED_HIGH   = "C0392B"
GOLD_ACC   = "D4A017"
SILVER     = "B0BEC5"
DEEP_TEAL  = "0E6655"

def hf(hex_code):
    return PatternFill("solid", fgColor=hex_code)

def tb(top=True, bottom=True, left=True, right=True, color="D0D8E8"):
    s = Side(style="thin", color=color)
    return Border(
        top=s if top else None, bottom=s if bottom else None,
        left=s if left else None, right=s if right else None
    )

def mb(color=MIDNIGHT):
    s = Side(style="medium", color=color)
    return Border(top=s, bottom=s, left=s, right=s)

def scw(ws, col, width):
    ws.column_dimensions[get_column_letter(col)].width = width

def ms(ws, rng, text, bg, fsz=11, bold=True, fc=WHITE, halign="center", wrap=False):
    ws.merge_cells(rng)
    tl = ws[rng.split(":")[0]]
    tl.value = text
    tl.fill = hf(bg)
    tl.font = Font(name="Calibri", size=fsz, bold=bold, color=fc)
    tl.alignment = Alignment(horizontal=halign, vertical="center", wrap_text=wrap)

def wc(ws, row, col, val, bg=None, fsz=10, bold=False, fc=DARK_TXT,
       halign="left", wrap=False, border=True):
    c = ws.cell(row=row, column=col, value=val)
    if bg:
        c.fill = hf(bg)
    c.font = Font(name="Calibri", size=fsz, bold=bold, color=fc)
    c.alignment = Alignment(horizontal=halign, vertical="center", wrap_text=wrap)
    if border:
        c.border = tb()
    return c

# ═══════════════════════════════════════════════════════════════════════════
# DATA
# ═══════════════════════════════════════════════════════════════════════════

SECTORS = [
    {
        "id": "Banking & PSU Banks",
        "color": ROYAL,
        "momentum": "Strong",
        "drivers": (
            "Record FY26 profits across the sector. SBI PAT ₹80,032 cr (record). "
            "Credit growth 11–14% YoY. ROE expanding: SBI 18.57%, ICICI 17–18%. "
            "RBI rate at 5.25% — near-bottom cycle. NIM stabilising after 2 years of "
            "compression. Improving asset quality across PSU and private banks."
        ),
        "valuation": "Attractive — SBI at 1.1x book (record cheap); ICICI at 15–17x PE below 5yr avg",
        "cagr_path": "NIM normalization + credit growth + ROE expansion → 15–20% EPS CAGR",
        "risk": "Medium",
        "key_risk": "NIM compression if rate cuts are deeper-than-expected; unsecured credit stress",
    },
    {
        "id": "Automobiles & Auto Ancillaries",
        "color": EMERALD,
        "momentum": "Strong",
        "drivers": (
            "M&M FY26 PAT +35%, Revenue +25%. Maruti Q1 FY26 revenue +28.7%. "
            "India SUV supercycle in full swing; premiumisation of passenger vehicles. "
            "EV adoption accelerating: M&M targets 18–20% EV sales mix by FY27. "
            "Rural income recovery boosting 2-wheeler and small car demand."
        ),
        "valuation": "Fair — M&M at ~25–28x PE, Maruti at ~25x; both below peak 30–35x levels",
        "cagr_path": "Volume growth + premiumisation + EV revenue premium → 20–25% EPS CAGR",
        "risk": "Medium",
        "key_risk": "EV margin dilution in near term; commodity (steel, aluminium) cost spikes; global slowdown",
    },
    {
        "id": "Telecom (Digital India)",
        "color": SAFFRON,
        "momentum": "Strong",
        "drivers": (
            "Bharti Airtel Q4 FY26 revenue +15.7% YoY; PAT +38.7%. ARPU ₹257 → "
            "targeting ₹300 as 5G monetisation kicks in. 181 million 5G customers. "
            "74% India population covered by 5G. Duopoly market (Airtel + Jio) "
            "supports rational pricing. EBITDA margins 57.8% — best-in-class globally."
        ),
        "valuation": "Fair-to-Premium — PE ~35–40x; justified by operating leverage and ARPU re-rating",
        "cagr_path": "ARPU expansion + subscriber growth + Africa optionality → 20–25% EPS CAGR",
        "risk": "Low-Medium",
        "key_risk": "ARPU plateau if Jio undercuts; spectrum cost; Africa FX volatility",
    },
    {
        "id": "Diversified Conglomerate",
        "color": DEEP_TEAL,
        "momentum": "Moderate",
        "drivers": (
            "Reliance Industries: FY26 EBITDA +13.4% to ₹2.08L cr. Jio+Retail now "
            "55% of group EBITDA. Jio IPO approaching = massive re-rating catalyst. "
            "RIL down 8% in 1 year — trading at discount to its own historical PE. "
            "Green energy Giga complex entering execution phase from investment phase."
        ),
        "valuation": "Fair/Attractive — PE ~20–22x; below its own 5-year avg; Jio IPO is unlocking event",
        "cagr_path": "Jio ARPU expansion + Retail customer base growth + Jio IPO re-rating → 15–18% CAGR",
        "risk": "Low-Medium",
        "key_risk": "O2C (refining) cyclicality; Jio IPO delays; green energy capex overrun",
    },
    {
        "id": "Power & Renewable Energy",
        "color": AMBER_MID,
        "momentum": "Strong",
        "drivers": (
            "NTPC Group PAT +15% FY26 to ₹27,546 cr. Record peak demand 271 GW "
            "May 2026. India needs 900 GW by FY32 (from 538 GW now). "
            "NTPC: 60% renewable target by 2032. Macquarie: Rs 480 target (35% upside). "
            "Power Grid: regulated 15.5% equity return assured on all new projects."
        ),
        "valuation": "Attractive — NTPC at ~12x PE; among the cheapest quality Nifty 50 stocks",
        "cagr_path": "Capacity addition + regulated tariffs + green energy transition → 14–18% total return",
        "risk": "Low",
        "key_risk": "Regulatory tariff revision; project execution delays; fuel cost spikes",
    },
    {
        "id": "Capital Goods & Cement",
        "color": STEEL,
        "momentum": "Strong",
        "drivers": (
            "L&T order book ₹5.66L cr (3x FY26 revenue). UltraTech crosses 200 mtpa "
            "domestic capacity; ₹10,255 cr expansion to 240 mtpa by FY28. "
            "Govt infra capex ₹12.2L cr in Union Budget 2026-27. "
            "UltraTech EPS CAGR forecast 24.6% per annum; Nomura top pick."
        ),
        "valuation": "Fair — L&T ~26x PE; UltraTech ~35–40x; premium warranted by order-book visibility",
        "cagr_path": "Backlog conversion + capacity utilisation + infra demand → 18–25% EPS CAGR",
        "risk": "Medium",
        "key_risk": "Execution lag; cement price volatility; private capex timing uncertainty",
    },
    {
        "id": "Healthcare & FMCG",
        "color": GREEN_OK,
        "momentum": "Moderate",
        "drivers": (
            "Sun Pharma: ROCE 25.6%, EBIT CAGR 20.79% (5yr); specialty US pipeline. "
            "ITC: Revenue ₹81,640 cr (+9.9%), PAT ₹20,286 cr. Cigarette monopoly "
            "generates huge free cash. FMCG segment +11% YoY. Hotel demerger "
            "unlocking hidden value. FMCG sector targeting ₹10.2L cr by 2026."
        ),
        "valuation": "Mixed — Sun Pharma fair at 36x; ITC cheap (PE ~25x ex-hotel demerger) with 3–4% div",
        "cagr_path": "Pharma specialty ramp + ITC hotel demerger value + dividend compounding → 12–18% CAGR",
        "risk": "Low-Medium",
        "key_risk": "US FDA risk (Sun Pharma); ITC cigarette volume risk from regulation; rural income pressure",
    },
]

STOCKS = [
    # ── BANKING ──
    {
        "no": 1, "company": "ICICI Bank", "ticker": "ICICIBANK", "exchange": "NSE",
        "sector": "Banking & PSU Banks", "nifty50": "Yes",
        "mktcap": "₹9.8L cr (Nifty Top 5)",
        "why": (
            "India's best private bank by NIM (4.4%) and ROE (17–18%). "
            "Improving operating leverage — costs stable while loan growth is strong. "
            "15–20% EPS CAGR projected FY26–28E. Capital adequacy 17.11%. "
            "Analysts: Elara Buy target Rs 1,783 (25%+ upside)."
        ),
        "risks": "NIM compression if rates cut sharply; unsecured loan slippage risk",
        "val": "Attractive — PE ~17x; 10–15% below own 5-yr average",
        "val_tag": "Attractive", "val_col": GREEN_OK,
        "roe": "17–18%", "roce": "N/A (Bank)",
        "sales_cagr": "~16%", "pat_cagr": "~22%",
        "de": "N/A; CAR 17.1%",
        "risk": "Medium", "risk_col": AMBER_MID,
    },
    {
        "no": 2, "company": "State Bank of India", "ticker": "SBIN", "exchange": "NSE",
        "sector": "Banking & PSU Banks", "nifty50": "Yes",
        "mktcap": "₹6.8L cr",
        "why": (
            "Record FY26 PAT ₹80,032 cr. ROE 18.57%, ROA 1.12% — best ever. "
            "Trades at just 1.1x book value: cheapest quality bank in India. "
            "Analyst targets Rs 880–1,000 (14–38% upside from Rs 760). "
            "Loan growth 11.6%; SME grew 19% YoY. Largest public sector bank."
        ),
        "risks": "PSU bank governance risk; NIM narrower than private peers; agri loan stress",
        "val": "Very Attractive — 1.1x book; cheapest major quality bank in India",
        "val_tag": "Attractive", "val_col": GREEN_OK,
        "roe": "18.6%", "roce": "N/A (Bank)",
        "sales_cagr": "~12%", "pat_cagr": "~15%",
        "de": "N/A; CAR ~14.3%",
        "risk": "Low-Med", "risk_col": "5DADE2",
    },
    {
        "no": 3, "company": "HDFC Bank", "ticker": "HDFCBANK", "exchange": "NSE",
        "sector": "Banking & PSU Banks", "nifty50": "Yes",
        "mktcap": "₹14.2L cr (Nifty #1)",
        "why": (
            "India's largest private bank by assets. Post-HDFC Ltd merger, ROE recovering "
            "to 16–17%, NIM at 3.8–4.0% (improving). PE 15.28x — below 10-yr avg. "
            "Merger-related overhang is lifting: loan-to-deposit ratio improving, "
            "deposit franchise outperforming sector. Multi-year re-rating potential."
        ),
        "risks": "Slower post-merger credit growth vs peers; NIM still below pre-merger levels",
        "val": "Fair/Attractive — PE 15.3x; below own 5-yr average; re-rating as merger benefits flow",
        "val_tag": "Attractive", "val_col": GREEN_OK,
        "roe": "15–17%", "roce": "N/A (Bank)",
        "sales_cagr": "~14%", "pat_cagr": "~15%",
        "de": "N/A; CAR ~18.8%",
        "risk": "Low-Med", "risk_col": "5DADE2",
    },
    # ── TELECOM ──
    {
        "no": 4, "company": "Bharti Airtel", "ticker": "BHARTIARTL", "exchange": "NSE",
        "sector": "Telecom (Digital India)", "nifty50": "Yes",
        "mktcap": "₹10.5L cr",
        "why": (
            "Q4 FY26: Revenue +15.7% YoY, PAT +38.7%, EBITDA margins 57.8%. "
            "ARPU Rs 257 → targeting Rs 300 as 5G monetisation deepens. "
            "181 million 5G customers; 74% India coverage. Duopoly with Jio = pricing power. "
            "Africa business adds optionality. Nirmal Bang: Buy with strong ARPU growth thesis."
        ),
        "risks": "Jio ARPU undercut risk; huge spectrum debt (though deleveraging); Africa FX",
        "val": "Fair-to-Premium — PE ~35–40x; justified by margin expansion and ARPU tailwind",
        "val_tag": "Fair/Premium", "val_col": AMBER_MID,
        "roe": "~25–30%", "roce": "~12–15%",
        "sales_cagr": "~18%", "pat_cagr": "~30%+",
        "de": "~1.2x (declining; spectrum debt)",
        "risk": "Low-Med", "risk_col": "5DADE2",
    },
    # ── DIVERSIFIED ──
    {
        "no": 5, "company": "Reliance Industries", "ticker": "RELIANCE", "exchange": "NSE",
        "sector": "Diversified Conglomerate", "nifty50": "Yes",
        "mktcap": "₹16.5L cr (Nifty #1 by mktcap)",
        "why": (
            "FY26 EBITDA +13.4% to ₹2.08L cr. Jio+Retail now 55% of EBITDA. "
            "Jio IPO approaching — massive value unlocking event. "
            "Down 8% in 1 year; trades at discount to own historical PE. "
            "Net debt/EBITDA 0.6x (comfortable). Green Energy Giga complex operational."
        ),
        "risks": "O2C (refining) cyclicality; Jio IPO timeline uncertainty; huge capex commitments",
        "val": "Fair/Attractive — PE ~20–22x; at discount to own 5-yr avg; Jio IPO = re-rating trigger",
        "val_tag": "Attractive", "val_col": GREEN_OK,
        "roe": "~12–14%", "roce": "~10–12%",
        "sales_cagr": "~12%", "pat_cagr": "~12%",
        "de": "~0.5x (net D/E; comfortable)",
        "risk": "Low-Med", "risk_col": "5DADE2",
    },
    # ── AUTO ──
    {
        "no": 6, "company": "Mahindra & Mahindra", "ticker": "M&M", "exchange": "NSE",
        "sector": "Automobiles & Auto Ancillaries", "nifty50": "Yes",
        "mktcap": "₹4.0L cr",
        "why": (
            "FY26 PAT +35% to ₹17,099 cr; Revenue +25% to ₹1,98,639 cr. "
            "#1 SUV maker by revenue share (25.3%); #1 EV by revenue. "
            "EV sales target 18–20% by FY27. Tractor market share 43.6%. "
            "EV biz Q1 EBITDA positive. Strong execution across auto + farm + defence."
        ),
        "risks": "EV margin dilution in near term; commodity cost spikes; competition in SUV space",
        "val": "Fair — PE ~25–28x; reasonable for 30%+ PAT growth; EV optionality not priced in",
        "val_tag": "Fair", "val_col": AMBER_MID,
        "roe": "~20–22%", "roce": "~18%",
        "sales_cagr": "~18%", "pat_cagr": "~25%",
        "de": "~0.1x (near debt-free auto biz)",
        "risk": "Medium", "risk_col": AMBER_MID,
    },
    {
        "no": 7, "company": "Maruti Suzuki India", "ticker": "MARUTI", "exchange": "NSE",
        "sector": "Automobiles & Auto Ancillaries", "nifty50": "Yes",
        "mktcap": "₹3.8L cr",
        "why": (
            "India's largest passenger vehicle maker (42% market share). "
            "FY26 revenue ₹1,87,673 cr; Q1 FY26 revenue +28.7%. "
            "Successfully pivoted to SUV segment (Brezza, Grand Vitara, Fronx, Invicto). "
            "Strong CNG leadership. Suzuki partnership = technology + export platform. "
            "10-yr revenue CAGR 12%; accelerating with SUV mix shift."
        ),
        "risks": "EV latecomer risk; Japanese yen appreciation raising costs; competition from Hyundai/Tata",
        "val": "Fair — PE ~25x; reasonable for India's auto market leader; dividend yield ~1.5%",
        "val_tag": "Fair", "val_col": AMBER_MID,
        "roe": "~18–20%", "roce": "~22%",
        "sales_cagr": "~14%", "pat_cagr": "~18%",
        "de": "Zero debt (net cash ₹50,000+ cr)",
        "risk": "Low-Med", "risk_col": "5DADE2",
    },
    # ── POWER ──
    {
        "no": 8, "company": "NTPC", "ticker": "NTPC", "exchange": "NSE",
        "sector": "Power & Renewable Energy", "nifty50": "Yes",
        "mktcap": "₹3.6L cr",
        "why": (
            "Group PAT +15% FY26 to ₹27,546 cr. India's largest power generator (74GW+). "
            "Targets 60% renewable by 2032 via NTPC Green Energy. "
            "Macquarie: Buy target Rs 480 (35% upside). PE ~12x — lowest in Nifty 50. "
            "Peak demand 271 GW May 2026 (record) creates utilisation + tariff tailwind."
        ),
        "risks": "Regulated tariff model caps upside; project execution risk; coal price volatility",
        "val": "Attractive — PE ~12x; significant discount to Nifty avg ~21x; 2–3% div yield",
        "val_tag": "Attractive", "val_col": GREEN_OK,
        "roe": "~13–14%", "roce": "~10–11%",
        "sales_cagr": "~12%", "pat_cagr": "~15%",
        "de": "~1.5x (infra leverage; acceptable)",
        "risk": "Low", "risk_col": GREEN_OK,
    },
    # ── CAPITAL GOODS / CEMENT ──
    {
        "no": 9, "company": "Larsen & Toubro", "ticker": "LT", "exchange": "NSE",
        "sector": "Capital Goods & Cement", "nifty50": "Yes",
        "mktcap": "₹5.6L cr",
        "why": (
            "India's #1 EPC + Engineering conglomerate. Order book ₹5.66L cr = 3x FY26 revenue. "
            "Diversified across infra, defence, green energy, and IT services. "
            "Govt capex ₹12.2L cr FY27 = direct order beneficiary. "
            "ROE recovering; PAT CAGR ~18–20% over 3-year horizon from backlog conversion."
        ),
        "risks": "Execution lag on large projects; working capital intensity; private capex delay",
        "val": "Fair — PE ~26x; not cheap but 3x revenue order book provides strong earnings floor",
        "val_tag": "Fair", "val_col": AMBER_MID,
        "roe": "~14–15%", "roce": "~12–14%",
        "sales_cagr": "~14%", "pat_cagr": "~18%",
        "de": "~0.3x (ex-financial services arm)",
        "risk": "Medium", "risk_col": AMBER_MID,
    },
    {
        "no": 10, "company": "UltraTech Cement", "ticker": "ULTRACEMCO", "exchange": "NSE",
        "sector": "Capital Goods & Cement", "nifty50": "Yes",
        "mktcap": "₹3.2L cr",
        "why": (
            "India's largest cement company. FY26 revenue ₹89,089 cr (+16.2%). "
            "Crossed 200 mtpa domestic capacity in FY26; expanding to 240 mtpa by FY28. "
            "EPS CAGR forecast 24.6% per annum. Nomura top pick. "
            "Infra capex boom = sustained volume demand for next 5+ years."
        ),
        "risks": "Cement price volatility (excess supply risk); high capex outlay; PE premium at 35–40x",
        "val": "Fair-to-Premium — PE ~35–40x; high but EPS CAGR of 24–25% makes PEG attractive at ~1.5x",
        "val_tag": "Fair/Premium", "val_col": AMBER_MID,
        "roe": "~11–14%", "roce": "~13–15%",
        "sales_cagr": "~14%", "pat_cagr": "~20%",
        "de": "~0.4x",
        "risk": "Medium", "risk_col": AMBER_MID,
    },
    # ── HEALTHCARE ──
    {
        "no": 11, "company": "Sun Pharmaceutical", "ticker": "SUNPHARMA", "exchange": "NSE",
        "sector": "Healthcare & FMCG", "nifty50": "Yes",
        "mktcap": "₹4.0L cr",
        "why": (
            "India's largest pharma by revenue and market cap. FY26 revenue ₹58,220 cr (+11.9%). "
            "ROCE 25.6%, 5-yr EBIT CAGR 20.79%. Specialty US brands (Ilumya, Cequa) growing fast. "
            "Semaglutide generics = ₹12,000 cr potential market. 67% international revenue."
        ),
        "risks": "US FDA plant inspection risk; specialty product launch delays; generic price erosion",
        "val": "Fair — PE ~36x; premium to peers (Dr Reddy's 26x, Cipla 27x) for specialty pipeline",
        "val_tag": "Fair", "val_col": AMBER_MID,
        "roe": "~15%", "roce": "~25.6%",
        "sales_cagr": "~11%", "pat_cagr": "~17%",
        "de": "~0.1x (near debt-free)",
        "risk": "Medium", "risk_col": AMBER_MID,
    },
    # ── FMCG ──
    {
        "no": 12, "company": "ITC", "ticker": "ITC", "exchange": "NSE",
        "sector": "Healthcare & FMCG", "nifty50": "Yes",
        "mktcap": "₹5.3L cr",
        "why": (
            "FY26 Revenue ₹81,640 cr (+9.9%), PAT ₹20,286 cr. Cigarette monopoly "
            "generates massive free cash. FMCG +11% YoY; Hotels demerger = value unlock. "
            "ROE 30%+ on cigarette capital. Dividend ₹8/share; ~3–4% yield. "
            "EPS CAGR may seem modest (~8–10%) but total return = EPS growth + 3–4% dividend + "
            "potential PE re-rating as FMCG mix grows. Extremely low-risk compounder."
        ),
        "risks": "Cigarette volume growth slowdown; regulatory risk on tobacco; FMCG competition",
        "val": "Fair/Cheap — PE ~25x (ex-hotel, ex-agri); well below consumer peers at 45–60x",
        "val_tag": "Cheap", "val_col": GREEN_OK,
        "roe": "~30%+ (cigarette biz)", "roce": "~28%",
        "sales_cagr": "~10%", "pat_cagr": "~8–10%",
        "de": "Zero debt (net cash positive)",
        "risk": "Low", "risk_col": GREEN_OK,
    },
]

FRAMEWORK = [
    ("5-Year Revenue CAGR",          "≥ 10% (prefer ≥ 14%)",
     "For bluechip large-caps, 10%+ revenue CAGR over 5 years signals durable demand. "
     "Bluechips grow slower than mid-caps — total return comes from earnings + PE re-rating + dividends.",
     "10–14%+"),
    ("5-Year PAT (Profit) CAGR",     "≥ 12% (prefer ≥ 15%)",
     "Profits must grow faster than revenue via operating leverage. Watch for one-time items "
     "inflating PAT (e.g., asset sales, deferred tax). Check operating PAT separately.",
     "12–15%+"),
    ("ROE (Return on Equity)",       "≥ 15% for non-financials; ≥ 16% for banks (with CAR ≥ 14%)",
     "Sustained ROE > 15% with low debt = genuine value creation. Avoid 'debt-inflated ROE'. "
     "For banks, use ROA ≥ 1.0% as additional filter (PSU banks: ROA ≥ 0.9%).",
     "≥ 15–18%"),
    ("ROCE (Return on Capital)",     "≥ 12% for capital-intensive; ≥ 20% for asset-light",
     "ROCE > cost of capital (12% WACC) = economic value creation. Capital-intensive sectors "
     "(infra, cement) naturally have lower ROCE but it should be trending up.",
     "≥ 12–20%"),
    ("Debt-to-Equity Ratio",         "≤ 0.5x (≤ 1.5x for infra/power; Banks: CAR ≥ 14%)",
     "Bluechips can carry moderate leverage if cash flows are predictable. "
     "Infra/Power: higher D/E is normal. Red flag: non-financial firm with D/E > 2.0x.",
     "≤ 0.5–1.5x"),
    ("Interest Coverage Ratio",      "≥ 4x (floor: 3x)",
     "EBIT / Interest Expense. A bluechip should comfortably service debt even in a downturn. "
     "Below 3x = watch closely. Banks: use Net Interest Margin (NIM) > 3% instead.",
     "≥ 4x"),
    ("PE vs 5-Year Historical Avg",  "Prefer ≤ 1.0x own historical PE",
     "For bluechips, buying at or below their 5-year average PE significantly improves "
     "your probability of 16%+ total return. Avoid stocks at 1.5–2x their own avg PE.",
     "≤ 100–110% of 5yr avg"),
    ("Promoter / Institutional Hold","Promoter: stable; FII+DII combined ≥ 40%",
     "For PSU banks: Govt holding 51%+ is fine. For private companies, watch promoter "
     "pledging — above 25% of their holding is a red flag. DII buying = vote of confidence.",
     "Stable/increasing hold"),
    ("Dividend Yield + Buyback",     "≥ 1.5% yield or active buyback",
     "For bluechips aiming at 16% total return: even 2–3% dividend yield means you need "
     "only 13–14% price appreciation. Buybacks are tax-efficient alternative to dividends.",
     "≥ 1.5–3%"),
    ("Market Cap & Liquidity",       "Nifty 100 constituent; daily vol ≥ ₹100 cr",
     "True bluechips have high institutional ownership, analyst coverage, and daily liquidity. "
     "Minimum ₹10,000 cr market cap; prefer Nifty 50 / Nifty Next 50 constituents.",
     "₹10,000 cr+ / Nifty 100"),
]

WATCHLIST = [
    ("Banking", "ICICI Bank", "ICICIBANK",
     "ROE 17–18%; NIM 4.4% (best in class); 15–20% EPS CAGR; analyst: Rs 1,783 target (+25%)",
     "NIM compression; unsecured loan stress", "Attractive (PE ~17x)", "Medium"),
    ("Banking", "State Bank of India", "SBIN",
     "Record PAT ₹80,032 cr; ROE 18.57%; 1.1x book (cheapest quality bank); 14–38% analyst upside",
     "PSU governance risk; narrower NIM vs private peers", "Very Attractive (1.1x book)", "Low-Med"),
    ("Banking", "HDFC Bank", "HDFCBANK",
     "India's largest private bank; merger overhang lifting; ROE recovering; PE 15.3x below avg",
     "Slow post-merger loan growth; NIM below pre-merger level", "Attractive (PE ~15x)", "Low-Med"),
    ("Telecom", "Bharti Airtel", "BHARTIARTL",
     "Q4 revenue +15.7%, PAT +38.7%; ARPU ₹257→₹300 target; 5G 74% India coverage; EBITDA margin 57.8%",
     "Jio ARPU undercut; spectrum debt (deleveraging); Africa FX", "Fair/Premium (PE ~38x)", "Low-Med"),
    ("Diversified", "Reliance Industries", "RELIANCE",
     "EBITDA +13.4%; Jio+Retail = 55% EBITDA; Jio IPO = re-rating catalyst; at discount to own history",
     "O2C cyclicality; Jio IPO timing; green energy capex risk", "Attractive (PE ~21x)", "Low-Med"),
    ("Auto", "Mahindra & Mahindra", "M&M",
     "PAT +35%; Revenue +25%; #1 SUV (25.3% share); #1 EV by revenue; tractor leader 43.6%",
     "EV margin dilution; commodity costs; SUV competition", "Fair (PE ~27x)", "Medium"),
    ("Auto", "Maruti Suzuki", "MARUTI",
     "India's largest carmaker (42% share); Q1 revenue +28.7%; SUV pivot; ₹50,000+ cr net cash",
     "EV latecomer risk; Japanese yen cost risk; Hyundai/Tata competition", "Fair (PE ~25x)", "Low-Med"),
    ("Power", "NTPC", "NTPC",
     "PAT +15% FY26; 74GW+ capacity; Macquarie target Rs 480 (35% up); cheapest Nifty 50 at PE ~12x",
     "Regulated tariff caps upside; project delays; coal price volatility", "Attractive (PE ~12x)", "Low"),
    ("Cap Goods", "Larsen & Toubro", "LT",
     "Order book ₹5.66L cr (3x revenue); diversified infra+defence+green; PAT CAGR 18–20% forecast",
     "Execution lag; working capital; private capex timing", "Fair (PE ~26x)", "Medium"),
    ("Cement", "UltraTech Cement", "ULTRACEMCO",
     "Revenue +16.2%; 200 mtpa+ capacity; EPS CAGR 24.6% forecast; Nomura top pick; 240 mtpa by FY28",
     "Cement price volatility; capex intensity; premium valuation", "Fair/Premium (PE ~38x)", "Medium"),
    ("Pharma", "Sun Pharmaceutical", "SUNPHARMA",
     "ROCE 25.6%; EBIT CAGR 21% (5yr); specialty US brands; semaglutide generics opportunity",
     "US FDA risk; specialty ramp timeline; generic price erosion", "Fair (PE ~36x)", "Medium"),
    ("FMCG", "ITC", "ITC",
     "ROE 30%+ (cigarettes); FY26 PAT ₹20,286 cr; 3–4% dividend yield; hotel demerger value unlock",
     "Cigarette volume risk; regulatory risk; FMCG competition", "Fair/Cheap (PE ~25x)", "Low"),
]

# ═══════════════════════════════════════════════════════════════════════════
# BUILD WORKBOOK
# ═══════════════════════════════════════════════════════════════════════════
wb = openpyxl.Workbook()
wb.remove(wb.active)

SECTOR_COLOR_MAP = {s["id"]: s["color"] for s in SECTORS}

# ─────────────────────────────────────────────────────────────────────────
# SHEET 1 · COVER
# ─────────────────────────────────────────────────────────────────────────
ws1 = wb.create_sheet("01 · Cover & Overview")
ws1.sheet_view.showGridLines = False

# Full dark background rows 1-18
for r in range(1, 20):
    ws1.row_dimensions[r].height = 22
    for c in range(1, 15):
        ws1.cell(r, c).fill = hf(MIDNIGHT)

# Saffron stripe
ws1.row_dimensions[1].height = 6
for c in range(1, 15):
    ws1.cell(1, c).fill = hf(SAFFRON)

# Title
ms(ws1, "B3:N5", "INDIA BLUECHIP EQUITY WATCHLIST",
   MIDNIGHT, fsz=28, bold=True, fc=GOLD_ACC)
ms(ws1, "B6:N7",
   "Nifty 50 / Large-Cap Research | 16% CAGR Target | 2-Year Horizon | NSE/BSE",
   MIDNIGHT, fsz=13, bold=False, fc="C8D6E5")
ms(ws1, "B8:N9",
   f"Date: {datetime.date.today().strftime('%B %d, %Y')}  ·  "
   "All 12 stocks are Nifty 50 constituents  ·  Sectors: 7  ·  Research Candidates: 12",
   MIDNIGHT, fsz=10, bold=False, fc="7F8C9A")

# Saffron divider
ws1.row_dimensions[10].height = 5
for c in range(1, 15):
    ws1.cell(10, c).fill = hf(SAFFRON)

# Disclaimer
ms(ws1, "B11:N13",
   "⚠  IMPORTANT: This document presents research candidates for personal study only and does NOT "
   "constitute investment advice or buy/sell recommendations. Past performance is not indicative "
   "of future results. All data sourced from publicly available broker reports and company filings "
   "(June 2026). Please consult a SEBI-registered investment adviser before taking any action.",
   "2C1A00", fsz=9, bold=False, fc=GOLD_ACC, halign="center")

# KPI cards
kpi_data = [
    ("B", "D", "12\nNifty 50\nStocks",    MIDNIGHT),
    ("E", "G", "7\nSectors\nCovered",     ROYAL),
    ("H", "J", "16%+\nTarget\nCAGR",      SAFFRON),
    ("K", "M", "2-Year\nInvestment\nHorizon", EMERALD),
]
for start, end, label, bg in kpi_data:
    rng = f"{start}19:{end}22"
    ws1.merge_cells(rng)
    c = ws1[f"{start}19"]
    c.value = label
    c.fill = hf(bg)
    c.font = Font(name="Calibri", size=15, bold=True, color=WHITE)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = Border(
        top=Side(style="medium", color=SAFFRON),
        bottom=Side(style="medium", color=SAFFRON),
        left=Side(style="medium", color=SAFFRON),
        right=Side(style="medium", color=SAFFRON),
    )
for r in range(19, 23):
    ws1.row_dimensions[r].height = 22

# Macro Snapshot
row = 24
ms(ws1, f"B{row}:N{row}", "MACRO SNAPSHOT — INDIA JUNE 2026",
   ROYAL, fsz=12, bold=True, fc=GOLD_ACC)
ws1.row_dimensions[row].height = 28

macro = [
    ("Nifty 50 Trailing PE",   "~20.9x",       "~11% discount to 10-yr average of 23.4x — market not expensive"),
    ("Nifty Bank PE",          "~14–16x",       "Significantly below 5-yr average of 18–20x — banking deeply discounted"),
    ("RBI Repo Rate",          "5.25%",         "Near-bottom rate cycle; potential cuts ahead = equity re-rating catalyst"),
    ("India GDP FY27E",        "~6.5–7%",       "Fastest growing major economy; nominal GDP growth ~10–11%"),
    ("Nifty 500 PAT Growth",   "~21.6% YoY",   "Broad market profit growth as of May 2026; earnings recovery on track"),
    ("Govt Infra Capex FY27",  "₹12.2L Crore", "Record Union Budget allocation; direct tailwind for L&T, NTPC, UltraTech"),
    ("Peak Power Demand",      "271 GW",        "Record May 2026; 275–285 GW forecast — NTPC, Power Grid beneficiaries"),
    ("Nifty IT Correction",    "–24% in 2026",  "AI-disruption fear = opportunity to buy quality IT at reasonable prices"),
]
for i, (m, v, n) in enumerate(macro):
    r = row + 1 + i
    ws1.row_dimensions[r].height = 22
    bg = LIGHT_STEEL if i % 2 == 0 else WHITE
    wc(ws1, r, 2, m,  bg, fsz=10, bold=True,  fc=ROYAL,   halign="left")
    ws1.cell(r, 2).alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws1.merge_cells(f"B{r}:B{r}")
    wc(ws1, r, 3, v,  bg, fsz=11, bold=True,  fc=SAFFRON, halign="center")
    ws1.merge_cells(f"C{r}:D{r}")
    wc(ws1, r, 5, n,  bg, fsz=9,  bold=False, fc="444444", halign="left", wrap=True)
    ws1.merge_cells(f"E{r}:N{r}")
    ws1.cell(r, 5).alignment = Alignment(horizontal="left", vertical="center", wrap_text=True, indent=1)

# Navigation
nav = row + len(macro) + 2
ws1.row_dimensions[nav].height = 26
ms(ws1, f"B{nav}:N{nav}", "WORKBOOK NAVIGATION", EMERALD, fsz=11, bold=True, fc=WHITE)
sheets = [
    ("01 · Cover & Overview",        "This page — macro context, KPI summary, workbook guide"),
    ("02 · Sector Landscape",        "7 sectors: drivers, valuation, path to 16% CAGR, risks"),
    ("03 · Stock Deep-Dive",         "12 Nifty 50 research candidates with full fundamental profile"),
    ("04 · Selection Framework",     "Your personalised screening criteria — thresholds + step-by-step guide"),
    ("05 · Watchlist Summary",       "Board-ready summary table: colour-coded by valuation and risk"),
    ("06 · Risk & Return Matrix",    "Risk-return positioning + PAT CAGR bar chart for all 12 stocks"),
]
for i, (sh, desc) in enumerate(sheets):
    r = nav + 1 + i
    ws1.row_dimensions[r].height = 20
    bg = LIGHT_CREAM if i % 2 == 0 else WHITE
    wc(ws1, r, 2, sh,   bg, fsz=10, bold=True,  fc=MIDNIGHT, halign="left")
    ws1.merge_cells(f"B{r}:E{r}")
    wc(ws1, r, 6, desc, bg, fsz=10, bold=False, fc="333333", halign="left")
    ws1.merge_cells(f"F{r}:N{r}")

for col, w in [(1,2),(2,20),(3,8),(4,8),(5,42),(6,2),(7,2),(8,2),(9,2),(10,2),(11,2),(12,2),(13,2),(14,2)]:
    scw(ws1, col, w)

# ─────────────────────────────────────────────────────────────────────────
# SHEET 2 · SECTOR LANDSCAPE
# ─────────────────────────────────────────────────────────────────────────
ws2 = wb.create_sheet("02 · Sector Landscape")
ws2.sheet_view.showGridLines = False

ms(ws2, "A1:I1", "SECTOR LANDSCAPE — 7 HIGH-POTENTIAL SECTORS FOR BLUECHIP 16% CAGR",
   MIDNIGHT, fsz=13, bold=True, fc=GOLD_ACC)
ws2.row_dimensions[1].height = 34

h2 = ["#", "Sector", "Momentum", "Structural Drivers (2025–27)",
      "Valuation vs History", "Path to 16%+ CAGR", "Key Risk", "Risk Level"]
w2 = [4,  26,        12,         52,
      34,              40,             28,          13]

r = 2
ws2.row_dimensions[r].height = 26
for ci, (h, w) in enumerate(zip(h2, w2), 1):
    c = ws2.cell(r, ci, h)
    c.fill = hf(ROYAL)
    c.font = Font(name="Calibri", size=10, bold=True, color=WHITE)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = tb()
    scw(ws2, ci, w)

for i, s in enumerate(SECTORS):
    r = 3 + i
    ws2.row_dimensions[r].height = 88
    bg = LIGHT_STEEL if i % 2 == 0 else WHITE
    rmap = {"Low": GREEN_OK, "Low-Medium": "5DADE2", "Medium": AMBER_MID, "High": RED_HIGH}
    rbg = rmap.get(s["risk"].replace("-Med","").replace("-Medium",""), AMBER_MID)

    row_data = [
        (i+1,           "center", False, DARK_TXT, bg),
        (s["id"],       "left",   True,  WHITE,    s["color"]),
        (s["momentum"], "center", True,  DARK_TXT, bg),
        (s["drivers"],  "left",   False, DARK_TXT, bg),
        (s["valuation"],"left",   False, DARK_TXT, bg),
        (s["cagr_path"],"left",   False, DARK_TXT, bg),
        (s["key_risk"], "left",   False, DARK_TXT, bg),
        (s["risk"],     "center", True,  WHITE,    rbg),
    ]
    for ci, (val, al, bd, fc, fb) in enumerate(row_data, 1):
        c = ws2.cell(r, ci, val)
        c.fill = hf(fb)
        c.font = Font(name="Calibri", size=9, bold=bd, color=fc)
        c.alignment = Alignment(horizontal=al, vertical="top", wrap_text=True, indent=1)
        c.border = tb()

# ─────────────────────────────────────────────────────────────────────────
# SHEET 3 · STOCK DEEP-DIVE
# ─────────────────────────────────────────────────────────────────────────
ws3 = wb.create_sheet("03 · Stock Deep-Dive")
ws3.sheet_view.showGridLines = False

ms(ws3, "A1:L1",
   "BLUECHIP RESEARCH CANDIDATES — 12 NIFTY 50 STOCKS (NOT Buy/Sell Recommendations)",
   MIDNIGHT, fsz=13, bold=True, fc=GOLD_ACC)
ws3.row_dimensions[1].height = 34

h3 = ["#", "Company (NSE)", "Ticker", "Sector", "Market Cap",
      "Why it fits 16% CAGR", "Key Risks", "Valuation",
      "ROE", "5Y Rev CAGR", "5Y PAT CAGR", "Risk"]
w3 = [4,   24,              12,       20,      16,
      52,                   34,        28,
      12,  13,              13,        12]

r = 2
ws3.row_dimensions[r].height = 26
for ci, (h, w) in enumerate(zip(h3, w3), 1):
    c = ws3.cell(r, ci, h)
    c.fill = hf(ROYAL)
    c.font = Font(name="Calibri", size=10, bold=True, color=WHITE)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = tb()
    scw(ws3, ci, w)

for i, st in enumerate(STOCKS):
    r = 3 + i
    ws3.row_dimensions[r].height = 88
    bg = LIGHT_STEEL if i % 2 == 0 else WHITE
    sc = SECTOR_COLOR_MAP.get(st["sector"], ROYAL)

    vals = [
        (st["no"],       "center", False, DARK_TXT, bg),
        (st["company"],  "left",   True,  MIDNIGHT, bg),
        (st["ticker"],   "center", True,  WHITE,    SAFFRON),
        (st["sector"],   "center", True,  WHITE,    sc),
        (st["mktcap"],   "center", False, DARK_TXT, bg),
        (st["why"],      "left",   False, DARK_TXT, bg),
        (st["risks"],    "left",   False, "555555", bg),
        (st["val"],      "left",   True,  WHITE,    st["val_col"]),
        (st["roe"],      "center", True,  DARK_TXT, bg),
        (st["sales_cagr"],"center",True,  DARK_TXT, bg),
        (st["pat_cagr"], "center", True,  DARK_TXT, bg),
        (st["risk"],     "center", True,  WHITE,    st["risk_col"]),
    ]
    for ci, (val, al, bd, fc, fb) in enumerate(vals, 1):
        c = ws3.cell(r, ci, val)
        c.fill = hf(fb)
        c.font = Font(name="Calibri", size=9, bold=bd, color=fc)
        c.alignment = Alignment(horizontal=al, vertical="top", wrap_text=True, indent=1)
        c.border = tb()

ws3.freeze_panes = "A3"

# ─────────────────────────────────────────────────────────────────────────
# SHEET 4 · SELECTION FRAMEWORK
# ─────────────────────────────────────────────────────────────────────────
ws4 = wb.create_sheet("04 · Selection Framework")
ws4.sheet_view.showGridLines = False

ms(ws4, "A1:F1",
   "BLUECHIP STOCK SELECTION FRAMEWORK — Thresholds for 16%+ CAGR Candidates",
   MIDNIGHT, fsz=13, bold=True, fc=GOLD_ACC)
ws4.row_dimensions[1].height = 34

ms(ws4, "A2:F2",
   "Verify each stock against these criteria on Screener.in / Tijori Finance / Tickertape.in before investing.",
   ROYAL, fsz=10, bold=False, fc=LIGHT_STEEL)
ws4.row_dimensions[2].height = 22

h4 = ["#", "Criterion", "Minimum Threshold", "Why It Matters for Bluechips", "Benchmark"]
w4 = [4,   30,           22,                  56,                              18]

r = 3
ws4.row_dimensions[r].height = 26
for ci, (h, w) in enumerate(zip(h4, w4), 1):
    c = ws4.cell(r, ci, h)
    c.fill = hf(ROYAL)
    c.font = Font(name="Calibri", size=10, bold=True, color=WHITE)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = tb()
    scw(ws4, ci, w)

for i, (crit, thresh, why, bench) in enumerate(FRAMEWORK):
    r = 4 + i
    ws4.row_dimensions[r].height = 68
    bg = LIGHT_STEEL if i % 2 == 0 else WHITE
    row_data = [
        (i+1,   "center", False, DARK_TXT, bg),
        (crit,  "left",   True,  MIDNIGHT, bg),
        (thresh,"center", True,  WHITE,    EMERALD),
        (why,   "left",   False, DARK_TXT, bg),
        (bench, "center", True,  WHITE,    SAFFRON),
    ]
    for ci, (val, al, bd, fc, fb) in enumerate(row_data, 1):
        c = ws4.cell(r, ci, val)
        c.fill = hf(fb)
        c.font = Font(name="Calibri", size=9, bold=bd, color=fc)
        c.alignment = Alignment(horizontal=al, vertical="top", wrap_text=True, indent=1)
        c.border = tb()

# Step-by-step guide
gr = 4 + len(FRAMEWORK) + 2
ws4.row_dimensions[gr].height = 26
ms(ws4, f"A{gr}:F{gr}",
   "PRACTICAL STEP-BY-STEP GUIDE — How to Use This Framework", EMERALD, fsz=11, bold=True, fc=WHITE)

steps = [
    ("Step 1", "Go to screener.in → Custom Screen. Set: Revenue growth 5yr > 10, Profit growth 5yr > 12, ROE > 14, Debt/Equity < 1.5. Filter by Large Cap."),
    ("Step 2", "Cross-reference filtered list with Nifty 50 / Nifty Next 50 constituents. These are your safest bluechip universe."),
    ("Step 3", "For each shortlisted stock: Compare current PE to its own 5-year average PE (use Tijori Finance → 'Valuation History')."),
    ("Step 4", "Check if PAT growth is genuine: open the P&L on screener.in and verify last 5 years of operating profit (not just PAT)."),
    ("Step 5", "For banks: use ROE > 15% + Net NPA < 1.5% + CAR > 14% instead of standard D/E ratio."),
    ("Step 6", "Check promoter holding trend on BSE filings: steady or increasing = positive signal. Any large pledge % = flag."),
    ("Step 7", "Build 10–12 stock portfolio across ≥ 5 sectors. No single stock > 15% of portfolio. Review after each quarterly result."),
    ("Step 8", "Total return check: Price CAGR target + Dividend yield = 16%+. Example: 14% price CAGR + 2.5% dividend = 16.5% total return."),
]
for i, (step, desc) in enumerate(steps):
    r = gr + 1 + i
    ws4.row_dimensions[r].height = 32
    bg = LIGHT_CREAM if i % 2 == 0 else WHITE
    wc(ws4, r, 1, step, SAFFRON, fsz=10, bold=True, fc=WHITE, halign="center")
    wc(ws4, r, 2, desc, bg, fsz=9, bold=False, fc=DARK_TXT, halign="left", wrap=True)
    ws4.merge_cells(f"B{r}:F{r}")

# ─────────────────────────────────────────────────────────────────────────
# SHEET 5 · WATCHLIST SUMMARY
# ─────────────────────────────────────────────────────────────────────────
ws5 = wb.create_sheet("05 · Watchlist Summary")
ws5.sheet_view.showGridLines = False

ms(ws5, "A1:H1",
   "INDIA BLUECHIP WATCHLIST — 12 RESEARCH CANDIDATES | 16% CAGR TARGET | JUNE 2026",
   MIDNIGHT, fsz=13, bold=True, fc=GOLD_ACC)
ws5.row_dimensions[1].height = 34

ms(ws5, "A2:H2",
   "For personal research only · Not a buy/sell recommendation · All 12 stocks are Nifty 50 constituents",
   ROYAL, fsz=9, bold=False, fc=LIGHT_STEEL)
ws5.row_dimensions[2].height = 22

h5 = ["#", "Sector", "Company", "Ticker (NSE)",
      "Why it fits 16% CAGR", "Key Risks", "Valuation View", "Risk"]
w5 = [4,   22,        24,        14,
      54,              34,        26,          12]

r = 3
ws5.row_dimensions[r].height = 26
for ci, (h, w) in enumerate(zip(h5, w5), 1):
    c = ws5.cell(r, ci, h)
    c.fill = hf(ROYAL)
    c.font = Font(name="Calibri", size=10, bold=True, color=WHITE)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = tb()
    scw(ws5, ci, w)

val_color_map = {
    "Attractive":    GREEN_OK,
    "Very Attractive": GREEN_OK,
    "Fair":          AMBER_MID,
    "Fair/Premium":  AMBER_MID,
    "Fair/Cheap":    "5DADE2",
    "Cheap":         GREEN_OK,
    "Expensive":     RED_HIGH,
}
risk_color_map = {
    "Low":     GREEN_OK,
    "Low-Med": "5DADE2",
    "Medium":  AMBER_MID,
    "Med-High":"D35400",
    "High":    RED_HIGH,
}

current_sec = None
row_num = 4

for i, (sec, co, tick, why, risks, val, risk) in enumerate(WATCHLIST):
    if sec != current_sec:
        ws5.row_dimensions[row_num].height = 20
        ms(ws5, f"A{row_num}:H{row_num}",
           f"  ── {sec.upper()} ──",
           ROYAL, fsz=9, bold=True, fc=GOLD_ACC, halign="left")
        row_num += 1
        current_sec = sec

    r = row_num
    ws5.row_dimensions[r].height = 72
    bg = LIGHT_STEEL if i % 2 == 0 else WHITE
    sc = SECTOR_COLOR_MAP.get(
        next((s["id"] for s in SECTORS if any(kw in s["id"] for kw in sec.split())), ""), ROYAL)

    val_tag = val.split("(")[0].strip()
    vbg = val_color_map.get(val_tag, AMBER_MID)
    rbg = risk_color_map.get(risk, AMBER_MID)

    row_data = [
        (i+1,  "center", False, DARK_TXT, bg),
        (sec,  "center", True,  WHITE,    sc),
        (co,   "left",   True,  MIDNIGHT, bg),
        (tick, "center", True,  WHITE,    SAFFRON),
        (why,  "left",   False, DARK_TXT, bg),
        (risks,"left",   False, "555555", bg),
        (val,  "left",   True,  WHITE,    vbg),
        (risk, "center", True,  WHITE,    rbg),
    ]
    for ci, (val_d, al, bd, fc, fb) in enumerate(row_data, 1):
        c = ws5.cell(r, ci, val_d)
        c.fill = hf(fb)
        c.font = Font(name="Calibri", size=9, bold=bd, color=fc)
        c.alignment = Alignment(horizontal=al, vertical="top", wrap_text=True, indent=1)
        c.border = tb()
    row_num += 1

ws5.freeze_panes = "A4"

# ─────────────────────────────────────────────────────────────────────────
# SHEET 6 · RISK & RETURN MATRIX
# ─────────────────────────────────────────────────────────────────────────
ws6 = wb.create_sheet("06 · Risk & Return Matrix")
ws6.sheet_view.showGridLines = False

ms(ws6, "A1:K1", "RISK & RETURN MATRIX — All 12 Bluechip Research Candidates",
   MIDNIGHT, fsz=13, bold=True, fc=GOLD_ACC)
ws6.row_dimensions[1].height = 34
ms(ws6, "A2:K2",
   "Green = Attractive / Low Risk  ·  Amber = Fair / Medium Risk  ·  Blue = Fair / Low-Med Risk  ·  Red = Expensive / High Risk",
   ROYAL, fsz=9, bold=False, fc=LIGHT_STEEL)
ws6.row_dimensions[2].height = 22

h6 = ["#","Company","Ticker","Sector","Market Cap","5Y Rev CAGR","5Y PAT CAGR","ROE","ROCE","Valuation","Risk"]
w6 = [4,  24,       12,      20,      14,          13,           13,           10,    10,    26,         12]

r = 3
ws6.row_dimensions[r].height = 26
for ci, (h, w) in enumerate(zip(h6, w6), 1):
    c = ws6.cell(r, ci, h)
    c.fill = hf(ROYAL)
    c.font = Font(name="Calibri", size=10, bold=True, color=WHITE)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = tb()
    scw(ws6, ci, w)

for i, st in enumerate(STOCKS):
    r = 4 + i
    ws6.row_dimensions[r].height = 28
    bg = LIGHT_STEEL if i % 2 == 0 else WHITE
    sc = SECTOR_COLOR_MAP.get(st["sector"], ROYAL)

    vals = [
        (st["no"],        "center", False, DARK_TXT, bg),
        (st["company"],   "left",   True,  MIDNIGHT, bg),
        (st["ticker"],    "center", True,  WHITE,    SAFFRON),
        (st["sector"],    "center", False, WHITE,    sc),
        (st["mktcap"],    "center", False, DARK_TXT, bg),
        (st["sales_cagr"],"center", True,  DARK_TXT, bg),
        (st["pat_cagr"],  "center", True,  DARK_TXT, bg),
        (st["roe"],       "center", True,  DARK_TXT, bg),
        (st["roce"],      "center", True,  DARK_TXT, bg),
        (st["val_tag"],   "center", True,  WHITE,    st["val_col"]),
        (st["risk"],      "center", True,  WHITE,    st["risk_col"]),
    ]
    for ci, (val, al, bd, fc, fb) in enumerate(vals, 1):
        c = ws6.cell(r, ci, val)
        c.fill = hf(fb)
        c.font = Font(name="Calibri", size=9, bold=bd, color=fc)
        c.alignment = Alignment(horizontal=al, vertical="center", wrap_text=True, indent=1)
        c.border = tb()

# Legend
legend_r = 4 + len(STOCKS) + 2
ws6.row_dimensions[legend_r].height = 24
ms(ws6, f"A{legend_r}:K{legend_r}", "COLOUR LEGEND & KEY NOTES",
   EMERALD, fsz=11, bold=True, fc=WHITE)

legend = [
    (GREEN_OK,  WHITE,    "ATTRACTIVE / LOW RISK",
     "Strong fundamentals + reasonable valuation. NTPC, ITC, HDFC Bank, ICICI, SBI, RIL. Core holdings."),
    ("5DADE2",  WHITE,    "FAIR / LOW-MEDIUM RISK",
     "Good growth, slight valuation premium. Airtel, Maruti, SBI. Good entry points on 5–8% corrections."),
    (AMBER_MID, WHITE,    "FAIR / MEDIUM RISK",
     "Solid businesses but valuation is fair-to-premium. M&M, L&T, Sun Pharma, UltraTech. Buy on dips."),
    (MIDNIGHT,  GOLD_ACC, "KEY PRINCIPLE",
     "Diversify across ≥ 5 sectors. Max 15–20% per stock. Bluechips compound via earnings + dividends + re-rating."),
    ("2C1A00",  GOLD_ACC, "DISCLAIMER",
     "Data as of June 2026 from public broker reports. Not investment advice. "
     "Verify all metrics on Screener.in before any investment decision."),
]
for i, (bg, fc, label, desc) in enumerate(legend):
    r = legend_r + 1 + i
    ws6.row_dimensions[r].height = 36
    wc(ws6, r, 1, label, bg, fsz=10, bold=True, fc=fc, halign="center")
    ws6.merge_cells(f"A{r}:C{r}")
    wc(ws6, r, 4, desc, LIGHT_STEEL if i % 2 == 0 else WHITE,
       fsz=9, bold=False, fc=DARK_TXT, halign="left", wrap=True)
    ws6.merge_cells(f"D{r}:K{r}")

# BAR CHART — PAT CAGR
chart_start = legend_r + len(legend) + 3
ws6.cell(chart_start, 1, "Company").font = Font(bold=True)
ws6.cell(chart_start, 2, "5Y PAT CAGR (%)").font = Font(bold=True)
cagr_pairs = [
    ("ICICIBANK", 22), ("SBIN", 15), ("HDFCBANK", 15),
    ("BHARTIARTL", 30), ("RELIANCE", 12),
    ("M&M", 25), ("MARUTI", 18),
    ("NTPC", 15), ("LT", 18), ("ULTRACEMCO", 20),
    ("SUNPHARMA", 17), ("ITC", 9),
]
for j, (nm, v) in enumerate(cagr_pairs):
    ws6.cell(chart_start + 1 + j, 1, nm)
    ws6.cell(chart_start + 1 + j, 2, v)

chart = BarChart()
chart.type = "col"
chart.style = 10
chart.title = "Estimated 5-Year PAT CAGR — 12 Bluechip Candidates (%)"
chart.y_axis.title = "PAT CAGR %"
chart.x_axis.title = "Stock (NSE Ticker)"
chart.width = 26
chart.height = 14

data_r = Reference(ws6, min_col=2, min_row=chart_start,
                   max_col=2, max_row=chart_start + len(cagr_pairs))
cats   = Reference(ws6, min_col=1, min_row=chart_start + 1,
                   max_row=chart_start + len(cagr_pairs))
chart.add_data(data_r, titles_from_data=True)
chart.set_categories(cats)
chart.series[0].graphicalProperties.solidFill = "1D3F6B"

ws6.add_chart(chart, f"A{chart_start + len(cagr_pairs) + 2}")

# ── Tab colours & print settings ──────────────────────────────────────────
tab_cols = [MIDNIGHT, ROYAL, EMERALD, SAFFRON, DEEP_TEAL, AMBER_MID]
for ws, tc in zip([ws1, ws2, ws3, ws4, ws5, ws6], tab_cols):
    ws.sheet_properties.tabColor = tc
    ws.page_setup.orientation  = "landscape"
    ws.page_setup.fitToPage    = True
    ws.page_setup.fitToWidth   = 1
    ws.page_setup.fitToHeight  = 0
    ws.print_title_rows        = "1:3"

# ── Save ──────────────────────────────────────────────────────────────────
out = "/home/user/Claude-/India_Bluechip_Watchlist_16pct_CAGR.xlsx"
wb.save(out)
print(f"Saved → {out}")
