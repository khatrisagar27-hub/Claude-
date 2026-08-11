# Learning Plan — System & Control Improvements

**Client:** MFP Products Pvt Ltd — sauces, condiments, dips & pickles · single unit, Makarpura GIDC · FY turnover ₹30 crore
**Engagement:** Full-scope system and control improvement, all processes
**Prepared for:** CA Sagar Khatri & Associates
**Companion workbooks:** `MFP_Diagnostic_Toolkit.xlsx` (margin & EBITDA diagnostic) · `MFP_Control_Testing_WorkingPapers.xlsx` (control testing WPs)

---

## 0. Read this first — what the two workbooks are, and are not

**The workbooks contain sample data, not client data.** Every rupee figure, every RED/AMBER rating, every entry in the RACM and the Deficiency Register is illustrative — put there to prove the formulas link correctly and to show management what the output will look like. The toolkit's own README says so: *"Sample data = 10 illustrative batches / 1 month of transactions, NOT a full month's volume."*

That matters more than it might sound, and it shapes this entire plan:

- **What you have built is architecture.** The variance logic, the annualisation basis, the attribute-testing method, the deficiency-to-improvement-plan flow — that is real work and it is sound. It is the skeleton.
- **What you have not built is a baseline.** MFP's actual yield, actual price realisation, actual incentive gap, actual control ratings — none of it is known yet. The `Data_Request` sheet confirms this: 12 of 16 items are still Pending, including BMRs, issue slips, wastage logs, customer contracts, export documents, GRN register, weighbridge log, utility bills and payroll.
- **The illustrative findings are hypotheses, not facts.** "No BOM master exists", "RoDTEP not claimed on 4 of 5 shipping bills", "PET jar shrinkage on test count" — these are the failures a food manufacturer of this size *typically* has. They are intelligent priors and a good scoping device. They are not evidence, and none of them can go into a report until tested.

So this plan has two jobs, not one:

1. **Build the capability** to test, quantify and fix every process at MFP — the syllabus in Section 2.
2. **Convert the architecture into a real baseline** — replace illustrative cells with client data, and confirm or reject each hypothesis with evidence. Section 5 lists what needs confirming.

There is a third job implied by the scope. The two workbooks cover six cycles — P2P, Stores, Production, OTC, Exports, Costing/MIS. That is roughly a quarter of the process universe of a food manufacturer. NPD and recipe control, QA/QC and food safety, planning, maintenance, utilities, logistics, channel schemes, recall and traceability, job work, HR, IT and user access, treasury, capex, statutory calendar, EPR — these are absent from the papers entirely. An engagement scoped as "everything" that delivers on six cycles will be judged on the eighteen it did not reach.

Every module below terminates in a deliverable that plugs into the existing workbooks: a new RACM row, a new test-of-controls tab, a new diagnostic sheet. You are not studying to know things; you are studying to be able to test, quantify and fix things at this client.

**Effort envelope:** ~185 hours over 26 weeks (~7 hrs/week). Modules 1, 2, 3 and 11 are front-loaded because the rest depends on them.

**On statutory content:** every regulatory item below is marked with what to read and, where a rate or threshold matters, a **[VERIFY]** flag. The RoDTEP 1.4% and DBK 1.9% sitting in `Export_Incentives` are placeholders like everything else in the sample — they must be confirmed against the current schedule for the actual HS codes on MFP's shipping bills before a rupee of incentive gap goes into a report.

---

## 1. The complete process universe at MFP — and honest coverage today

Twenty-seven processes. This is the "no process left out" list; everything downstream in this plan hangs off it.

### Legend
`TEMPLATE` — a working paper exists in the correct format, populated with sample data; the structure is ready, the client testing is not done · `DIAG` — named in the audit programme but no working paper built · `GAP` — neither

| # | Domain | Process | Status today | Where it sits / must sit |
|---|---|---|---|---|
| 1 | Source | Vendor selection, approval & vendor master | TEMPLATE (partial) | `TOC_P2P` — programme row 2 written, no attributes drafted |
| 2 | Source | Purchasing, PO, rate benchmarking, 3-way match | TEMPLATE | `TOC_P2P`, `Procurement` |
| 3 | Source | Inward QC, rejection, short receipt, debit notes | TEMPLATE (partial) | `TOC_P2P` A4 only |
| 4 | Source | Job work / co-packing (inward and outward) | **GAP** | New — `TOC_JobWork` |
| 5 | Source | Import purchase, customs, BoE reconciliation | **GAP** | New — fold into `TOC_P2P` or Exports |
| 6 | Make | NPD, formulation, recipe & spec change control | **GAP** | New — `TOC_NPD` |
| 7 | Make | Production planning, S&OP, MRP, batch scheduling | **GAP** | New — `TOC_Planning` |
| 8 | Make | Batch manufacture, BMR, BOM issue, yield | TEMPLATE | `TOC_Production`, `Production_Log`, `RM_Variance` |
| 9 | Make | Filling, fill-weight/giveaway control, changeover | **GAP** | New — `Fill_Giveaway` diagnostic + attribute in `TOC_Production` |
| 10 | Make | Wastage, rework, rejection, write-off approval | TEMPLATE | `TOC_Production`, `Wastage` |
| 11 | Make | QA/QC, lab, CCP monitoring, release & retention | **GAP** | New — `TOC_QAQC` |
| 12 | Make | Maintenance, engineering, spares, AMC, calibration | **GAP** | New — `TOC_Maintenance` |
| 13 | Make | Utilities & energy — boiler/fuel, power, water, ETP | DIAG | Programme row 17; new `TOC_Utilities` + `Energy_Diagnostic` |
| 14 | Store | Stores issue discipline, FEFO, expiry, bin accuracy | TEMPLATE | `TOC_Stores`, `Stock_Verification` |
| 15 | Store | FG warehouse, despatch, 3PL, transit damage, freight | **GAP** | New — `TOC_Logistics` + `Freight_Diagnostic` |
| 16 | Store | Traceability, mock recall, complaint handling | **GAP** | New — `TOC_Traceability` |
| 17 | Sell | Order to cash — pricing, credit, dispatch-to-invoice | TEMPLATE | `TOC_OTC`, `Price_Realisation` |
| 18 | Sell | Channel schemes, distributor claims, secondary sales | **GAP** (only CNs in scope) | New — `TOC_Schemes` + `Claims_Register` |
| 19 | Sell | Exports, incentives, forex realisation, destination compliance | TEMPLATE | `TOC_Exports`, `Export_Incentives` |
| 20 | Sell | Returns, expiry from market, saleable/non-saleable | **GAP** | New — fold into `TOC_Traceability` |
| 21 | Enable | Costing, standard cost maintenance, MIS | TEMPLATE | `TOC_Costing_MIS`, `Monthly_MIS` |
| 22 | Enable | HR, payroll, contract labour, overtime, statutory dues | DIAG | Programme row 18; new `TOC_Payroll` |
| 23 | Enable | IT / Tally governance, user access, SoD, backup, cyber | **GAP** | New — `TOC_ITGC` |
| 24 | Enable | Treasury, banking, borrowing, forex exposure, insurance | **GAP** | New — `TOC_Treasury` |
| 25 | Enable | Fixed assets & capex governance | DIAG | Programme row 19; new `TOC_FixedAssets` |
| 26 | Enable | Statutory compliance calendar — GST, TDS, IT, ROC, labour, GPCB, factory, boiler, legal metrology, EPR | **GAP** | New — `Compliance_Calendar` + `TOC_Compliance` |
| 27 | Govern | Delegation of authority, related-party, entity-level controls | **GAP** | New — `TOC_ELC` + DoA matrix |

**Score: 6 of 27 processes have a working-paper structure. 3 more are named in the programme without one. 18 are untouched. And of the 6, zero carry a client-tested conclusion yet.** That is the honest starting position, and both numbers — coverage and evidence — are what this plan is built to move.

---

## 2. Learning modules

Each module states: what you must be able to *do*, why it matters at MFP specifically, the syllabus, the sources, the deliverable that proves it, and hours.

---

### Module 1 — Product & process technology: sauces, condiments, pickles
**Hours: 16 · Weeks 1–3 · Gates: M4, M6, M11**

**Capability target:** Walk the plant and independently name, at each unit operation, what physically can be lost, what can be substituted, and what can be over-consumed — without the production head telling you.

