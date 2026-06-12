"""
India Equity Watchlist – Board-Ready Excel Report
16% CAGR Target | 2-Year Horizon | NSE/BSE Focus
"""

import openpyxl
from openpyxl.styles import (
    Font, PatternFill, Alignment, Border, Side, GradientFill
)
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.series import DataPoint
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles.numbers import FORMAT_PERCENTAGE
import datetime

# ── colour palette ──────────────────────────────────────────────────────────
NAVY      = "1B3A6B"   # primary dark
GOLD      = "D4A017"   # accent
TEAL      = "2E86AB"   # secondary
LIGHT_BG  = "EEF2F7"   # row alternate
WHITE     = "FFFFFF"
DARK_TEXT = "1A1A2E"
GREEN_OK  = "27AE60"
AMBER     = "F39C12"
RED_RISK  = "E74C3C"
LIGHT_GOLD = "FFF3CC"
LIGHT_TEAL = "E8F4F8"
DARK_GOLD  = "B8860B"
HEADER_BG  = "0D2137"

def hex_fill(hex_code):
    return PatternFill("solid", fgColor=hex_code)

def thin_border(top=True, bottom=True, left=True, right=True):
    s = Side(style="thin", color="CCCCCC")
    return Border(
        top=s if top else None,
        bottom=s if bottom else None,
        left=s if left else None,
        right=s if right else None
    )

def thick_border():
    s = Side(style="medium", color=NAVY)
    return Border(top=s, bottom=s, left=s, right=s)

def header_font(size=11, bold=True, color=WHITE):
    return Font(name="Calibri", size=size, bold=bold, color=color)

def body_font(size=10, bold=False, color=DARK_TEXT):
    return Font(name="Calibri", size=size, bold=bold, color=color)

def set_col_width(ws, col, width):
    ws.column_dimensions[get_column_letter(col)].width = width

def merge_and_style(ws, cell_range, text, fill_hex, font_size=11,
                    bold=True, font_color=WHITE, align="center", wrap=False):
    ws.merge_cells(cell_range)
    top_left = ws[cell_range.split(":")[0]]
    top_left.value = text
    top_left.fill = hex_fill(fill_hex)
    top_left.font = Font(name="Calibri", size=font_size, bold=bold, color=font_color)
    top_left.alignment = Alignment(horizontal=align, vertical="center", wrap_text=wrap)

def write_cell(ws, row, col, value, fill_hex=None, font_sz=10, bold=False,
               font_color=DARK_TEXT, align="left", wrap=False, border=True,
               num_format=None):
    c = ws.cell(row=row, column=col, value=value)
    if fill_hex:
        c.fill = hex_fill(fill_hex)
    c.font = Font(name="Calibri", size=font_sz, bold=bold, color=font_color)
    c.alignment = Alignment(horizontal=align, vertical="center", wrap_text=wrap)
    if border:
        c.border = thin_border()
    if num_format:
        c.number_format = num_format
    return c

# ═══════════════════════════════════════════════════════════════════════════
# DATA
# ═══════════════════════════════════════════════════════════════════════════

SECTORS = [
    {
        "name": "Banking & NBFC",
        "icon": "🏦",
        "momentum": "Strong",
        "drivers": (
            "Credit growth at 12–14% YoY; RBI rate cycle nearing bottom (repo 5.25%); "
            "improving asset quality; NIMs stabilising at 3.8–4.4%; "
            "formalisation of credit via Jan Dhan/GST data driving NBFC expansion."
        ),
        "valuation": "Fair to Attractive — Nifty Bank trades ~10% below its 5-year avg P/B",
        "cagr_path": "NII growth + credit expansion + asset-quality normalisation → 15–20% EPS CAGR",
        "key_risk": "NIM compression if rate cuts are deeper; unsecured credit stress in NBFC segment",
        "rating": "Medium",
        "color": "2E86AB",
    },
    {
        "name": "Capital Goods & Infra",
        "icon": "🏗️",
        "momentum": "Strong",
        "drivers": (
            "₹12.2 lakh crore government infra capex in Union Budget 2026–27; "
            "500 GW renewable energy target driving grid investment; "
            "PLI schemes boosting industrial capex; book-to-bill ratio ~3.8x providing "
            "multi-year earnings visibility."
        ),
        "valuation": "Premium — Sector at 35x vs 10-yr avg 28x; justified by order-book size",
        "cagr_path": "Revenue backlog conversion + 18–22% revenue growth → 20%+ EPS CAGR for leaders",
        "key_risk": "Execution lag; margin compression; delay in private capex pickup",
        "rating": "Medium",
        "color": "D4A017",
    },
    {
        "name": "Healthcare & Pharma",
        "icon": "💊",
        "momentum": "Moderate",
        "drivers": (
            "Indian pharma exports grew 9.4% to $30.47B in FY25; "
            "US generics + biosimilars pipeline; specialty pharma premiumisation; "
            "semaglutide generic opportunity (₹12,000 cr potential market); "
            "chronic therapy (diabetes, cardio) driving domestic growth."
        ),
        "valuation": "Reasonable — Dr Reddy's 26x, Cipla 27x, Sun Pharma 36x; sector below 5-yr peak",
        "cagr_path": "Export ramp + specialty mix improvement → 12–18% EPS CAGR",
        "key_risk": "US FDA regulatory risk; price erosion in generics; rupee appreciation",
        "rating": "Medium",
        "color": "27AE60",
    },
    {
        "name": "Consumer Discretionary",
        "icon": "💎",
        "momentum": "Strong",
        "drivers": (
            "India's aspirational middle class expanding; jewellery formalisation "
            "(hallmarking norms); Trent's Zudio rapid store expansion into Tier 2–3 cities; "
            "premiumisation of fashion + watches; gold price tailwind for jewellery retailers."
        ),
        "valuation": "Premium — Titan at 92x, Trent at high PE; premium warranted by 30–40% CAGR history",
        "cagr_path": "Store expansion + premiumisation + operating leverage → 20–25% EPS CAGR",
        "key_risk": "Valuation de-rating risk; gold import duty changes; rural income slowdown",
        "rating": "Medium-High",
        "color": "8E44AD",
    },
    {
        "name": "Power & Renewables",
        "icon": "⚡",
        "momentum": "Strong",
        "drivers": (
            "Peak power demand hit 271 GW in May 2026 (record); target 900 GW by FY32; "
            "NTPC's 60% renewable target by 2032; ₹51B grid investment required by 2035; "
            "India's 500 GW renewable energy target under Paris accord commitment."
        ),
        "valuation": "Fair — NTPC at ~12x earnings; Power Grid at ~15x; regulated returns model",
        "cagr_path": "Capacity addition + regulated tariffs + green energy transition → 12–18% CAGR",
        "key_risk": "Regulatory tariff revision; project execution delays; fuel cost volatility",
        "rating": "Low-Medium",
        "color": "E67E22",
    },
    {
        "name": "IT Services",
        "icon": "💻",
        "momentum": "Moderate",
        "drivers": (
            "AI-driven deal wins accelerating (TCS $2.3B AI revenue in FY26); "
            "large deal pipeline at record highs for TCS & Infosys; "
            "enterprise digitalisation cycle; strong dividend yield and buybacks; "
            "USD revenue insulates from INR weakness."
        ),
        "valuation": "Fair — TCS ~25x, Infosys ~22x; below 5-yr peaks seen in FY21-22",
        "cagr_path": "Deal conversion + AI efficiency tailwinds → 8–14% revenue CAGR; higher EPS via margins",
        "key_risk": "AI disrupting labour model (3–4% annual rev headwind); US recession risk; visa issues",
        "rating": "Medium",
        "color": "2980B9",
    },
]

