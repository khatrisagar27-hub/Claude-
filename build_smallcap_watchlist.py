"""
India Small-Cap Equity Watchlist — Board-Ready Excel Report
16% CAGR Target | 2-3 Year Horizon | Nifty Smallcap 250 / Emerging Mid-Cap Focus
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, Reference
import datetime

# ── Forest × Cobalt × Amber colour palette ─────────────────────────────────
FOREST     = "0A2E1A"
COBALT     = "1A3A8F"
AMBER      = "C47A00"
ORANGE     = "CC4A00"
TEAL_D     = "0C5C5C"
PURPLE     = "4A1082"
MINT       = "EAF5EA"
LAVENDOR   = "EBF3FF"
CREAM_L    = "FFF8EE"
WHITE      = "FFFFFF"
DARK_TXT   = "1C1C2E"
GREEN_OK   = "1E7E34"
AMBER_MID  = "B8610A"
RED_HIGH   = "B03030"
GOLD       = "C8970A"
STEEL_L    = "D8E8F0"

def hf(h): return PatternFill("solid", fgColor=h)
def tb(c="C8D8C8"):
    s = Side(style="thin", color=c)
    return Border(top=s, bottom=s, left=s, right=s)
def scw(ws, col, w): ws.column_dimensions[get_column_letter(col)].width = w

def ms(ws, rng, text, bg, fsz=11, bold=True, fc=WHITE, ha="center", wrap=False):
    ws.merge_cells(rng)
    tl = ws[rng.split(":")[0]]
    tl.value = text
    tl.fill = hf(bg)
    tl.font = Font(name="Calibri", size=fsz, bold=bold, color=fc)
    tl.alignment = Alignment(horizontal=ha, vertical="center", wrap_text=wrap)

def wc(ws, row, col, val, bg=None, fsz=10, bold=False, fc=DARK_TXT,
       ha="left", wrap=False, bdr=True):
    c = ws.cell(row=row, column=col, value=val)
    if bg: c.fill = hf(bg)
    c.font = Font(name="Calibri", size=fsz, bold=bold, color=fc)
    c.alignment = Alignment(horizontal=ha, vertical="center", wrap_text=wrap)
    if bdr: c.border = tb()
    return c

# ═══════════════════════════════════════════════════════════════════════════
# DATA
# ═══════════════════════════════════════════════════════════════════════════

SECTORS = [
    {
        "id": "Defence & Aerospace",
        "color": COBALT,
        "momentum": "Very Strong",
        "drivers": (
            "India's defence indigenisation policy: 509-item 'positive indigenisation list' "
            "mandates domestic procurement. Defence budget growing 8-10% YoY. "
            "Data Patterns order inflows +216% YoY to ₹1,121 cr; order book ₹2,062 cr. "
            "ISRO launch cadence doubling (50+ missions by 2030). "
            "SpaceX competition forcing India to fast-track domestic space economy."
        ),
        "valuation": "Expensive — PE 60–75x; justified by order-book visibility and policy lock-in",
        "cagr_path": "Order book conversion + new programme wins → 25–35% EPS CAGR; PE expansion as sector re-rates",
        "risk": "Medium-High",
        "key_risk": "Lumpy defence contracts cause quarterly revenue volatility; single-customer concentration risk",
    },
    {
        "id": "Electronics Manufacturing (EMS)",
        "color": TEAL_D,
        "momentum": "Strong",
        "drivers": (
            "PLI scheme for electronics driving massive capex. India EMS sector CAGR 27% "
            "projected FY24–FY29 (HDFC Securities). Jefferies: EPS CAGR 44% FY25–28E. "
            "China+1 sourcing driving global contract wins. 5G, IoT, defence electronics "
            "adding premium product mix. Syrma SGS: Revenue +27%, PAT +87% FY26."
        ),
        "valuation": "Expensive — PE 50–70x; high but next-phase growth requires profitability improvement",
        "cagr_path": "Revenue scale + margin expansion + product mix premiumisation → 30–40% EPS CAGR",
        "risk": "Medium",
        "key_risk": "Margin compression on assembly-led revenue; competition from larger EMS players; client concentration",
    },
    {
        "id": "Specialty Chemicals",
        "color": AMBER,
        "momentum": "Strong (Recovery)",
        "drivers": (
            "China+1 supply chain diversification. India specialty chemicals targeting "
            "$100B by 2030. Navin Fluorine: EBITDA +103% YoY in FY26. Fluorine chemistry "
            "for pharma + agrochem; HFO refrigerant phase-in under Montreal Protocol. "
            "Vinati Organics' ATBS expansion commissioned Nov 2025 → revenue ramp FY27. "
            "Clean Science: high-ROCE green-chemistry moat with pricing power."
        ),
        "valuation": "Fair-to-Premium — Navin at ~30x (reasonable post-60% correction); Vinati ~35x; Clean ~42x",
        "cagr_path": "New capacity utilisation + pricing power + export ramp → 20–30% EPS CAGR",
        "risk": "Medium",
        "key_risk": "China dumping risk; agrochem demand cycle; customer inventory corrections",
    },
    {
        "id": "CDMO & Contract Pharma",
        "color": GREEN_OK,
        "momentum": "Strong",
        "drivers": (
            "India CDMO market: $13.5B → $27.9B by 2033 (8.4% CAGR). "
            "Suven Pharma: EBITDA margins 52–56%, 20%+ CAGR 4 years. Macquarie Outperform. "
            "Blue Jet Healthcare: FY26 weak year (contrast media cycle); Q4 PAT +60% QoQ "
            "signals recovery. Both benefit from China+1 sourcing and NCE outsourcing."
        ),
        "valuation": "Reasonable — Blue Jet at 34x (cheap vs sector avg 86x); Suven at 43x; Macquarie Buy both",
        "cagr_path": "Capacity ramp + margin expansion (10–12 ppt per Macquarie) → 20–30% EPS CAGR",
        "risk": "Medium",
        "key_risk": "Client programme delays; forex risk (USD revenue); regulated pricing in US market",
    },
    {
        "id": "Bio-Energy & Cleantech",
        "color": FOREST,
        "momentum": "Strong",
        "drivers": (
            "India's 20% ethanol blending target (E20 by 2025); currently ~15%. "
            "Praj Industries: India's only full-stack bioethanol plant EPC company. "
            "New bio-CNG + SAF (sustainable aviation fuel) contracts. "
            "Wastewater treatment orders growing. "
            "Direct policy beneficiary with captive domestic market and export optionality."
        ),
        "valuation": "Attractive — PE ~25–30x; reasonable for policy-backed structural growth",
        "cagr_path": "Ethanol order ramp + bio-CNG + SAF exports → 18–22% EPS CAGR over 3 years",
        "risk": "Low-Med",
        "key_risk": "Policy rollback on ethanol blending; sugarcane/grain supply cycles; commodity input costs",
    },
    {
        "id": "Pharma Intermediates & New Materials",
        "color": PURPLE,
        "momentum": "Strong",
        "drivers": (
            "Ami Organics: Pharma NCE intermediates + electrolyte chemicals for EV batteries. "
            "EmPS (electrolytes) segment opening a ₹5,000+ cr addressable market as India "
            "scales EV battery manufacturing. FY26 pharma biz growing 20%+ YoY; "
            "electrolyte revenues ramp starting FY27. Dual-growth-engine story."
        ),
        "valuation": "Fair — PE ~35–40x; EV electrolyte optionality not priced in yet",
        "cagr_path": "Pharma volumes + EV electrolyte ramp → 25–30% revenue CAGR over 3 years",
        "risk": "Medium",
        "key_risk": "EV electrolyte scale-up risk; pharma margin pressure; customer concentration",
    },
    {
        "id": "Affordable Housing Finance",
        "color": ORANGE,
        "momentum": "Strong",
        "drivers": (
            "Aptus Value Housing Finance: AUM +21% to ₹13,107 cr FY26; PAT +26% to ₹943 cr. "
            "Serves self-employed Tier 2–4 borrowers in South India (lowest NPAs in sector). "
            "ROE 20.1%, ROA 7.9% — among best in HFC sector. "
            "PM Awas Yojana (PMAY-U 2.0) target: 1 crore urban houses — direct AUM tailwind. "
            "Guidance: 22–24% AUM growth in FY27."
        ),
        "valuation": "Fair — PE ~18x FY27E; analyst fair value ₹340–360 (23–27% upside); quality at discount",
        "cagr_path": "AUM compounding 22–24% + ROE 20%+ → 25–28% EPS CAGR; re-rating as sector discovers quality",
        "risk": "Low-Med",
        "key_risk": "Concentration in South India; self-employed borrower stress if rural income slows; competition from large HFCs",
    },
]

STOCKS = [
    # ── DEFENCE ──
    {
        "no": 1, "co": "Data Patterns (India)", "ticker": "DATAPATTNS", "exch": "NSE",
        "sector": "Defence & Aerospace",
        "mktcap": "~₹25,000 cr",
        "why": (
            "India's only vertically integrated defence electronics company. "
            "FY26: Revenue ₹925 cr (+31%), EBITDA ₹371 cr (+35%), PAT ₹271 cr. "
            "Order book ₹2,062 cr; order inflows +216% YoY to ₹1,121 cr. "
            "90% indigenous content — direct beneficiary of indigenisation push. "
            "Stock up 111% from 2026 lows on order momentum."
        ),
        "risks": "Lumpy defence orders cause quarterly volatility; customer concentration; high PE 73x",
        "val": "Expensive — PE ~73x; order backlog 2.2x annual revenue partially justifies premium",
        "val_tag": "Expensive", "val_col": RED_HIGH,
        "roe": "~15%", "roce": "~18%",
        "rev_cagr": "~31% (FY26)", "pat_cagr": "~28%",
        "de": "~0.1x (near debt-free)",
        "risk": "Med-High", "risk_col": AMBER_MID,
    },
    {
        "no": 2, "co": "MTAR Technologies", "ticker": "MTARTECH", "exch": "NSE",
        "sector": "Defence & Aerospace",
        "mktcap": "~₹5,500 cr",
        "why": (
            "Precision engineering for ISRO (PSLV/GSLV/Gaganyaan), DRDO, HAL, "
            "nuclear energy, and Bloom Energy (clean energy). "
            "Only Indian company certified to machine nuclear fuel handling equipment. "
            "Revenue growing 25–30% CAGR. Expanding into civil aerospace as "
            "Space Economy policy opens up. Deep technology moat."
        ),
        "risks": "Very lumpy revenues; small revenue base; delayed ISRO mission schedules",
        "val": "Expensive — PE ~60–70x; deep-tech moat + ISRO mission ramp justifies",
        "val_tag": "Expensive", "val_col": RED_HIGH,
        "roe": "~18–20%", "roce": "~20%",
        "rev_cagr": "~25–30%", "pat_cagr": "~25%",
        "de": "~0.2x",
        "risk": "High", "risk_col": RED_HIGH,
    },
    # ── EMS ──
    {
        "no": 3, "co": "Syrma SGS Technology", "ticker": "SYRMA", "exch": "NSE",
        "sector": "Electronics Manufacturing (EMS)",
        "mktcap": "~₹6,000 cr",
        "why": (
            "India's cleanest EMS execution story. FY26: Revenue ₹4,857 cr (+27%), "
            "PAT ₹346 cr (+87%), EBITDA ₹545 cr (+68%), net cash ₹467 cr. "
            "RFID, defence electronics, precision PCBAs. Q4 FY26 revenue +56%, PAT +67%. "
            "Targets ₹6,000 cr+ revenue FY27. Standout: profit growing faster than revenue."
        ),
        "risks": "Margin pressure from low-value assembly; client concentration; PLI dependency",
        "val": "Fair — PE ~50–55x; profit growth 87% makes PEG ratio attractive at ~0.6x",
        "val_tag": "Fair", "val_col": AMBER_MID,
        "roe": "~16%", "roce": "~17%",
        "rev_cagr": "~27% (FY26)", "pat_cagr": "~87% (FY26); ~35% normalised",
        "de": "Net cash (₹467 cr)",
        "risk": "Medium", "risk_col": AMBER_MID,
    },
    {
        "no": 4, "co": "Kaynes Technology India", "ticker": "KAYNES", "exch": "NSE",
        "sector": "Electronics Manufacturing (EMS)",
        "mktcap": "~₹15,000 cr",
        "why": (
            "IoT-connected, intelligent EMS focusing on medical, industrial, "
            "aerospace & defence electronics. Revenue +26.2% in Q4 FY26. "
            "High-margin product mix (not commodity assembly) = superior moat. "
            "Expanding into Space EMS. Jefferies: 44% EPS CAGR FY25–28E for sector. "
            "Order book strong; Airbus, defence clients are long-cycle anchors."
        ),
        "risks": "Q4 FY26 profit fell 21.5% (transitional quarter); PE 65x at full price; small absolute profits",
        "val": "Expensive — PE ~65x; high-quality product mix (medical/defence) is the differentiator",
        "val_tag": "Expensive", "val_col": RED_HIGH,
        "roe": "~10–12% (scaling)", "roce": "~12%",
        "rev_cagr": "~30%", "pat_cagr": "~35%",
        "de": "~0.3x",
        "risk": "Med-High", "risk_col": AMBER_MID,
    },
    # ── SPECIALTY CHEMICALS ──
    {
        "no": 5, "co": "Navin Fluorine International", "ticker": "NAVINFLUOR", "exch": "NSE",
        "sector": "Specialty Chemicals",
        "mktcap": "~₹18,000 cr",
        "why": (
            "India's fluorine chemistry powerhouse. FY26: Revenue ₹3,314 cr (+41%), "
            "EBITDA ₹1,082 cr (+103%), EBITDA margins 32.6%, net profit +130% to ₹664 cr. "
            "HFO refrigerant demand (Montreal Protocol phase-in). Pharma fluorine API pipeline. "
            "Stock had corrected 50%+ from peak — entry much better than 2022 levels."
        ),
        "risks": "Agrochem export cycles; customer inventory de-stocking; China competition in commodity fluorine",
        "val": "Fair — PE ~28–32x; significant re-rating already done from 60x peak; now reasonable",
        "val_tag": "Fair", "val_col": AMBER_MID,
        "roe": "~18–20%", "roce": "~20%",
        "rev_cagr": "~20–25%", "pat_cagr": "~25–30%",
        "de": "~0.1x",
        "risk": "Medium", "risk_col": AMBER_MID,
    },
    {
        "no": 6, "co": "Vinati Organics", "ticker": "VINATIORGA", "exch": "NSE",
        "sector": "Specialty Chemicals",
        "mktcap": "~₹13,000 cr",
        "why": (
            "Global leader (65%+ share) in ATBS monomers; #2 globally in IBB. "
            "FY26: PAT ₹488 cr (+17.5%), zero debt (cleared ₹63 cr borrowing). "
            "ATBS expansion commissioned Nov 2025 → FY27 revenue ramp guided at 15%. "
            "EBITDA margins stable at ~27%. Founder-promoter ownership >70%. "
            "Pricing power from monopoly-like global positions."
        ),
        "risks": "Revenue was flat FY26; ATBS expansion revenue ramp may lag; single-product revenue risk",
        "val": "Fair — PE ~33–38x; premium for global monopoly positioning and zero debt",
        "val_tag": "Fair", "val_col": AMBER_MID,
        "roe": "~22%", "roce": "~25%",
        "rev_cagr": "~15% (FY27E)", "pat_cagr": "~20–25%",
        "de": "Zero debt",
        "risk": "Medium", "risk_col": AMBER_MID,
    },
    {
        "no": 7, "co": "Clean Science & Technology", "ticker": "CLEAN", "exch": "NSE",
        "sector": "Specialty Chemicals",
        "mktcap": "~₹8,000 cr",
        "why": (
            "World's lowest-cost producer of MEHQ, BHA, and anisole via "
            "proprietary green catalytic chemistry. EBITDA margins ~35%+. "
            "ROCE: ~30%+ (one of highest in specialty chemicals). Zero debt. "
            "Expanding into performance chemicals + agrochemical intermediates. "
            "Environmental regulations globally tightening → cleaner chemistry premium."
        ),
        "risks": "Concentrated product portfolio; commodity price pass-through risk; PE 40x not cheap",
        "val": "Fair — PE ~40–45x; extraordinary ROCE of 30%+ justifies premium; buy on 15%+ corrections",
        "val_tag": "Fair", "val_col": AMBER_MID,
        "roe": "~25%", "roce": "~30%+",
        "rev_cagr": "~18–20%", "pat_cagr": "~22–25%",
        "de": "Zero debt",
        "risk": "Medium", "risk_col": AMBER_MID,
    },
    # ── CDMO ──
    {
        "no": 8, "co": "Blue Jet Healthcare", "ticker": "BLUEJET", "exch": "NSE",
        "sector": "CDMO & Contract Pharma",
        "mktcap": "~₹9,000 cr",
        "why": (
            "Niche CDMO for contrast media intermediates (iodine-based imaging agents). "
            "FY26 was a weak year (revenue -8%, PAT -19%) due to inventory destocking. "
            "But Q4 FY26 PAT jumped 60% QoQ — recovery underway. "
            "PE 34x vs pharma sector avg 86x = significant undervaluation. "
            "Macquarie: Outperform; EBITDA margin expansion ahead as capacity utilises."
        ),
        "risks": "FY26 was a down year; contrast media market is concentrated (limited clients); pricing risk",
        "val": "Attractive — PE ~34x; cheapest CDMO in India vs sector avg 86x; buy the dip",
        "val_tag": "Attractive", "val_col": GREEN_OK,
        "roe": "~20%", "roce": "~22%",
        "rev_cagr": "~18–20% (FY27E recovery)", "pat_cagr": "~22–25% (FY27E+)",
        "de": "~0.1x",
        "risk": "Medium", "risk_col": AMBER_MID,
    },
    {
        "no": 9, "co": "Suven Pharma (Cohance)", "ticker": "SUVENPHAR", "exch": "NSE",
        "sector": "CDMO & Contract Pharma",
        "mktcap": "~₹14,000 cr",
        "why": (
            "India's highest-margin CDMO (EBITDA 52–56%!). Specialises in NCE drug "
            "discovery synthesis and early-phase CDMO for global pharma innovators. "
            "ROE 26.12%, 20%+ revenue CAGR for 4 consecutive years. "
            "Now rebranded Cohance Lifesciences. Macquarie Outperform. "
            "Citi: Revenue to expand 3x and EBITDA 4x by FY30 (for sector)."
        ),
        "risks": "Dependent on global innovator pipeline; molecule trial failures = order loss; PE 43x elevated",
        "val": "Fair — PE ~43x; premium justified by 52%+ EBITDA margin and 20%+ growth; few peers globally",
        "val_tag": "Fair", "val_col": AMBER_MID,
        "roe": "~26%", "roce": "~28%",
        "rev_cagr": "~20–25%", "pat_cagr": "~22–25%",
        "de": "~0.1x",
        "risk": "Medium", "risk_col": AMBER_MID,
    },
    # ── BIO-ENERGY ──
    {
        "no": 10, "co": "Praj Industries", "ticker": "PRAJIND", "exch": "NSE",
        "sector": "Bio-Energy & Cleantech",
        "mktcap": "~₹11,000 cr",
        "why": (
            "India's only full-stack bioethanol plant EPC + technology company. "
            "Direct beneficiary of India's E20 (20% ethanol blending) policy. "
            "New verticals: bio-CNG, sustainable aviation fuel (SAF), wastewater. "
            "ROE ~20%, ROCE ~22%, consistent dividend. Order book driven by "
            "sugar mills + grain-based distilleries expanding capacity. "
            "Export orders for Africa/ASEAN bioethanol plants growing."
        ),
        "risks": "Ethanol policy rollback risk; sugarcane supply volatility; grain diversion controversy",
        "val": "Attractive — PE ~25–28x; below capital-goods peers; policy-backed structural story",
        "val_tag": "Attractive", "val_col": GREEN_OK,
        "roe": "~20%", "roce": "~22%",
        "rev_cagr": "~18–20%", "pat_cagr": "~20%",
        "de": "~0.1x (near debt-free)",
        "risk": "Low-Med", "risk_col": GREEN_OK,
    },
    # ── PHARMA INTERMEDIATES ──
    {
        "no": 11, "co": "Ami Organics", "ticker": "AMIORG", "exch": "NSE",
        "sector": "Pharma Intermediates & New Materials",
        "mktcap": "~₹5,000 cr",
        "why": (
            "Two growth engines in one: (1) Pharma NCE intermediates growing 20%+ YoY "
            "for innovator drug programmes; (2) EmPS (electrolyte salts for EV batteries) "
            "— a potential ₹5,000+ cr market opening as India scales EV manufacturing. "
            "ROCE ~22%, ROE ~20%, low debt. Founder-led. Rare combination of "
            "cash-generative pharma + high-optionality EV materials in a single small-cap."
        ),
        "risks": "EV electrolyte ramp slower than expected; pharma client concentration; small company risk",
        "val": "Fair — PE ~35–40x; EV electrolyte optionality not yet priced in = embedded call option",
        "val_tag": "Fair", "val_col": AMBER_MID,
        "roe": "~20%", "roce": "~22%",
        "rev_cagr": "~22–25%", "pat_cagr": "~25%",
        "de": "~0.3x",
        "risk": "Med-High", "risk_col": AMBER_MID,
    },
    # ── AFFORDABLE HOUSING ──
    {
        "no": 12, "co": "Aptus Value Housing Finance", "ticker": "APTUS", "exch": "NSE",
        "sector": "Affordable Housing Finance",
        "mktcap": "~₹11,000 cr",
        "why": (
            "India's best affordable housing NBFC. FY26: AUM ₹13,107 cr (+21%), "
            "Revenue ₹2,246 cr (+25%), PAT ₹943 cr (+26%), ROE 20.1%, ROA 7.9%. "
            "Serves self-employed Tier 2-4 South India borrowers — near-zero NPA. "
            "PMAY-U 2.0 targets 1 crore urban houses — massive tailwind. "
            "Analyst fair value ₹340–360 (23–27% upside). FY27 guidance: 22–24% AUM growth."
        ),
        "risks": "South India geographic concentration; self-employed borrower stress risk; rural income dependence",
        "val": "Fair — PE ~18x FY27E; reasonable for 26% PAT growth + 20% ROE quality",
        "val_tag": "Fair", "val_col": AMBER_MID,
        "roe": "~20%", "roce": "~14.5%",
        "rev_cagr": "~25% (FY26)", "pat_cagr": "~26% (FY26)",
        "de": "~4x (standard HFC leverage; NPA near zero)",
        "risk": "Low-Med", "risk_col": GREEN_OK,
    },
]

FRAMEWORK = [
    ("Revenue CAGR (3–5 Year)",         "≥ 18% (prefer ≥ 22%)",
     "Small-caps justify risk premium only with higher revenue growth. Below 15% = "
     "insufficient to compensate for illiquidity and volatility. Look at 3-yr CAGR, not just latest year.",
     "18–25%+"),
    ("PAT CAGR (3–5 Year)",             "≥ 20% (prefer ≥ 25%)",
     "Profit must grow faster than revenue. For small-caps, operating leverage should "
     "kick in at scale. Beware of one-time other income or tax reversals inflating PAT.",
     "20–25%+"),
    ("ROCE",                            "≥ 20% (prefer ≥ 25%)",
     "This is THE critical metric for small-cap compounders. ROCE > 20% means every rupee "
     "reinvested creates more than one rupee of value. Nifty avg ROCE is ~14% — "
     "small-cap premium requires >20%.",
     "≥ 20–30%"),
    ("ROE",                             "≥ 18% (without excessive debt)",
     "High ROE driven by genuine business profitability, not leverage. For small-cap HFCs: "
     "ROE ≥ 15% + ROA ≥ 2%. Avoid companies with D/E > 0.5x showing high ROE.",
     "≥ 18–25%"),
    ("Debt-to-Equity",                  "≤ 0.3x for non-financials; ≤ 0.5x for small mfg",
     "Small-cap companies have limited access to capital in downturns. Zero or minimal debt "
     "gives them survivability during bad years and flexibility to grab opportunities. "
     "Above 1.0x in a non-infra small-cap = red flag.",
     "≤ 0.3–0.5x"),
    ("EBITDA Margin Trend",             "Stable or expanding; ≥ 15% for mfg; ≥ 25% for niche",
     "Contracting EBITDA margins signal pricing power loss or cost pressure. "
     "Best small-caps have margins expanding 100–200 bps per year as scale increases.",
     "Expanding trend"),
    ("Promoter Holding",                "≥ 50%; pledging < 10% of holding",
     "Founder-promoter skin in the game is critical for small-caps. Promoter shareholding "
     "decreasing rapidly = flag. Pledging > 20% of their holding = serious red flag.",
     "≥ 50% stable"),
    ("PE vs PEG Ratio",                 "PEG < 1.5x (PE / 5-yr PAT CAGR)",
     "For high-growth small-caps, PEG ratio is more relevant than PE alone. A company at "
     "PE 50x growing at 40% has PEG 1.25 = reasonable. PE 50x growing at 12% = PEG 4.2 = avoid.",
     "PEG ≤ 1.5x"),
    ("Market Cap + Daily Liquidity",    "₹1,000–₹20,000 cr; avg daily vol ≥ ₹20 cr",
     "Below ₹500 cr market cap = micro-cap with significant liquidity risk. "
     "Daily traded volume < ₹5 crore means you may struggle to exit in a falling market. "
     "Small-caps for 2yr+ horizon — avoid illiquid names.",
     "₹1,000–20,000 cr"),
    ("Sector Tailwind Duration",        "Policy/structural tailwind ≥ 5 years",
     "Best small-cap returns come from being early in a multi-year structural theme: "
     "defence indigenisation, EMS PLI, CDMO China+1, EV materials, affordable housing. "
     "Cyclical small-caps (commodity, agrochem) require different approach.",
     "≥ 5-yr structural tailwind"),
]

WATCHLIST = [
    ("Defence", "Data Patterns", "DATAPATTNS",
     "Order inflows +216% YoY; order book ₹2,062 cr; 90% indigenous; revenue +31% FY26",
     "Lumpy revenues; high PE 73x; customer concentration", "Expensive (PE ~73x)", "Med-High"),
    ("Defence", "MTAR Technologies", "MTARTECH",
     "Only certified nuclear precision machinist in India; ISRO/DRDO/HAL; 25–30% rev CAGR",
     "Very lumpy; small base; mission schedule delays", "Expensive (PE ~65x)", "High"),
    ("EMS", "Syrma SGS Technology", "SYRMA",
     "Revenue +27%, PAT +87%, net cash ₹467 cr; RFID+defence EMS; targeting ₹6,000 cr revenue",
     "Assembly margin pressure; client concentration; PE ~52x", "Fair (PEG ~0.6x)", "Medium"),
    ("EMS", "Kaynes Technology", "KAYNES",
     "IoT/medical/defence EMS; high-margin product mix; revenue +26%; Jefferies 44% EPS CAGR sector",
     "Q4 FY26 profit fell 21.5%; PE 65x; small absolute profit base", "Expensive (PE ~65x)", "Med-High"),
    ("Spec Chem", "Navin Fluorine", "NAVINFLUOR",
     "EBITDA +103% FY26; PAT +130%; margins 32.6%; HFO + pharma fluorine pipeline",
     "Agrochem cycle risk; customer destocking; China competition", "Fair (PE ~30x)", "Medium"),
    ("Spec Chem", "Vinati Organics", "VINATIORGA",
     "Global #1 ATBS; zero debt; ATBS expansion commissioned; FY27 rev guide +15%; ROCE 25%",
     "Revenue was flat FY26; ATBS ramp may lag; single-product risk", "Fair (PE ~35x)", "Medium"),
    ("Spec Chem", "Clean Science & Tech", "CLEAN",
     "ROCE 30%+; EBITDA margin 35%+; zero debt; green chemistry monopoly in MEHQ/BHA/anisole",
     "Concentrated portfolio; commodity pass-through risk; PE ~42x", "Fair (PE ~42x)", "Medium"),
    ("CDMO", "Blue Jet Healthcare", "BLUEJET",
     "PE 34x vs sector 86x = deeply undervalued; Q4 FY26 PAT +60% QoQ; Macquarie Outperform",
     "FY26 was a down year; contrast media concentration; order lumpiness", "Attractive (PE ~34x)", "Medium"),
    ("CDMO", "Suven Pharma (Cohance)", "SUVENPHAR",
     "EBITDA 52–56%; ROE 26%; 20%+ CAGR 4yrs; Macquarie Outperform; Citi: 4x EBITDA by FY30",
     "NCE programme risk; PE 43x; molecule trial failure = order loss", "Fair (PE ~43x)", "Medium"),
    ("Bio-Energy", "Praj Industries", "PRAJIND",
     "Only full-stack bioethanol EPC; E20 policy direct beneficiary; bio-CNG+SAF new verticals",
     "Ethanol policy risk; sugarcane supply cycles; grain diversion controversy", "Attractive (PE ~26x)", "Low-Med"),
    ("New Materials", "Ami Organics", "AMIORG",
     "Pharma NCE intermediates + EV electrolyte salts (EmPS); dual growth engines; ROCE 22%",
     "EV electrolyte ramp risk; pharma concentration; small company risk", "Fair (PE ~38x)", "Med-High"),
    ("Housing Finance", "Aptus Value Housing", "APTUS",
     "PAT +26%; AUM +21% to ₹13,107 cr; ROE 20.1%; ROA 7.9%; PMAY-U 2.0 tailwind",
     "South India concentration; self-employed borrower stress; competition from large HFCs",
     "Fair (PE ~18x FY27E)", "Low-Med"),
]

# ═══════════════════════════════════════════════════════════════════════════
# BUILD WORKBOOK
# ═══════════════════════════════════════════════════════════════════════════
wb = openpyxl.Workbook()
wb.remove(wb.active)
SC_COLOR = {s["id"]: s["color"] for s in SECTORS}

# ─────────────────────────────────────────────────────────────────────────
# SHEET 1 · COVER
# ─────────────────────────────────────────────────────────────────────────
ws1 = wb.create_sheet("01 · Cover & Risk Notice")
ws1.sheet_view.showGridLines = False

for r in range(1, 20):
    ws1.row_dimensions[r].height = 22
    for c in range(1, 15): ws1.cell(r, c).fill = hf(FOREST)

ws1.row_dimensions[1].height = 6
for c in range(1, 15): ws1.cell(1, c).fill = hf(ORANGE)

ms(ws1, "B3:N5", "INDIA SMALL-CAP EQUITY WATCHLIST",
   FOREST, fsz=26, bold=True, fc=GOLD)
ms(ws1, "B6:N7",
   "Nifty Smallcap 250 / Emerging Mid-Cap | 16%+ CAGR Target | 2–3 Year Horizon | NSE",
   FOREST, fsz=13, bold=False, fc="B8D4C8")
ms(ws1, "B8:N9",
   f"Date: {datetime.date.today().strftime('%B %d, %Y')}  ·  "
   "12 Research Candidates across 7 High-Growth Themes  ·  All Niche Market Leaders",
   FOREST, fsz=10, bold=False, fc="7FA899")

ws1.row_dimensions[10].height = 5
for c in range(1, 15): ws1.cell(10, c).fill = hf(ORANGE)

# Risk Warning Box
ms(ws1, "B11:N14",
   "⚠  IMPORTANT RISK NOTICE: Small-cap stocks are significantly more volatile than large-caps. "
   "The Nifty Smallcap 100 has historically fallen 40–60% in bear markets and doubled in "
   "bull markets within 18 months. This report is for RESEARCH PURPOSES ONLY and does NOT "
   "constitute investment advice. Maximum 5–8% portfolio weight per stock is recommended. "
   "Minimum investment horizon: 3 years. Consult a SEBI-registered adviser before investing.",
   "3A1000", fsz=9, bold=False, fc="FFB347", ha="center", wrap=True)
ws1.row_dimensions[11].height = 26
ws1.row_dimensions[12].height = 26
ws1.row_dimensions[13].height = 26
ws1.row_dimensions[14].height = 26

kpi_data = [
    ("B", "D", "12\nResearch\nCandidates",   COBALT),
    ("E", "G", "7\nNiche\nSectors",           FOREST),
    ("H", "J", "16%+\nCAGR\nTarget",          ORANGE),
    ("K", "M", "3-Year\nIdeal\nHorizon",      TEAL_D),
]
for st, en, lbl, bg in kpi_data:
    ws1.merge_cells(f"{st}19:{en}22")
    c = ws1[f"{st}19"]
    c.value = lbl
    c.fill = hf(bg)
    c.font = Font(name="Calibri", size=15, bold=True, color=WHITE)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = Border(top=Side(style="medium", color=ORANGE),
                      bottom=Side(style="medium", color=ORANGE),
                      left=Side(style="medium", color=ORANGE),
                      right=Side(style="medium", color=ORANGE))
for r in range(19, 23): ws1.row_dimensions[r].height = 22

row = 24
ms(ws1, f"B{row}:N{row}", "WHY SMALL-CAPS FOR 16%+ CAGR?", COBALT, fsz=12, bold=True, fc=GOLD)
ws1.row_dimensions[row].height = 28

reasons = [
    ("Higher Growth Ceiling",    "~14–16% earnings CAGR",
     "Small-caps can deliver 25–40% earnings CAGR vs 12–15% for large-caps, by capturing niche markets, gaining share from unorganised players, and expanding across geographies."),
    ("Nifty Smallcap 100 PE",    "~20x (below 10-yr avg)",
     "India's smallcap index trades at a meaningful discount to its long-term average after the 2024–2025 correction. Quality small-caps at fair valuations = strong entry point."),
    ("Structural Themes",        "Defence / EMS / CDMO / Chem",
     "7 sectors in this report are driven by multi-year policy (PLI, indigenisation, E20, PMAY) and global structural shifts (China+1) — not just economic cycles."),
    ("Size Advantage",           "Market cap < ₹20,000 cr",
     "FIIs and large domestic funds cannot meaningfully participate in stocks below ₹5,000 cr market cap. When they enter, re-rating is dramatic. Early positions capture this."),
    ("Margin of Safety",         "Post-2024 correction",
     "Many quality small-caps corrected 40–60% from peak in 2024–2025. Several now trade below their historical average PE, offering better risk-reward than 2021–2022 levels."),
]
for i, (metric, val, note) in enumerate(reasons):
    r = row + 1 + i
    ws1.row_dimensions[r].height = 26
    bg = MINT if i % 2 == 0 else WHITE
    wc(ws1, r, 2, metric, bg, fsz=10, bold=True,  fc=COBALT, ha="left")
    ws1.cell(r, 2).alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws1.merge_cells(f"B{r}:B{r}")
    wc(ws1, r, 3, val, bg, fsz=10, bold=True, fc=ORANGE, ha="center")
    ws1.merge_cells(f"C{r}:D{r}")
    wc(ws1, r, 5, note, bg, fsz=9, bold=False, fc="333333", ha="left", wrap=True)
    ws1.merge_cells(f"E{r}:N{r}")
    ws1.cell(r, 5).alignment = Alignment(horizontal="left", vertical="center", wrap_text=True, indent=1)

nav = row + len(reasons) + 2
ws1.row_dimensions[nav].height = 26
ms(ws1, f"B{nav}:N{nav}", "WORKBOOK NAVIGATION", TEAL_D, fsz=11, bold=True, fc=WHITE)
sheets = [
    ("01 · Cover & Risk Notice",   "This page — rationale, risk warning, why small-caps, navigation guide"),
    ("02 · Sector Analysis",       "7 niche sectors with structural drivers, valuation, path to 16%+ CAGR"),
    ("03 · Stock Deep-Dive",       "12 research candidates: full profile — ROE, ROCE, CAGR, D/E, valuation"),
    ("04 · Selection Framework",   "10 small-cap screening criteria + step-by-step guide (screener.in ready)"),
    ("05 · Watchlist Summary",     "Colour-coded board-ready table: sector, stock, why, risks, valuation, risk"),
    ("06 · Risk & Growth Matrix",  "Side-by-side comparison of all 12 stocks + PAT CAGR chart"),
]
for i, (sh, desc) in enumerate(sheets):
    r = nav + 1 + i
    ws1.row_dimensions[r].height = 20
    bg = CREAM_L if i % 2 == 0 else WHITE
    wc(ws1, r, 2, sh,   bg, fsz=10, bold=True,  fc=FOREST, ha="left")
    ws1.merge_cells(f"B{r}:E{r}")
    wc(ws1, r, 6, desc, bg, fsz=10, bold=False, fc="333333", ha="left")
    ws1.merge_cells(f"F{r}:N{r}")

for col, w in [(1,2),(2,22),(3,8),(4,8),(5,44),(6,2),(7,2),(8,2),(9,2),(10,2),(11,2),(12,2),(13,2),(14,2)]:
    scw(ws1, col, w)

# ─────────────────────────────────────────────────────────────────────────
# SHEET 2 · SECTOR ANALYSIS
# ─────────────────────────────────────────────────────────────────────────
ws2 = wb.create_sheet("02 · Sector Analysis")
ws2.sheet_view.showGridLines = False
ms(ws2, "A1:I1",
   "SECTOR ANALYSIS — 7 HIGH-GROWTH SMALL-CAP THEMES FOR 16%+ CAGR (2025–2028)",
   FOREST, fsz=13, bold=True, fc=GOLD)
ws2.row_dimensions[1].height = 34

h2 = ["#","Sector / Theme","Momentum","Structural Drivers (3-yr view)",
      "Valuation vs History","Path to 16%+ CAGR","Key Risk","Risk Level"]
w2 = [4,  24,              12,         50,
      34,                  38,              30,          13]
r = 2
ws2.row_dimensions[r].height = 26
for ci, (h, w) in enumerate(zip(h2, w2), 1):
    c = ws2.cell(r, ci, h)
    c.fill = hf(COBALT); c.font = Font(name="Calibri", size=10, bold=True, color=WHITE)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = tb()
    scw(ws2, ci, w)

rmap = {"Very Strong": GREEN_OK, "Strong": GREEN_OK, "Strong (Recovery)": AMBER_MID,
        "Moderate": AMBER_MID, "Low-Med": GREEN_OK}
risk_bg = {"Low": GREEN_OK, "Low-Med": "5DADE2", "Medium": AMBER_MID, "Medium-High": AMBER_MID,
           "High": RED_HIGH}

for i, s in enumerate(SECTORS):
    r = 3 + i
    ws2.row_dimensions[r].height = 90
    bg = MINT if i % 2 == 0 else WHITE
    rb = risk_bg.get(s["risk"], AMBER_MID)
    row_data = [
        (i+1,           "center", False, DARK_TXT, bg),
        (s["id"],       "left",   True,  WHITE,    s["color"]),
        (s["momentum"], "center", True,  WHITE,    rmap.get(s["momentum"], AMBER_MID)),
        (s["drivers"],  "left",   False, DARK_TXT, bg),
        (s["valuation"],"left",   False, DARK_TXT, bg),
        (s["cagr_path"],"left",   False, DARK_TXT, bg),
        (s["key_risk"], "left",   False, DARK_TXT, bg),
        (s["risk"],     "center", True,  WHITE,    rb),
    ]
    for ci, (val, al, bd, fc, fb) in enumerate(row_data, 1):
        c = ws2.cell(r, ci, val)
        c.fill = hf(fb); c.font = Font(name="Calibri", size=9, bold=bd, color=fc)
        c.alignment = Alignment(horizontal=al, vertical="top", wrap_text=True, indent=1)
        c.border = tb()

# ─────────────────────────────────────────────────────────────────────────
# SHEET 3 · STOCK DEEP-DIVE
# ─────────────────────────────────────────────────────────────────────────
ws3 = wb.create_sheet("03 · Stock Deep-Dive")
ws3.sheet_view.showGridLines = False
ms(ws3, "A1:L1",
   "SMALL-CAP RESEARCH CANDIDATES — 12 STOCKS (NOT Buy/Sell Recommendations) | Minimum 3-Year Horizon",
   FOREST, fsz=13, bold=True, fc=GOLD)
ws3.row_dimensions[1].height = 34

h3 = ["#","Company (NSE)","Ticker","Sector","Market Cap",
      "Why it fits 16%+ CAGR","Key Risks","Valuation",
      "ROE","3Y Rev CAGR","3Y PAT CAGR","Risk"]
w3 = [4,  24,              12,      24,      14,
      52,                  32,       28,
      12,  14,              14,       12]

r = 2
ws3.row_dimensions[r].height = 26
for ci, (h, w) in enumerate(zip(h3, w3), 1):
    c = ws3.cell(r, ci, h)
    c.fill = hf(COBALT); c.font = Font(name="Calibri", size=10, bold=True, color=WHITE)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = tb()
    scw(ws3, ci, w)

for i, st in enumerate(STOCKS):
    r = 3 + i
    ws3.row_dimensions[r].height = 88
    bg = MINT if i % 2 == 0 else WHITE
    sc = SC_COLOR.get(st["sector"], COBALT)
    vals = [
        (st["no"],       "center", False, DARK_TXT, bg),
        (st["co"],       "left",   True,  FOREST,   bg),
        (st["ticker"],   "center", True,  WHITE,    ORANGE),
        (st["sector"],   "center", True,  WHITE,    sc),
        (st["mktcap"],   "center", False, DARK_TXT, bg),
        (st["why"],      "left",   False, DARK_TXT, bg),
        (st["risks"],    "left",   False, "555555", bg),
        (st["val"],      "left",   True,  WHITE,    st["val_col"]),
        (st["roe"],      "center", True,  DARK_TXT, bg),
        (st["rev_cagr"], "center", True,  DARK_TXT, bg),
        (st["pat_cagr"], "center", True,  DARK_TXT, bg),
        (st["risk"],     "center", True,  WHITE,    st["risk_col"]),
    ]
    for ci, (val, al, bd, fc, fb) in enumerate(vals, 1):
        c = ws3.cell(r, ci, val)
        c.fill = hf(fb); c.font = Font(name="Calibri", size=9, bold=bd, color=fc)
        c.alignment = Alignment(horizontal=al, vertical="top", wrap_text=True, indent=1)
        c.border = tb()
ws3.freeze_panes = "A3"

# ─────────────────────────────────────────────────────────────────────────
# SHEET 4 · SELECTION FRAMEWORK
# ─────────────────────────────────────────────────────────────────────────
ws4 = wb.create_sheet("04 · Selection Framework")
ws4.sheet_view.showGridLines = False
ms(ws4, "A1:F1",
   "SMALL-CAP STOCK SELECTION FRAMEWORK — Higher Standards Required for Higher Risk",
   FOREST, fsz=13, bold=True, fc=GOLD)
ws4.row_dimensions[1].height = 34
ms(ws4, "A2:F2",
   "Small-caps demand stricter fundamental gates than large-caps. Higher growth, lower debt, higher ROCE. Verify on screener.in.",
   COBALT, fsz=10, bold=False, fc=STEEL_L)
ws4.row_dimensions[2].height = 22

h4 = ["#","Criterion","Minimum Threshold","Why It Matters for Small-Caps","Benchmark"]
w4 = [4,   30,          22,                54,                              18]
r = 3
ws4.row_dimensions[r].height = 26
for ci, (h, w) in enumerate(zip(h4, w4), 1):
    c = ws4.cell(r, ci, h)
    c.fill = hf(COBALT); c.font = Font(name="Calibri", size=10, bold=True, color=WHITE)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = tb()
    scw(ws4, ci, w)

for i, (crit, thresh, why, bench) in enumerate(FRAMEWORK):
    r = 4 + i
    ws4.row_dimensions[r].height = 68
    bg = MINT if i % 2 == 0 else WHITE
    row_data = [
        (i+1,   "center", False, DARK_TXT, bg),
        (crit,  "left",   True,  FOREST,   bg),
        (thresh,"center", True,  WHITE,    AMBER),
        (why,   "left",   False, DARK_TXT, bg),
        (bench, "center", True,  WHITE,    TEAL_D),
    ]
    for ci, (val, al, bd, fc, fb) in enumerate(row_data, 1):
        c = ws4.cell(r, ci, val)
        c.fill = hf(fb); c.font = Font(name="Calibri", size=9, bold=bd, color=fc)
        c.alignment = Alignment(horizontal=al, vertical="top", wrap_text=True, indent=1)
        c.border = tb()

gr = 4 + len(FRAMEWORK) + 2
ws4.row_dimensions[gr].height = 26
ms(ws4, f"A{gr}:F{gr}", "STEP-BY-STEP GUIDE — How to Screen Small-Caps on Screener.in",
   AMBER, fsz=11, bold=True, fc=WHITE)

steps = [
    ("Step 1", "screener.in → Custom Screen: Revenue growth 3yr > 18, Profit growth 3yr > 20, ROCE > 20, Debt/Equity < 0.5, Market Cap > 1000 Cr."),
    ("Step 2", "Filter further: Promoter holding > 50%, No pledge or < 5% pledged, EBITDA margin > 15%."),
    ("Step 3", "Check if the company is in a structural sector: defence, EMS, specialty chem, CDMO, bio-energy, new materials, affordable housing."),
    ("Step 4", "Calculate PEG Ratio = PE / 3-yr PAT CAGR. PEG < 1.5 = reasonably priced for growth. PEG > 2 = expensive, wait for correction."),
    ("Step 5", "Verify 5 years of quarterly revenue trend: consistent growth or cyclical recovery? Revenue should not swing >30% between quarters without reason."),
    ("Step 6", "Read at least 2 recent management commentary / earnings call transcripts. Does management have specific targets? Track record of meeting guidance?"),
    ("Step 7", "Check FII + DII ownership trend: Increasing institutional ownership is a positive signal. Sudden large FII exit = flag."),
    ("Step 8", "Position size: Maximum 5–8% of your equity portfolio per small-cap stock. Total small-cap allocation: maximum 30–40% of equity portfolio."),
    ("Step 9", "Set a tracking discipline: Review after every quarterly result. If PAT growth drops below 15% for 2 consecutive quarters — reassess thesis."),
]
for i, (step, desc) in enumerate(steps):
    r = gr + 1 + i
    ws4.row_dimensions[r].height = 32
    bg = CREAM_L if i % 2 == 0 else WHITE
    wc(ws4, r, 1, step, ORANGE, fsz=10, bold=True, fc=WHITE, ha="center")
    wc(ws4, r, 2, desc, bg, fsz=9, bold=False, fc=DARK_TXT, ha="left", wrap=True)
    ws4.merge_cells(f"B{r}:F{r}")

# ─────────────────────────────────────────────────────────────────────────
# SHEET 5 · WATCHLIST SUMMARY
# ─────────────────────────────────────────────────────────────────────────
ws5 = wb.create_sheet("05 · Watchlist Summary")
ws5.sheet_view.showGridLines = False
ms(ws5, "A1:H1",
   "INDIA SMALL-CAP WATCHLIST — 12 RESEARCH CANDIDATES | 16%+ CAGR | JUNE 2026 | RESEARCH ONLY",
   FOREST, fsz=13, bold=True, fc=GOLD)
ws5.row_dimensions[1].height = 34
ms(ws5, "A2:H2",
   "⚠ Small-caps are HIGH RISK. Max 5–8% per stock. Minimum 3-year hold. Not investment advice. Verify on screener.in before investing.",
   ORANGE, fsz=9, bold=True, fc=WHITE)
ws5.row_dimensions[2].height = 22

h5 = ["#","Sector","Company","Ticker (NSE)",
      "Why it fits 16%+ CAGR","Key Risks","Valuation","Risk"]
w5 = [4,  24,       24,       14,
      52,             32,        26,        12]
r = 3
ws5.row_dimensions[r].height = 26
for ci, (h, w) in enumerate(zip(h5, w5), 1):
    c = ws5.cell(r, ci, h)
    c.fill = hf(COBALT); c.font = Font(name="Calibri", size=10, bold=True, color=WHITE)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = tb()
    scw(ws5, ci, w)

val_cm = {"Attractive": GREEN_OK, "Fair": AMBER_MID, "Expensive": RED_HIGH, "Fair/Premium": AMBER_MID}
rsk_cm = {"Low": GREEN_OK, "Low-Med": "5DADE2", "Medium": AMBER_MID, "Med-High": AMBER_MID, "High": RED_HIGH}

cur_sec = None
rn = 4
for i, (sec, co, tick, why, risks, val, risk) in enumerate(WATCHLIST):
    if sec != cur_sec:
        ws5.row_dimensions[rn].height = 20
        ms(ws5, f"A{rn}:H{rn}", f"  ── {sec.upper()} ──",
           COBALT, fsz=9, bold=True, fc=GOLD, ha="left")
        rn += 1; cur_sec = sec
    r = rn; ws5.row_dimensions[r].height = 72
    bg = MINT if i % 2 == 0 else WHITE
    sc = SC_COLOR.get(next((s["id"] for s in SECTORS
                            if any(kw.lower() in s["id"].lower() for kw in sec.split())), ""), COBALT)
    vtag = val.split("(")[0].strip()
    vbg = val_cm.get(vtag, AMBER_MID)
    rbg = rsk_cm.get(risk, AMBER_MID)
    row_d = [
        (i+1,  "center", False, DARK_TXT, bg),
        (sec,  "center", True,  WHITE,    sc),
        (co,   "left",   True,  FOREST,   bg),
        (tick, "center", True,  WHITE,    ORANGE),
        (why,  "left",   False, DARK_TXT, bg),
        (risks,"left",   False, "555555", bg),
        (val,  "left",   True,  WHITE,    vbg),
        (risk, "center", True,  WHITE,    rbg),
    ]
    for ci, (val_d, al, bd, fc, fb) in enumerate(row_d, 1):
        c = ws5.cell(r, ci, val_d)
        c.fill = hf(fb); c.font = Font(name="Calibri", size=9, bold=bd, color=fc)
        c.alignment = Alignment(horizontal=al, vertical="top", wrap_text=True, indent=1)
        c.border = tb()
    rn += 1
ws5.freeze_panes = "A4"

# ─────────────────────────────────────────────────────────────────────────
# SHEET 6 · RISK & GROWTH MATRIX
# ─────────────────────────────────────────────────────────────────────────
ws6 = wb.create_sheet("06 · Risk & Growth Matrix")
ws6.sheet_view.showGridLines = False
ms(ws6, "A1:K1", "RISK & GROWTH MATRIX — All 12 Small-Cap Research Candidates",
   FOREST, fsz=13, bold=True, fc=GOLD)
ws6.row_dimensions[1].height = 34
ms(ws6, "A2:K2",
   "Green = Attractive / Lower Risk  ·  Amber = Fair / Medium Risk  ·  Red = Expensive / Higher Risk",
   COBALT, fsz=9, bold=False, fc=STEEL_L)
ws6.row_dimensions[2].height = 22

h6 = ["#","Company","Ticker","Sector","Mkt Cap","3Y Rev CAGR","3Y PAT CAGR","ROE","ROCE","Valuation","Risk"]
w6 = [4,  24,       12,      22,      12,        14,            14,           10,   10,    26,         12]
r = 3
ws6.row_dimensions[r].height = 26
for ci, (h, w) in enumerate(zip(h6, w6), 1):
    c = ws6.cell(r, ci, h)
    c.fill = hf(COBALT); c.font = Font(name="Calibri", size=10, bold=True, color=WHITE)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = tb()
    scw(ws6, ci, w)

for i, st in enumerate(STOCKS):
    r = 4 + i
    ws6.row_dimensions[r].height = 28
    bg = MINT if i % 2 == 0 else WHITE
    sc = SC_COLOR.get(st["sector"], COBALT)
    vals = [
        (st["no"],       "center", False, DARK_TXT, bg),
        (st["co"],       "left",   True,  FOREST,   bg),
        (st["ticker"],   "center", True,  WHITE,    ORANGE),
        (st["sector"],   "center", False, WHITE,    sc),
        (st["mktcap"],   "center", False, DARK_TXT, bg),
        (st["rev_cagr"], "center", True,  DARK_TXT, bg),
        (st["pat_cagr"], "center", True,  DARK_TXT, bg),
        (st["roe"],      "center", True,  DARK_TXT, bg),
        (st["roce"],     "center", True,  DARK_TXT, bg),
        (st["val_tag"],  "center", True,  WHITE,    st["val_col"]),
        (st["risk"],     "center", True,  WHITE,    st["risk_col"]),
    ]
    for ci, (val, al, bd, fc, fb) in enumerate(vals, 1):
        c = ws6.cell(r, ci, val)
        c.fill = hf(fb); c.font = Font(name="Calibri", size=9, bold=bd, color=fc)
        c.alignment = Alignment(horizontal=al, vertical="center", wrap_text=True, indent=1)
        c.border = tb()

# Legend
lr = 4 + len(STOCKS) + 2
ws6.row_dimensions[lr].height = 24
ms(ws6, f"A{lr}:K{lr}", "KEY NOTES & RISK LEGEND", AMBER, fsz=11, bold=True, fc=WHITE)
legend = [
    (GREEN_OK,  WHITE,    "ATTRACTIVE / LOW-MED RISK",
     "Best risk-reward. Blue Jet (PE 34x vs sector 86x), Praj Industries (PE 26x policy-backed), Aptus Housing Finance (PE 18x, ROE 20%). Strong thesis + reasonable valuation."),
    (AMBER_MID, WHITE,    "FAIR / MEDIUM RISK",
     "Good quality + fair valuation. Syrma SGS (PAT +87%), Navin Fluorine (EBITDA +103%), Vinati Organics (zero debt), Clean Science (ROCE 30%+), Suven Pharma (EBITDA 52%+), Ami Organics."),
    (RED_HIGH,  WHITE,    "EXPENSIVE / HIGHER RISK",
     "Excellent businesses but premium valuations. Data Patterns (PE 73x), MTAR Tech (PE 65x), Kaynes (PE 65x). Buy only in tranches over 3-6 months; never > 5% of portfolio."),
    (FOREST,    GOLD,     "CRITICAL SMALL-CAP RULES",
     "1) Max 5-8% per stock. 2) Min 3-year holding period. 3) Diversify across ≥ 4 sectors. "
     "4) Never chase momentum — buy on thesis, exit on thesis break. 5) Track quarterly earnings."),
    ("3A1000",  "FFB347", "DISCLAIMER",
     "All data as of June 2026. Small-caps can fall 40-60% in bear markets. This is NOT investment advice. "
     "Verify all data on screener.in / tijorifinance.com. Consult a SEBI-registered adviser."),
]
for i, (bg, fc, label, desc) in enumerate(legend):
    r = lr + 1 + i
    ws6.row_dimensions[r].height = 42
    wc(ws6, r, 1, label, bg, fsz=10, bold=True, fc=fc, ha="center")
    ws6.merge_cells(f"A{r}:C{r}")
    wc(ws6, r, 4, desc, MINT if i % 2 == 0 else WHITE,
       fsz=9, bold=False, fc=DARK_TXT, ha="left", wrap=True)
    ws6.merge_cells(f"D{r}:K{r}")

# Chart
cs = lr + len(legend) + 3
ws6.cell(cs, 1, "Stock").font = Font(bold=True)
ws6.cell(cs, 2, "3Y PAT CAGR (%)").font = Font(bold=True)
chart_data = [
    ("DATAPATTNS", 28), ("MTARTECH", 25), ("SYRMA", 35), ("KAYNES", 35),
    ("NAVINFLUOR", 28), ("VINATIORGA", 22), ("CLEAN", 23), ("BLUEJET", 23),
    ("SUVENPHAR", 23), ("PRAJIND", 20), ("AMIORG", 25), ("APTUS", 26),
]
for j, (nm, v) in enumerate(chart_data):
    ws6.cell(cs + 1 + j, 1, nm)
    ws6.cell(cs + 1 + j, 2, v)

chart = BarChart()
chart.type = "col"; chart.style = 10
chart.title = "Estimated 3-Year PAT CAGR — 12 Small-Cap Candidates (%)"
chart.y_axis.title = "PAT CAGR %"; chart.x_axis.title = "Stock (NSE Ticker)"
chart.width = 28; chart.height = 14
dr = Reference(ws6, min_col=2, min_row=cs, max_col=2, max_row=cs + len(chart_data))
ct = Reference(ws6, min_col=1, min_row=cs + 1, max_row=cs + len(chart_data))
chart.add_data(dr, titles_from_data=True)
chart.set_categories(ct)
chart.series[0].graphicalProperties.solidFill = "0A2E1A"
ws6.add_chart(chart, f"A{cs + len(chart_data) + 2}")

# ── Tab colours & print settings ──
tabs = [FOREST, COBALT, TEAL_D, AMBER, ORANGE, PURPLE]
for ws, tc in zip([ws1, ws2, ws3, ws4, ws5, ws6], tabs):
    ws.sheet_properties.tabColor = tc
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.print_title_rows = "1:3"

out = "/home/user/Claude-/India_SmallCap_Watchlist_16pct_CAGR.xlsx"
wb.save(out)
print(f"Saved → {out}")