You cannot audit a yield you do not understand. The whole BOM-and-yield workstream will be signed off by a production head who knows the process far better than you do. If the standard yields you propose are naive, the BOM you build will be argued down within a month and genuine usage variance will be reclassified as "normal process loss". The sample toolkit currently carries 95% yield for ketchup, 97% mayonnaise, 93% hot sauce and 98% pickle — **those are placeholder numbers and you must be able to derive, defend or replace every one of them from first principles.**

**Syllabus**

1. **Unit operations, per product family MFP runs**
   - Ketchup/sauce line: paste reconstitution and dilution, hot-break vs cold-break paste behaviour, batching and dosing, steam-jacketed kettle cooking, starch hydration, deaeration, homogenisation, pasteurisation (HTST/tubular), hot fill, cap, invert, cooling tunnel.
   - Mayonnaise/dips: cold-process emulsification, oil dosing rate and shear, emulsion stability and break. Mayonnaise is oil-cost-dominated — a small oil rate movement flows almost 1:1 to margin, so the oil buying calendar is a bigger lever here than anywhere else in the plant.
   - Hot sauce / Chinese sauces: acidification, chilli paste variability, pH control.
   - Pickles: brining, oil/masala loading, maturation, drained-weight vs net-weight declaration.
2. **The mass balance that governs yield.** Solids in = solids out. Tomato paste at 28–30 Brix becoming ketchup at its finished TSS is a *solids* calculation, not a weight calculation. Learn to build a Brix/TSS balance for a batch and use it to challenge any "standard yield %" — including the ones currently sitting in `SKU_Master` as samples.
3. **Where the kilograms actually go.** Cook-off/evaporation (not recoverable — but it must be *inside* the standard, not outside it), kettle and pipeline hold-up, line purge at start/stop, filler drip, changeover flush, rework loops, QC sampling, spillage, filter/strainer retention.
4. **Fill weight and giveaway.** Target fill vs declared net quantity vs statistical control. A 1 kg pouch filled at 1.015 kg average gives away 1.5% of RM and PM cost silently, forever, and it appears in *no* variance report because the batch reconciles perfectly. **This is the classic un-found item at a plant like MFP's and it is entirely absent from the current toolkit.** Learn checkweigher operation, average-fill systems, and the legal minimum (Module 2). Then measure it — do not estimate it.
5. **Changeover and cleaning losses.** SKU/flavour changeover in sauces means CIP flush and a first-run purge. Frequent short batches destroy yield. Learn to read the batch register for changeover frequency and link it to Module 6's planning work.
6. **Shelf life, spoilage mechanisms and why FEFO is not optional.** Mould/yeast in high-acid ambient product, emulsion separation, colour degradation, syneresis. This is the physical mechanism behind expiry write-offs and the reason FEFO discipline is a cost control, not a housekeeping preference.

**Sources:** a food-technology text on fruit & vegetable processing (any standard Indian FPI curriculum text covers ketchup/sauce/pickle unit ops); MoFPI / IIFPT process guidance; equipment vendor manuals for the kettle, homogeniser, filler and checkweigher actually installed at Makarpura — add them to the data request; two structured half-days on the shop floor with the production head and the QA head, with a notebook, not a laptop.

**Deliverable (prove it):** a one-page **Process Flow & Loss Map** per product family — flow diagram with every loss point annotated, each tagged normal or abnormal, each with a measurement method. Add it to the diagnostic toolkit as `Process_Loss_Map`. It becomes the evidence base for setting real standard yields in `SKU_Master` and for the new fill-giveaway sheet.

**Competency test:** given a real BMR for a ketchup batch, compute expected output two ways (weight basis and solids basis), reconcile the difference, and state which of the two you would defend in front of the production head and why.

---

### Module 2 — Food safety, QA/QC and the regulatory perimeter
**Hours: 24 · Weeks 2–6 · Gates: M6, M7, M9**

**Capability target:** Test any food-safety, labelling, packaging or licensing control at MFP and quantify the exposure of failure — and never let a cost recommendation create a compliance breach.

This is the module where a systems engagement at a food company earns or loses its credibility. Every cost lever in the plan has a compliance edge: cutting preservative dosage hits FSSAI additive limits; re-basing private-label prices touches contractual specs; reducing packaging weight touches net-quantity and EPR obligations; extending shelf life to cut write-offs touches validated shelf-life studies. And MFP exports — the sample assumes UAE, KSA, UK, Qatar and Malaysia; confirm the actual destination list, because each one carries its own regulatory perimeter and at least two will expect halal certification.

**Syllabus**

1. **FSS Act 2006 and the regulation set that binds MFP**
   - Licensing & Registration Regulations — licence category, scope, and whether the licence actually covers every product family being made. Making a category not on the licence is a common and expensive finding. **[VERIFY]** licence scope against the actual SKU list.
   - Food Products Standards & Food Additives Regulations — the *product standards* for tomato ketchup/sauce, mayonnaise, culinary sauces and pickles: minimum TSS, acidity, permitted additives and their maximum limits (benzoates, sorbates, class II preservatives, emulsifiers, stabilisers, colours). Read the actual entries for each product family. **[VERIFY]** every additive in the real material master against permitted limits for each product it goes into.
   - Labelling & Display Regulations 2020 — mandatory declarations, nutritional panel, veg/non-veg mark, allergen declaration, date marking, FSSAI logo and licence number, front-of-pack developments. **[VERIFY]** current status of front-of-pack labelling requirements.
   - Schedule 4 hygiene and sanitary practices; Food Recall Regulations 2017.
2. **Legal Metrology (Packaged Commodities) Rules 2011** — declarations on pre-packed commodities, net quantity and permitted error, MRP, retail sale price, importer/manufacturer particulars, e-mark. This is the statutory floor under Module 1's fill-giveaway work: know the *legal minimum* fill before recommending any change to the *actual* fill. **[VERIFY]** the maximum permissible error table applicable to MFP's pack sizes.
3. **FSSC 22000 / HACCP / BRCGS** — whatever certification MFP holds or needs for its private-label customers. Learn: hazard analysis, CCP determination and decision tree, critical limits, monitoring, corrective action, verification, validation; prerequisite programmes; the internal audit and management review requirements. Programme row 20 flags "BMR/CCP records maintained" — you need to test it properly, not just confirm files exist.
4. **QA/QC as a control system, not a lab.** Sampling plan and AQL; in-process checks (pH, Brix, viscosity/Bostwick, salt, colour); finished-goods release protocol; retention samples; COA issue and reliance — including whether there is a supplier-COA verification policy behind any reliance placed on vendor certificates; out-of-spec handling; instrument calibration; microbiological testing and NABL-accredited external labs.
5. **Extended Producer Responsibility — Plastic Waste Management Rules.** MFP puts PET jars, HDPE jars, laminate pouches, BOPP labels and sachet film into the market. EPR registration, category-wise targets, recycling certificates, annual filing, and the cost of non-compliance. This is potentially an unfunded liability that belongs on the risk register and possibly in the P&L. **[VERIFY]** current registration status, category classification and target obligations.
6. **Export destination compliance.** Gulf/UAE and KSA requirements, halal certification and the segregation and documentation it imposes, UK/EU labelling on export packs, shelf-life declaration differences, importing-country additive limits that may be tighter than FSSAI. A rejected consignment costs more than most of what this engagement will find.
7. **Environment, factory and plant statutes touching a food unit with a boiler:** GPCB consent to operate and ETP discharge norms, Factories Act registrations and returns, Boiler Act inspection and certificate, fire NOC, PESO if fuel is stored in bulk.

**Sources:** FSSAI website — the consolidated regulations and the specific product-standard entries, read directly, not summarised; Legal Metrology Department publications; FSSC 22000 scheme documents; GPCB Gujarat; a half-day with MFP's QA head plus a review of the last FSSAI inspection report, last customer/certification audit report and last CAPA log.

**Deliverable:** (a) a **Compliance Perimeter Register** — every licence, registration, consent, certificate and periodic filing MFP is subject to, with validity date, owner, evidence seen, and gap; (b) `TOC_QAQC` working paper in the standard format (control objective, key control, procedure, attributes A1–A6, sample, rating).

**Competency test:** take one MFP SKU and one export destination and produce a complete compliance trace — product standard conformity, label conformity in both markets, additive limits, packaging EPR category, incentive HS classification. If any of those five cannot be answered from documents on file, that is your first evidenced finding.

---

### Module 3 — Control frameworks and audit craft, upgraded
**Hours: 18 · Weeks 1–5 · Gates: everything**