STOCKS = [
    # BANKING & NBFC
    {
        "sector": "Banking & NBFC",
        "company": "ICICI Bank",
        "ticker": "ICICIBANK",
        "exchange": "NSE",
        "why_fits": (
            "India's best-in-class private bank. ROE ~17–18%, NIM 4.3–4.4% (highest among peers). "
            "FY26 CAR 17.11%. Improving operating leverage with consistent loan growth. "
            "Analysts project 15–20% EPS CAGR over FY26–28. Valuation shifted from fair to attractive."
        ),
        "key_risks": "NIM compression; unsecured loan stress if economy slows; regulatory caps on fees",
        "valuation_view": "Attractive — PE ~15–19x vs historical 18–22x; ~10% discount to own history",
        "roe": "17–18%",
        "roce": "N/A (Bank)",
        "sales_cagr_5yr": "~16%",
        "pat_cagr_5yr": "~22%",
        "de_ratio": "N/A (Bank; CAR 17.1%)",
        "risk": "Medium",
        "risk_color": AMBER,
        "valuation_tag": "Attractive",
        "val_color": GREEN_OK,
    },
    {
        "sector": "Banking & NBFC",
        "company": "Bajaj Finance",
        "ticker": "BAJFINANCE",
        "exchange": "NSE",
        "why_fits": (
            "India's premier consumer NBFC. AUM CAGR 24% FY27–28E. "
            "Earnings CAGR 27% FY27–28E (Axis Securities). ROE 19–21%, ROA 4.3–4.4%. "
            "NII+AUM grew 21–22% QoQ in Q3 FY26 despite one-time provisioning. "
            "Diversified loan book across consumer, SME, commercial."
        ),
        "key_risks": "Unsecured consumer credit quality; RBI NBFC tightening; PE premium at 32x",
        "valuation_view": "Fair-to-Premium — PE ~32x; priced for strong growth; watch credit quality closely",
        "roe": "19–21%",
        "roce": "~14% (NBFC)",
        "sales_cagr_5yr": "~26%",
        "pat_cagr_5yr": "~24%",
        "de_ratio": "~3.5x (typical NBFC leverage)",
        "risk": "Medium",
        "risk_color": AMBER,
        "valuation_tag": "Fair/Premium",
        "val_color": AMBER,
    },
    # CAPITAL GOODS
    {
        "sector": "Capital Goods & Infra",
        "company": "Larsen & Toubro",
        "ticker": "LT",
        "exchange": "NSE",
        "why_fits": (
            "India's largest EPC and engineering conglomerate. Order book ₹5.66 lakh crore "
            "(3x FY26 revenue) providing multi-year visibility. Diversified across infra, "
            "defence, green energy, and IT. Order inflows growing strongly with ₹12.2L cr "
            "government capex. ROE ~14–15%, improving with margin leverage."
        ),
        "key_risks": "Execution lag on large orders; working capital intensity; political execution risk",
        "valuation_view": "Fair — PE ~25–28x; not cheap but order-book size justifies premium",
        "roe": "14–15%",
        "roce": "~12–14%",
        "sales_cagr_5yr": "~14%",
        "pat_cagr_5yr": "~18%",
        "de_ratio": "~0.3x (ex-financial services)",
        "risk": "Medium",
        "risk_color": AMBER,
        "valuation_tag": "Fair",
        "val_color": AMBER,
    },
    {
        "sector": "Capital Goods & Infra",
        "company": "Siemens India",
        "ticker": "SIEMENS",
        "exchange": "NSE",
        "why_fits": (
            "Zero-debt automation & electrification leader. ROCE 30.3%, 5-yr EBIT CAGR 17.56%. "
            "Order intake growth 32.6% in FY26. Beneficiary of India's grid modernisation "
            "and manufacturing PLI. Parent Siemens AG provides technology transfer advantage. "
            "Strong moat in industrial automation."
        ),
        "key_risks": "Margin compression (EBIT dipped to 9.6% Q4); premium valuation; slow private capex",
        "valuation_view": "Expensive — PE ~50–55x; ROCE quality justifies premium partially",
        "roe": "13–14%",
        "roce": "30.3%",
        "sales_cagr_5yr": "~11%",
        "pat_cagr_5yr": "~18%",
        "de_ratio": "Zero debt",
        "risk": "Medium",
        "risk_color": AMBER,
        "valuation_tag": "Expensive",
        "val_color": RED_RISK,
    },
    # PHARMA
    {
        "sector": "Healthcare & Pharma",
        "company": "Sun Pharmaceutical",
        "ticker": "SUNPHARMA",
        "exchange": "NSE",
        "why_fits": (
            "India's largest pharma by market cap. FY26 revenue ₹58,220 cr (+11.9%), "
            "PAT ₹11,479 cr. ROE 15.21%, ROCE 25.6%. 5-yr EBIT CAGR 20.79%. "
            "67% international revenues; specialty brands (Ilumya, Cequa) driving US mix. "
            "Semaglutide generic entry adds ₹12,000 cr potential market."
        ),
        "key_risks": "US FDA plant inspections; specialty product ramp timeline; price erosion in generics",
        "valuation_view": "Fair — PE ~36x; premium to Dr Reddy's (26x) justified by specialty pipeline",
        "roe": "15%",
        "roce": "25.6%",
        "sales_cagr_5yr": "~11%",
        "pat_cagr_5yr": "~17%",
        "de_ratio": "~0.1x (near debt-free)",
        "risk": "Medium",
        "risk_color": AMBER,
        "valuation_tag": "Fair",
        "val_color": AMBER,
    },
    {
        "sector": "Healthcare & Pharma",
        "company": "Dr. Reddy's Laboratories",
        "ticker": "DRREDDY",
        "exchange": "NSE",
        "why_fits": (
            "Strong US generics + biosimilars pipeline. Balanced revenue mix (US 50%, "
            "India 25%, Europe/RoW 25%). Glatiramer acetate, teriflunomide, biosimilars "
            "driving incremental revenue. FY26 PAT growth ~15–18%. Lowest PE among Big-4 "
            "pharma at ~26x makes it relatively better value."
        ),
        "key_risks": "US generics price erosion; biosimilar launch delays; currency headwinds",
        "valuation_view": "Attractive — PE ~26x; cheapest among large-cap Indian pharma peers",
        "roe": "~18–20%",
        "roce": "~22%",
        "sales_cagr_5yr": "~14%",
        "pat_cagr_5yr": "~20%",
        "de_ratio": "~0.1x",
        "risk": "Medium",
        "risk_color": AMBER,
        "valuation_tag": "Attractive",
        "val_color": GREEN_OK,
    },
    # CONSUMER DISCRETIONARY
    {
        "sector": "Consumer Discretionary",
        "company": "Titan Company",
        "ticker": "TITAN",
        "exchange": "NSE",
        "why_fits": (
            "India's premier branded jewellery + watches + eyewear company. "
            "ROE 32.25%, ROCE 28.37%, 5-yr sales CAGR 30.75%, EBIT CAGR 42.48%. "
            "JP Morgan: 13% revenue CAGR + 20% EPS CAGR FY26–28E. Tata Group backing. "
            "Hallmarking norms formalising unorganised market share → structural tailwind."
        ),
        "key_risks": "Valuation de-rating (PE 92x); gold import duty changes; rural income risk",
        "valuation_view": "Expensive — PE ~92x; stellar track record partially justifies premium; enter on dips",
        "roe": "32%",
        "roce": "28.4%",
        "sales_cagr_5yr": "~31%",
        "pat_cagr_5yr": "~35%",
        "de_ratio": "~0.1x",
        "risk": "Medium-High",
        "risk_color": AMBER,
        "valuation_tag": "Expensive",
        "val_color": RED_RISK,
    },
    {
        "sector": "Consumer Discretionary",
        "company": "Trent",
        "ticker": "TRENT",
        "exchange": "NSE",
        "why_fits": (
            "Tata Group's fast fashion retailer (Westside + Zudio). Revenue ₹4.2B→₹47B "
            "at ~40% CAGR FY19–FY26. EBIT margins reached double digits (~10%) via "
            "operating leverage. Zudio is the fastest growing value-fashion brand in India, "
            "aggressively penetrating Tier 2–3 cities. Ambit's top conviction 'Buy'."
        ),
        "key_risks": "Intense competition from Reliance Retail / Myntra; inventory risk; high PE",
        "valuation_view": "Expensive — Trades at premium; 40% revenue CAGR makes high PE defensible",
        "roe": "~28–30%",
        "roce": "~25%",
        "sales_cagr_5yr": "~38%",
        "pat_cagr_5yr": "~45%",
        "de_ratio": "~0.2x",
        "risk": "Medium-High",
        "risk_color": AMBER,
        "valuation_tag": "Expensive",
        "val_color": RED_RISK,
    },
    # POWER
    {
        "sector": "Power & Renewables",
        "company": "NTPC",
        "ticker": "NTPC",
        "exchange": "NSE",
        "why_fits": (
            "India's largest power utility (74 GW+ installed). Targets 60% renewable "
            "by 2032; NTPC Green Energy subsidiary for RE portfolio. Macquarie's top pick "
            "in power sector. Regulated ROE model + rising capacity → predictable earnings. "
            "FY26 dividend ₹3.5/share. Peak demand 271 GW May 2026 creates pricing power."
        ),
        "key_risks": "Regulated tariff model limits upside; fuel cost volatility; project delays",
        "valuation_view": "Attractive — PE ~12–13x; significant discount to market; steady dividend yield",
        "roe": "~13–14%",
        "roce": "~10–11%",
        "sales_cagr_5yr": "~12%",
        "pat_cagr_5yr": "~14%",
        "de_ratio": "~1.5x (infra-type leverage; acceptable)",
        "risk": "Low",
        "risk_color": GREEN_OK,
        "valuation_tag": "Attractive",
        "val_color": GREEN_OK,
    },
    {
        "sector": "Power & Renewables",
        "company": "Power Grid Corp of India",
        "ticker": "POWERGRID",
        "exchange": "NSE",
        "why_fits": (
            "India's monopoly inter-state transmission company. Q4 FY26 PAT +9.7% YoY "
            "to ₹4,546 cr. FY26 capex ₹40,000 cr (above guidance); added 4,765 ckms lines. "
            "Dividend ₹9/share FY26; consistent 4–5% yield. Regulated ROCE model with "
            "assured 15.5% equity return on all projects. Very low-risk compounder."
        ),
        "key_risks": "Regulatory changes to tariff mechanism; capex execution delays; modest growth",
        "valuation_view": "Fair — PE ~15x; attractive dividend yield 4–5%; defensive compounder",
        "roe": "~19–20%",
        "roce": "~9–10%",
        "sales_cagr_5yr": "~10%",
        "pat_cagr_5yr": "~11%",
        "de_ratio": "~1.8x (regulated infra; normal for sector)",
        "risk": "Low",
        "risk_color": GREEN_OK,
        "valuation_tag": "Fair",
        "val_color": AMBER,
    },
    # IT SERVICES
    {
        "sector": "IT Services",
        "company": "Tata Consultancy Services",
        "ticker": "TCS",
        "exchange": "NSE",
        "why_fits": (
            "$2.3B AI revenue in FY26 (12% QoQ growth). India's largest IT exporter. "
            "Kotak's top IT pick. Dividend + buyback yield ~3–4% per year. "
            "Margin resilience at ~24–25%. Large deal TCV growing; strong client stickiness. "
            "USD revenue buffers INR depreciation. Conservative management; low execution risk."
        ),
        "key_risks": "AI disrupting traditional IT labour model (3–4% annual rev headwind); US demand slowdown",
        "valuation_view": "Fair — PE ~25x; below FY21 peak of 35x; dividend yield makes holding cost lower",
        "roe": "~50%",
        "roce": "~60%",
        "sales_cagr_5yr": "~12%",
        "pat_cagr_5yr": "~12%",
        "de_ratio": "Debt-free (net cash)",
        "risk": "Low-Medium",
        "risk_color": GREEN_OK,
        "valuation_tag": "Fair",
        "val_color": AMBER,
    },
    {
        "sector": "IT Services",
        "company": "Infosys",
        "ticker": "INFY",
        "exchange": "NSE",
        "why_fits": (
            "FY26 large deal wins $4.8B (57% net new); revenue $5,099M Q3 FY26. "
            "Infosys Topaz (AI platform) winning enterprise AI mandates. "
            "Revised FY26 guidance 3–3.5% CC growth. Operating margins 20–22%. "
            "Strong free cash flow; consistent buybacks. Second-largest Indian IT by revenue."
        ),
        "key_risks": "Moderate revenue growth (4–5% industry CAGR FY27); client budget scrutiny; AI headwinds",
        "valuation_view": "Fair — PE ~22x; reasonable for quality; total return aided by ~3% dividend + buyback",
        "roe": "~32–34%",
        "roce": "~40%",
        "sales_cagr_5yr": "~12%",
        "pat_cagr_5yr": "~11%",
        "de_ratio": "Debt-free (net cash)",
        "risk": "Low-Medium",
        "risk_color": GREEN_OK,
        "valuation_tag": "Fair",
        "val_color": AMBER,
    },
]

