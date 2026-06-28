# Claude Prompt Library for Chartered Accountants, vCFOs & Family Offices

**A copy-paste prompt playbook for a modern India-based CA practice — covering audit, direct & indirect tax, corporate/secretarial & legal compliance, financial reporting, virtual-CFO advisory, family office, transactions and FEMA.**

> Prepared for **Sagar Khatri & Associates, Chartered Accountants**. India-primary: prompts cite Indian statutes, sections and forms so you can use them as-is. Pair them with your own tools — **LexComply India**, the **Continuous Audit Engine (CAE)** and the **Foreign Gain/(Loss) workbook** — where noted.

---

## Table of contents

1. [How to use this library](#1-how-to-use-this-library)
2. [How these prompts save you time & energy](#2-how-these-prompts-save-you-time--energy)
3. [Prompt anatomy for CAs (the 5-part formula)](#3-prompt-anatomy-for-cas-the-5-part-formula)
4. [Guardrails — read this first](#4-guardrails--read-this-first)
5. [A. Audit & Assurance](#a-audit--assurance)
6. [B. Direct Tax — Income Tax & TDS](#b-direct-tax--income-tax--tds)
7. [C. Indirect Tax — GST](#c-indirect-tax--gst)
8. [D. Companies Act 2013 / ROC & Secretarial](#d-companies-act-2013--roc--secretarial)
9. [E. Labour & Other Statutory Compliance](#e-labour--other-statutory-compliance)
10. [F. Financial Reporting & Accounting](#f-financial-reporting--accounting)
11. [G. vCFO / FP&A](#g-vcfo--fpa)
12. [H. Family Office & Private Wealth](#h-family-office--private-wealth)
13. [I. Transaction Advisory / M&A / Valuation / Due Diligence](#i-transaction-advisory--ma--valuation--due-diligence)
14. [J. FEMA & Cross-border](#j-fema--cross-border)
15. [K. Practice Management & Client Communication](#k-practice-management--client-communication)
16. [Ways of working — beyond single prompts](#ways-of-working--beyond-single-prompts)
17. [Quick-reference index](#quick-reference-index)

---

## 1. How to use this library

Each prompt below is a **card** with a consistent structure:

> **Use case** — when to reach for it.
> **The prompt** — a fenced block you copy, paste and fill in the `[BRACKETED PLACEHOLDERS]`.
> **What you get** — the shape of Claude's output.
> **Time saved** — an honest range vs. doing it from scratch.
> **Quality tips & caveats** — how to get a better answer and what to double-check.

**Workflow:** copy the prompt → replace every `[PLACEHOLDER]` → paste your data (figures, trial balance extract, notice text) → review the output with professional skepticism → edit and sign off. Claude produces the *first draft and the reasoning*; **you** remain the professional of record.

> **Tip:** Keep this file open in a second window during the working day. Most prompts take under 30 seconds to fill in and save 30 minutes to several hours each.

---

## 2. How these prompts save you time & energy

The leverage is not "Claude does your job" — it is that Claude removes the **blank-page tax** and the **mechanical grind**, so your scarce hours go to judgement, review and client relationships.

| Where the time goes today | What Claude accelerates | Typical saving |
|---|---|---|
| Drafting (letters, notices, resolutions, memos, reports) | First draft in your house style, properly structured | 60–80% of drafting time |
| Reconciliation **reasoning** (not the maths) | Explaining *why* lines differ, what to check next, how to bucket exceptions | 30–50% |
| Summarising long documents (notices, agreements, circulars, ledgers) | Plain-English summary + action list + risk flags | 70–90% |
| Building checklists & programs | Complete, section-referenced checklists tailored to the client | 50–70% |
| First-draft research & "explain the law" | A structured starting point you then verify | 40–60% |
| Client communication | Clear, professional, plain-language explainers | 50–70% |

**The compounding benefit:** lower mental fatigue. Offloading the mechanical first draft means you arrive at the *review* stage fresh — which is where errors actually get caught and where you add value.

---

## 3. Prompt anatomy for CAs (the 5-part formula)

A reliable prompt has five parts. Skip any of them and quality drops.

1. **Role** — *"You are a chartered accountant in India specialising in GST litigation."*
2. **Context** — the facts: entity type, turnover, period, the document, the figures.
3. **Task** — exactly what you want produced.
4. **Format** — table / memo / letter / bullet list / point-wise reply; length.
5. **Constraints** — Indian law only, cite sections, flag assumptions, ask before guessing, no fabricated citations.

**Before → After**

> ❌ *"Write a reply to a GST notice."*
>
> ✅ *"You are a CA in India handling GST litigation. A private limited company (turnover ₹12 cr, FY 2023-24, regular scheme) received an ASMT-10 alleging ITC mismatch of ₹3.4 lakh between GSTR-3B and GSTR-2B for Sep 2023. The actual reason is that two supplier invoices were filed by them in the next quarter. Draft a point-wise reply in formal letter format, reference the relevant CGST Act sections and rules, keep it under one page, and list the documents I should annex. Flag any assumption you make and do not cite case law unless you are certain it exists."*

> **Reusable instruction to keep in your back pocket (paste at the end of any prompt):**
> *"Cite exact Indian sections/forms; clearly mark anything you are assuming; if you are not certain a case/citation exists, say so rather than inventing it; ask me for any figure you need instead of guessing."*

---

## 4. Guardrails — read this first

Using AI in a regulated profession carries real obligations. Treat these as non-negotiable.

- **Confidentiality (ICAI Code of Ethics).** Do not paste a client's personally identifiable, price-sensitive or UDIN-linked confidential data into a consumer chatbot. Anonymise — use `[CLIENT]`, mask PAN/GSTIN/Aadhaar, replace names with roles. For sensitive engagements, prefer an enterprise/no-training deployment and confirm the data-handling terms.
- **AI can hallucinate.** It may invent a section number, a circular, a case citation or a due date that sounds right. **Always verify every statutory reference, rate, threshold and date against the bare Act, the latest Finance Act, CBDT/CBIC circulars or the ICAI material before relying on it.**
- **No outsourcing of judgement.** Claude drafts and reasons; the CA reviews, exercises professional skepticism and **signs**. Audit opinions, certifications, UDINs and filings remain entirely your professional responsibility.
- **Currency of law.** Tax rates, thresholds, ITC rules and compliance dates change every year. Tell Claude the assessment/financial year and re-verify — its knowledge has a cut-off.
- **Independence & ethics.** Don't use AI in a way that impairs independence, creates a self-review threat, or substitutes for required audit evidence. AI output is an *input* to your file, not audit evidence in itself.

> Treat AI output the way you treat a bright articled assistant's first draft: useful, fast, and **always reviewed before it leaves the office**.

---

## A. Audit & Assurance

### A1 · Build a statutory audit program
**Use case:** Kick off a new statutory audit with a tailored, SA-referenced program.

```
You are a chartered accountant planning a statutory audit under the Companies Act, 2013 and the ICAI Standards on Auditing.
Client: [INDUSTRY] [PRIVATE/PUBLIC LTD], turnover ₹[X] cr, [NUMBER] locations, accounting under [Ind AS / AS].
Key risk areas I already see: [E.G. REVENUE RECOGNITION, RELATED-PARTY TXNS, INVENTORY].
Produce an audit program organised by financial-statement area (revenue, purchases, payroll, fixed assets, inventory, cash & bank, statutory dues, related parties). For each area give: assertion(s) covered, the audit procedure, and the relevant SA reference. Format as a table. Flag where I should consider analytical vs. substantive testing.
```
**What you get:** A ready-to-edit, area-wise audit program mapped to assertions and SAs.
**Time saved:** 2–4 hours per new engagement.
**Quality tips & caveats:** Add the client's specific risks for sharper procedures. Verify SA numbers and that the program covers CARO 2020 reporting needs separately.

### A2 · Turn CAE exceptions into review notes
**Use case:** Convert raw exceptions from your **Continuous Audit Engine** (fraud / working-capital / journal rules) into client-ready audit observations.

```
You are a CA documenting audit findings. Below are exception rows from our continuous-audit system [PASTE: rule name, transaction, amount, date, counterparty, why-flagged].
For each, draft a concise audit observation with: (1) the issue in plain English, (2) the risk/impact, (3) the likely root cause, (4) the further evidence I should obtain, and (5) a suggested recommendation to management. Group similar exceptions. Output as a numbered working-paper note.
```
**What you get:** Structured working-paper notes and a draft management-letter point per exception.
**Time saved:** 1–3 hours per batch.
**Quality tips & caveats:** Pairs directly with `cae/backend/app/engines/fraud_engine.py` and the rules in `cae/backend/app/rules/`. Confirm amounts/causes against the actual transaction before finalising — the engine flags, you conclude.

### A3 · Management letter / audit observations drafting
**Use case:** Draft the management letter at the end of fieldwork.

```
You are a CA drafting a management letter for [CLIENT], FY [YEAR]. Here are my raw observations: [BULLET LIST OF FINDINGS].
For each, write a formal paragraph with: Observation, Implication/Risk, and Recommendation. Order by severity (high to low). Open with a short covering paragraph and close professionally. Keep the tone constructive, not accusatory.
```
**What you get:** A polished, severity-ordered management letter.
**Time saved:** 1–2 hours.
**Quality tips & caveats:** Ensure each point is supported by your working papers before issuing.

### A4 · Going-concern assessment memo
**Use case:** Document going-concern evaluation (SA 570).

```
You are a CA assessing going concern under SA 570 for [CLIENT], FY [YEAR].
Financial indicators: [NET WORTH, CURRENT RATIO, CASH POSITION, LOSSES, DEFAULTS, MATURING LOANS].
Other indicators: [LOSS OF KEY CUSTOMER / LITIGATION / PROMOTER FUNDING etc.].
Draft a going-concern assessment memo: list the events/conditions casting doubt, management's mitigating plans I should ask for, the additional procedures I should perform, and a recommended reporting conclusion with the SA 570 reference. Mark anything you assume.
```
**What you get:** A structured going-concern memo for the audit file.
**Time saved:** 1–2 hours.
**Quality tips & caveats:** Obtain management's written representation and cash-flow projections before concluding; verify SA 570 paragraph references.

### A5 · Sampling rationale & ICFR narrative
**Use case:** Justify a sampling approach or document an internal-control narrative.

```
You are a CA documenting [SAMPLING APPROACH for AREA] / [the internal financial controls narrative for the PROCESS, e.g. PROCURE-TO-PAY].
Context: [POPULATION SIZE, VALUE, KEY RISKS, CONTROLS IN PLACE].
Produce: a clear rationale referencing the relevant SA / IFC framework, the control objectives, the key controls and how I would test each (design + operating effectiveness), and the deficiencies to watch for. Format as a table.
```
**What you get:** A defensible sampling/ICFR working paper.
**Time saved:** 1–2 hours.
**Quality tips & caveats:** Align with your firm's methodology; AI output supports but is not itself audit evidence.

---

## B. Direct Tax — Income Tax & TDS

### B1 · Review an income-tax computation
**Use case:** Sanity-check a computation before filing.

```
You are a CA reviewing an income-tax computation for [INDIVIDUAL / FIRM / COMPANY], AY [YEAR], [OLD/NEW REGIME].
Here is the computation: [PASTE HEADS OF INCOME, DEDUCTIONS, ADJUSTMENTS].
Review for: missed deductions/exemptions, incorrect head classification, disallowances under sections 40(a)/43B/14A, set-off & carry-forward errors, and applicable surcharge/cess. List issues as: line item → concern → section → suggested correction. Then flag the top 3 tax-planning opportunities I should discuss with the client. Verify-against-current-law where rates/limits are involved.
```
**What you get:** A line-by-line review note plus planning ideas.
**Time saved:** 45–90 minutes.
**Quality tips & caveats:** Confirm every rate, limit and section against the current Finance Act and the chosen regime.

### B2 · Draft a reply to an income-tax notice
**Use case:** Respond to notices u/s 139(9), 143(1), 142(1), 143(2) or 148.

```
You are a CA drafting a reply to an income-tax notice. The notice is u/s [SECTION] for AY [YEAR] for [ASSESSEE TYPE]. Notice text/issue: [PASTE OR SUMMARISE THE DISCREPANCY].
The actual facts/explanation are: [YOUR EXPLANATION + EVIDENCE AVAILABLE].
Draft a formal point-wise reply suitable for upload on the e-filing portal: restate each query, give the factual response, reference the relevant section/rule, and list the documents I will annex. Keep it precise and respectful. Flag any point where my facts are weak.
```
**What you get:** A portal-ready, point-wise reply plus an annexure list.
**Time saved:** 1–2 hours.
**Quality tips & caveats:** Never paste the assessee's PAN/full name into a public tool — anonymise. Verify limitation dates yourself.

### B3 · AIS / 26AS vs. books reconciliation
**Use case:** Explain mismatches between AIS/Form 26AS and the books.

```
You are a CA reconciling Form 26AS / AIS with the books for [ASSESSEE], AY [YEAR].
26AS/AIS shows: [PASTE ENTRIES]. Books show: [PASTE ENTRIES].
Identify each mismatch, the likely reason (timing, TDS not booked, income reported by deductor but not received, double-count, wrong PAN), and the action to resolve it. Output a reconciliation table with a "treatment in return" column.
```
**What you get:** A reconciliation table with causes and treatment.
**Time saved:** 30–90 minutes.
**Quality tips & caveats:** Claude reasons about *why* lines differ; do the figure-matching in a spreadsheet and verify TDS credits on the portal.

### B4 · TDS default & applicability analysis
**Use case:** Determine correct TDS section, rate and exposure.

```
You are a CA advising on TDS. Transaction: [NATURE OF PAYMENT], to [RESIDENT/NON-RESIDENT], amount ₹[X], payer is [ENTITY TYPE]. PAN available: [Y/N]. Lower-deduction certificate: [Y/N].
Tell me: the applicable TDS section, the correct rate, the threshold, the timing of deduction, and the consequences of short/non-deduction (interest u/s 201, disallowance u/s 40(a)). If non-resident, note any DTAA/Section 195 considerations. Show your reasoning and flag what to verify.
```
**What you get:** A TDS determination note with exposure and next steps.
**Time saved:** 20–45 minutes.
**Quality tips & caveats:** Rates and thresholds change annually — confirm against the current Act. For non-residents, get the TRC/Form 10F position from the file.

### B5 · Advance-tax & capital-gains planning
**Use case:** Plan advance-tax instalments or structure a capital-gains transaction.

```
You are a CA advising [ASSESSEE] for FY [YEAR]. [Estimated income by head / details of the asset being sold: type, cost, indexation year, sale value, holding period].
Compute the indicative tax/capital-gains position, the advance-tax instalment schedule with due dates, and the exemptions available (e.g. 54/54F/54EC) with their conditions and timelines. Present as a clear plan with dates and amounts, and list the documents/actions needed to claim each exemption. Note that I will verify all rates.
```
**What you get:** An indicative computation, instalment plan and exemption roadmap.
**Time saved:** 45–90 minutes.
**Quality tips & caveats:** Treat figures as indicative; re-verify indexation, rates and exemption limits before advising the client.

---

## C. Indirect Tax — GST

### C1 · GSTR-3B vs. 2B vs. books reconciliation logic
**Use case:** Make sense of ITC and output-tax mismatches.

```
You are a CA reconciling GST for [CLIENT], GSTIN [MASKED], for [PERIOD].
Data: GSTR-3B [VALUES], GSTR-2B [VALUES], books [VALUES], GSTR-1 [VALUES].
Identify mismatches across output tax and ITC. For each, give the likely cause (supplier filed late, RCM, ineligible/blocked credit u/s 17(5), timing, amendment) and the corrective action (claim, reverse, follow up with supplier, report in next return). Output a reconciliation table with an "action + section/rule" column and a short summary of net impact.
```
**What you get:** A cause-and-action reconciliation table with net GST impact.
**Time saved:** 1–2 hours.
**Quality tips & caveats:** Pairs with `cae/backend/app/engines/gst_engine.py`. Do the numeric matching in your tool; use Claude for the *why* and the treatment.

### C2 · ITC eligibility & RCM analysis
**Use case:** Decide if a credit is eligible and whether RCM applies.

```
You are a CA advising on GST input tax credit. Expense/transaction: [DESCRIPTION], supplier type: [REGISTERED/UNREGISTERED/IMPORT], amount ₹[X], used for [BUSINESS PURPOSE].
Tell me: is ITC eligible or blocked under Section 17(5)? Does RCM apply (and under which notification/category)? What conditions under Section 16 must be met? Give a clear yes/no with reasoning and the section/rule. Flag documentation I must retain.
```
**What you get:** A clear eligibility/RCM determination with reasoning.
**Time saved:** 15–40 minutes.
**Quality tips & caveats:** Verify the blocked-credit list and RCM notifications against current CBIC material.

### C3 · Reply to GST notice (ASMT-10 / DRC-01 / scrutiny)
**Use case:** Draft a reply to a GST departmental notice.

```
You are a CA handling GST litigation. Notice: [ASMT-10 / DRC-01A / DRC-01], period [X], allegation: [SUMMARISE, e.g. ITC MISMATCH, TURNOVER UNDER-REPORTING].
Actual position/explanation: [YOUR FACTS + EVIDENCE]. Draft a formal point-wise reply: restate each allegation, give the factual + legal response with CGST/SGST Act sections and rules, and list annexures. Keep it under [LENGTH]. Mark weak points and suggest a fallback position.
```
**What you get:** A point-wise, annexure-backed reply.
**Time saved:** 1.5–3 hours.
**Quality tips & caveats:** Anonymise the GSTIN/name. Verify section references and limitation/response deadlines.

### C4 · HSN/SAC classification & rate reasoning
**Use case:** Justify a classification and rate.

```
You are a CA advising on GST classification. Product/service: [DETAILED DESCRIPTION, COMPOSITION, USE].
Suggest the most appropriate HSN/SAC, the GST rate, and the reasoning (rules of interpretation, relevant chapter notes, any AAR positions you are certain about). Flag classification risk and any alternative the department might argue.
```
**What you get:** A reasoned classification note with risk flags.
**Time saved:** 30–60 minutes.
**Quality tips & caveats:** Classification is litigation-prone — verify against the tariff and confirm any AAR/case before citing.

### C5 · GSTR-9 / 9C preparation notes
**Use case:** Build the working notes for the annual return and reconciliation statement.

```
You are a CA preparing GSTR-9 and GSTR-9C for [CLIENT], FY [YEAR], turnover ₹[X] cr.
Inputs: [ANNUAL 3B/1 SUMMARY, BOOKS TURNOVER, ITC SUMMARY].
Produce a table-by-table preparation checklist mapping each GSTR-9 table to its data source, list the common reconciling items between books and returns for 9C, and flag the items most likely to attract notice. Note where auditor reconciliation remarks are typically needed.
```
**What you get:** A table-wise prep checklist and 9C reconciliation map.
**Time saved:** 1–2 hours.
**Quality tips & caveats:** Confirm current-year table structure and thresholds; figures must tie to your filed returns.

---

## D. Companies Act 2013 / ROC & Secretarial

### D1 · Draft board / AGM resolutions
**Use case:** Produce a resolution quickly and correctly.

```
You are a company-secretary-grade drafter under the Companies Act, 2013. Draft a [BOARD / SPECIAL / ORDINARY] resolution for [COMPANY], a [PRIVATE/PUBLIC] company, for the purpose of [E.G. APPOINTMENT OF AUDITOR / BORROWING u/s 180 / RELATED-PARTY TXN u/s 188 / DIRECTOR APPOINTMENT].
Include the correct recital, the operative resolution, and any "RESOLVED FURTHER" authorisations. Note the section/rule, the type of meeting required, and the related ROC form + deadline. Use formal Indian corporate drafting style.
```
**What you get:** A ready resolution plus the filing form and deadline.
**Time saved:** 20–40 minutes each.
**Quality tips & caveats:** Confirm the section, e-form (e.g. MGT-14, DIR-12) and timeline against current MCA rules.

### D2 · Director's Report & AOC-4 / MGT-7 narratives
**Use case:** Draft the board's report and statutory narratives.

```
You are a CA drafting the Director's Report under Section 134 for [COMPANY], FY [YEAR].
Inputs: [FINANCIAL HIGHLIGHTS, DIVIDEND, RESERVES, KEY EVENTS, CHANGES IN DIRECTORS, LOANS/INVESTMENTS, RPTs].
Draft the report covering all mandatory disclosures under Section 134(3) and the Companies (Accounts) Rules, including the directors' responsibility statement. Use headings per the statutory list and insert [PLACEHOLDER] where I must add data. List the annexures required (e.g. AOC-2, MGT-9 extract if applicable).
```
**What you get:** A structured, disclosure-complete Director's Report skeleton.
**Time saved:** 1–2 hours.
**Quality tips & caveats:** Verify the current list of mandatory disclosures and which annexures still apply.

### D3 · Contract / agreement review (plain-English + risk)
**Use case:** Review a commercial contract for a client.

```
You are a CA/legal-savvy advisor reviewing a contract for [CLIENT]. Here is the agreement: [PASTE OR SUMMARISE].
Give me: (1) a plain-English summary of key terms, (2) the financial and tax implications (GST, TDS, stamp duty), (3) risky or one-sided clauses with suggested redlines, (4) missing protections, and (5) a short list of questions to raise with the counterparty. Output as a structured memo.
```
**What you get:** A reviewer's memo with redlines and tax flags.
**Time saved:** 1–3 hours.
**Quality tips & caveats:** For enforceability questions, involve a lawyer; AI is not a substitute for legal opinion.

### D4 · Statutory register & compliance checklist
**Use case:** Confirm ROC/secretarial housekeeping for a company.

```
You are a CA. For a [PRIVATE/PUBLIC] company, FY [YEAR], produce a Companies Act, 2013 compliance checklist covering: statutory registers to maintain, board/AGM meeting requirements and minimum numbers, annual filings with forms and due dates (AOC-4, MGT-7/7A, DIR-3 KYC, etc.), and event-based filings. Format as a table with "form / section / due date / status" columns I can fill in.
```
**What you get:** A fill-in compliance tracker.
**Time saved:** 45–90 minutes.
**Quality tips & caveats:** Cross-check against **LexComply** and current MCA due dates — these shift.

---

## E. Labour & Other Statutory Compliance

### E1 · Applicability analysis across labour laws
**Use case:** Determine which labour laws apply to a client and the resulting obligations.

```
You are a CA advising on Indian labour-law compliance. Establishment: [TYPE], [STATE], [NUMBER] employees, [HAS FACTORY? FACTORY WORKERS], wage range [X], started [DATE].
Tell me which laws apply (EPF, ESI, Gratuity, Bonus, POSH, Shops & Establishments, Professional Tax, Labour Welfare Fund, Contract Labour) with the trigger threshold for each, and for each applicable law list the registration, the periodic returns with due dates, the contribution rates, and the penalties for default. Output as a table.
```
**What you get:** An applicability + obligations matrix.
**Time saved:** 1–2 hours.
**Quality tips & caveats:** Mirrors your **LexComply** `laws.js` logic (e.g. EPF ≥ 20, Gratuity ≥ 10) — use LexComply as the authoritative source and have Claude turn it into client-ready narrative. State-specific laws vary; verify locally.

### E2 · Draft notice / calendar for a specific law
**Use case:** Produce a compliance calendar or a notice (e.g. POSH constitution, gratuity computation).

```
You are a CA. For [LAW, e.g. PAYMENT OF GRATUITY ACT 1972], produce [a 12-month compliance calendar / a gratuity computation for an employee with details: last drawn salary ₹[X], years of service [Y] / a POSH Internal Committee constitution note].
Include exact due dates, forms, authorities, and penalties. Format clearly for the client.
```
**What you get:** A calendar/notice/computation ready to share.
**Time saved:** 30–60 minutes.
**Quality tips & caveats:** Verify formulae (e.g. gratuity = 15/26 × last salary × years) and caps against the Act.

---

## F. Financial Reporting & Accounting

### F1 · Ind AS / AS application memo
**Use case:** Document the accounting treatment for a transaction.

```
You are a CA determining the accounting treatment under [Ind AS / AS] for [CLIENT].
Transaction: [DESCRIBE — e.g. multi-element revenue contract / lease / ECL on receivables / business combination].
Identify the applicable standard, the recognition & measurement principle, the journal entries, the disclosures required, and any judgement areas. Cite the standard and paragraph. Output as a memo with a worked example using my figures: [FIGURES].
```
**What you get:** A standard-referenced accounting memo with entries and disclosures.
**Time saved:** 1–2 hours.
**Quality tips & caveats:** Verify the standard paragraph and confirm whether Ind AS or AS applies to the entity.

### F2 · Schedule III formatting & notes-to-accounts drafting
**Use case:** Draft notes and ensure Schedule III presentation.

```
You are a CA preparing financial statements under Schedule III, Division [I/II/III] for [CLIENT], FY [YEAR].
Here is the trial balance / grouping: [PASTE]. Draft the notes to accounts for [SPECIFIC ITEMS, e.g. PPE, BORROWINGS, RELATED PARTIES, AGEING SCHEDULES], in Schedule III format with prior-year columns as [PLACEHOLDER], and list the additional regulatory disclosures (ratios, ageing, CSR, etc.) now required.
```
**What you get:** Draft notes in the correct presentation format.
**Time saved:** 1–3 hours.
**Quality tips & caveats:** Confirm the current Schedule III disclosure list (ageing schedules, ratios, struck-off companies, etc.) — it has expanded in recent years.

### F3 · Ratio analysis & MD&A commentary
**Use case:** Turn financials into narrative analysis.

```
You are a CA/financial analyst. Here are two years of financials for [CLIENT]: [PASTE P&L + BALANCE SHEET]. 
Compute the key ratios (liquidity, solvency, profitability, efficiency), explain the year-on-year movement in plain English, flag concerns and positives, and draft a short management-discussion-style commentary. Present ratios as a table followed by the narrative.
```
**What you get:** A ratio table plus written commentary.
**Time saved:** 1–2 hours.
**Quality tips & caveats:** Check the ratio formulae match your figures; commentary is a draft for your review.

---

## G. vCFO / FP&A

### G1 · Monthly MIS commentary
**Use case:** Write the narrative for a monthly MIS pack.

```
You are the virtual CFO for [COMPANY], a [SECTOR] business. Here is this month's data: revenue ₹[X] (budget ₹[Y]), gross margin [%], EBITDA ₹[Z], cash balance ₹[C], key variances [LIST].
Write a crisp one-page MIS commentary for the founder/board: performance vs budget, what drove the variances, cash position and runway, three risks, and three recommended actions. Use clear business language, not accounting jargon.
```
**What you get:** Board-ready MIS narrative.
**Time saved:** 45–90 minutes per month, per client.
**Quality tips & caveats:** Feed accurate figures; the value is the *interpretation*, which you should sanity-check.

### G2 · 13-week cash-flow forecast structure
**Use case:** Build or review a short-term cash forecast.

```
You are a vCFO building a 13-week rolling cash-flow forecast for [COMPANY].
Inputs: opening cash ₹[X], weekly receipts assumptions [DETAIL], payroll ₹[X] on [DATES], statutory dues [GST/TDS/PF DATES & AMOUNTS], loan EMIs [DETAIL], capex [DETAIL].
Lay out the forecast structure week-by-week, list the line items, show where the cash pinch points fall, and recommend actions (collection focus, payment deferral, drawdown) for the tightest weeks. Output as a table plus a short action note.
```
**What you get:** A forecast layout with pinch-point analysis.
**Time saved:** 1–2 hours.
**Quality tips & caveats:** Use Claude for structure and reasoning; keep the live model in a spreadsheet for accuracy.

### G3 · Budget vs. actual variance analysis
**Use case:** Explain budget variances for management.

```
You are a vCFO. Here is the budget vs. actual for [COMPANY], [PERIOD]: [PASTE TABLE].
For each significant variance (> [THRESHOLD]%), state whether it is favourable/adverse, the likely driver, whether it is timing or permanent, and the recommended management response. Summarise the overall story in three sentences at the top.
```
**What you get:** A variance bridge in words plus an executive summary.
**Time saved:** 45–90 minutes.
**Quality tips & caveats:** Confirm drivers with operational data before presenting as fact.

### G4 · Board deck / investor-update narrative
**Use case:** Draft the board pack or monthly investor update.

```
You are a vCFO preparing the [BOARD DECK / MONTHLY INVESTOR UPDATE] for [COMPANY], [PERIOD].
Inputs: [KEY METRICS, WINS, CHALLENGES, FINANCIALS, ASKS].
Draft the narrative slide-by-slide: highlights, financial performance, KPIs, cash & runway, risks & mitigation, and asks. Keep each slide to tight bullets a founder can present. Suggest one chart per section.
```
**What you get:** A slide-by-slide narrative outline.
**Time saved:** 1.5–3 hours.
**Quality tips & caveats:** Keep confidential metrics anonymised if using a public tool.

### G5 · Fundraising support — model, cap table & dilution explainer
**Use case:** Prepare for a raise and explain the mechanics to founders.

```
You are a vCFO advising [COMPANY] on a [SEED/SERIES A] round of ₹[X] at a [PRE/POST] valuation of ₹[Y].
Existing cap table: [PASTE]. Explain in plain English: the post-round cap table and each shareholder's dilution, the impact of an [ESOP POOL] top-up, how a [SAFE/CCPS/CONVERTIBLE] would convert, and the key terms (liquidation preference, anti-dilution) a founder must understand. Show the cap table as a before/after table.
```
**What you get:** A before/after cap table and a founder-friendly explainer.
**Time saved:** 1–3 hours.
**Quality tips & caveats:** Double-check the dilution maths; instrument terms (CCPS/SAFE) have specific Indian regulatory and tax angles to verify.

---

## H. Family Office & Private Wealth

### H1 · Family constitution / charter
**Use case:** Draft a governance charter for a business family.

```
You are an advisor to a [GENERATION]-generation Indian business family with [BUSINESS + INVESTMENT ASSETS]. 
Draft a family constitution covering: family values & vision, ownership vs. management separation, the family council and its role, entry/exit of family members into the business, dividend & reinvestment policy, conflict-resolution mechanism, and a framework for next-gen induction. Use clear, non-legal language as a starting charter the family will refine with counsel. Insert [PLACEHOLDER] where family-specific choices are needed.
```
**What you get:** A structured first-draft charter for facilitation.
**Time saved:** 3–6 hours.
**Quality tips & caveats:** This is a facilitation starting point — final governance/legal structuring needs lawyers and family buy-in.

### H2 · Succession & estate-planning options memo
**Use case:** Lay out succession structuring choices.

```
You are a CA advising on succession and estate planning for [FAMILY HEAD], with assets: [BUSINESS STAKE, REAL ESTATE, FINANCIAL ASSETS, FOREIGN ASSETS]. Family: [SPOUSE, CHILDREN, DEPENDANTS].
Lay out the structuring options — will, private family trust, HUF, gifting — with the pros/cons, the tax implications (no estate duty currently, but income clubbing, capital gains on transfer, stamp duty), control and succession outcomes for each. Recommend a combination and list the next steps and documents. Present as a comparison table + recommendation.
```
**What you get:** An options comparison with a recommended structure.
**Time saved:** 2–4 hours.
**Quality tips & caveats:** High-stakes — validate trust/tax positions with specialists; verify current law (estate duty, clubbing, trust taxation).

### H3 · Investment Policy Statement (IPS)
**Use case:** Create an IPS for the family's portfolio.

```
You are a family-office advisor drafting an Investment Policy Statement for [FAMILY/ENTITY].
Inputs: total investable corpus ₹[X], objectives [GROWTH/PRESERVATION/INCOME], risk tolerance [LOW/MED/HIGH], time horizon, liquidity needs, constraints [E.G. NO TOBACCO, ESG, REAL-ESTATE HEAVY ALREADY].
Draft an IPS covering objectives, target asset allocation with ranges, permitted instruments, rebalancing policy, liquidity reserve, and review frequency. Present allocation as a table.
```
**What you get:** A board-quality IPS document.
**Time saved:** 2–3 hours.
**Quality tips & caveats:** Allocation suggestions are illustrative; align with a registered investment adviser where regulated advice is involved.

### H4 · Consolidated portfolio review & asset-allocation commentary
**Use case:** Turn a multi-asset portfolio into a review note.

```
You are a family-office CA reviewing a consolidated portfolio for [FAMILY], as at [DATE].
Holdings: [EQUITY ₹X, MF ₹X, DEBT ₹X, REAL ESTATE ₹X, GOLD ₹X, PMS/AIF ₹X, FOREIGN ₹X].
Produce: current allocation vs. the target [IPS allocation], concentration/risk flags, performance commentary, tax-efficiency observations (LTCG harvesting, exit timing), and rebalancing recommendations. Output an allocation table + commentary + action list.
```
**What you get:** A consolidated review with rebalancing actions.
**Time saved:** 1.5–3 hours.
**Quality tips & caveats:** Verify valuations and current capital-gains rules before acting on tax suggestions.

### H5 · Philanthropy / CSR structuring & next-gen education
**Use case:** Structure giving or build a next-gen finance primer.

```
You are a family-office advisor. [Design a philanthropy structure for the family — options: donation, Section 8 company, charitable trust, CSR alignment — with tax (80G/12A) and governance implications] OR [create a 6-module financial-literacy curriculum for the family's next generation covering reading financials, investing basics, the family business, taxes and wealth stewardship].
Present clearly with steps/modules and key points.
```
**What you get:** A giving structure or a ready training curriculum.
**Time saved:** 2–4 hours.
**Quality tips & caveats:** Confirm 80G/12A and CSR rules; registration processes change.

---

## I. Transaction Advisory / M&A / Valuation / Due Diligence

### I1 · Financial due-diligence request list & red-flag memo
**Use case:** Run buy-side or sell-side financial DD.

```
You are a CA leading financial due diligence on [TARGET], a [SECTOR] company, turnover ₹[X] cr, for a potential [ACQUISITION/INVESTMENT].
First, produce a comprehensive DD information-request list grouped by area (quality of earnings, working capital, debt & debt-like items, tax, related parties, contingent liabilities, statutory compliance).
Then, given these preliminary findings: [PASTE WHAT YOU'VE SEEN], draft a red-flag memo highlighting deal risks, their potential financial impact, and recommended further work or deal protections (price adjustment, indemnity, escrow).
```
**What you get:** A DD request list and a red-flag memo.
**Time saved:** 2–4 hours.
**Quality tips & caveats:** Quantify impacts from actual data; AI structures the analysis, you substantiate it.

### I2 · Valuation approach note
**Use case:** Document a valuation methodology and assumptions.

```
You are a CA/registered valuer preparing a valuation note for [COMPANY/ASSET], purpose [E.G. FUNDRAISE / FEMA / 56(2)(x) / SLUMP-SUM SALE].
Inputs: [FINANCIALS, GROWTH, MARGINS, COMPARABLES, DISCOUNT RATE BASIS].
Explain which approach(es) apply (DCF, comparable companies, NAV), the key assumptions and how I'd justify each, a worked DCF skeleton with my figures, and the sensitivities to disclose. Note the regulatory valuation requirement for the stated purpose. Present assumptions in a table.
```
**What you get:** A methodology note with a worked skeleton and sensitivities.
**Time saved:** 1.5–3 hours.
**Quality tips & caveats:** Statutory valuations (FEMA, Income Tax Rule 11UA) have prescribed methods — verify and ensure a registered valuer signs where required.

### I3 · SPA / term-sheet plain-English review
**Use case:** Decode deal documents for a client.

```
You are a CA advising a [BUYER/SELLER/FOUNDER] on a [TERM SHEET / SHARE PURCHASE AGREEMENT]. Document: [PASTE OR SUMMARISE].
Summarise the commercial terms in plain English, flag clauses with financial/tax consequences (consideration mechanism, earn-out, indemnity caps, tax indemnities, MAC clause), identify one-sided terms, and list the negotiation points I should raise. Output a structured memo.
```
**What you get:** A plain-English review with negotiation points.
**Time saved:** 1–3 hours.
**Quality tips & caveats:** Loop in legal counsel for binding interpretation.

---

## J. FEMA & Cross-border

### J1 · Remittance & 15CA/CB determination
**Use case:** Decide the correct treatment for a foreign remittance.

```
You are a CA advising on a foreign remittance. Payer: [RESIDENT ENTITY]. Beneficiary: [COUNTRY], nature of payment: [E.G. SOFTWARE / ROYALTY / IMPORT / DIVIDEND / CONSULTANCY], amount [CURRENCY + VALUE].
Determine: whether the income is taxable in India, the withholding rate under the Act vs. the DTAA, whether Form 15CA/15CB is required and which part, the FEMA route/permissibility, and the documents needed (TRC, Form 10F, no-PE declaration). Show reasoning and flag what to verify.
```
**What you get:** A remittance determination with the 15CA/CB position.
**Time saved:** 30–60 minutes.
**Quality tips & caveats:** Verify the DTAA article and rate; non-resident taxation is fact-sensitive.

### J2 · ODI / FDI compliance note
**Use case:** Map the compliance for inbound/outbound investment.

```
You are a CA advising on [INBOUND FDI into / OUTBOUND ODI from] [ENTITY] of [AMOUNT] in [SECTOR/COUNTRY].
Set out: the applicable route (automatic/approval), sectoral caps/conditions, the RBI/FEMA filings with forms and timelines (e.g. FC-GPR, FC-TRS, FLA, APR, Form ODI), pricing-guideline requirements, and the penalties for non-compliance/compounding. Output as a step-by-step compliance checklist.
```
**What you get:** A route-and-filings checklist.
**Time saved:** 1–2 hours.
**Quality tips & caveats:** FEMA forms and sectoral caps change — verify against the current Master Directions.

### J3 · Forex gain/loss & exposure commentary
**Use case:** Explain forex impact for the books or management.

```
You are a CA analysing foreign-exchange gain/(loss) for [CLIENT], [PERIOD].
Data: [FOREIGN-CURRENCY RECEIVABLES/PAYABLES, RATES AT TXN DATE, YEAR-END RATE, REALISED SETTLEMENTS].
Explain the realised vs. unrealised forex gain/loss, the correct accounting treatment under [Ind AS 21 / AS 11], the P&L vs. equity classification, and the tax treatment. Summarise the entity's net forex exposure and suggest a simple hedging consideration.
```
**What you get:** A forex impact note with accounting and tax treatment.
**Time saved:** 45–90 minutes.
**Quality tips & caveats:** Pairs with your **Foreign Gain/(Loss) workbook** — use the workbook for the figures and Claude for the treatment/commentary. Verify the standard's restatement rules.

---

## K. Practice Management & Client Communication

### K1 · Engagement letter / proposal
**Use case:** Issue a scoped engagement letter or pitch.

```
You are a CA drafting an [ENGAGEMENT LETTER / PROPOSAL] for [CLIENT] for [SERVICE: e.g. STATUTORY AUDIT / vCFO RETAINER / GST COMPLIANCE].
Include: scope of work, exclusions, deliverables and timelines, our and the client's responsibilities, fee and billing terms, and standard clauses (confidentiality, limitation of liability, dispute resolution). Use professional Indian CA-firm language. Insert [PLACEHOLDER] for fees and dates.
```
**What you get:** A ready-to-edit engagement letter/proposal.
**Time saved:** 45–90 minutes.
**Quality tips & caveats:** Align scope and liability clauses with ICAI norms and your firm's standard terms.

### K2 · Client-friendly explainer of complex law
**Use case:** Explain a notice, a budget change or a new compliance to a non-finance client.

```
You are a CA explaining [TOPIC, e.g. THE NEW TDS ON E-COMMERCE / WHY THEY GOT A 143(1) INTIMATION / THE NEW GST RULE] to a business owner with no finance background.
Explain in simple language: what it is, why it matters to them, what they must do, by when, and what happens if they don't. Keep it under [LENGTH], friendly and reassuring. End with a clear next step.
```
**What you get:** A plain-language client explainer.
**Time saved:** 20–40 minutes.
**Quality tips & caveats:** Verify the technical facts before sending; simplicity must not introduce error.

### K3 · Internal SOP / training material
**Use case:** Standardise a recurring process for your team/articles.

```
You are a CA-firm partner documenting a standard operating procedure for [PROCESS, e.g. MONTHLY GST FILING / AUDIT FILE REVIEW / NEW-CLIENT ONBOARDING].
Write a step-by-step SOP with: responsibilities, the sequence of steps, the documents/tools used, the review checkpoints, and the common errors to avoid. Format so a first-year article can follow it.
```
**What you get:** A team-ready SOP.
**Time saved:** 1–2 hours.
**Quality tips & caveats:** Tailor to your actual tools (LexComply, CAE, Tally) and review controls.

### K4 · Meeting minutes & summary generation
**Use case:** Turn rough notes or a transcript into minutes/action points.

```
You are a CA assistant. Here are my rough notes / the transcript from a [BOARD MEETING / CLIENT CALL]: [PASTE].
Produce: formal minutes (or a structured summary), a decisions list, and an action-item table with owner and due date. Keep it factual and concise.
```
**What you get:** Clean minutes plus an action tracker.
**Time saved:** 30–60 minutes.
**Quality tips & caveats:** Confirm decisions and figures with attendees before circulating.

---

## Ways of working — beyond single prompts

Single prompts are the start. The bigger gains come from **repeatable workflows** and **good habits**.

**1. Recurring monthly workflows.** Build a saved prompt chain for the work you do every month:
- *Monthly close:* trial-balance review prompt → MIS commentary (G1) → variance analysis (G3) → board narrative (G4).
- *GST routine:* reconciliation logic (C1) → exception review → notice replies if any (C3).
- *Audit file review:* CAE exceptions → review notes (A2) → management letter (A3).

**2. Work with spreadsheets and documents, not just text.** Paste CSV/ledger extracts and ask Claude to reason over them (find outliers, explain mismatches, draft commentary). Keep the **authoritative calculations in your own tools** — the **CAE** for audit analytics, **LexComply** for applicability, the **forex workbook** for currency figures — and use Claude to interpret and write up the results. AI complements the signed work; it does not replace it.

**3. Build a house-style snippet bank.** Save your firm's best prompts (engagement letter, MIS, notice reply) with your tone and standard clauses baked in. Over time this becomes a team asset that makes every article's first draft consistent.

**4. Always end high-stakes prompts with the verification instruction** from Section 3. It measurably reduces fabricated sections and citations.

**5. Anonymise by default.** Make masking client identifiers a habit, not an afterthought — replace names with roles, mask PAN/GSTIN/Aadhaar, and keep genuinely sensitive engagements on an enterprise/no-training deployment.

---

## Quick-reference index

| When you need to… | Go to |
|---|---|
| Start a statutory audit | A1 |
| Write up audit exceptions / management letter | A2, A3 |
| Document going concern | A4 |
| Review a tax computation | B1 |
| Reply to an income-tax notice | B2 |
| Reconcile 26AS/AIS with books | B3 |
| Decide TDS section/rate/exposure | B4 |
| Plan advance tax / capital gains | B5 |
| Reconcile GST 3B/2B/books | C1 |
| Check ITC eligibility / RCM | C2 |
| Reply to a GST notice | C3 |
| Classify HSN/SAC & rate | C4 |
| Prepare GSTR-9/9C | C5 |
| Draft a resolution | D1 |
| Draft Director's Report | D2 |
| Review a contract | D3 |
| ROC compliance checklist | D4 |
| Labour-law applicability | E1 |
| Accounting treatment memo | F1 |
| Schedule III notes | F2 |
| Ratio analysis / commentary | F3 |
| Monthly MIS commentary | G1 |
| 13-week cash forecast | G2 |
| Budget vs. actual | G3 |
| Board deck / investor update | G4 |
| Fundraise / cap table / dilution | G5 |
| Family constitution | H1 |
| Succession & estate options | H2 |
| Investment Policy Statement | H3 |
| Portfolio review | H4 |
| Philanthropy / next-gen | H5 |
| Financial due diligence | I1 |
| Valuation note | I2 |
| SPA / term-sheet review | I3 |
| Foreign remittance / 15CA-CB | J1 |
| ODI / FDI compliance | J2 |
| Forex gain/loss commentary | J3 |
| Engagement letter / proposal | K1 |
| Explain law to a client | K2 |
| SOP / training material | K3 |
| Minutes & action points | K4 |

---

*Disclaimer: This library is a productivity aid. Every statutory reference, rate, threshold and due date must be independently verified against current law (Acts, Finance Act, CBDT/CBIC circulars, MCA/RBI/ICAI material) before reliance. AI output is a draft input to professional work — the chartered accountant remains responsible for all judgement, certification and filings.*