**Capability target:** Design a defensible control framework for a whole company, not a set of tests for a few cycles — and communicate deficiencies in a way that survives a director's pushback.

The methodology already in the working papers is sound: attribute testing, tolerable deviation, design-vs-operating split, deficiency register, retest discipline. That craft is right and should not be re-invented. What is missing is the layer *above* it — entity-level controls, delegation of authority, and the risk assessment that decides which of the 27 processes deserve which testing intensity. Right now testing depth looks intuition-led. It needs to be visibly risk-led, which is also how you justify the fee for covering 27 processes rather than 6.

**Syllabus**

1. **COSO 2013** — five components, seventeen principles. Map MFP's control environment against all seventeen. Cycle-level conclusions tell you *what* is weak; a COSO mapping is what lets you tell a promoter *why* — and at owner-managed companies of this size the answer is usually that the control environment and risk assessment components are near-absent, which is what makes the process-level failures inevitable rather than accidental.
2. **Entity-level controls and delegation of authority.** Board/management review cadence, a DoA matrix by rupee threshold and transaction type, related-party governance, whistleblower route, code of conduct, management override risk. Post-facto approvals and unauthorised credit notes are DoA failures presenting as process failures — fixing them at the process level alone never holds.
3. **Segregation of duties, done properly.** Build an actual SoD matrix for MFP: initiate / approve / execute / record / custody / reconcile, mapped to named roles. In a ₹30 cr single-unit business full SoD is impossible — so learn the compensating-control vocabulary (independent review, exception reporting, mandatory leave, surprise counts, dual signatures) and where each is genuinely sufficient rather than cosmetic.
4. **Standards and pronouncements you should be citing.** SA 315 (risk assessment and understanding internal control), SA 330 (responses), SA 265 (communicating deficiencies to those charged with governance) — the *significant deficiency* vs *material weakness* distinction is exactly the language the Deficiency Register should speak. ICAI's Standards on Internal Audit (SIA series) for the internal-audit-flavoured parts of this engagement. IIA's Three Lines Model (2020) for how MFP should organise assurance after you leave. **[VERIFY]** applicability of s.143(3)(i) internal financial controls reporting and s.138 internal audit to MFP given its actual turnover and borrowings — both carry thresholds, and whether MFP crosses them changes what you should recommend as a *permanent* structure.
5. **Risk assessment that drives scope.** Build a risk-scored heat map across all 27 processes (likelihood × financial impact × compliance impact) and use it to allocate testing depth and sample sizes. Do this in week 5, before the bulk of fieldwork, and get management to agree it.
6. **Sampling, sharpened.** The `Sampling_Guide` is reasonable but conservative. Learn: attribute sampling statistics, why ~25 items for a daily key manual control, when to extend the sample after exceeding tolerable rather than concluding RED, and — most important at MFP — **when to abandon sampling entirely for full-population CAAT testing.** Tally holds the whole purchase register, sales register, CN register and stock ledger. "Every invoice billed below price master" is one query, not an eight-item sample. Since the current findings are sample-based extrapolations anyway, moving to full-population testing is the single biggest upgrade available to the engagement's credibility.
7. **Root cause and recommendation craft.** Every deficiency needs a root cause that is a *system* statement, not a person statement, and a recommendation that names the control type (preventive/detective, manual/automated), the owner, the evidence it will leave behind, and the retest.

**Sources:** COSO Internal Control — Integrated Framework (2013); ICAI SA 315/330/265; ICAI SIA series; IIA Three Lines Model 2020; ICAI Guidance Note on Audit of Internal Financial Controls Over Financial Reporting (for the control-design vocabulary even where reporting is not mandated).

**Deliverable:** (a) `ELC_Assessment` — COSO 17-principle mapping with evidence and gap; (b) `SoD_Matrix` — roles × activities with conflicts flagged and compensating controls named; (c) `Risk_Heatmap` — all 27 processes scored, driving the agreed testing plan; (d) a revised `Sampling_Guide` with a CAAT-first column.

**Competency test:** once real testing produces real exceptions, classify each in SA 265 language (deficiency / significant deficiency / material weakness) and defend every classification.

---

### Module 4 — Cost systems: standard costing, variance architecture, SKU costing and pricing
**Hours: 20 · Weeks 4–9**

**Capability target:** Build MFP's standard costing system from nothing and design the variance report that keeps it honest — including the variances the current toolkit cannot compute.

Whether MFP has usable standard costing is the first thing to establish; the toolkit's working assumption is that it does not, which is typical at this size. If that holds, this module closes the largest structural gap in the engagement, because nearly every pricing and margin recommendation downstream depends on a cost number nobody can currently produce.

**Syllabus**

1. **Standard cost design.** What a standard is (attainable, not ideal), how often it is refreshed, who owns it, how a standard change is authorised and audited. Standard cost card per SKU: RM at standard rate × standard qty, PM per unit, conversion at standard rate per machine-hour or per MT, overhead absorption base.
2. **The variance architecture the toolkit is missing.** It computes usage variance and rate variance. For a multi-ingredient recipe that is not enough — you need **mix variance and yield variance split out of the usage variance**. When the plant substitutes cheaper starch for tomato paste, total usage variance can look flat while the product silently degrades. Learn the mix/yield decomposition and add it to `RM_Variance`. Also: PM usage vs breakage split, conversion cost variances (efficiency, spending, capacity/volume), and fixed overhead absorption variance.
3. **Costing methods and where each belongs.** Batch/process costing for the plant; joint and by-product treatment; treatment of rework, normal loss and abnormal loss. Note that the normal/abnormal split in the `Wastage` sheet is a *costing* decision with P&L consequences — normal loss is absorbed by good output, abnormal loss goes straight to P&L — so the classification must be principled and documented, driven by a stated allowance per stage, not typed in case by case. Add activity-based allocation where volume-based absorption distorts: small-pack SKUs consume disproportionate packing and QC effort and almost always under-absorb.
4. **SKU/channel P&L.** Contribution by SKU, by channel (Domestic / Export / Private Label / HORECA), and by customer. Any "shift the mix to higher-contribution products" recommendation is unarguable with this and indefensible without it.
5. **Pricing governance.** Cost-plus formula for private label, RM-linked escalation clauses — often the single most valuable contract change available to a contract manufacturer — list-price and discount architecture, the net realisable price waterfall (gross price → scheme → discount → CN → freight → net), and the approval matrix over it.
6. **Working capital and cash conversion.** Inventory days by RM/PM/WIP/FG, debtor days by channel, creditor days, cash conversion cycle. Perishable RM plus long HORECA credit is a specific and testable risk at this client.
7. **Cost records and cost audit applicability.** **[VERIFY]** whether MFP falls within the Companies (Cost Records and Audit) Rules 2014 — check product classification and turnover thresholds. If it does, that is a compliance finding, and the standard costing you are building serves double duty.

**Sources:** ICAI-CMA Cost Accounting Standards (CAS-3 overheads, CAS-6 material cost, CAS-7 employee cost, CAS-8 utilities, CAS-13 service cost centres); a standard cost accounting text for the mix/yield decomposition; MFP's own trial balance and the last twelve months of MIS.

**Deliverable:** (a) `Std_Cost_Card` — one per SKU, formula-linked to `BOM_RM`, `BOM_PM`, `Material_Master`; (b) extended `RM_Variance` with mix and yield columns; (c) `SKU_PL` — contribution by SKU and channel; (d) `Price_Waterfall` — gross to net realisation per channel; (e) a redesigned monthly MIS pack with a day-10 close deadline.

**Competency test:** take one month of *client* actuals and produce a complete variance bridge from standard cost of actual production to actual cost incurred, fully explained, with no residual balancing figure. If a plug is needed, the architecture is wrong.

---

### Module 5 — Source: procurement, vendor ecosystem, job work and imports
**Hours: 12 · Weeks 6–9**

**Capability target:** Test the whole source-side, including the two pieces currently invisible — job work and imports.

P2P is the cycle where documentation is usually healthiest and rate discipline weakest, which makes it easy to under-scope. A clean PO file tells you nothing about whether the rate paid was right. Design the testing so that both questions get asked separately.

**Syllabus**