FRAMEWORK = [
    ("Sales CAGR (5-Year)", "≥ 12% preferred; ≥ 16% ideal",
     "Consistent revenue growth signals demand strength and pricing power. Below 10% for 2 consecutive years = flag.",
     "12–16%+"),
    ("PAT / Profit CAGR (5-Year)", "≥ 15% preferred; ≥ 20% ideal",
     "Profit must grow faster than revenue — indicates operating leverage. Check if growth is organic or due to one-time items.",
     "15–20%+"),
    ("ROCE (Return on Capital Employed)", "≥ 15% for capital-intensive; ≥ 20% for asset-light",
     "Measures efficiency of capital deployed. A ROCE > cost of capital (WACC ~12%) is a minimum threshold for value creation.",
     "15–20%+"),
    ("ROE (Return on Equity)", "≥ 15% for banks/NBFC; ≥ 18% for industrials/consumer",
     "ROE > 15% with low leverage is better than ROE > 25% driven by high debt. Beware of 'debt-inflated ROE'.",
     "15–18%+"),
    ("Debt-to-Equity Ratio", "≤ 0.5x for industrials; ≤ 1.0x for infra; Banks: CAR ≥ 15%",
     "Exclude financial companies from this metric; use CAR for banks. For non-financial firms, D/E > 1.5x is a red flag.",
     "≤ 0.5–1.0x"),
    ("Interest Coverage Ratio", "≥ 5x (minimum 3x)",
     "EBIT / Interest Expense. Companies paying 30%+ of EBIT as interest are vulnerable in downturns. Below 3x = avoid.",
     "≥ 5x"),
    ("P/E vs 5-Year Historical Average", "Prefer PE ≤ 1.1x its own 5-yr average",
     "Overpaying for quality destroys returns. Even great companies bought at 2x their historical PE may underperform for years.",
     "≤ 110% of 5yr avg"),
    ("Promoter Holding", "≥ 40% (stable or increasing)",
     "High, stable promoter holding aligns management with shareholders. Significant pledging (>30% of holding) is a red flag.",
     "≥ 40%"),
    ("Free Cash Flow Yield", "≥ 2–3%",
     "FCF = PAT – Capex + D&A. Companies consistently generating free cash can fund growth without dilution or debt.",
     "≥ 2–3%"),
    ("Market Cap (Liquidity)", "Prefer ≥ ₹5,000 crore (large/mid-cap)",
     "Smaller companies have higher liquidity risk. For a 2-year horizon, stick to stocks with average daily volume > ₹50 crore.",
     "≥ ₹5,000 Cr"),
]

