"""
Device data for the smartphone comparison workbook.

All prices are Indian rupees, base variant, and were collected on 26 Aug 2026
from public retail/price-tracker listings (see the "Read Me" sheet for the
source list). Street prices move daily -- treat them as an indication of the
band, not a quote.
"""

AS_OF = "26 August 2026"

# Column order for every table in the workbook.
DEVICES = [
    "Galaxy Z Fold 7",
    "Galaxy Z Fold 6",
    "Galaxy Z Fold 5",
    "Galaxy S26 Ultra",
    "Galaxy S25 Ultra",
    "Galaxy S24 Ultra",
    "Galaxy S23 Ultra",
    "iPhone 17",
    "iPhone 16",
    "iPhone 15",
]

# (section, attribute, [value per device in DEVICES order])
SPEC_ROWS = [
    # ---------------------------------------------------------------- identity
    ("Identity", "Brand / family", [
        "Samsung – Galaxy Z (foldable)", "Samsung – Galaxy Z (foldable)", "Samsung – Galaxy Z (foldable)",
        "Samsung – Galaxy S Ultra", "Samsung – Galaxy S Ultra", "Samsung – Galaxy S Ultra", "Samsung – Galaxy S Ultra",
        "Apple – iPhone (base)", "Apple – iPhone (base)", "Apple – iPhone (base)"]),
    ("Identity", "Generation age (from launch)", [
        "1 year", "2 years", "3 years",
        "6 months", "1.5 years", "2.5 years", "3.5 years",
        "11 months", "2 years", "3 years"]),
    ("Identity", "India launch date", [
        "25 Jul 2025", "24 Jul 2024", "11 Aug 2023",
        "25 Feb 2026", "6 Feb 2025", "31 Jan 2024", "17 Feb 2023",
        "19 Sep 2025", "20 Sep 2024", "22 Sep 2023"]),
    ("Identity", "Sales status (Aug 2026)", [
        "Outgoing – Fold 8 launched 22 Jul 2026", "Clearance / limited stock", "End of life – thin stock, mostly grey/refurb",
        "Current flagship", "Widely stocked, heavily discounted", "Clearance / limited stock", "End of life – thin stock",
        "Current – iPhone 18 Pro expected ~9 Sep 2026", "Still officially sold, price cut", "Discontinued by Apple India – channel stock only"]),
    ("Identity", "Form factor", [
        "Book-style foldable", "Book-style foldable", "Book-style foldable",
        "Slab, flat screen", "Slab, flat screen", "Slab, flat screen", "Slab, curved screen",
        "Slab", "Slab", "Slab"]),

    # ----------------------------------------------------------------- pricing
    ("Pricing (India)", "Base variant priced here", [
        "12 GB / 256 GB", "12 GB / 256 GB", "12 GB / 256 GB",
        "12 GB / 256 GB", "12 GB / 256 GB", "12 GB / 256 GB", "8 GB / 256 GB",
        "256 GB", "128 GB", "128 GB"]),
    ("Pricing (India)", "Launch MRP (base)", "LINK:C"),
    ("Pricing (India)", "Best street price today", "LINK:D"),
    ("Pricing (India)", "Effective price after bank offer", "LINK:F"),
    ("Pricing (India)", "Fall from launch MRP", "LINK:G"),

    # ----------------------------------------------------------------- display
    ("Display", "Main screen size", [
        '8.0"', '7.6"', '7.6"',
        '6.9"', '6.9"', '6.8"', '6.8"',
        '6.3"', '6.1"', '6.1"']),
    ("Display", "Main screen resolution", [
        "2184 x 1968 QXGA+", "2160 x 1856 QXGA+", "2176 x 1812 QXGA+",
        "3120 x 1440 QHD+", "3120 x 1440 QHD+", "3120 x 1440 QHD+", "3088 x 1440 QHD+",
        "2622 x 1206", "2556 x 1179", "2556 x 1179"]),
    ("Display", "Panel type", [
        "Dynamic AMOLED 2X (foldable)", "Dynamic AMOLED 2X (foldable)", "Dynamic AMOLED 2X (foldable)",
        "Dynamic AMOLED 2X", "Dynamic AMOLED 2X", "Dynamic AMOLED 2X", "Dynamic AMOLED 2X",
        "Super Retina XDR OLED", "Super Retina XDR OLED", "Super Retina XDR OLED"]),
    ("Display", "Refresh rate", [
        "1–120 Hz adaptive", "1–120 Hz adaptive", "1–120 Hz adaptive",
        "1–120 Hz adaptive", "1–120 Hz adaptive", "1–120 Hz adaptive", "1–120 Hz adaptive",
        "1–120 Hz ProMotion", "60 Hz only", "60 Hz only"]),
    ("Display", "Peak brightness (claimed)", [
        "2,600 nits", "2,600 nits", "1,750 nits",
        "2,600 nits", "2,600 nits", "2,600 nits", "1,750 nits",
        "3,000 nits", "2,000 nits", "2,000 nits"]),
    ("Display", "Always-on display", [
        "Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes",
        "Yes", "No", "No"]),
    ("Display", "Cover / secondary screen", [
        '6.5" FHD+ 120 Hz (usable width)', '6.3" 120 Hz (narrow)', '6.2" 120 Hz (very narrow)',
        "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]),
    ("Display", "Front glass / protection", [
        "Gorilla Glass Ceramic 2 (cover)", "Gorilla Glass Victus 2 (cover)", "Gorilla Glass Victus 2 (cover)",
        "Gorilla Armor 3 (anti-reflective)", "Gorilla Armor 2 (anti-reflective)", "Gorilla Armor (anti-reflective)", "Gorilla Glass Victus 2",
        "Ceramic Shield 2", "Ceramic Shield", "Ceramic Shield"]),

    # ------------------------------------------------------------- performance
    ("Performance", "Chipset", [
        "Snapdragon 8 Elite for Galaxy", "Snapdragon 8 Gen 3 for Galaxy", "Snapdragon 8 Gen 2 for Galaxy",
        "Snapdragon 8 Elite Gen 5 for Galaxy", "Snapdragon 8 Elite for Galaxy", "Snapdragon 8 Gen 3 for Galaxy", "Snapdragon 8 Gen 2 for Galaxy",
        "Apple A19", "Apple A18", "Apple A16 Bionic"]),
    ("Performance", "Fabrication node", [
        "3 nm", "4 nm", "4 nm",
        "3 nm", "3 nm", "4 nm", "4 nm",
        "3 nm", "3 nm", "4 nm"]),
    ("Performance", "Peak clock", [
        "4.47 GHz", "3.39 GHz", "3.36 GHz",
        "4.74 GHz", "4.47 GHz", "3.39 GHz", "3.36 GHz",
        "~4.3 GHz", "~4.0 GHz", "~3.5 GHz"]),
    ("Performance", "Geekbench 6 multi-core (indicative)", [
        "~9,700", "~7,200", "~5,100",
        "~11,400", "~10,100", "~7,200", "~5,000",
        "~8,500", "~8,200", "~6,600"]),
    ("Performance", "RAM options", [
        "12 GB / 16 GB", "12 GB", "12 GB",
        "12 GB / 16 GB", "12 GB", "12 GB", "8 GB / 12 GB",
        "8 GB", "8 GB", "6 GB"]),
    ("Performance", "Storage options", [
        "256 GB / 512 GB / 1 TB", "256 GB / 512 GB / 1 TB", "256 GB / 512 GB / 1 TB",
        "256 GB / 512 GB / 1 TB", "256 GB / 512 GB / 1 TB", "256 GB / 512 GB / 1 TB", "256 GB / 512 GB / 1 TB",
        "256 GB / 512 GB", "128 / 256 / 512 GB", "128 / 256 / 512 GB"]),
    ("Performance", "Sustained-load cooling", [
        "Vapour chamber (enlarged)", "Vapour chamber", "Vapour chamber",
        "Vapour chamber (largest in series)", "Vapour chamber", "Vapour chamber", "Vapour chamber",
        "Vapour chamber (new for iPhone 17)", "Graphite only", "Graphite only"]),

    # ------------------------------------------------------------------ camera
    ("Camera", "Main camera", [
        "200 MP f/1.7 OIS", "50 MP f/1.8 OIS", "50 MP f/1.8 OIS",
        "200 MP f/1.4 OIS", "200 MP f/1.7 OIS", "200 MP f/1.7 OIS", "200 MP f/1.7 OIS",
        "48 MP f/1.6 Fusion", "48 MP f/1.6 Fusion", "48 MP f/1.6"]),
    ("Camera", "Ultra-wide", [
        "12 MP f/2.2", "12 MP f/2.2", "12 MP f/2.2",
        "50 MP f/1.9 with autofocus", "50 MP f/1.9 with autofocus", "12 MP f/2.2", "12 MP f/2.2",
        "48 MP f/2.2 with macro", "12 MP f/2.2 with macro", "12 MP f/2.4"]),
    ("Camera", "Telephoto 1", [
        "10 MP 3x f/2.4", "10 MP 3x f/2.4", "10 MP 3x f/2.4",
        "10 MP 3x f/2.4", "10 MP 3x f/2.4", "10 MP 3x f/2.4", "10 MP 3x f/2.4",
        "None (2x sensor crop)", "None (2x sensor crop)", "None (2x sensor crop)"]),
    ("Camera", "Telephoto 2 (periscope)", [
        "None", "None", "None",
        "50 MP 5x f/2.8 periscope", "50 MP 5x f/3.4 periscope", "50 MP 5x f/3.4 periscope", "10 MP 10x f/4.9 periscope",
        "None", "None", "None"]),
    ("Camera", "Best optical zoom", [
        "3x", "3x", "3x",
        "5x (100x Space Zoom digital)", "5x (100x digital)", "5x (100x digital)", "10x (100x digital)",
        "2x (crop)", "2x (crop)", "2x (crop)"]),
    ("Camera", "Selfie camera", [
        "10 MP cover + 10 MP inner", "10 MP cover + 4 MP under-display", "10 MP cover + 4 MP under-display",
        "12 MP autofocus", "12 MP autofocus", "12 MP autofocus", "12 MP autofocus",
        "18 MP Center Stage (square sensor)", "12 MP TrueDepth", "12 MP TrueDepth"]),
    ("Camera", "Max video", [
        "8K30 / 4K120", "8K30 / 4K60", "8K30 / 4K60",
        "8K30 / 4K120 (10-bit HDR, LOG)", "8K30 / 4K120 (LOG)", "8K30 / 4K120", "8K30 / 4K60",
        "4K60 Dolby Vision, dual capture", "4K60 Dolby Vision", "4K60 Dolby Vision"]),
    ("Camera", "Camera stand-out", [
        "Best-in-class foldable camera – Ultra-grade 200 MP in a fold", "Competent, not flagship-grade", "Ageing 50 MP set-up",
        "f/1.4 main lets in ~47% more light than S24 Ultra – best low-light in this list", "Most complete zoom stack for the money", "Excellent 5x periscope, proven ProVisual engine", "Only phone here with 10x true optical",
        "Cleanest point-and-shoot video; new 18 MP selfie is a genuine upgrade", "Reliable 48 MP main, weak ultra-wide", "Good main sensor, dated processing"]),

    # ------------------------------------------------------- battery, charging
    ("Battery & charging", "Battery capacity", [
        "4,400 mAh", "4,400 mAh", "4,400 mAh",
        "5,000 mAh", "5,000 mAh", "5,000 mAh", "5,000 mAh",
        "~3,692 mAh", "~3,561 mAh", "~3,349 mAh"]),
    ("Battery & charging", "Wired charging", [
        "25 W", "25 W", "25 W",
        "60 W", "45 W", "45 W", "45 W",
        "Up to 40 W (50% in ~20 min)", "Up to 30 W", "Up to 27 W"]),
    ("Battery & charging", "Wireless charging", [
        "15 W", "15 W", "10 W",
        "25 W", "15 W", "15 W", "15 W",
        "25 W MagSafe / Qi2", "25 W MagSafe", "15 W MagSafe"]),
    ("Battery & charging", "Reverse wireless", [
        "Yes 4.5 W", "Yes 4.5 W", "Yes 4.5 W",
        "Yes 4.5 W", "Yes 4.5 W", "Yes 4.5 W", "Yes 4.5 W",
        "Yes (wired, via USB-C)", "Yes (wired, via USB-C)", "Yes (wired, via USB-C)"]),
    ("Battery & charging", "Realistic screen-on time", [
        "5–6 hrs", "5–6 hrs", "4.5–5.5 hrs",
        "8–9 hrs", "7.5–8.5 hrs", "7.5–8 hrs", "7–8 hrs",
        "7–8 hrs", "6.5–7 hrs", "5.5–6.5 hrs"]),
    ("Battery & charging", "Charger in box", [
        "No", "No", "No", "No", "No", "No", "No",
        "No", "No", "No"]),

    # ---------------------------------------------------------------- software
    ("Software & support", "OS shipping today", [
        "One UI 8 / Android 16", "One UI 8 / Android 16", "One UI 8 / Android 16",
        "One UI 8.5 / Android 16", "One UI 8.5 / Android 16", "One UI 8 / Android 16", "One UI 8 / Android 16",
        "iOS 26", "iOS 26", "iOS 26"]),
    ("Software & support", "OS upgrades promised", [
        "7 major (through Android 22)", "7 major (through Android 21)", "4 major (through Android 17)",
        "7 major (through Android 23)", "7 major (through Android 22)", "7 major (through Android 21)", "4 major (through Android 17)",
        "~6–7 years (Apple norm)", "~6–7 years (Apple norm)", "~6–7 years (Apple norm)"]),
    ("Software & support", "Security updates until", [
        "Jul 2032", "Jul 2031", "Aug 2028",
        "Feb 2033", "Feb 2032", "Jan 2031", "Feb 2028",
        "~2031–32", "~2030–31", "~2029–30"]),
    ("Software & support", "Support runway left from today", [
        "~6 years", "~5 years", "~2 years",
        "~6.5 years", "~5.5 years", "~4.5 years", "~1.5 years",
        "~5.5 years", "~4.5 years", "~3.5 years"]),
    ("Software & support", "On-device AI", [
        "Galaxy AI + Gemini, 7-yr free tier", "Galaxy AI + Gemini", "Galaxy AI (retro-fitted, reduced set)",
        "Galaxy AI (full), multimodal Bixby/Gemini", "Galaxy AI (full)", "Galaxy AI (full)", "Galaxy AI (reduced set)",
        "Apple Intelligence", "Apple Intelligence", "NOT supported (A16 / 6 GB RAM)"]),
    ("Software & support", "Desktop mode", [
        "Samsung DeX (wired + wireless)", "Samsung DeX", "Samsung DeX",
        "Samsung DeX", "Samsung DeX", "Samsung DeX", "Samsung DeX",
        "No (Stage Manager on iPad only)", "No", "No"]),

    # ------------------------------------------------------ design & handling
    ("Design & build", "Dimensions", [
        "158.4 x 143.2 x 4.2 mm open / 8.9 mm folded", "153.5 x 132.6 x 5.6 mm open / 12.1 mm folded", "154.9 x 129.9 x 6.1 mm open / 13.4 mm folded",
        "149.6 x 71.7 x 7.2 mm", "162.8 x 77.6 x 8.2 mm", "162.3 x 79.0 x 8.6 mm", "163.4 x 78.1 x 8.9 mm",
        "149.6 x 71.5 x 7.95 mm", "147.6 x 71.6 x 7.80 mm", "147.6 x 71.6 x 7.80 mm"]),
    ("Design & build", "Weight", [
        "215 g", "239 g", "253 g",
        "214 g", "218 g", "232 g", "234 g",
        "177 g", "170 g", "171 g"]),
    ("Design & build", "Frame / back", [
        "Armor Aluminium / Gorilla Ceramic 2", "Armor Aluminium / Victus 2", "Armor Aluminium / Victus 2",
        "Titanium / Gorilla Armor 3", "Titanium / Gorilla Armor 2", "Titanium / Gorilla Armor", "Armor Aluminium / Victus 2",
        "Aluminium / Ceramic Shield back", "Aluminium / glass", "Aluminium / frosted glass"]),
    ("Design & build", "Water & dust rating", [
        "IP48 (no dust-tight rating)", "IP48", "IPX8 (no dust rating at all)",
        "IP68", "IP68", "IP68", "IP68",
        "IP68", "IP68", "IP68"]),
    ("Design & build", "Stylus", [
        "NOT supported – S Pen dropped on Fold 7", "S Pen Fold Edition (sold separately, no silo)", "S Pen Fold Edition (sold separately, no silo)",
        "Built-in S Pen in silo (no Bluetooth/Air Actions)", "Built-in S Pen in silo (no Bluetooth)", "Built-in S Pen with Bluetooth + Air Actions", "Built-in S Pen with Bluetooth + Air Actions",
        "No", "No", "No"]),
    ("Design & build", "One-handed usability", [
        "Good closed, two-handed open", "Poor – narrow cover screen", "Poor – narrow cover screen",
        "Fair – large but thin", "Fair", "Fair", "Fair",
        "Excellent", "Excellent", "Excellent"]),

    # ------------------------------------------------------------ connectivity
    ("Connectivity", "SIM (India units)", [
        "Nano-SIM + eSIM", "Nano-SIM + eSIM", "Nano-SIM + eSIM",
        "Nano-SIM + eSIM", "Nano-SIM + eSIM", "Nano-SIM + eSIM", "Dual nano-SIM",
        "Nano-SIM + eSIM", "Nano-SIM + eSIM", "Nano-SIM + eSIM"]),
    ("Connectivity", "Wi-Fi / Bluetooth", [
        "Wi-Fi 7 / BT 5.4", "Wi-Fi 7 / BT 5.3", "Wi-Fi 6E / BT 5.3",
        "Wi-Fi 7 / BT 5.4", "Wi-Fi 7 / BT 5.4", "Wi-Fi 7 / BT 5.3", "Wi-Fi 6E / BT 5.3",
        "Wi-Fi 7 / BT 6", "Wi-Fi 7 / BT 5.3", "Wi-Fi 6 / BT 5.3"]),
    ("Connectivity", "USB port", [
        "USB-C 3.2 (fast data)", "USB-C 3.2", "USB-C 3.2",
        "USB-C 3.2", "USB-C 3.2", "USB-C 3.2", "USB-C 3.2",
        "USB-C 2.0 (slow data)", "USB-C 2.0 (slow data)", "USB-C 2.0 (slow data)"]),
    ("Connectivity", "UWB / satellite SOS", [
        "UWB yes / no satellite in India", "UWB yes / no", "UWB yes / no",
        "UWB yes / no satellite in India", "UWB yes / no", "UWB yes / no", "UWB yes / no",
        "UWB yes / satellite features not enabled in India", "UWB yes / not in India", "UWB yes / not in India"]),

    # ----------------------------------------------------------- India context
    ("India ownership", "Warranty", [
        "1 yr (Samsung India)", "1 yr", "1 yr",
        "1 yr (Samsung India)", "1 yr", "1 yr", "1 yr",
        "1 yr (Apple India)", "1 yr", "1 yr"]),
    ("India ownership", "Typical out-of-warranty screen repair", [
        "Very high – inner folding panel", "Very high", "Very high",
        "High", "High", "High", "High",
        "Moderate", "Moderate", "Moderate"]),
    ("India ownership", "Resale value after 2 years (rule of thumb)", [
        "~40–45% of MRP", "~35–40%", "~30%",
        "~50%", "~45%", "~40%", "~35%",
        "~60–65%", "~55%", "~50%"]),
    ("India ownership", "Service network reach", [
        "Very wide (Samsung; fold repairs at select centres only)", "Very wide (fold repairs at select centres)", "Very wide (fold repairs at select centres)",
        "Very wide", "Very wide", "Very wide", "Very wide",
        "Narrower – Apple centres in metros, authorised partners elsewhere", "Same as above", "Same as above"]),
]

# Launch MRP, best street price seen on 26 Aug 2026, store, typical bank offer.
PRICING = {
    #  device            : (base variant, launch MRP, best price, store, bank offer, note)
    "Galaxy Z Fold 7":   ("12/256 GB", 174999, 161855, "Croma / Samsung.com",  7000,
                          "Cut ~Rs 13,000 after the Fold 8 launched on 22 Jul 2026; HDFC card knocks off another Rs 7,000."),
    "Galaxy Z Fold 6":   ("12/256 GB", 164999, 109999, "Amazon",               5000,
                          "Clearance pricing; stock is thinning. Verify it is a fresh, sealed India unit before paying."),
    "Galaxy Z Fold 5":   ("12/256 GB", 154999, 108990, "Flipkart / Croma",     4000,
                          "Barely cheaper than a Fold 6 that is a full generation newer -- weak buy at this price."),
    "Galaxy S26 Ultra":  ("12/256 GB", 139999, 124999, "Flipkart",             5000,
                          "Rs 15,000 below February launch MRP after six months. Expect deeper cuts in the festive sale."),
    "Galaxy S25 Ultra":  ("12/256 GB", 129999,  92990, "Amazon",               5000,
                          "Record-low territory; has traded as low as ~Rs 88,500. The value pick of the Ultra line."),
    "Galaxy S24 Ultra":  ("12/256 GB", 129999,  78999, "Flipkart",             4000,
                          "Effective ~Rs 75,000 with bank offer. Still a titanium Ultra with a 5x periscope."),
    "Galaxy S23 Ultra":  ("8/256 GB",  124999,  74999, "Amazon / Flipkart",    4000,
                          "Priced against the S24 Ultra but a year older with ~1.5 yrs of updates left. Refurb ~Rs 53,000."),
    "iPhone 17":         ("256 GB",     82900,  81900, "Flipkart",             4000,
                          "Has touched Rs 75,900. Apple's next event is ~9 Sep 2026 -- prices historically move then."),
    "iPhone 16":         ("128 GB",     79900,  65900, "Flipkart",             4000,
                          "Official MRP cut after the iPhone 17 launch; has traded near Rs 62,900."),
    "iPhone 15":         ("128 GB",     79900,  51999, "Flipkart / Amazon",    3000,
                          "Discontinued by Apple India -- channel stock only. No Apple Intelligence, ever."),
}

# Judgement ratings, 1-10. These are opinions, not measurements -- documented on
# the Scorecard sheet so a reader can overwrite any of them.
RATING_CATEGORIES = [
    ("Performance", 0.15),
    ("Display", 0.15),
    ("Camera", 0.20),
    ("Battery & charging", 0.15),
    ("Software support life", 0.10),
    ("Design & portability", 0.10),
    ("Features & ecosystem", 0.15),
]

RATINGS = {
    #                     Perf  Disp  Cam   Batt  SW    Des   Feat
    "Galaxy Z Fold 7":  [ 9.0, 10.0,  8.0,  6.0,  9.0,  8.0, 10.0],
    "Galaxy Z Fold 6":  [ 8.0,  9.0,  7.0,  6.0,  8.0,  6.0,  9.0],
    "Galaxy Z Fold 5":  [ 7.0,  8.0,  6.5,  5.5,  6.0,  5.0,  8.0],
    "Galaxy S26 Ultra": [10.0, 10.0, 10.0,  9.0, 10.0,  8.0,  9.0],
    "Galaxy S25 Ultra": [ 9.0,  9.5,  9.5,  8.0,  9.0,  8.0,  9.0],
    "Galaxy S24 Ultra": [ 8.0,  9.0,  9.0,  8.0,  8.0,  7.5,  9.0],
    "Galaxy S23 Ultra": [ 7.0,  8.0,  8.5,  8.0,  6.0,  7.0,  8.5],
    "iPhone 17":        [ 9.5,  9.0,  8.5,  8.0,  9.0,  9.0,  8.0],
    "iPhone 16":        [ 8.5,  7.0,  7.5,  7.5,  8.5,  9.0,  7.5],
    "iPhone 15":        [ 7.0,  6.5,  7.0,  6.5,  6.5,  9.0,  6.5],
}

# (device, three best features, the one thing only this phone does, two drawbacks, who it suits)
FEATURES = {
    "Galaxy Z Fold 7": (
        ["8.0-inch tablet screen that folds into a normal-width 6.5-inch phone",
         "200 MP Ultra-grade main camera -- the first fold that does not compromise the camera",
         "4.2 mm unfolded / 215 g -- lighter than most slab flagships"],
        "The only foldable here with a genuinely usable cover screen AND a flagship 200 MP sensor.",
        ["4,400 mAh with only 25 W charging -- weakest battery story in this workbook",
         "S Pen support was removed; IP48 means no dust-tight rating"],
        "Someone who reads, edits documents and runs two apps side by side on the move.",
    ),
    "Galaxy Z Fold 6": (
        ["Same 7-year update promise as the newest phones, at clearance price",
         "S Pen Fold Edition support for handwritten mark-up",
         "IP48 and a Snapdragon 8 Gen 3 that is still comfortably fast"],
        "Cheapest way into a modern, still-supported book foldable with stylus support.",
        ["Narrow 6.3-inch cover screen is awkward for typing",
         "Only a 50 MP main camera and a 4 MP under-display selfie"],
        "A foldable-curious buyer who will not pay Fold 7 money.",
    ),
    "Galaxy Z Fold 5": (
        ["Lowest entry price into a Galaxy Fold",
         "S Pen supported",
         "Snapdragon 8 Gen 2 still handles everything mainstream"],
        "Nothing unique remains -- it is superseded on every axis by the Fold 6.",
        ["Security updates end Aug 2028; only Android 17 to come",
         "IPX8 with no dust rating, 253 g, 13.4 mm folded -- the thickest and heaviest here"],
        "Nobody at the current asking price. Only worth it below roughly Rs 85,000.",
    ),
    "Galaxy S26 Ultra": (
        ["f/1.4 main camera -- about 47% more light than the S24 Ultra, best low-light in this list",
         "60 W wired and 25 W wireless charging on a 5,000 mAh cell",
         "Privacy Display that narrows the viewing angle at pixel level"],
        "The pixel-level Privacy Display -- genuinely useful for reading confidential material in public.",
        ["Costs roughly Rs 32,000 more than an S25 Ultra that does 90% of the same job",
         "Still only a 10 MP 3x tele; the mid-zoom range is unchanged since 2022"],
        "Someone who wants the best Android phone available and keeps a phone 4+ years.",
    ),
    "Galaxy S25 Ultra": (
        ["Full zoom stack -- 200 MP main, 50 MP ultra-wide with autofocus, 3x and 5x optical",
         "Titanium frame, anti-reflective Gorilla Armor 2 glass, built-in S Pen",
         "Updates to Feb 2032 -- 5.5 years of runway left"],
        "Best price-to-capability ratio in the entire workbook at roughly Rs 93,000.",
        ["45 W charging feels slow next to the S26 Ultra's 60 W",
         "S Pen lost Bluetooth Air Actions from the S24 Ultra"],
        "Almost everyone shopping for a premium Android phone right now.",
    ),
    "Galaxy S24 Ultra": (
        ["50 MP 5x periscope and 200 MP main -- the same camera hardware philosophy as today's Ultras",
         "First titanium, flat-screen, anti-reflective Ultra",
         "Updates run to Jan 2031"],
        "Cheapest phone here with a true 5x periscope plus a Bluetooth S Pen with Air Actions.",
        ["Snapdragon 8 Gen 3 is two generations behind; runs warmer under sustained load",
         "232 g and 12 GB RAM ceiling"],
        "A value-first buyer who wants Ultra features around Rs 75,000.",
    ),
    "Galaxy S23 Ultra": (
        ["The only phone in this comparison with a true 10x optical periscope",
         "Bluetooth S Pen with Air Actions",
         "5,000 mAh with 45 W charging"],
        "10x optical zoom -- Samsung has not shipped it since, so this is the last of its kind.",
        ["Security updates end Feb 2028 -- under 18 months of runway",
         "At roughly Rs 75,000 it is priced against a newer, better S24 Ultra"],
        "A zoom specialist who understands the short support window. Otherwise skip.",
    ),
    "iPhone 17": (
        ["120 Hz ProMotion with always-on -- the first non-Pro iPhone to get it",
         "256 GB base storage at the old 128 GB price",
         "18 MP Center Stage front camera that auto-frames and shoots landscape while held upright"],
        "The Center Stage square front sensor -- no other phone here reframes a selfie without rotating.",
        ["No telephoto lens at all; 2x is a sensor crop",
         "USB-C is still capped at USB 2.0 transfer speeds"],
        "Anyone in the Apple ecosystem buying to keep for five or more years.",
    ),
    "iPhone 16": (
        ["A18 with Apple Intelligence, the cheapest AI-capable iPhone here",
         "Camera Control button and Action button",
         "170 g -- the lightest phone in the comparison"],
        "Cheapest new iPhone that will run Apple Intelligence for its whole life.",
        ["60 Hz screen in 2026 at roughly Rs 66,000",
         "12 MP ultra-wide and no telephoto"],
        "A budget-conscious iPhone buyer who can live without a high refresh rate.",
    ),
    "iPhone 15": (
        ["Dynamic Island and a 48 MP main camera under Rs 52,000",
         "USB-C, so it shares chargers with everything else",
         "Best resale value per rupee spent in this workbook"],
        "The cheapest way into a current-generation iOS experience -- but with a hard ceiling.",
        ["Will never run Apple Intelligence -- A16 and 6 GB RAM are below the bar",
         "60 Hz, discontinued by Apple India, shortest support runway of the three iPhones"],
        "A first-time iPhone buyer on a strict budget who does not care about AI features.",
    ),
}