1. **Vendor master integrity as a fraud control.** Duplicate vendors, vendors sharing a bank account or PAN or address with an employee, dormant vendor reactivation, one-time vendors, vendor master change log. Programme row 2 exists with no attributes — build them, and run this as a CAAT over the full Tally vendor master rather than a sample.
2. **Rate benchmarking that actually works.** Three quotes is a weak control for commodity RM with observable published prices (tomato paste, sugar, refined oil). Design instead: an index-linked benchmark for commodity items, a rate-approval matrix for the rest, quarterly re-benchmarking, and a should-cost model for packaging (resin/paper index + conversion). `Material_Master` already carries a "Current Mkt Rate" column — that column does nothing until someone owns updating it from a named source on a stated cadence.
3. **Contracting.** Annual rate contracts vs spot, escalation and de-escalation clauses tied to the same index, quality specs and rejection terms, delivery and penalty terms, MSME vendor identification and its payment-timeline consequence. **[VERIFY]** MSME status across MFP's vendor base and the s.43B(h) income-tax disallowance exposure for delayed payment — this can be a material tax finding with nothing to do with operations, and it is invisible in both workbooks.
4. **Inward QC and rejection economics.** Sampling plan for inward RM, COA reliance policy, rejection and return-to-vendor process, short-receipt recovery, moisture/Brix/purity testing on incoming paste and its cost impact, and weighbridge coverage on bulk inward.
5. **Job work and co-packing.** Establish first whether MFP sends material out (grinding, filling, labelling) or takes work in — both are common at this size and neither appears anywhere in the current papers. Controls: job-work challans, GST job-work provisions and time limits for return of goods, input-output reconciliation, scrap and loss norms at the job worker, insurance of goods at third-party premises, ITC implications. **[VERIFY]** current GST job-work time limits and return-filing requirements. If MFP does any co-packing, this is a live GST exposure sitting in a blind spot.
6. **Imports.** If any RM is imported (paste, emulsifiers and specialty starches often are): Bill of Entry to GRN reconciliation, customs duty and IGST credit, exchange-rate treatment at three different dates (BoE, payment, accounting), FSSAI import clearance, and demurrage/detention leakage.

**Deliverable:** extended `TOC_P2P` with vendor-master attributes; new `TOC_JobWork`; a `Should_Cost` sheet for the top five RM and top three PM items; an MSME/43B(h) exposure schedule.

**Competency test:** run a full-population CAAT over the client's Tally purchase register for the year and produce: purchases without a prior-dated PO, purchases above benchmark by vendor, vendor concentration by material, price-paid variance between vendors for identical material, and payments to MSME vendors beyond the statutory window. That output replaces the sampled `Procurement` sheet with a real number.

---

### Module 6 — Make: planning, batch control, yield and loss architecture
**Hours: 18 · Weeks 7–12**

**Capability target:** Design the production control system MFP needs — from demand plan through batch reconciliation to loss accounting — and make the yield fix stick.

The toolkit's working hypothesis is that production runs without a BOM master and without yield reconciliation. Test that first. But note that even if it is true, "build a BOM master and reconcile monthly" only addresses half the problem. The other half is upstream: batch size, run length and changeover frequency are set by a planning process, and if that process does not exist, no BOM will recover the yield lost to short runs.

**Syllabus**

1. **S&OP and demand planning.** Monthly cycle, forecast accuracy measurement (MAPE/bias), consensus process, capacity check, frozen period. At MFP: forecast by SKU by channel, with private-label and export orders contractual and retail forecast — very different planning logic in the same plan.
2. **MRP and material planning.** Reorder point vs min-max vs MRP, safety stock computed from demand and lead-time variability rather than from feel, lead times for imported and seasonal RM (tomato paste is seasonal and price-volatile — a buying calendar is a real margin lever), and shelf-life-constrained purchasing, which is where most "stores expiry" losses are actually created.
3. **Batch scheduling and changeover.** Campaign scheduling to minimise flavour changeovers, allergen and non-veg sequencing constraints (egg-based mayonnaise makes sequencing and cleaning validation a food-safety matter, not just a cost one), SMED thinking applied to CIP and flavour change, batch-size optimisation against kettle capacity.
4. **BMR design.** What a Batch Manufacturing Record must capture to be auditable: material issued with batch numbers, actual quantities weighed, process parameters at each CCP, in-process QC results, output quantity and pack breakdown, rework in and out, wastage with reason code, and *two* signatures — production and QC. Then design the reconciliation on top: input + rework in = output + rework out + wastage + samples + unaccounted, with **unaccounted** as the number that triggers investigation.
5. **Loss taxonomy and reason codes.** The sample `Wastage` sheet uses free-text reasons. Replace with a fixed reason-code hierarchy so that twelve months of client data becomes a Pareto rather than an anecdote. Codes should map to an owner and a fix type.
6. **Fill-weight and giveaway control.** From Module 1. Design: target fill setting with a statistical basis, checkweigher with reject and trending, daily average-fill report against declared quantity, giveaway valued in rupees on the shop-floor board. Get filler and checkweigher data in the first data-request round.
7. **OEE and TPM basics.** Availability × performance × quality. Not because MFP needs a TPM programme, but because yield loss, line loss and downtime loss are three different problems with three different owners, and OEE is how you separate them.
8. **Rework economics.** When to rework vs write off, rework dilution limits under product standards, the approval that must precede either, and the costing treatment of rework.

**Deliverable:** `TOC_Planning`; revised BMR template; `Batch_Reconciliation` sheet (input–output–unaccounted); `Loss_Codes` master; `Fill_Giveaway` diagnostic with rupee quantification from measured data; an added attribute A6 (fill-weight control) in `TOC_Production`.

**Competency test:** reconcile one full month of *client* production bottom-up — RM issued, converted at BOM standard, to FG produced, to FG received in store, to FG despatched — and close the loop to within a defined tolerance. Every gap you cannot explain is a finding, and this is the test that converts the illustrative `Production_Log` into a real baseline.

---

### Module 7 — Store: warehouse, traceability, recall, logistics
**Hours: 14 · Weeks 9–13**

**Capability target:** Test stock integrity end-to-end and run a mock recall.

Stores testing in the current papers stops at the RM/PM store. FG warehouse, despatch, transit and 3PL are untested, and traceability — the control that decides whether a contamination event costs ₹5 lakh or ₹5 crore — is not in the papers at all.

**Syllabus**