WATCHLIST = [
    ("Banking & NBFC",   "ICICI Bank",             "ICICIBANK", "ROE 17–18%; best NIM 4.4%; 15–20% EPS CAGR; improving operating leverage",          "NIM compression; unsecured loan stress",             "Attractive (PE ~17x)",  "Medium"),
    ("Banking & NBFC",   "Bajaj Finance",          "BAJFINANCE","AUM CAGR 24%; earnings CAGR 27% FY27-28E; ROE 19–21%; diversified loan book",         "Unsecured credit quality; RBI tightening",           "Fair/Premium (PE ~32x)","Medium"),
    ("Cap Goods & Infra","L&T",                    "LT",        "Order book 3x revenue; ₹5.66L cr backlog; diversified across infra+defence+green",   "Execution lag; working capital intensity",            "Fair (PE ~26x)",        "Medium"),
    ("Cap Goods & Infra","Siemens India",          "SIEMENS",   "ROCE 30.3%; zero debt; order intake +32.6%; industrial automation moat",             "Margin compression; expensive valuation PE ~52x",    "Expensive (PE ~52x)",   "Medium"),
    ("Healthcare",       "Sun Pharmaceutical",     "SUNPHARMA", "ROCE 25.6%; EBIT CAGR 21%; specialty pharma US growth; semaglutide generics",        "US FDA risk; specialty ramp timeline",               "Fair (PE ~36x)",        "Medium"),
    ("Healthcare",       "Dr. Reddy's Labs",       "DRREDDY",   "Cheapest large-cap pharma (PE 26x); biosimilars pipeline; 18–20% ROE",               "US price erosion; biosimilar delays; currency risk",  "Attractive (PE ~26x)",  "Medium"),
    ("Consumer Discr.",  "Titan Company",          "TITAN",     "ROE 32%; ROCE 28%; EPS CAGR 20% FY26-28E; jewellery formalisation tailwind",         "Valuation de-rating risk (PE 92x); gold duty changes","Expensive (PE ~92x)",   "Med-High"),
    ("Consumer Discr.",  "Trent",                  "TRENT",     "Revenue CAGR ~40%; Zudio Tier 2-3 expansion; EBIT margin expanded to ~10%",          "Competition from Reliance Retail; inventory risk",    "Expensive (high PE)",   "Med-High"),
    ("Power & RE",       "NTPC",                   "NTPC",      "74GW+ capacity; green energy pivot (60% RE by 2032); Macquarie top pick; PE ~12x",   "Regulated tariff; project delays; fuel costs",        "Attractive (PE ~12x)",  "Low"),
    ("Power & RE",       "Power Grid Corp",        "POWERGRID", "Regulated 15.5% ROE guarantee; 4–5% div yield; ₹40,000 cr capex FY26",              "Tariff regulation changes; modest PAT growth ~11%",   "Fair (PE ~15x + div)",  "Low"),
    ("IT Services",      "TCS",                    "TCS",       "$2.3B AI revenue FY26; 50%+ ROE; ~3–4% div+buyback yield; net-cash balance sheet",   "AI disruption; US recession risk; 12% rev CAGR only", "Fair (PE ~25x)",        "Low-Med"),
    ("IT Services",      "Infosys",                "INFY",      "$4.8B large deals FY26; Topaz AI platform; 32–34% ROE; consistent buybacks",         "Moderate 4–5% industry rev growth; client scrutiny",  "Fair (PE ~22x)",        "Low-Med"),
]

# ═══════════════════════════════════════════════════════════════════════════
# BUILD WORKBOOK
# ═══════════════════════════════════════════════════════════════════════════

wb = openpyxl.Workbook()
wb.remove(wb.active)  # remove default sheet

# ─────────────────────────────────────────────────────────────────────────
# SHEET 1 · COVER / EXECUTIVE SUMMARY
# ─────────────────────────────────────────────────────────────────────────
ws1 = wb.create_sheet("01 · Executive Summary")
ws1.sheet_view.showGridLines = False
ws1.row_dimensions[1].height = 8

# Background gradient-like header bar
for r in range(2, 18):
    ws1.row_dimensions[r].height = 22
for c in range(1, 15):
    for r in range(2, 18):
        ws1.cell(r, c).fill = hex_fill(HEADER_BG)

# Title block
merge_and_style(ws1, "B3:N5",
    "INDIA EQUITY WATCHLIST — 16% CAGR TARGET",
    HEADER_BG, font_size=26, bold=True, font_color=GOLD)
merge_and_style(ws1, "B6:N7",
    "2-Year Investment Horizon | NSE / BSE | Disciplined Research-Driven Selection",
    HEADER_BG, font_size=13, bold=False, font_color=WHITE)
merge_and_style(ws1, "B8:N9",
    f"Prepared: {datetime.date.today().strftime('%B %d, %Y')}  |  "
    "Focus: Chartered Accountant, Vadodara  |  Sectors: 6  |  Research Candidates: 12",
    HEADER_BG, font_size=11, bold=False, font_color="AABBCC")

# Gold divider
for c in range(2, 15):
    ws1.cell(10, c).fill = hex_fill(GOLD)
    ws1.row_dimensions[10].height = 4

# Disclaimer banner
merge_and_style(ws1, "B11:N13",
    "⚠  IMPORTANT DISCLAIMER: This document presents research candidates for personal study only. "
    "It does NOT constitute investment advice or a buy/sell recommendation. Past performance is not "
    "indicative of future results. Consult a SEBI-registered investment adviser before investing. "
    "All data sourced from publicly available broker reports and company filings (June 2026).",
    "3D1A00", font_size=9, bold=False, font_color="FFD700", align="center")

for c in range(2, 15):
    ws1.cell(14, c).fill = hex_fill(HEADER_BG)

# ── Key metrics row ────────────────────────────────────────────────────────
ws1.row_dimensions[18].height = 10
ws1.row_dimensions[19].height = 30
ws1.row_dimensions[20].height = 50
ws1.row_dimensions[21].height = 30
ws1.row_dimensions[22].height = 10

kpi_items = [
    ("B", "D", "6 SECTORS\nAnalysed",         NAVY),
    ("E", "G", "12 RESEARCH\nCandidates",      TEAL),
    ("H", "J", "16%+\nCAGR Target",            DARK_GOLD),
    ("K", "M", "2-Year\nHorizon",              "1B5E20"),
]
for start_col, end_col, label, bg in kpi_items:
    ws1.merge_cells(f"{start_col}19:{end_col}21")
    c = ws1[f"{start_col}19"]
    c.value = label
    c.fill = hex_fill(bg)
    c.font = Font(name="Calibri", size=16, bold=True, color=WHITE)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = Border(
        top=Side(style="medium", color=GOLD),
        bottom=Side(style="medium", color=GOLD),
        left=Side(style="medium", color=GOLD),
        right=Side(style="medium", color=GOLD)
    )

# ── Macro Context Table ────────────────────────────────────────────────────
ws1.row_dimensions[24].height = 8
row = 25
merge_and_style(ws1, f"B{row}:N{row}",
    "INDIA MACRO CONTEXT — June 2026", NAVY, font_size=12, bold=True, font_color=GOLD)
ws1.row_dimensions[row].height = 28

macro_items = [
    ("Nifty 50 Trailing PE",       "~20.9x",   "~11% discount to 10-year avg of 23.4x — market not expensive"),
    ("RBI Repo Rate",              "5.25%",    "Rate cycle near bottom; possible cuts ahead supportive for equities"),
    ("India GDP Growth (FY27E)",   "~6.5–7%",  "Among fastest growing major economies globally"),
    ("Broad Market PAT Growth",    "~21.6% YoY","Median profit growth (NSE500) as of May 2026"),
    ("India Pharma Exports",       "$30.47B",  "FY25 exports; targeting double-digit growth by FY27"),
    ("Govt Infra Capex FY27",      "₹12.2L Cr","Record government capital expenditure in Union Budget 2026-27"),
    ("Peak Power Demand (May'26)", "271 GW",   "Record high; 275–285 GW forecast for summer — power sector tailwind"),
    ("FII Flows",                  "Net Seller","Selling slowing; reversal when US rates moderate = re-rating trigger"),
]

for i, (metric, value, note) in enumerate(macro_items):
    r = row + 1 + i
    ws1.row_dimensions[r].height = 22
    bg = LIGHT_BG if i % 2 == 0 else WHITE
    write_cell(ws1, r, 2, metric, bg, font_sz=10, bold=True, font_color=NAVY, align="left")
    ws1.merge_cells(f"B{r}:B{r}")
    ws1.cell(r, 2).alignment = Alignment(horizontal="left", vertical="center", indent=1)

    write_cell(ws1, r, 3, value, bg, font_sz=11, bold=True, font_color=TEAL, align="center")
    ws1.merge_cells(f"C{r}:D{r}")

    write_cell(ws1, r, 5, note, bg, font_sz=9, bold=False, font_color="444444", align="left", wrap=True)
    ws1.merge_cells(f"E{r}:N{r}")
    ws1.cell(r, 5).alignment = Alignment(horizontal="left", vertical="center", wrap_text=True, indent=1)

# ── Sheet navigation guide ────────────────────────────────────────────────
nav_row = row + len(macro_items) + 2
ws1.row_dimensions[nav_row].height = 26
merge_and_style(ws1, f"B{nav_row}:N{nav_row}",
    "WORKBOOK NAVIGATION", TEAL, font_size=11, bold=True, font_color=WHITE)

sheets_info = [
    ("01 · Executive Summary",   "This page — macro context, key metrics, navigation guide"),
    ("02 · Sector Analysis",     "Detailed analysis of 6 high-potential sectors with growth drivers & risks"),
    ("03 · Stock Research",      "12 research candidates across 6 sectors with full fundamental profile"),
    ("04 · Selection Framework", "Your personalised screening criteria — thresholds, rationale, guardrails"),
    ("05 · Watchlist Table",     "Board-ready summary table: Ticker | Sector | Valuation | Risk | CAGR Thesis"),
    ("06 · Risk Matrix",         "Risk-Return positioning of all 12 candidates plotted visually"),
]
for i, (sh, desc) in enumerate(sheets_info):
    r = nav_row + 1 + i
    ws1.row_dimensions[r].height = 20
    bg = LIGHT_GOLD if i % 2 == 0 else WHITE
    write_cell(ws1, r, 2, sh,   bg, font_sz=10, bold=True,  font_color=NAVY,  align="left")
    ws1.merge_cells(f"B{r}:E{r}")
    write_cell(ws1, r, 6, desc, bg, font_sz=10, bold=False, font_color="333333", align="left")
    ws1.merge_cells(f"F{r}:N{r}")

# Column widths sheet 1
for col, w in [(1,2),(2,22),(3,8),(4,8),(5,45),(6,2),(7,2),(8,2),(9,2),
               (10,2),(11,2),(12,2),(13,2),(14,2)]:
    set_col_width(ws1, col, w)

# ─────────────────────────────────────────────────────────────────────────
# SHEET 2 · SECTOR ANALYSIS
# ─────────────────────────────────────────────────────────────────────────
ws2 = wb.create_sheet("02 · Sector Analysis")
ws2.sheet_view.showGridLines = False