1. **Inventory record accuracy as a discipline.** ABC/XYZ classification (MFP's item count is small enough that this is entirely tractable), cycle count design and frequency by class, count-to-book tolerance by item type, root-causing variances rather than adjusting them, and the rule that no variance is written off without an owner's sign-off. Design the programme; do not just name it.
2. **Batch/lot control and FEFO in the system.** Tally Prime supports batch-wise inventory with manufacturing and expiry dates and can enforce FEFO-oriented allocation. If MFP's item master lacks expiry fields, that is a *configuration* gap, not a software limitation — so learn the exact configuration (Module 11) and make the recommendation implementable rather than aspirational.
3. **Near-expiry management.** Ageing buckets, near-expiry report cadence, liquidation policy with approval, provisioning for slow-moving and near-expiry stock, and the accounting treatment. Most expiry write-offs had a preventable commercial alternative three months earlier.
4. **Traceability and recall.** One-up/one-back traceability, forward trace (batch → customers) and backward trace (complaint → batch → RM lots → vendor), the four-hour rule most certification schemes impose on a mock recall, mass-balance reconciliation during the trace, and mock-recall documentation. **Run one at MFP.** A failed mock recall is the most attention-getting evidenced finding you can put in front of a promoter, and it makes every other recommendation easier to sell.
5. **Complaints and returns.** Complaint capture and classification, CAPA linkage, market returns (saleable vs non-saleable), returned-goods quarantine and disposition, destruction certificates, and the GST credit-note treatment of returns — which links back to the CN register, since returns and rate differences carry different tax consequences and are often lumped together.
6. **Despatch and gate control.** Gate-pass-to-invoice matching frequency, weighbridge on outward, seal integrity, vehicle hygiene checks for food transport, e-way bill controls, and despatch → invoice → e-way bill three-way reconciliation as a revenue-completeness test.
7. **Logistics and freight cost.** Primary vs secondary freight, cost per MT per lane, 3PL contract and SLA, transit damage claims and whether insurance recoveries are actually pursued to conclusion, detention and demurrage, and cold-chain requirements if any SKU needs one.

**Deliverable:** `TOC_Logistics`; `TOC_Traceability` including a documented mock-recall result with elapsed time; `Cycle_Count_Programme`; `Ageing_NearExpiry` sheet; `Freight_Diagnostic` (cost per MT per lane vs benchmark).

**Competency test:** pick one FG batch at random. In under four hours, produce: every RM lot and vendor that went into it, every customer and invoice it went to, current stock position of that batch, and a mass balance accounting for 100% of it.

---

### Module 8 — Sell: pricing governance, schemes and claims, credit, channel economics
**Hours: 14 · Weeks 10–14**

**Capability target:** Find and close every rupee of revenue leakage between list price and bank receipt — not just invoice-level under-billing.

The price waterfall at a food FMCG company has six or seven steps. The current papers test two of them (billed rate, credit notes). Trade schemes, distributor claims, secondary-sales incentives, damage and expiry claims, and freight recovery are all untested — and in FMCG that is usually where the largest leakage lives, precisely because it is settled by credit note or deduction rather than by invoice.

**Syllabus**

1. **The full price waterfall.** Gross list → trade discount → scheme/promotion → quantity/slab rebate → credit notes → damage & expiry claims → freight & handling recovery → cash discount → net realisation. Build it per channel and test each step for authorisation, computation and accrual. The four channels behave completely differently and should not share one control design.
2. **Scheme design and claim settlement.** How a scheme is approved (who, what budget, what period), how it is communicated, how claims are raised by distributors, how claims are validated against actual secondary sales, and how unclaimed or over-claimed amounts are treated. Controls: scheme master in the system, claim-to-scheme matching, ageing of unsettled claims, and the period-end accrual. **This is untested at MFP and is the most likely home of an unrecorded liability** — worth checking before it becomes an audit issue rather than a systems one.
3. **Distributor and channel management.** Distributor ROI model, primary vs secondary sales visibility, channel stock and days-of-inventory at distributor, stock-and-sales statement discipline, period-end over-loading (a revenue-recognition and returns risk in one), and e-commerce/quick-commerce terms if MFP sells there — listing fees, marketplace deductions and returns make that a deduction-heavy channel needing its own reconciliation.
4. **Private label / OEM contracts.** Cost-plus formula, RM-index escalation clause, minimum volume commitments, exclusivity, spec ownership, liability and recall clauses, review cadence. If private-label prices have not been re-based since the contract was signed, the fix is a contract-terms fix, not a pricing-discipline fix, and it needs Module 4's cost card to negotiate.
5. **HORECA channel specifics.** Credit risk concentration, bulk pack pricing, direct-vs-distributor economics, and whether credit limits are enforced at order or only at invoice.
6. **Credit management.** Credit policy, limit-setting basis, system enforcement at order and at dispatch, AR ageing review cadence, collection escalation, provisioning policy, security (PDC, BG, LC for exports), and bad-debt history by channel.
7. **Revenue completeness.** Despatch → invoice → e-way bill → GST return → bank receipt, reconciled. Sales returns and CN treatment under GST. Revenue cut-off at period end.

**Deliverable:** `TOC_Schemes` (scheme approval and claim settlement); `Claims_Register`; extended `Price_Waterfall` with all steps tested; `Channel_PL`; `Credit_Exposure` with ageing and provision adequacy; a contract review note for the top three private-label agreements.

**Competency test:** for one distributor and one quarter of client data, reconcile gross invoiced value to cash actually received, explaining every rupee of the difference by category, and state which differences carried documented approval.

---

### Module 9 — Exports and trade incentives
**Hours: 10 · Weeks 12–15**

**Capability target:** Make MFP's export benefit capture complete and provable, and its export compliance defensible.

Under-claimed export incentives are among the most common findings at mid-size exporters and among the fastest to convert to cash — which is exactly why the technical detail has to be exactly right, and why the placeholder rates in the toolkit cannot survive into a report.

**Syllabus**

1. **RoDTEP** — scheme mechanics, notified rate by HS code and per-unit value cap, and the claim declaration on the shipping bill. The claim is generally made *at the time of filing the shipping bill*; a missed declaration is typically not recoverable later, which changes the recommendation from "claim it" to "never miss it again" and makes the CHA control the real subject of the finding. Scrip generation, transfer, and time windows. **[VERIFY]** current notified RoDTEP rate and cap for the HS codes covering sauces/condiments (2103 family) and pickles — the 1.4% in the workbook is a placeholder.
2. **Duty Drawback** — All Industry Rate vs Brand Rate, the interaction rules with other schemes, the claim and realisation process, and the BRC linkage. **[VERIFY]** the current AIR for MFP's actual HS codes; the 1.9% in the workbook is a placeholder.
3. **GST on exports** — LUT vs pay-IGST-and-refund, which suits MFP's cash position, refund application timelines and documentation, and refund of unutilised ITC where applicable.
4. **Realisation and forex.** e-BRC, the RBI realisation timeline for export proceeds, EDPMS follow-up and the consequences of unreconciled entries, forex gain/loss accounting at invoice and at realisation, and whether MFP's export billing volume justifies a hedging policy. **[VERIFY]** current RBI realisation period.
5. **Other schemes to test applicability of:** Advance Authorisation or duty-free import of inputs if RM is imported for export production, EPCG if capex is planned, state-level export incentives under Gujarat's industrial policy, and MoFPI/PLI schemes for food processing. **[VERIFY]** each — several are periodically revised or lapsed.
6. **Documentation and CHA control.** The complete export document set, CHA accountability and KPI, and a shipping-bill-to-incentive tracker that closes automatically rather than depending on someone remembering.
7. **Destination compliance** (from Module 2) — halal, labelling, additive limits, certificate of origin under applicable FTAs.

**Sources:** DGFT Foreign Trade Policy and Handbook of Procedures, current edition; CBIC drawback schedule; RoDTEP notified rate schedule; RBI Master Direction on Export of Goods and Services; and the actual shipping bills, e-BRCs and CHA correspondence for the last 12 months.

**Deliverable:** rebuilt `Export_Incentives` with verified live rates per HS code, extended to **all** shipping bills for 12 months rather than a five-bill sample — this is what converts an extrapolation into an actual recoverable number; `Export_Compliance_Tracker` (SB → BRC → incentive → refund, with ageing); a CHA SLA and KPI note.

**Competency test:** take the client's last 12 months of shipping bills and state, with rupee precision and per-bill evidence: what was claimable, what was claimed, what is still recoverable within the window, and what is permanently lost. The permanently-lost number is the one that changes behaviour.

---

### Module 10 — Enabling functions: people, plant, energy, assets, treasury
**Hours: 14 · Weeks 13–18**

**Capability target:** Bring the five enabling functions into the same testing discipline as the operating cycles.

Two of these (payroll, fixed assets) appear in the audit programme marked "(diagnostic)" with no working paper. Utilities has an initiative in the toolkit whose basis reads "management estimate — to be validated Phase 2" — that is the honest label for a number that has not been measured, and it should not sit in an EBITDA bridge at full weight until it has been. Treasury and maintenance are absent entirely.

**Syllabus**

1. **Utilities and energy — validate before you claim.** Boiler efficiency and fuel cost per MT of steam, steam-to-product ratio, fuel procurement and stock measurement (fuel stock is a classic uncounted shrinkage point), power — contract demand vs maximum demand, power factor penalty, load factor, ToD tariff optimisation, DG cost per unit vs grid, water and ETP operating cost and compliance. Build cost-per-MT-produced for each utility and trend it against the last twelve utility bills. **[VERIFY]** current Gujarat industrial tariff structure. Measure this or remove it from the bridge; do not carry an unmeasured estimate into a report.
2. **Maintenance and engineering.** Preventive maintenance schedule and adherence, breakdown analysis and MTBF/MTTR, spares stores (usually an uncounted, unprovisioned inventory pocket), AMC coverage and renewal, and calibration of weighing, filling, checkweigher, pH and Brix instruments. **Calibration failure invalidates every measurement in Modules 1, 4 and 6 — test it early, in week 13 at the latest**, because a yield finding built on an uncalibrated weighbridge collapses the moment anyone asks. Also: capex-vs-repair classification discipline.
3. **HR and payroll.** Attendance-to-payroll integrity, overtime pre-approval linked to output, contract labour — licence, register, principal-employer liability, PF/ESI compliance of the contractor — gratuity and leave provisioning, incentive scheme computation, full-and-final settlement, and statutory register maintenance under the Factories Act and applicable labour codes. **[VERIFY]** current status and applicability of the labour codes to a Gujarat factory of MFP's headcount.
4. **Fixed assets and capex.** Capex approval and DoA, capitalisation policy and the point of capitalisation, asset register with tagging and location, physical verification programme, disposal and scrap sale controls (scrap sale is a cash-leakage and GST-exposure point at nearly every plant), depreciation policy under Schedule II vs income-tax, insurance adequacy against replacement value, and idle or impaired asset identification.
5. **Treasury, banking and insurance.** Banking mandates and authorisation matrix, cash and bank reconciliation discipline, borrowing structure and covenant compliance, drawing-power computation and the accuracy of stock statements submitted to the bank — **cross-check those against the physical verification results, because stock statements that do not agree to the books are a real and common exposure** — interest cost optimisation, forex exposure and hedging policy, and an insurance coverage review: fire, burglary, stock in transit, product liability and recall. A food company without product-liability and recall cover is carrying an existential uninsured risk; check it in week 13, not week 25.

**Deliverable:** `TOC_Utilities` + `Energy_Diagnostic` with measured cost per MT by utility; `TOC_Maintenance` including a calibration status register; `TOC_Payroll`; `TOC_FixedAssets`; `TOC_Treasury` including an insurance adequacy note and a bank-stock-statement reconciliation.

**Competency test:** replace the utilities initiative's management estimate with a measured, defensible number — or delete it from the EBITDA bridge and say plainly why.

---

### Module 11 — Systems and data: Tally as a control platform, ERP readiness, ITGC
**Hours: 16 · Weeks 5–10 (early, deliberately) · Gates: most remediation**

**Capability target:** Convert control recommendations into system configuration that cannot be bypassed — and test the general IT controls everything else depends on.

Look at the shape of the Improvement Plan: block GRN without approved PO, add expiry to item master and a FEFO pick list, lock billing to the price master, hold dispatch at credit limit. **A third of the remediation actions are system configuration tasks.** If you cannot specify them precisely, they get delegated to a Tally partner, half-implemented, and the retest fails. That is why this module sits early.

**Syllabus**

1. **Tally Prime as a control platform — what it can actually enforce.** Work hands-on in a test company, not from documentation. Configure and test: order/PO processing with GRN linkage; batch-wise inventory with manufacturing and expiry dates; BOM and manufacturing journal (this is how a BOM standard gets enforced *at issue* rather than reviewed after the fact); multiple price levels and price lists (how under-billing gets prevented rather than detected); credit limits with over-limit control; cost centres and categories; user-level restrictions and approvals; audit trail / edit log — **[VERIFY]** the audit-trail requirement's applicability to MFP under the Companies (Accounts) Rules and whether the feature is actually enabled, since a disabled audit trail is itself a reportable finding.
2. **Where Tally will not stretch, and what to do about it.** Honest assessment: scheme and claim management, quality and lab data, maintenance, checkweigher/SCADA data, and a real S&OP process will not live in Tally. Options: TDL customisation, standalone modules with a reconciliation, or an ERP move. Learn to produce a **structured ERP readiness assessment and a make/buy recommendation** rather than defaulting to "implement an ERP" — at ₹30 cr, a badly chosen ERP is a bigger risk than the gaps it closes.
3. **Master data management.** Item, vendor, customer, price and BOM masters: who creates, who approves, change log, periodic review, duplicate detection, and a naming and coding standard. Almost every control in this engagement rests on a master that someone can quietly edit.
4. **User access and SoD in the system.** User list review, orphan and shared logins (near-universal at this size), privilege appropriateness, the administrator account, and mapping the Module 3 SoD matrix onto actual system rights.
5. **ITGC basics.** Change management, backup and restore — **test a restore, do not accept an assertion** — disaster recovery, physical and logical security, patching, antivirus, email and ransomware hygiene, and data retention. For a company whose entire financial record lives in one Tally data file, backup-restore is a first-order business continuity control and takes twenty minutes to test.
6. **Data analytics / CAAT capability.** This is the multiplier for the whole engagement, and the direct answer to the sample-data problem. Learn to extract Tally data (export, ODBC or XML) into Excel Power Query or Python and run full-population tests: duplicate invoices, gaps in document number series, weekend and after-hours entries, round-sum entries, entries by user, Benford analysis on purchases, price-below-master exceptions, and journal entries touching inventory outside the normal route. Every sampled sheet in the diagnostic toolkit — `Procurement`, `Price_Realisation`, `CN_Register`, `Export_Incentives` — can become a full-population result instead of a ×12 extrapolation. **That single change is what turns the toolkit from a demonstration into evidence.**
7. **Digital compliance interfaces.** GST portal reconciliation (GSTR-2B vs purchase register, GSTR-1 vs sales register, GSTR-3B vs books), e-invoice and e-way bill applicability and controls, TDS reconciliation with Form 26AS/AIS.

**Deliverable:** `TOC_ITGC`; a **Tally Configuration Specification** — a numbered, implementable list of exactly which settings must change to enforce each recommendation, written so a Tally partner can execute it and you can retest it; `CAAT_Library` — the saved queries for full-population tests; an ERP readiness note with a recommendation.

**Competency test:** in a test company, configure and demonstrate the four system controls from the Improvement Plan, then attempt to bypass each one. A control you can bypass in the test company will be bypassed in the live one.

---

### Module 12 — Governance, compliance calendar and implementation craft
**Hours: 19 · Weeks 15–26 · Runs alongside remediation**

**Capability target:** Make the improvements survive your departure.

This is the module most engagements skip, and it is why most control improvement plans decay within two quarters. The Improvement Plan currently has twelve actions, all "Proposed", with blank owners and blank dates. Once the fieldwork produces real findings, the difference between a report and a change programme is entirely in this module.

**Syllabus**

1. **The compliance calendar.** Build MFP's complete statutory calendar in one place: GST (GSTR-1/3B/9/9C, e-invoice, e-way bill), TDS/TCS returns and certificates, income tax (advance tax, return, tax audit — **[VERIFY]** applicability thresholds), ROC/MCA filings, PF/ESI/PT, Factories Act returns, GPCB consent renewal and returns, boiler certificate renewal, FSSAI licence renewal and annual return, legal metrology registration, EPR annual filing, fire NOC, and any trade licence. Each with due date, owner, evidence and escalation. This is deliverable-grade work in itself and is absent from both workbooks. Your firm's LexComply asset is a natural scaffold for the calendar structure.
2. **Delegation of authority, formalised.** A DoA matrix with rupee thresholds covering capex, purchase, price deviation, credit note, write-off, credit limit, recruitment, banking and contract signing. Approved by the board and configured into the system where possible. A large share of the deficiencies a company like MFP will show are DoA absences wearing process clothing.
3. **Policy set.** Write the policies that do not exist: procurement, inventory and write-off, pricing and discount, credit, wastage and abnormal-loss approval, fixed assets and capex, forex, plus SoPs for the operating cycles. Keep them short. A two-page policy that is followed beats a twenty-page one that is filed.
4. **KPI and MIS architecture.** The day-10 MIS pack from Module 4, plus a daily/weekly operating dashboard: yield %, giveaway %, OEE, abnormal loss ₹, price realisation vs list, DSO/DIO/DPO, incentive claim status, open-deficiency count. Each KPI gets one named owner. `Monthly_MIS` is the seed — it needs an operational layer above the P&L layer.
5. **Change management.** Kotter's eight steps or any equivalent frame, applied honestly to a promoter-run 30-crore business: who resists a BOM master and why (usually the person whose consumption becomes visible), how to sequence quick wins to buy credibility for structural change, and the difference between a control the plant accepts and one the plant works around. The quick wins already identified — price master enforcement, export incentive claiming, CN approval matrix — are correctly chosen because they are fast, visible and self-funding. Land those first, whatever the real numbers turn out to be.
6. **Retest discipline and the assurance handover.** Every remediation gets a retest date and a re-run of the original TOC; nothing closes on assertion. Then design what happens after: an internal audit charter (or an outsourced IA arrangement with your firm), the Three Lines allocation of who monitors what, a management review cadence, and a control self-assessment routine MFP's own staff can run monthly.
7. **Reporting.** Structure the final deliverable: executive summary with the EBITDA bridge, control effectiveness summary, deficiency register with severity, prioritised improvement plan with owners and dates, and an appendix of working papers. Write every finding as Condition / Criteria / Cause / Consequence / Corrective action — the current register format captures condition and recommendation but is thin on criteria and consequence, and those two are exactly what stop a finding being argued away.

**Deliverable:** `Compliance_Calendar`; `DoA_Matrix`; the policy and SoP set; the KPI dashboard design; a fully populated `Improvement_Plan` with named owners, dated targets and retest dates; the final report structure.

**Competency test:** every evidenced deficiency has a named owner, a dated target, a defined retest, and a stated rupee consequence of not fixing it. Zero "Proposed" statuses remain.

---

## 3. Twenty-six week schedule

Assumes ~7 hours a week of study, running alongside fieldwork. Module hours are study; fieldwork is additional. Note how much of the first ten weeks is about *getting data* — the syllabus cannot outrun the document flow.

| Weeks | Primary study | Fieldwork running in parallel | Milestone |
|---|---|---|---|
| 1–2 | M1 (process tech), M3 start (COSO, SA 315/330/265) | Plant walkthroughs; **close out the Phase 0 `Data_Request` — 12 of 16 items still Pending** | Process & Loss Map drafted |
| 3–4 | M1 finish, M2 start (FSSAI, product standards, labelling) | QA head sessions; licence and certification file review | Compliance Perimeter Register v1 |
| 5–6 | M2 (legal metrology, FSSC, EPR), M3 (SoD, risk heatmap), M11 start | Fill-weight data pull; risk workshop with management | **Risk heatmap across all 27 processes → agreed testing plan** |
| 7–8 | M11 (Tally configuration hands-on), M4 start (standard costing) | Build real BOM masters for every SKU; test-company configuration | Tally Configuration Specification v1; **BOMs replace samples** |
| 9–10 | M4 (variance architecture, SKU P&L), M5 (procurement, vendors) | CAAT extraction of full-year purchase and sales registers | **Sampled sheets replaced by full-population results** |
| 11–12 | M6 (planning, BMR, batch reconciliation, giveaway) | BMR redesign; batch reconciliation on real batches | First real yield baseline; giveaway measured |
| 13–14 | M7 (traceability, warehouse), M9 start (RoDTEP/DBK verification) | **Mock recall**; calibration audit; insurance check; full 12-month shipping-bill review | Mock recall result; verified incentive rates and recoverable amount |
| 15–16 | M8 (price waterfall, schemes, claims), M9 finish | Scheme and claim register reconstruction; contract review | Claims exposure quantified |
| 17–18 | M10 (utilities, maintenance, payroll, assets, treasury) | Energy measurement against 12 months of bills | **Utilities estimate validated or withdrawn** |
| 19–20 | M12 (compliance calendar, DoA, policies) | Calendar build; DoA drafting with the promoter | Compliance calendar live |
| 21–22 | M12 (KPI/MIS, change management) | MIS pack redesign; day-10 close dry run | New MIS pack issued for one month |
| 23–24 | M12 (reporting, assurance handover) | Retest of the three quick wins | **First retests pass** |
| 25–26 | Consolidation; gap review against the 27-process list | Final report; management presentation | Complete deliverable set; every process on the list touched, every figure client-sourced |

**Two sequencing decisions worth defending:** M11 sits at weeks 5–10 rather than late, because a third of the remediation actions are system configurations and a configuration you cannot specify in week 8 becomes a retest you cannot pass in week 24. Calibration testing (M10) is pulled forward to week 13 because every yield and variance number produced after it depends on the instruments being trustworthy.

---

## 4. Coverage matrix — every process ends somewhere

Use this as the completion checklist. The engagement is done when every row has a working paper reference **and a client-evidenced rating** — not a sample one.

| # | Process | Module | Diagnostic sheet | Working paper | Structure? | Client-tested? |
|---|---|---|---|---|---|---|
| 1 | Vendor master & approval | M5 | — | `TOC_P2P` (extend) | Partial | No |
| 2 | Purchasing & rate discipline | M5 | `Procurement`, `Should_Cost` | `TOC_P2P` | Yes | No |
| 3 | Inward QC & short receipt | M2, M5 | — | `TOC_P2P` (extend) | Partial | No |
| 4 | Job work / co-packing | M5 | — | `TOC_JobWork` | **Build** | No |
| 5 | Imports & BoE reconciliation | M5 | — | `TOC_P2P` (extend) | **Build** | No |
| 6 | NPD & recipe change control | M1, M2 | `Process_Loss_Map` | `TOC_NPD` | **Build** | No |
| 7 | Planning / S&OP / MRP | M6 | — | `TOC_Planning` | **Build** | No |
| 8 | Batch manufacture, BOM, yield | M1, M6 | `Production_Log`, `RM_Variance`, `Batch_Reconciliation` | `TOC_Production` | Yes | No |
| 9 | Fill weight & giveaway | M1, M6 | `Fill_Giveaway` | `TOC_Production` A6 | **Build** | No |
| 10 | Wastage, rework, write-off | M4, M6 | `Wastage`, `Loss_Codes` | `TOC_Production` | Yes | No |
| 11 | QA/QC, CCP, release, retention | M2 | — | `TOC_QAQC` | **Build** | No |
| 12 | Maintenance & calibration | M10 | — | `TOC_Maintenance` | **Build** | No |
| 13 | Utilities & energy | M10 | `Energy_Diagnostic` | `TOC_Utilities` | **Build** | No |
| 14 | Stores, FEFO, expiry, counts | M7 | `Stock_Verification`, `Cycle_Count_Programme`, `Ageing_NearExpiry` | `TOC_Stores` | Yes | No |
| 15 | FG warehouse, despatch, freight | M7 | `Freight_Diagnostic` | `TOC_Logistics` | **Build** | No |
| 16 | Traceability, recall, complaints | M7 | — | `TOC_Traceability` | **Build** | No |
| 17 | Order to cash | M8 | `Price_Realisation`, `Price_Waterfall` | `TOC_OTC` | Yes | No |
| 18 | Schemes, claims, secondary sales | M8 | `Claims_Register`, `Channel_PL` | `TOC_Schemes` | **Build** | No |
| 19 | Exports & incentives | M9 | `Export_Incentives`, `Export_Compliance_Tracker` | `TOC_Exports` | Yes | No |
| 20 | Returns & market expiry | M7, M8 | — | `TOC_Traceability` | **Build** | No |
| 21 | Costing & MIS | M4 | `Std_Cost_Card`, `SKU_PL`, `Monthly_MIS` | `TOC_Costing_MIS` | Yes | No |
| 22 | HR, payroll, contract labour | M10 | — | `TOC_Payroll` | **Build** | No |
| 23 | IT / Tally governance, access | M11 | `CAAT_Library`, Tally Config Spec | `TOC_ITGC` | **Build** | No |
| 24 | Treasury, banking, forex, insurance | M10 | — | `TOC_Treasury` | **Build** | No |
| 25 | Fixed assets & capex | M10 | — | `TOC_FixedAssets` | **Build** | No |
| 26 | Statutory compliance calendar | M12 | `Compliance_Calendar` | `TOC_Compliance` | **Build** | No |
| 27 | Entity-level controls & DoA | M3, M12 | `ELC_Assessment`, `SoD_Matrix`, `DoA_Matrix`, `Risk_Heatmap` | `TOC_ELC` | **Build** | No |

**16 new working papers, 18 new diagnostic sheets, and 27 processes needing a client-evidenced conclusion.** That is the real size of "all the system improvements", and it is why the learning has to be structured rather than picked up as you go.

---

## 5. Turning the sample workbooks into a client baseline

The architecture is good. These are the specific things to fix or confirm as the real data arrives — do them early, because everything downstream inherits them.

**Structural fixes to the toolkit**

1. **Possible double count between `RM_Variance` rate variance and `Procurement` excess.** The Initiatives sheet notes the exclusion in the basis text for the procurement initiative, but the Dashboard adds "RM rate variance" and "Procurement above benchmark" as two separate lines. Both measure paying above the benchmark rate. Reconcile them explicitly or the total leakage figure will be overstated, and a sharp CFO will find it in the first meeting.
2. **`RM_Variance` has no mix/yield split** (Module 4). With seven-ingredient recipes this hides ingredient substitution entirely.
3. **`Wastage` normal/abnormal classification has no stated criteria.** The `Assumptions` sheet should carry a normal-loss allowance per stage, and the classification should compute from it rather than being typed per row. As it stands the split is an opinion, and abnormal loss is the number that hits P&L.
4. **No fill-giveaway sheet exists at all** (Modules 1 and 6). Add it.
5. **The ×12 annualisation is doing very heavy lifting.** It assumes one month is representative — for seasonal RM and seasonal demand it is not. Wherever full-population CAAT testing is possible — procurement, pricing, credit notes, exports — replace extrapolation with the actual annual number (Module 11). This is the highest-leverage change available.
6. **`Stock_Verification` annualises one count ×4** across a partial item list. Complete the count across all codes before annualising anything.
7. **Deficiency Register owners and target dates are blank; every Improvement Plan status reads "Proposed".** Nothing is assigned to anyone. Fix this the moment the first real findings exist — it is the first thing a reviewer notices.

**Hypotheses in the sample that fieldwork must confirm or reject**

Every one of these is currently an assumption. None can be reported until tested. Treat this list as the initial fieldwork agenda:

| Sample hypothesis | Test it in | Confirm by |
|---|---|---|
| No BOM master exists; consumption not reconciled to standard | M6 | Inspecting the item/BOM setup in Tally and the issue process |
| Yield not compared to standard batch-wise | M6 | Reviewing the last 3 months of BMRs |
| POs raised post-facto for a material share of purchases | M5 | Full-population PO date vs GRN date CAAT |
| Purchases made above benchmark without approval | M5 | Full-population rate comparison against an established benchmark |
| FEFO not followed; item master lacks expiry fields | M7, M11 | Inspecting the item master configuration and observing stores issue |
| Physical stock shortage / shrinkage | M7 | A complete physical verification, all codes |
| Under-billing against approved price list | M8 | Full-population invoice-rate vs price-master CAAT |
| Credit notes issued without authorisation | M8 | 100% of CNs above threshold vouched to policy and sign-off |
| RoDTEP/DBK not claimed on most shipping bills | M9 | All 12 months of shipping bills vs verified rate schedule |
| Dispatch beyond credit limit | M8 | Order and dispatch testing against limits in Tally |
| Gate pass to invoice matched only weekly | M7 | Observation plus despatch–invoice–e-way bill reconciliation |
| No standard costing; MIS is a basic P&L issued late | M4 | Inspecting the last 3 monthly MIS packs and their issue dates |
| Abnormal loss written off without approval | M6 | Vouching write-offs to approvals |
| Overtime approved after the fact | M10 | Payroll and OT approval testing |
| Utilities savings opportunity exists | M10 | Measured cost per MT against 12 months of bills |

**Items not in the sample at all, which experience says to check anyway:** fill giveaway, scheme and distributor claim leakage, job-work GST exposure, MSME 43B(h) disallowance, EPR obligation, product-liability and recall insurance, backup restorability, instrument calibration status, and stock statements submitted to the bank versus book stock.

---

## 6. Reading and source register

**Primary — read the actual text, not a summary**
- FSS Act 2006 and the Food Products Standards & Food Additives Regulations — the specific entries for tomato ketchup/sauce, mayonnaise, culinary sauces and pickles
- FSSAI Labelling & Display Regulations 2020; Licensing & Registration Regulations; Schedule 4; Food Recall Regulations 2017
- Legal Metrology (Packaged Commodities) Rules 2011
- Plastic Waste Management Rules and the current EPR guidelines
- DGFT Foreign Trade Policy and Handbook of Procedures — current edition; CBIC drawback schedule; RoDTEP notified rates
- RBI Master Direction on Export of Goods and Services
- CGST Act and Rules — job work provisions, export refunds, credit notes, e-invoice and e-way bill
- Companies Act 2013 — s.134, s.138, s.143(3)(i), Schedule II; Companies (Accounts) Rules — audit trail; Companies (Cost Records and Audit) Rules 2014
- Factories Act, Boiler Act, and Gujarat GPCB consent conditions

**Frameworks**
- COSO Internal Control — Integrated Framework (2013)
- ICAI SA 315, SA 330, SA 265; ICAI Standards on Internal Audit (SIA series)
- ICAI Guidance Note on Audit of Internal Financial Controls Over Financial Reporting
- IIA Three Lines Model (2020)
- FSSC 22000 scheme documents; Codex HACCP principles
- ICAI-CMA Cost Accounting Standards — CAS-3, 6, 7, 8, 13

**Technical**
- A standard fruit & vegetable processing / food technology text covering sauce, ketchup, mayonnaise and pickle unit operations
- MoFPI and IIFPT technical publications on condiment processing
- Equipment manuals for MFP's own kettle, homogeniser, filler, checkweigher and boiler — request these
- Tally Prime documentation, worked hands-on in a test company

**Client documents to obtain — this is the gating dependency for the whole plan**

The `Data_Request` sheet shows 12 of 16 items still Pending: BMRs, RM/PM issue slips, wastage logs, customer contracts and discount policy, export documents, GRN register and pending-PO report, weighbridge log, physical stock reports, utility bills, payroll summary, SKU master with price lists, and recipes. Add to that list:

FSSAI licence and last inspection report · certification audit reports and CAPA log · product specifications and shelf-life studies · filler and checkweigher data · calibration records · insurance policies · bank stock statements and sanction letters · scheme circulars and distributor claim files · job-work challans · import Bills of Entry · vendor master extract with bank details · Tally user list with rights · last 12 months of shipping bills and e-BRCs · EPR registration and filings · maintenance and breakdown logs.

**No module in this plan can be completed without its underlying documents. Chase the data request before chasing the syllabus** — and consider making document release a milestone in the engagement letter, because at week 26 a missing weighbridge log is your problem, not the client's.

---

## 7. Self-assessment — rate yourself at week 13 and week 26

Score 1 (cannot do) to 5 (can do unsupervised and defend it to a challenging CFO). Target: all 4+ by week 26.

| # | Capability | Module | Wk 13 | Wk 26 |
|---|---|---|---|---|
| 1 | Explain every loss point in a sauce line and how to measure each | M1 | | |
| 2 | Build and defend a standard yield from a solids mass balance | M1, M4 | | |
| 3 | Quantify fill giveaway in rupees and design its control | M1, M6 | | |
| 4 | Test any FSSAI, labelling or legal-metrology control | M2 | | |
| 5 | Assess EPR obligation and exposure | M2 | | |
| 6 | Test a food-safety management system against its scheme | M2 | | |
| 7 | Map an entity to COSO's 17 principles with evidence | M3 | | |
| 8 | Build an SoD matrix with compensating controls for a 30-crore business | M3 | | |
| 9 | Classify deficiencies in SA 265 language and defend it | M3 | | |
| 10 | Design a standard costing system from nothing | M4 | | |
| 11 | Decompose usage variance into mix and yield | M4 | | |
| 12 | Build SKU and channel contribution P&L | M4 | | |
| 13 | Design a cost-plus contract with an RM escalation clause | M4, M8 | | |
| 14 | Run a full-population CAAT over Tally data | M11 | | |
| 15 | Write an implementable Tally configuration specification | M11 | | |
| 16 | Test ITGCs including a restore test | M11 | | |
| 17 | Design an S&OP and MRP process | M6 | | |
| 18 | Design a BMR and batch reconciliation that closes | M6 | | |
| 19 | Run a mock recall within four hours | M7 | | |
| 20 | Design a cycle-count programme and root-cause variances | M7 | | |
| 21 | Build a full price waterfall and test every step | M8 | | |
| 22 | Test scheme approval and distributor claim settlement | M8 | | |
| 23 | Compute and verify RoDTEP and drawback per shipping bill | M9 | | |
| 24 | Reconcile export realisation and assess forex exposure | M9 | | |
| 25 | Measure utility cost per MT and validate a savings case | M10 | | |
| 26 | Test payroll, contract labour and fixed-asset controls | M10 | | |
| 27 | Assess insurance adequacy including product liability and recall | M10 | | |
| 28 | Build a complete statutory compliance calendar | M12 | | |
| 29 | Draft a DoA matrix and get it approved | M12 | | |
| 30 | Land a control change against organisational resistance | M12 | | |

---

## 8. The one-paragraph version

The workbooks are a well-built skeleton carrying sample data — the architecture is right, the baseline does not exist yet, and the illustrative findings are intelligent hypotheses rather than evidence. So the plan has to do three things at once: cover the eighteen processes the papers never reach, build the capability to test them properly, and replace every sample cell with a client-sourced number. Modules 1, 2, 3 and 11 are the gates — process technology so the yield standards survive contact with the production head, the regulatory perimeter so no cost recommendation creates a compliance breach, control frameworks so the work has a spine above the cycle tests, and Tally plus CAAT capability so remediation becomes enforcement and sampled extrapolations become full-population facts. Chase the data request before the syllabus; measure the utilities case or drop it; verify the incentive rates before a rupee of them is reported; and check fill giveaway early, because it is the largest thing the current toolkit cannot see.

---

*Working document. Update the coverage matrix as working papers are completed and client-tested, and re-score the self-assessment at weeks 13 and 26.*