# Header
merge_and_style(ws2, "A1:J1", "SECTOR LANDSCAPE ANALYSIS — INDIA EQUITIES 2025–2027",
                HEADER_BG, font_size=14, bold=True, font_color=GOLD)
ws2.row_dimensions[1].height = 36

col_headers = ["#", "Sector", "Momentum", "Key Structural Drivers",
               "Valuation vs History", "Path to 16%+ CAGR", "Key Sector Risk", "Risk Level"]
col_widths   = [4,   22,       12,         52,
                32,              38,                28,          13]

row = 2
ws2.row_dimensions[row].height = 28
for ci, (h, w) in enumerate(zip(col_headers, col_widths), 1):
    c = ws2.cell(row, ci, h)
    c.fill   = hex_fill(NAVY)
    c.font   = Font(name="Calibri", size=10, bold=True, color=WHITE)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = thin_border()
    set_col_width(ws2, ci, w)

for i, s in enumerate(SECTORS):
    r = row + 1 + i
    ws2.row_dimensions[r].height = 90
    bg = LIGHT_BG if i % 2 == 0 else WHITE
    risk_bg = GREEN_OK if "Low" in s["rating"] else (RED_RISK if "High" in s["rating"] else AMBER)

    data = [
        (i+1,     "center", False, DARK_TEXT),
        (s["name"],"center", True,  s["color"]),
        (s["momentum"],"center", True, DARK_TEXT),
        (s["drivers"], "left",  False, DARK_TEXT),
        (s["valuation"],"left", False, DARK_TEXT),
        (s["cagr_path"],"left", False, DARK_TEXT),
        (s["key_risk"], "left", False, DARK_TEXT),
        (s["rating"],   "center",True, WHITE),
    ]
    fills = [bg, bg, bg, bg, bg, bg, bg, risk_bg]
    for ci, ((val, al, bd, fc), fb) in enumerate(zip(data, fills), 1):
        c = ws2.cell(r, ci, val)
        c.fill = hex_fill(fb)
        c.font = Font(name="Calibri", size=9, bold=bd, color=fc)
        c.alignment = Alignment(horizontal=al, vertical="top", wrap_text=True, indent=1)
        c.border = thin_border()

# ─────────────────────────────────────────────────────────────────────────
# SHEET 3 · STOCK RESEARCH
# ─────────────────────────────────────────────────────────────────────────
ws3 = wb.create_sheet("03 · Stock Research")
ws3.sheet_view.showGridLines = False

merge_and_style(ws3, "A1:L1",
    "RESEARCH CANDIDATES — 12 STOCKS ACROSS 6 SECTORS (Not Buy/Sell Recommendations)",
    HEADER_BG, font_size=13, bold=True, font_color=GOLD)
ws3.row_dimensions[1].height = 34

h3 = ["#", "Company", "Ticker", "Sector", "Why it fits 16% CAGR",
      "Key Risks", "Valuation View", "ROE", "5Y Sales CAGR", "5Y PAT CAGR", "D/E Ratio", "Risk"]
w3 = [4, 24, 13, 22, 52, 35, 28, 10, 14, 14, 18, 12]

r = 2
ws3.row_dimensions[r].height = 26
for ci, (h, w) in enumerate(zip(h3, w3), 1):
    c = ws3.cell(r, ci, h)
    c.fill = hex_fill(NAVY)
    c.font = Font(name="Calibri", size=10, bold=True, color=WHITE)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = thin_border()
    set_col_width(ws3, ci, w)

current_sector = None
sector_colors = {s["name"]: s["color"] for s in SECTORS}

for i, st in enumerate(STOCKS):
    r = 3 + i
    ws3.row_dimensions[r].height = 88
    bg = LIGHT_BG if i % 2 == 0 else WHITE
    sc = sector_colors.get(st["sector"], NAVY)
    risk_bg = st["risk_color"]

    vals = [
        (i+1,             "center", False, DARK_TEXT, bg),
        (st["company"],   "left",   True,  NAVY,      bg),
        (st["ticker"],    "center", True,  WHITE,     sc),
        (st["sector"],    "center", True,  WHITE,     sc),
        (st["why_fits"],  "left",   False, DARK_TEXT, bg),
        (st["key_risks"], "left",   False, DARK_TEXT, bg),
        (st["valuation_view"], "left", False, DARK_TEXT, bg),
        (st["roe"],       "center", True,  DARK_TEXT, bg),
        (st["sales_cagr_5yr"],"center",True,DARK_TEXT,bg),
        (st["pat_cagr_5yr"], "center",True,DARK_TEXT, bg),
        (st["de_ratio"],  "center", False, DARK_TEXT, bg),
        (st["risk"],      "center", True,  WHITE,     risk_bg),
    ]
    for ci, (val, al, bd, fc, fb) in enumerate(vals, 1):
        c = ws3.cell(r, ci, val)
        c.fill = hex_fill(fb)
        c.font = Font(name="Calibri", size=9, bold=bd, color=fc)
        c.alignment = Alignment(horizontal=al, vertical="top", wrap_text=True, indent=1)
        c.border = thin_border()

# Freeze panes
ws3.freeze_panes = "A3"

# ─────────────────────────────────────────────────────────────────────────
# SHEET 4 · SELECTION FRAMEWORK
# ─────────────────────────────────────────────────────────────────────────
ws4 = wb.create_sheet("04 · Selection Framework")
ws4.sheet_view.showGridLines = False

merge_and_style(ws4, "A1:F1",
    "STOCK SELECTION FRAMEWORK — Minimum Thresholds for 16% CAGR Candidates",
    HEADER_BG, font_size=13, bold=True, font_color=GOLD)
ws4.row_dimensions[1].height = 34

merge_and_style(ws4, "A2:F2",
    "Use this framework on Screener.in or Tickertape.in to filter and verify any stock before adding to your watchlist.",
    NAVY, font_size=10, bold=False, font_color=LIGHT_GOLD)
ws4.row_dimensions[2].height = 24

h4 = ["#", "Screening Criterion", "Minimum Threshold", "Why It Matters", "Notes / Caveats"]
w4 = [4,   30,                    22,                   52,               32]

r = 3
ws4.row_dimensions[r].height = 26
for ci, (h, w) in enumerate(zip(h4, w4), 1):
    c = ws4.cell(r, ci, h)
    c.fill = hex_fill(NAVY)
    c.font = Font(name="Calibri", size=10, bold=True, color=WHITE)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = thin_border()
    set_col_width(ws4, ci, w)

for i, (criterion, threshold, why, notes) in enumerate(FRAMEWORK):
    r = 4 + i
    ws4.row_dimensions[r].height = 70
    bg = LIGHT_TEAL if i % 2 == 0 else WHITE
    vals = [
        (i+1,       "center", False, DARK_TEXT),
        (criterion, "left",   True,  NAVY),
        (threshold, "center", True,  WHITE),
        (why,       "left",   False, DARK_TEXT),
        (notes,     "left",   False, "555555"),
    ]
    fills = [bg, bg, TEAL, bg, bg]
    for ci, ((val, al, bd, fc), fb) in enumerate(zip(vals, fills), 1):
        c = ws4.cell(r, ci, val)
        c.fill = hex_fill(fb)
        c.font = Font(name="Calibri", size=9, bold=bd, color=fc)
        c.alignment = Alignment(horizontal=al, vertical="top", wrap_text=True, indent=1)
        c.border = thin_border()

# ── PRACTICAL USAGE GUIDE ─────────────────────────────────────────────────
gr = 4 + len(FRAMEWORK) + 2
ws4.row_dimensions[gr].height = 26
merge_and_style(ws4, f"A{gr}:F{gr}",
    "HOW TO USE THIS FRAMEWORK — Practical Step-by-Step Guide",
    TEAL, font_size=11, bold=True, font_color=WHITE)

steps = [
    ("Step 1", "Go to screener.in → Custom Screen → Apply ROCE > 15, ROE > 15, Debt/Equity < 1, Sales growth 5yr > 12%"),
    ("Step 2", "From the filtered list, shortlist stocks in your target sectors (Banking, Capital Goods, Pharma, Consumer, Power, IT)"),
    ("Step 3", "For each shortlisted stock: Compare current PE to its own 5-year historical PE average (use Tijori or Tickertape)"),
    ("Step 4", "Verify PAT CAGR is genuine: Check if growth is driven by operating leverage, not one-time gains or tax benefits"),
    ("Step 5", "Check promoter holding trend: Increasing is positive; Pledging > 30% of holding = disqualify"),
    ("Step 6", "Verify free cash flow: PAT > 0 does not mean cash is being generated. Use CFO / CAPEX data on screener.in"),
    ("Step 7", "Build a 6–10 stock portfolio across at least 4 sectors. Review quarterly results; re-evaluate if thesis breaks"),
]
for i, (step, desc) in enumerate(steps):
    r = gr + 1 + i
    ws4.row_dimensions[r].height = 30
    bg = LIGHT_GOLD if i % 2 == 0 else WHITE
    write_cell(ws4, r, 1, step, GOLD, font_sz=10, bold=True, font_color=DARK_TEXT, align="center")
    write_cell(ws4, r, 2, desc, bg,   font_sz=9,  bold=False, font_color=DARK_TEXT, align="left", wrap=True)
    ws4.merge_cells(f"B{r}:F{r}")

# ─────────────────────────────────────────────────────────────────────────
# SHEET 5 · WATCHLIST TABLE
# ─────────────────────────────────────────────────────────────────────────
ws5 = wb.create_sheet("05 · Watchlist Table")
ws5.sheet_view.showGridLines = False

merge_and_style(ws5, "A1:H1",
    "INDIA EQUITY WATCHLIST — 12 RESEARCH CANDIDATES | 16% CAGR TARGET | JUNE 2026",
    HEADER_BG, font_size=13, bold=True, font_color=GOLD)
ws5.row_dimensions[1].height = 34

merge_and_style(ws5, "A2:H2",
    "For personal research only. Not a buy/sell recommendation. Verify all data before investing. "
    "Data sourced from broker reports, NSE filings, and company results (June 2026).",
    "3D1A00", font_size=9, bold=False, font_color=LIGHT_GOLD)
ws5.row_dimensions[2].height = 24

h5 = ["#", "Sector", "Company", "Ticker (NSE)",
      "Why it fits 16% CAGR Target", "Key Risks", "Valuation View", "Risk Level"]
w5 = [4,   22,        24,         14,
      52,                         36,              26,               12]

r = 3
ws5.row_dimensions[r].height = 26
for ci, (h, w) in enumerate(zip(h5, w5), 1):
    c = ws5.cell(r, ci, h)
    c.fill = hex_fill(NAVY)
    c.font = Font(name="Calibri", size=10, bold=True, color=WHITE)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = thin_border()
    set_col_width(ws5, ci, w)

risk_colors_map = {
    "Low":     GREEN_OK,
    "Low-Med": "5DADE2",
    "Medium":  AMBER,
    "Med-High":"E67E22",
    "High":    RED_RISK,
}
val_colors_map = {
    "Attractive": GREEN_OK,
    "Fair":       AMBER,
    "Expensive":  RED_RISK,
    "Fair/Premium": "E67E22",
}

current_sector_ws5 = None
row_num = 4

for i, (sector, company, ticker, why, risks, val, risk) in enumerate(WATCHLIST):
    # Sector sub-header
    if sector != current_sector_ws5:
        ws5.row_dimensions[row_num].height = 22
        merge_and_style(ws5, f"A{row_num}:H{row_num}",
            f"  ── {sector.upper()} ──",
            NAVY, font_size=9, bold=True, font_color=GOLD, align="left")
        row_num += 1
        current_sector_ws5 = sector

    r = row_num
    ws5.row_dimensions[r].height = 72
    bg = LIGHT_BG if i % 2 == 0 else WHITE

    # determine colours
    risk_bg = risk_colors_map.get(risk, AMBER)
    val_tag = val.split("(")[0].strip()
    val_bg  = val_colors_map.get(val_tag, AMBER)

    data_row = [
        (i+1,    "center", False, DARK_TEXT, bg),
        (sector, "center", True,  WHITE,     sector_colors.get(
            next((s["name"] for s in SECTORS if s["name"].lower() in sector.lower()), ""), NAVY)),
        (company,"left",   True,  NAVY,      bg),
        (ticker, "center", True,  WHITE,     TEAL),
        (why,    "left",   False, DARK_TEXT, bg),
        (risks,  "left",   False, "555555",  bg),
        (val,    "left",   True,  WHITE,     val_bg),
        (risk,   "center", True,  WHITE,     risk_bg),
    ]
    for ci, (val_d, al, bd, fc, fb) in enumerate(data_row, 1):
        c = ws5.cell(r, ci, val_d)
        c.fill = hex_fill(fb)
        c.font = Font(name="Calibri", size=9, bold=bd, color=fc)
        c.alignment = Alignment(horizontal=al, vertical="top", wrap_text=True, indent=1)
        c.border = thin_border()
    row_num += 1

# Freeze
ws5.freeze_panes = "A4"

# ─────────────────────────────────────────────────────────────────────────
# SHEET 6 · RISK MATRIX
# ─────────────────────────────────────────────────────────────────────────
ws6 = wb.create_sheet("06 · Risk & Valuation Matrix")
ws6.sheet_view.showGridLines = False

merge_and_style(ws6, "A1:J1",
    "RISK & VALUATION MATRIX — All 12 Research Candidates",
    HEADER_BG, font_size=13, bold=True, font_color=GOLD)
ws6.row_dimensions[1].height = 34

merge_and_style(ws6, "A2:J2",
    "Colour coding: Green = Low Risk / Attractive Valuation  |  Amber = Medium Risk / Fair Valuation  |  Red = Higher Risk / Expensive Valuation",
    NAVY, font_size=9, bold=False, font_color=LIGHT_GOLD)
ws6.row_dimensions[2].height = 22

# Matrix table
h6 = ["#","Company","Ticker","Sector","5Y Sales CAGR","5Y PAT CAGR","ROE","ROCE","Valuation","Risk"]
w6 = [4,   24,       13,      20,      15,             15,           10,   10,    26,         12]

r = 3
ws6.row_dimensions[r].height = 26
for ci, (h, w) in enumerate(zip(h6, w6), 1):
    c = ws6.cell(r, ci, h)
    c.fill = hex_fill(NAVY)
    c.font = Font(name="Calibri", size=10, bold=True, color=WHITE)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = thin_border()
    set_col_width(ws6, ci, w)

for i, st in enumerate(STOCKS):
    r = 4 + i
    ws6.row_dimensions[r].height = 28
    bg = LIGHT_BG if i % 2 == 0 else WHITE
    sc = sector_colors.get(st["sector"], NAVY)
    risk_bg = st["risk_color"]
    val_bg  = st["val_color"]

    vals_m = [
        (i+1,                 "center", False, DARK_TEXT, bg),
        (st["company"],       "left",   True,  NAVY,      bg),
        (st["ticker"],        "center", True,  WHITE,     TEAL),
        (st["sector"],        "center", False, WHITE,     sc),
        (st["sales_cagr_5yr"],"center", True,  DARK_TEXT, bg),
        (st["pat_cagr_5yr"],  "center", True,  DARK_TEXT, bg),
        (st["roe"],           "center", True,  DARK_TEXT, bg),
        (st["roce"],          "center", True,  DARK_TEXT, bg),
        (st["valuation_tag"], "center", True,  WHITE,     val_bg),
        (st["risk"],          "center", True,  WHITE,     risk_bg),
    ]
    for ci, (val_d, al, bd, fc, fb) in enumerate(vals_m, 1):
        c = ws6.cell(r, ci, val_d)
        c.fill = hex_fill(fb)
        c.font = Font(name="Calibri", size=9, bold=bd, color=fc)
        c.alignment = Alignment(horizontal=al, vertical="center", wrap_text=True, indent=1)
        c.border = thin_border()

# ── Legend ────────────────────────────────────────────────────────────────
legend_row = 4 + len(STOCKS) + 2
ws6.row_dimensions[legend_row].height = 24
merge_and_style(ws6, f"A{legend_row}:J{legend_row}",
    "LEGEND & INVESTMENT NOTES", TEAL, font_size=11, bold=True, font_color=WHITE)

legend_items = [
    (GREEN_OK, WHITE, "LOW RISK / ATTRACTIVE",
     "Strong fundamentals, reasonable valuation, predictable earnings. NTPC, Power Grid, TCS, ICICI Bank, Dr Reddy's."),
    (AMBER,    WHITE, "MEDIUM RISK / FAIR",
     "Good growth but valuation is at fair-to-premium levels. Monitor quarterly results closely. Bajaj Finance, L&T, Sun Pharma, Infosys."),
    (RED_RISK, WHITE, "HIGHER RISK / EXPENSIVE",
     "Excellent businesses but high valuation means lower margin of safety. Siemens, Titan, Trent. Buy only on meaningful dips."),
    (NAVY,     GOLD,  "KEY PRINCIPLE",
     "No single stock should exceed 15–20% of your equity portfolio. Diversify across ≥4 sectors. Review quarterly earnings."),
    (HEADER_BG,LIGHT_GOLD,"DISCLAIMER",
     "This is NOT investment advice. All data is based on publicly available information as of June 2026. "
     "Actual results may differ materially. Consult a SEBI-registered adviser before investing."),
]

for i, (bg, fc, label, desc) in enumerate(legend_items):
    r = legend_row + 1 + i
    ws6.row_dimensions[r].height = 38
    write_cell(ws6, r, 1, label, bg, font_sz=10, bold=True, font_color=fc, align="center")
    ws6.merge_cells(f"A{r}:B{r}")
    write_cell(ws6, r, 3, desc, LIGHT_BG if i % 2 == 0 else WHITE, font_sz=9,
               bold=False, font_color=DARK_TEXT, align="left", wrap=True)
    ws6.merge_cells(f"C{r}:J{r}")

# ── BAR CHART: 5Y PAT CAGR by company ────────────────────────────────────
# Build mini data table for chart
chart_start = legend_row + len(legend_items) + 3
ws6.cell(chart_start, 1, "Company").font = Font(bold=True)
ws6.cell(chart_start, 2, "5Y PAT CAGR (%)").font = Font(bold=True)

cagr_data = [
    ("ICICIBANK", 22), ("BAJFINANCE", 24), ("LT", 18), ("SIEMENS", 18),
    ("SUNPHARMA", 17), ("DRREDDY", 20),   ("TITAN", 35), ("TRENT", 45),
    ("NTPC", 14),      ("POWERGRID", 11), ("TCS", 12),   ("INFY", 11),
]
for j, (name, val) in enumerate(cagr_data):
    ws6.cell(chart_start + 1 + j, 1, name)
    ws6.cell(chart_start + 1 + j, 2, val)

chart = BarChart()
chart.type = "col"
chart.style = 10
chart.title = "Estimated 5-Year PAT CAGR by Stock (%)"
chart.y_axis.title = "PAT CAGR %"
chart.x_axis.title = "Stock"
chart.shape = 4
chart.width = 22
chart.height = 14

data_ref = Reference(ws6,
                     min_col=2, min_row=chart_start,
                     max_col=2, max_row=chart_start + len(cagr_data))
cats    = Reference(ws6, min_col=1, min_row=chart_start + 1,
                    max_row=chart_start + len(cagr_data))
chart.add_data(data_ref, titles_from_data=True)
chart.set_categories(cats)
chart.series[0].graphicalProperties.solidFill = "1B3A6B"

ws6.add_chart(chart, f"A{chart_start + len(cagr_data) + 2}")

# ═══════════════════════════════════════════════════════════════════════════
# FINAL TOUCHES — Tab colours
# ═══════════════════════════════════════════════════════════════════════════
tab_colors = [HEADER_BG, NAVY, TEAL, GOLD, GREEN_OK, AMBER]
for ws, col in zip([ws1, ws2, ws3, ws4, ws5, ws6], tab_colors):
    ws.sheet_properties.tabColor = col

# Print settings
for ws in [ws1, ws2, ws3, ws4, ws5, ws6]:
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToPage   = True
    ws.page_setup.fitToWidth  = 1
    ws.page_setup.fitToHeight = 0
    ws.print_title_rows       = "1:3"

# ═══════════════════════════════════════════════════════════════════════════
# SAVE
# ═══════════════════════════════════════════════════════════════════════════
output_path = "/home/user/Claude-/India_Equity_Watchlist_16pct_CAGR.xlsx"
wb.save(output_path)
print(f"Saved → {output_path}")
