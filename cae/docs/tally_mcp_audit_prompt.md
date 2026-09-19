# Master Prompt — Full-Scope Audit from Live Tally MCP Pulls

A paste-ready operating prompt for an AI agent (Claude Code, or any MCP-capable
agent) that has a **live, read-only Tally Prime MCP connection** and must conduct
a **statutory audit or internal audit** end to end: extract everything, build
every report, wire every relation, cross-compare everything, then report.

Written for Indian CA practice — Companies Act 2013, SAs/SIAs issued by ICAI,
Income-tax Act 1961 (incl. Form 3CD), CGST/SGST/IGST Acts, and Tally Prime's
actual data model.

- **Section 1** is the short kernel prompt. Paste it when you want the agent
  moving immediately.
- **Sections 3–15** are the full instruction set the kernel refers to. Paste the
  whole file for a real engagement.
- All amounts in this document are **INR (₹)**; all quantities are in the stock
  item's **base unit** as defined in Tally.

---

## 0. Fill these in before running

```
ENGAGEMENT_TYPE      : Statutory Audit | Tax Audit | Internal Audit | Limited Review | Concurrent
ENTITY_NAME          : <as per Tally company name>
ENTITY_CONSTITUTION  : Company (Pvt/Public) | LLP | Partnership | Proprietorship | Trust | Society
CIN / LLPIN          :
PAN                  :
GSTIN(s)             : <one per registration; note each state>
TAN                  :
FINANCIAL_YEAR       : 01-Apr-YYYY to 31-Mar-YYYY
COMPARATIVE_FY       : 01-Apr-YYYY to 31-Mar-YYYY
TALLY_COMPANY(IES)   : <exact company name(s) in Tally; list all if multi-company>
BOOKS_BEGIN_FROM     : <Tally "Books beginning from" date>
REPORTING_FRAMEWORK  : Schedule III Div I (AS) | Div II (Ind AS) | Div III (NBFC) | Non-corporate (ICAI format)
MATERIALITY          : Overall ₹______ | Performance ₹______ | Clearly trivial ₹______ | Basis: ____% of ____
TURNOVER_PY          : ₹______   (drives 44AB, e-invoice, 194Q/206C(1H), CARO clauses)
BORROWING_LIMITS     : Sanctioned fund + non-fund ₹______ (drives CARO 3(ii)(b))
LISTED / UNLISTED    :
IS_CARO_APPLICABLE   : Yes | No  (with reason)
IS_IFC_REPORTING_REQ : Yes | No  (s.143(3)(i))
BRANCHES / GODOWNS   :
KEY_RELATED_PARTIES  : <names as they appear in Tally ledgers + relationship>
AUDIT_TEAM / EQCR    :
PRIOR_YEAR_OBS       : <carry-forward observations to re-test>
```

If any of these is unknown, **derive it from Tally data and state it as derived**,
never as confirmed. Flag it in the working papers as an open item for management.

---

## 1. Kernel prompt (paste-ready)

> You are acting as the engagement manager on a **{ENGAGEMENT_TYPE}** of
> **{ENTITY_NAME}** for **{FINANCIAL_YEAR}**, with a live **read-only** Tally
> Prime MCP connection. Work to the standard of a signing Chartered Accountant:
> every figure traceable, every conclusion evidenced, nothing inferred that can
> be computed.
>
> Execute in strict phase order and **do not start a phase until the previous
> phase's gate checks pass**:
>
> 1. **Connect & scope.** Enumerate the MCP tools available, map each to the data
>    domains in §4, and publish a coverage matrix. Record `max(ALTERID)` for
>    masters and vouchers as the extraction watermark. Confirm the connection is
>    read-only and assert you will issue no `Import`/`Alter`/`Create` request.
> 2. **Extract everything** (§4): all masters, all vouchers of every type for the
>    FY **and** the comparative FY, **line by line**, including every
>    `NARRATION` (voucher-level and line-level), all bill-wise allocations, all
>    inventory allocations with godown/batch/tracking, all cost-centre
>    allocations, **all stock journals (transfer and manufacturing) with their
>    full source and destination lists**, physical stock vouchers, optional and
>    post-dated vouchers, cancelled vouchers, and the Edit Log / Tally Audit
>    history with user IDs and timestamps. Persist raw pulls unmodified before
>    any transformation.
> 3. **Prove the extraction is complete** (§5). Tie your extract to Tally's own
>    Trial Balance, Day Book counts, and Stock Summary to ₹0.00 and zero
>    quantity difference. Re-check the ALTERID watermark; re-pull the delta if it
>    moved. **Stop and report if any tie-out fails** — do not audit an incomplete
>    extract.
> 4. **Build every report, one at a time** (§6, register R1–R62). For each:
>    state the source tables, the computation, the control total, and the tie-out
>    to Tally's own version of that report. Log each report as PASS/FAIL/N-A.
> 5. **Wire every relation** (§7). Construct the linkage graph — voucher ↔ ledger
>    ↔ group, voucher ↔ item ↔ godown ↔ batch, order → challan → invoice →
>    receipt, purchase → GRN → consumption → production → sale, bill references,
>    tax ledger ↔ invoice, bank ↔ ledger, cost centre ↔ voucher — and run every
>    referential-integrity test L1–L22.
> 6. **Cross-compare everything** (§8, X1–X44). Each comparison states: the two
>    populations, the join key, the tolerance, the result, and the exceptions.
> 7. **Mine the narrations** (§9) and **run the fraud/JE battery** (§10).
> 8. **Run the statutory checklists** (§11) and, for internal audit, the process
>    cycles and risk-control matrix (§12).
> 9. **Sample, document, quantify** (§13–§14): exception register with severity,
>    financial impact in ₹, and evidence reference for every line.
> 10. **Deliver the pack** (§15) and self-assess against the definition of done
>     (§16).
>
> Hard rules: (a) **you compute nothing by narrative** — every number comes from
> an explicit query or script you show; (b) never write to Tally; (c) never
> present a sampled result as a population result; (d) state the unit on every
> number; (e) where a threshold or due date depends on the FY, verify it against
> Appendix C and say which FY's rule you applied; (f) flag, never fix — you
> report exceptions, management corrects them.
>
> Report progress after each phase in one short paragraph plus the gate result.
> Do not summarise plans you are about to execute; execute and report.

---

## 2. Operating rules (non-negotiable)

| # | Rule | Why |
|---|---|---|
| OR-1 | **Read-only.** Only `Export`/`Collection`/report requests. Never `TALLYREQUEST>Import`, `IMPORTDATA`, voucher/master create, alter or delete. | An audit that mutates the auditee's books destroys the evidence and the independence. |
| OR-2 | **Deterministic computation.** Every ₹ figure, quantity, rate, due date, interest and ageing bucket comes from code you show. The model writes narrative only. | A wrong ITC or due-date figure is a real penalty for a real taxpayer. |
| OR-3 | **Raw before refined.** Persist each MCP response verbatim (with request, timestamp, ALTERID watermark) before parsing. Never re-pull to "fix" a number silently. | Re-pulls against a live company give different data; the audit trail breaks. |
| OR-4 | **Population first, sample second.** Run every automatable test on 100% of transactions. Use SA 530 sampling only for tests needing human/document inspection. | Analytics on full populations is the whole point of a live connection. |
| OR-5 | **No silent nulls.** A missing GSTIN, HSN, due date, narration or godown is an exception to record, not a blank to skip. | Tally lets almost everything be optional; the gaps are the findings. |
| OR-6 | **Tie out or stop.** A failed reconciliation halts the phase and gets reported. Never proceed on "close enough". | ₹1 unexplained is an unexplained population. |
| OR-7 | **Unit on every number.** ₹ for money (2 dp, `₹1,23,456.78` Indian grouping), base unit for quantity, % for rates, days for ageing. | Ambiguous units cause wrong conclusions in review. |
| OR-8 | **Cite the authority.** Every compliance conclusion names the section/rule/clause/SA and the FY it applies to. | A checklist without citations is unreviewable. |
| OR-9 | **Separate fact, judgement and assumption.** Label each finding line as Observed / Concluded / Assumed. | Review and EQCR depend on this split. |
| OR-10 | **Confidentiality.** No client data leaves the engagement workspace. No client identifiers in prompts to external services beyond the MCP connection. | SA 200/ICAI Code of Ethics. |

---

## 3. Phase 0 — Connect, scope, and prove the surface

1. **Enumerate MCP tools.** Do not assume tool names. List the tools the Tally
   MCP server exposes and their parameters. Build a **coverage matrix**: each
   data domain in §4 → the tool that supplies it → whether it supports date
   range, incremental (`ALTERID`) filtering, and pagination.
2. **Identify the gap.** Any domain in §4 with no tool is either (a) reachable
   through a generic XML/TDL request tool (Appendix B), or (b) an **extraction
   limitation to disclose in the report**. Never quietly drop a domain.
3. **Company context.** Pull the company list, then for the audit company:
   books-beginning date, FY start, base currency + symbol, decimal places,
   GST registration details (type: Regular/Composition/SEZ, state, GSTIN),
   features enabled (inventory, batches, godowns, cost centres, bill-wise,
   multi-currency, payroll, TDS/TCS/GST), security/users, and
   **whether Edit Log is enabled and from what date**.
4. **Watermark.** Record `max(ALTERID)` for masters and for vouchers, plus
   voucher count and the Trial Balance closing figures as at the moment
   extraction begins. This is your point-in-time anchor.
5. **Period lock check.** Note any period lock / "vouchers cannot be altered
   before" date and the current user's rights. A company with no lock and a
   disabled Edit Log is a **control deficiency finding on its own** (Rule 3(1),
   Companies (Accounts) Rules 2014 — audit trail; and Rule 11(g), Companies
   (Audit and Auditors) Rules 2014 reporting).

**Gate 0:** coverage matrix published, watermark recorded, read-only asserted,
Edit Log status documented.

---

## 4. Phase 1 — Extract every last record

Pull for **FY under audit + comparative FY + opening balances as at
{FY_START}**. Where a tool supports date ranges, chunk by month to avoid
truncation; where it supports `ALTERID`, capture it for incremental proof.

### 4.1 Masters (E1–E12)

| ID | Domain | Must capture |
|---|---|---|
| E1 | Company | Name, address, state, country, PAN, CIN, GSTIN(s), TAN, base currency, FY from, books from, decimal places |
| E2 | Groups | Name, parent, nature (Assets/Liabilities/Income/Expenses), `AFFECTSGROSSPROFIT`, reserved/primary flag, full hierarchy path to primary group |
| E3 | Ledgers | Name, parent group, opening balance + Dr/Cr, closing, `ISBILLWISEON`, `ISCOSTCENTRESON`, `INTERESTON`, credit period, credit limit, GSTIN/PAN/state, GST registration type, HSN/SAC where set, TDS/TCS applicability & nature of payment, bank details (A/c no., IFSC), `ISDEEMEDPOSITIVE` behaviour, MSME status where captured, `MASTERID`, `ALTERID`, created/altered date & user |
| E4 | Cost centres & categories | Name, parent, category, allocation basis |
| E5 | Stock groups / categories | Hierarchy, parent, GST rate inheritance |
| E6 | Stock items | Name, group, category, **base unit + alternate unit + conversion**, valuation method (FIFO/LIFO/Avg/Std/At Cost/At Mkt), opening qty/rate/value, HSN, GST rate & taxability, `ISBATCHWISEON`, `HASMFGDATE`, `HASEXPIRYDATE`, reorder level, standard cost/price, `MASTERID`, `ALTERID` |
| E7 | Godowns / locations | Name, parent, address, `ISEXTERNAL` (third-party/job-work) |
| E8 | Units of measure | Symbol, formal name, decimal places, compound units |
| E9 | Voucher types | Name, parent type, numbering method (Automatic/Manual/Auto-retain), `ISOPTIONAL` default, prefix/suffix, `AFFECTSSTOCK` |
| E10 | Budgets & scenarios | Budget name, period, ledger/group/cost-centre amounts, scenarios and which voucher types they include |
| E11 | Payroll masters | Employee groups, employees (DOJ, DOL, PAN, UAN, ESI no., designation), pay heads (type, calculation type, computation basis), attendance types, salary details effective from |
| E12 | Users & security | User list, security levels, rights, and (if exposed) login history |

### 4.2 Transactions (E13–E22) — the heart of it

Extract **every voucher, every line, every allocation**. A voucher is only
"extracted" when you hold all of the following for it:

- Header: `GUID`, `VOUCHERKEY`, `MASTERID`, `ALTERID`, `VOUCHERNUMBER`, `DATE`,
  `REFERENCE` + `REFERENCEDATE`, `VOUCHERTYPENAME`, `PARTYLEDGERNAME`,
  `PARTYGSTIN`, place of supply, `ISOPTIONAL`, `ISCANCELLED`, `ISPOSTDATED`,
  `ISINVOICE`, `PERSISTEDVIEW`, entered-by / altered-by user, created &
  altered timestamps, `EFFECTIVEDATE` (for post-dated/effective-date vouchers).
- **`NARRATION` (voucher-level) verbatim, untruncated**, plus **line-level
  narration** on every ledger entry where "narration for each entry" is on.
  Record narration character length so truncation is detectable.
- Ledger lines (`ALLLEDGERENTRIES.LIST`): ledger name, `AMOUNT`,
  `ISDEEMEDPOSITIVE`, `ISPARTYLEDGER`, bill allocations, cost-centre
  allocations, tax classification, forex fields (`FOREXAMOUNT`,
  `RATEOFEXCHANGE`, `FORCESTYPE`).
- Inventory lines (`ALLINVENTORYENTRIES.LIST`): item, `ACTUALQTY`,
  `BILLEDQTY`, `RATE`, `AMOUNT`, `DISCOUNT`, `ACCOUNTINGALLOCATIONS.LIST`
  (which sales/purchase ledger the value hits), `BATCHALLOCATIONS.LIST`
  (godown, batch/lot, mfg & expiry date, **tracking number**, order reference),
  GST rate details, HSN.
- Bill allocations (`BILLALLOCATIONS.LIST`): bill name, **bill type**
  (`New Ref` / `Agst Ref` / `Advance` / `On Account`), amount, due date or
  credit days, interest parameters.

| ID | Voucher family | Types to pull |
|---|---|---|
| E13 | Sales side | Sales, Sales Order, Delivery Note, Rejections In, Credit Note, Debit Note (party), POS |
| E14 | Purchase side | Purchase, Purchase Order, Receipt Note (GRN), Rejections Out, Debit Note, Credit Note (party) |
| E15 | Money | Receipt, Payment, Contra |
| E16 | Journals | Journal, Reversing Journal, Memorandum |
| E17 | **Stock Journal** | **Transfer journals (godown-to-godown) and Manufacturing Journals — with full `SOURCEDESTINATIONLIST`: consumption (source) items/qty/rate/value/godown/batch, production (destination) items/qty/rate/value/godown/batch, BOM used, `ADDITIONALCOST`/cost-of-production allocations, and the by-product/scrap lines** |
| E18 | Physical Stock | Physical Stock vouchers: item, godown, batch, counted qty, date — and the book qty at that moment |
| E19 | Job work / material movement | Material In, Material Out, Job Work In/Out orders and their stock effect |
| E20 | Payroll | Payroll vouchers (pay head-wise), Attendance vouchers, employee-wise allocations |
| E21 | Optional / post-dated / cancelled | Everything flagged `ISOPTIONAL=Yes`, `ISPOSTDATED=Yes`, `ISCANCELLED=Yes`, plus scenario-only vouchers — kept **separately** from the books population |
| E22 | Opening balances | Ledger opening balances, bill-wise opening outstandings (with original bill dates), opening stock item-wise/godown-wise/batch-wise with rate and value |

### 4.3 Audit trail and history (E23–E24)

| ID | Domain | Must capture |
|---|---|---|
| E23 | **Edit Log / Tally Audit** | Per voucher: every version — created / altered / deleted, with user, timestamp, and the field-level before/after where exposed. Per master: alteration history. Deleted vouchers must be listed with their last-known content. |
| E24 | Reconciliation state | Bank reconciliation: bank date vs voucher date per bank entry, unreconciled items with age; and any "Post-dated" cheque register |

### 4.4 Extraction hygiene

- **Chunk and checksum.** Per month per voucher type: record count, sum of
  debits (₹), sum of credits (₹). Keep this manifest — Phase 2 depends on it.
- **No transformation in flight.** Do not round, re-sign, or normalise during
  the pull. Tally's sign convention (credits carry a negative `AMOUNT`, with
  `ISDEEMEDPOSITIVE` telling you the Dr/Cr intent) is resolved in Phase 2, on
  a copy.
- **Multi-company / multi-GSTIN.** Extract each Tally company separately; never
  merge before Phase 2, and keep the company key on every row.
- **Watermark re-read.** After the last pull, re-read `max(ALTERID)`. If it
  moved, pull the delta and repeat until stable. Log every iteration.

**Gate 1:** every domain E1–E24 either extracted with a manifest, or explicitly
recorded as unavailable with the reason and the audit impact.

---

## 5. Phase 2 — Prove the extract is complete and faithful

Build the working dataset from the raw pulls, then run **every** check below.
Each returns PASS/FAIL with the difference in ₹ (2 dp) or quantity (base unit).

| ID | Check | Expected |
|---|---|---|
| G1 | Per-voucher debit = credit (after resolving `ISDEEMEDPOSITIVE`) | ₹0.00 difference on every voucher; list any that fail |
| G2 | Aggregate debits = aggregate credits for the FY | ₹0.00 |
| G3 | Opening balances + FY movements = closing balances, per ledger | ₹0.00 per ledger |
| G4 | Your computed Trial Balance = Tally's own Trial Balance report | ₹0.00 on every ledger and on the total |
| G5 | Voucher count per type per month = Tally Day Book / voucher register count | exact match |
| G6 | Voucher-number continuity per voucher type per series | gaps listed with explanation (cancelled/deleted/manual numbering) |
| G7 | Stock: opening qty + inward − outward = closing qty, per item × godown × batch | 0 in base unit; tie total to Stock Summary |
| G8 | Closing stock **value** per Stock Summary = closing stock in Balance Sheet / Profit & Loss | ₹0.00 |
| G9 | Narration capture: count of vouchers with non-empty narration, and max narration length observed vs any API limit | no silent truncation; report % vouchers with blank narration |
| G10 | Bill-wise: sum of bill-wise outstanding per party = party ledger closing balance | ₹0.00 per party |
| G11 | Cost centre: sum of cost-centre allocations per voucher = allocable ledger amount | ₹0.00 |
| G12 | Optional/cancelled/post-dated vouchers excluded from the books population and reconciled separately | counts agree with E21 |
| G13 | ALTERID watermark stable between first and last pull | stable, or delta pulled |
| G14 | Comparative FY figures = prior-year audited/filed figures (where available) | differences listed as restatement/prior-period exceptions |
| G15 | Multi-currency: forex-denominated balances revalued at the reported closing rate agree with books | differences flagged as AS 11 / Ind AS 21 exceptions |

**Gate 2 (hard stop):** G1–G8, G10, G13 must PASS. If any fails, report the
failure with the reconciling items and do not proceed to Phase 3.

---

## 6. Phase 3 — Build every report, one by one

For **each** report: state (a) source tables, (b) the computation, (c) the
control total, (d) the tie-out to Tally's own version where Tally produces one,
(e) exceptions surfaced by the report itself. Produce them in this order —
later reports depend on earlier ones.

### 6.1 Core financial statements (R1–R10)
- **R1** Trial Balance — ledger-wise, with opening, Dr, Cr, closing; grouped to primary groups.
- **R2** Grouped Trial Balance / Group Summary — at every level of the group tree.
- **R3** Profit & Loss — Tally's own format, then mapped to Schedule III Division I/II (or ICAI non-corporate format).
- **R4** Balance Sheet — same two presentations, with Schedule III note numbering.
- **R5** Cash Flow Statement — indirect method (AS 3 / Ind AS 7), reconciled to the movement in cash and cash equivalents.
- **R6** Statement of Changes in Equity (Ind AS) or Reserves & Surplus movement (AS).
- **R7** Notes-to-accounts support schedules — every line item of R3/R4 broken to ledger level, so each note number has a ledger-level backing sheet.
- **R8** Monthly and quarterly P&L and Balance Sheet (12 columns) — for trend and cut-off work.
- **R9** Comparative FY vs CY with ₹ and % variance at note level and ledger level.
- **R10** Schedule III mandated ratios (current, debt-equity, DSCR, ROE, inventory/trade receivable/trade payable/net capital turnover, net profit %, ROCE, return on investment) with numerator, denominator and variance explanation.

### 6.2 Ledger and transaction registers (R11–R18)
- **R11** Day Book — full FY, every voucher, with narration.
- **R12** Ledger-wise statement of account — all ledgers, with running balance.
- **R13** Cash Book and Bank Book — daily, with **daily closing balance** (negative-balance detection).
- **R14** Journal register — all Journal/Reversing Journal vouchers with narration and user.
- **R15** Voucher register by type × month, with count and value (₹).
- **R16** Purchase register and Sales register — invoice-wise, with taxable value, tax, HSN, party GSTIN.
- **R17** Credit note / Debit note register — with reason from narration and linkage to the original invoice.
- **R18** Contra register — inter-bank/cash movements, with same-day pairing.

### 6.3 Receivables, payables, and money (R19–R26)
- **R19** Bills Receivable outstanding — bill-wise, with age from bill date (buckets 0–30/31–60/61–90/91–180/181–365/>365 days) and against credit period allowed.
- **R20** Bills Payable outstanding — same buckets, plus **MSME sub-analysis** (15/45-day test).
- **R21** Schedule III ageing of trade receivables and trade payables in the prescribed buckets (<6m, 6m–1y, 1–2y, 2–3y, >3y), split disputed/undisputed and MSME/others.
- **R22** Party-wise ledger confirmation pack — balance, last transaction date, bill-wise breakup, ready for SA 505 external confirmation.
- **R23** Advances from customers and to suppliers — with age and adjustment status.
- **R24** Bank reconciliation statement per bank account, as at FY end and at each quarter end, with unreconciled items aged.
- **R25** Cheque register — issued/received, post-dated, stale (>3 months), and cancelled.
- **R26** Interest / overdue analysis per bill using Tally's credit period and interest parameters (₹, with the rate and days shown).

### 6.4 Inventory — the part most audits under-do (R27–R38)
- **R27** Stock Summary — item-wise opening, inward, outward, closing (qty in base unit, rate ₹, value ₹).
- **R28** Godown-wise stock summary and movement; **negative stock by item × godown × date**.
- **R29** Batch-wise summary with manufacturing and expiry dates; **expired and near-expiry stock** valued.
- **R30** Stock item movement analysis — every inward and outward with voucher reference, for each item.
- **R31** **Stock Journal register — transfer journals and manufacturing journals separately**, each showing: consumption value (₹), production value (₹), additional cost (₹), and the **value differential absorbed into inventory**.
- **R32** Manufacturing/BOM variance — actual consumption vs BOM-implied consumption per production voucher, in qty and ₹; yield and scrap %.
- **R33** Physical stock vs book stock — per Physical Stock voucher: counted qty, book qty, difference in qty and ₹, and how the difference was accounted.
- **R34** Inventory ageing — by last movement date, with slow/non-moving (no movement in 90/180/365 days) valued.
- **R35** Valuation test — recompute closing value under the item's declared method (FIFO/weighted average) from the movement history and compare to Tally's value; also NRV/lower-of-cost-or-market test where selling price data exists (AS 2 / Ind AS 2, and s.145A for tax).
- **R36** Consumption and gross-margin analysis — per item and per item group: qty sold, sales value, cost of goods sold, gross margin ₹ and %.
- **R37** Purchase-to-consumption-to-sale quantity reconciliation per item: opening + purchases + production − consumption − sales − adjustments = closing.
- **R38** Job-work / third-party godown stock (goods lying with others, and others' goods with us) — quantity and value, for CARO 3(ii)(a) and Schedule III disclosure.

### 6.5 Indirect tax — GST (R39–R46)
- **R39** GSTR-1 style outward supply summary from books: B2B, B2C large/small, exports, SEZ, deemed exports, nil/exempt/non-GST, credit/debit notes, advances and adjustments.
- **R40** HSN-wise summary of outward supplies (qty, UQC, taxable value ₹, tax ₹) as required in GSTR-1 Table 12.
- **R41** GSTR-3B style computation from books — outward tax liability, RCM liability, ITC availed (inputs/capital goods/services), ITC reversal (Rules 37, 37A, 42, 43), net payable, and cash/credit utilisation.
- **R42** ITC register from books — invoice-wise, with supplier GSTIN, invoice date, tax split, and eligibility conclusion.
- **R43** GSTR-2B vs books ITC reconciliation — matched, in-2B-not-in-books, in-books-not-in-2B, value/tax mismatch; **ITC at risk quantified in ₹** with the reason code.
- **R44** Blocked credit review (s.17(5)) — expense ledgers screened for motor vehicles, food & beverages, club/health, employee benefits, works contract, CSR, personal use; ITC wrongly availed in ₹.
- **R45** RCM register — s.9(3)/9(4) supplies identified from vendor GSTIN status and expense nature; liability discharged vs ITC claimed; self-invoice compliance.
- **R46** E-invoice and e-way-bill compliance — invoices requiring IRN vs those carrying IRN; reporting-window breaches; movements over the e-way-bill threshold without a document number.

### 6.6 Direct tax (R47–R52)
- **R47** TDS register — section-wise (194C/194J/194H/194I/194Q/192/195...), deductee-wise: amount paid/credited ₹, rate applied %, TDS deducted ₹, TDS required ₹, short/excess ₹, deduction date vs credit date, payment date vs due date, interest u/s 201(1A) computed, late fee u/s 234E.
- **R48** TCS register — 206C(1H) and other clauses, with the same structure.
- **R49** Form 3CD data pack — clause-wise working papers (see §11.4), each clause pointing at the report that supports it.
- **R50** Disallowance schedule — s.40(a)(i)/(ia) (TDS default), 40A(3) (cash), 40A(2) (related party), 43B(h) (MSME), 36(1)(va) (employee PF/ESI beyond due date), 37 (personal/capital/penalty), 14A, with ₹ per head.
- **R51** Depreciation — Companies Act (Schedule II, useful life and residual value) and Income-tax Act (block-wise, half-rate for <180 days, additions/deletions), with the difference and its deferred-tax effect.
- **R52** Advance tax / self-assessment reconciliation — books vs challans, interest u/s 234A/B/C.

### 6.7 Payroll and statutory dues (R53–R56)
- **R53** Salary register — employee-wise, pay-head-wise, month-wise, gross to net.
- **R54** PF/ESI/PT register — wage base, employee and employer contribution, due date vs deposit date, delay in days and 36(1)(va) impact ₹.
- **R55** Headcount reconciliation — employees on master vs employees paid per month; joiners/leavers vs attendance; full-and-final settlements.
- **R56** Gratuity/leave-encashment provision adequacy indication (data-based only; actuarial valuation is management's).

### 6.8 Governance and risk (R57–R62)
- **R57** Related-party transaction register — from KEY_RELATED_PARTIES and ledger-name/PAN/address matching: transaction type, value ₹, terms, s.188 and s.177 approval status, Schedule III/AS 18/Ind AS 24 disclosure sheet.
- **R58** Cost-centre / segment profitability — revenue, direct cost, contribution per cost centre.
- **R59** Budget vs actual variance per ledger and cost centre, ₹ and %.
- **R60** Forex exposure and gain/loss — transaction-wise realised and unrealised, with rate used (ties to `build_forex_workbook.py` output format).
- **R61** Edit-log / audit-trail report — vouchers created, altered, deleted: count and value ₹ by user, by month, by voucher type; alterations after period close; deletions of high-value vouchers.
- **R62** User activity profile — vouchers per user per day, out-of-hours and holiday activity, and users posting outside their expected function.

**Gate 3:** every report R1–R62 marked PASS (tied out), FAIL (with the
difference), or N-A (with the reason — e.g. no payroll module in use).

---

## 7. Phase 4 — Build every relation

The audit value is in the joins. Construct an explicit linkage model, then test
its integrity.

### 7.1 Canonical keys

```
company        : company_name (+ GUID)
voucher        : voucher_guid (unique), (company, voucher_type, voucher_number, date)
ledger_line    : (voucher_guid, line_seq)
ledger         : ledger_name (+ MASTERID)
group          : group_name -> parent chain -> primary group
item           : item_name (+ MASTERID)
inventory_line : (voucher_guid, line_seq, item, godown, batch)
bill_ref       : (party_ledger, bill_name)
tracking_no    : tracking_number  (links GRN/Delivery Note <-> Invoice)
order_ref      : order_number     (links Order <-> Challan <-> Invoice)
cost_centre    : (voucher_guid, line_seq, cost_centre)
employee       : employee_name (+ MASTERID)
edit_version   : (voucher_guid, version_no)
```

### 7.2 Relations to build

| ID | Relation | Built from |
|---|---|---|
| L1 | voucher → ledger lines → ledger → group → primary group | `ALLLEDGERENTRIES.LIST` + group hierarchy walk |
| L2 | voucher → inventory lines → item → stock group/category | `ALLINVENTORYENTRIES.LIST` |
| L3 | inventory line → godown → batch → mfg/expiry date | `BATCHALLOCATIONS.LIST` |
| L4 | inventory line → accounting allocation → sales/purchase ledger | `ACCOUNTINGALLOCATIONS.LIST` |
| L5 | bill reference chain: `New Ref` → `Agst Ref` → settlement voucher | `BILLALLOCATIONS.LIST` bill type |
| L6 | Sales Order → Delivery Note → Sales Invoice → Receipt | order ref + tracking no + bill ref |
| L7 | Purchase Order → Receipt Note (GRN) → Purchase Invoice → Payment | order ref + tracking no + bill ref |
| L8 | Purchase → stock inward → **stock journal consumption → production** → stock outward → Sale | item + godown + batch + date sequence |
| L9 | invoice → tax ledger lines (CGST/SGST/IGST/Cess) → rate → HSN | tax lines vs item GST details |
| L10 | expense voucher → TDS ledger line → deductee ledger → section | TDS nature-of-payment on ledger |
| L11 | bank ledger line → bank reconciliation date → bank statement item | BRS data |
| L12 | voucher → cost-centre allocation → cost centre → category | `COSTCENTREALLOCATIONS.LIST` |
| L13 | voucher → user → timestamp → edit versions → current state | Edit Log |
| L14 | payroll voucher → employee → pay heads → statutory ledgers | payroll allocations |
| L15 | party ledger → GSTIN → state → place of supply on invoices | ledger GST details |
| L16 | item → HSN → GST rate → rate actually charged on invoices | item master vs invoice lines |
| L17 | related party ledger → transactions → approval register | KEY_RELATED_PARTIES + PAN/address match |
| L18 | Physical Stock voucher → item/godown/batch book position at that date | R33 |
| L19 | forex voucher → currency → rate → revaluation entry | forex fields |
| L20 | budget line → ledger/cost centre → actual | budgets vs postings |
| L21 | credit/debit note → original invoice | `REFERENCE`, narration, bill ref |
| L22 | job-work Material Out → Material In → BOM → finished goods | job-work vouchers |

### 7.3 Integrity tests on the graph

For each relation, report orphans and dangling references in count and ₹:

1. Ledger line whose ledger doesn't exist in masters, or whose group chain
   doesn't terminate at a primary group.
2. Inventory line with no accounting allocation, or an allocation that doesn't
   equal the line value (₹0.00 expected difference).
3. Inventory line with a batch on an item where batches are off, or without a
   godown where multi-godown is on.
4. `Agst Ref` allocation with no matching `New Ref` bill anywhere in the
   population (including opening bills) — a **hanging adjustment**.
5. Sales Invoice with no Delivery Note where the entity's stated process has
   one (and vice versa); GRN without Purchase Invoice beyond the FY end
   (**goods received not billed** — accrual exposure in ₹).
6. Order remaining open beyond the FY end — commitment disclosure.
7. Tax line on an invoice with no corresponding item-level GST rate, or a rate
   combination that cannot arise (e.g. CGST+SGST on an inter-state supply).
8. TDS ledger line with no expense line in the same voucher, or an expense
   attracting TDS with no TDS line.
9. Bank line with a reconciliation date before the voucher date.
10. Cost-centre allocation total ≠ ledger amount.
11. Voucher present in the Edit Log but absent from the current population
    (**deleted voucher**) — list with last-known value ₹.
12. Stock journal consumption line for an item/godown/batch with insufficient
    book quantity on that date (**negative stock through a stock journal**).

**Gate 4:** the graph is built, every L-test run, and every orphan quantified in
₹ and count.

---

## 8. Phase 5 — Compare every population against every other

This is the core analytical phase. Each test states: population A, population B,
join key, tolerance, result, exception count, exception value ₹.

### 8.1 Books-internal consistency (X1–X12)
- **X1** Sales register total vs P&L revenue vs GST outward taxable value.
- **X2** Purchase register total vs P&L purchases vs GST inward taxable value.
- **X3** Trade receivables per Balance Sheet vs sum of bill-wise outstandings vs party ledger balances.
- **X4** Trade payables — same three-way test.
- **X5** Closing stock per Stock Summary vs Balance Sheet vs P&L closing-stock credit.
- **X6** Cash book closing balance vs Balance Sheet cash; **daily cash balance never negative**.
- **X7** Bank book vs Balance Sheet vs BRS-adjusted bank balance.
- **X8** Inter-branch / inter-godown transfers net to zero in value and quantity.
- **X9** Contra pairs: every Contra has a matching opposite leg; cash-to-bank deposits vs bank credits on the same/next day.
- **X10** Credit notes vs original invoices — value never exceeding the invoice; note date ≥ invoice date.
- **X11** Opening balances of the FY vs closing balances of the comparative FY, ledger by ledger.
- **X12** Sum of monthly P&L = annual P&L; sum of quarterly = annual.

### 8.2 Quantity ↔ value ↔ tax (X13–X20)
- **X13** Per item: (sales qty × average rate) vs sales value in the P&L; explain the variance.
- **X14** Per item: quantity reconciliation R37 closes to zero; any residual quantified at cost ₹.
- **X15** **Stock journal effect test:** total value consumed vs total value produced per stock journal. A transfer journal must be value-neutral; a manufacturing journal's production value must equal consumption + additional cost. Report every journal where value was created or destroyed without a P&L entry, in ₹ — this is the classic route to inflate inventory without touching the books.
- **X16** Purchase rate vs consumption/issue rate vs valuation rate per item — flag items where the issue rate is inconsistent with the declared valuation method.
- **X17** GST charged per invoice line vs (taxable value × rate from item HSN master) — difference in ₹, exception if ≠ ₹0.00 beyond rounding of ₹1.
- **X18** Gross margin per item / per customer — negative or implausible margins listed with value ₹.
- **X19** Scrap and wastage % per production run vs the entity's norm and vs prior year.
- **X20** Physical stock differences (R33) vs the adjustment entries actually passed — unadjusted differences quantified.

### 8.3 Books ↔ external data (X21–X30)
Where the external data is provided by the client (portal downloads, statements,
26AS/AIS, challans), reconcile it; where it isn't available, say so and mark the
test as not performed — never simulate external data.
- **X21** GSTR-1 filed vs books outward supply (per month, per tax head).
- **X22** GSTR-3B filed vs books liability and ITC (per month, per tax head).
- **X23** GSTR-2B vs books ITC (R43) — with ITC at risk ₹ and the s.16(4) time-limit test.
- **X24** GSTR-1 vs GSTR-3B vs books three-way (the differences the department itself runs).
- **X25** Annual GSTR-9/9C vs books vs the sum of monthly returns.
- **X26** Bank statements vs bank books — transaction-level, with unmatched items aged.
- **X27** Form 26AS / AIS vs books income and TDS credit.
- **X28** TDS returns (24Q/26Q/27Q) filed vs books TDS register (R47) — deductee-wise.
- **X29** PF/ESI returns vs payroll register (R54).
- **X30** Prior-year audited financials vs comparative figures in this year's books (restatements).

### 8.4 Period, budget and trend (X31–X36)
- **X31** CY vs PY at ledger level — every variance above materiality explained (SA 520 substantive analytics).
- **X32** Month-on-month trend per major ledger; spike/dip detection with the value ₹ and the driver voucher(s).
- **X33** Budget vs actual (R59) — variances above tolerance, with narration evidence.
- **X34** Ratio movement (R10) vs PY and vs the entity's stated drivers; each ratio's numerator and denominator shown.
- **X35** **Cut-off testing:** vouchers dated in the last 7 days of the FY and the first 7 days of the next FY — revenue, purchase, GRN, delivery note, credit note: does the goods movement date support the revenue date (SA 501 / AS 9 / Ind AS 115)?
- **X36** Post-balance-sheet events window (SA 560): all vouchers after FY end that adjust FY balances — credit notes against FY sales, write-offs, provisions, recoveries.

### 8.5 Party-level and concentration (X37–X44)
- **X37** Customer concentration: top 10 by revenue — % of turnover, credit period actually taken vs allowed, and collection history.
- **X38** Vendor concentration: top 10 by purchases — plus vendors created during the FY who immediately became top-10 (suspicious onboarding).
- **X39** Same GSTIN / PAN / bank account / address across multiple ledgers — duplicate or related masters.
- **X40** Vendor bank account matching an employee bank account (ghost-vendor indicator).
- **X41** Parties with both receivable and payable balances — netting and confirmation risk.
- **X42** Dormant ledgers (no movement for >12 months) that were reactivated during the FY, with value ₹.
- **X43** Related-party transactions vs arm's-length indicators: rate charged to related parties vs average to others, per item, difference ₹ and %.
- **X44** Cash transactions per party per day aggregated for s.269ST (₹2,00,000) and per voucher for s.40A(3) (₹10,000; ₹35,000 goods carriage).

**Gate 5:** every X-test either executed with a quantified result, or recorded
as not performed with the missing input named.

---

## 9. Phase 6 — Narration mining (do not skip this)

Narrations are the only free-text evidence in Tally, and they are where the
reason for an entry usually lives. Treat them as a first-class population.

1. **Coverage.** % of vouchers with blank narration, by voucher type, by user,
   by value band. High-value journals with blank narrations are an exception in
   themselves (and a documentation deficiency under SA 230 reasoning applied to
   the client's records).
2. **Risk lexicon.** Flag and value (₹) narrations containing: `adjust`,
   `adjustment`, `rectify`, `correction`, `wrong entry`, `reverse`, `reversal`,
   `temporary`, `temp`, `suspense`, `to be adjusted`, `pending`, `as advised`,
   `as per instruction`, `as discussed`, `sir`, `madam`, owner/director names,
   `cash`, `hand loan`, `imprest`, `write off`, `bad debt`, `waive`, `discount
   given`, `commission`, `gift`, `donation`, `penalty`, `fine`, `personal`,
   `drawings`, `transfer to`, `balancing`, `difference`, `rounding`, `dummy`,
   `test`, `provision`, `year end`, `books closing`. Report count and value per
   keyword.
3. **Empty-of-meaning narrations.** Narrations equal to the ledger name, the
   voucher type, a single word, a number, or copied identically across many
   vouchers — cluster and count.
4. **Duplicate narrations on distinct vouchers** with similar amounts — possible
   duplicate booking.
5. **Narration vs entry contradiction.** Narration says "payment to X" but the
   ledger hit is Y; narration references an invoice number absent from the
   population; narration references a date inconsistent with the voucher date.
6. **Narration as the only support for a manual journal** — list every journal
   over performance materiality whose entire justification is a narration, for
   SA 240 journal-entry testing.
7. **Language/script mix, truncation, and control characters** — data-quality
   observations that can also indicate imported or scripted entries.
8. **Narration on stock journals specifically.** Production, transfer and
   shortage journals with no narration or a vague one, over a value threshold —
   quantify. A stock journal moving value with no explanation is a finding.
9. **Cross-reference narration keywords to the exception register**, so a
   narration flag can corroborate an independently detected anomaly (a
   round-sum journal + "adjustment" narration + posted by an unusual user is a
   different severity from any one of the three alone).

**Gate 6:** narration analysis complete with counts and ₹ values per flag
category, and the top flags carried into the exception register.

---

## 10. Phase 7 — Fraud, journal-entry and behavioural testing (SA 240)

Run each test on the full population; report count, value ₹, and the top items.
Where the CAE rule packs already codify a test, use the same rule code so the
findings are comparable (`SAL-`, `PUR-`, `INV-`, `JE-`, `PAY-`, `TRE-`).

| ID | Test |
|---|---|
| F1 | Duplicate invoices: same party + same amount + same/near date; same invoice number twice; same amount different number (`SAL-001` / `PUR-001` family) |
| F2 | Duplicate payments: same party, same amount, within N days; same bill referenced twice |
| F3 | Round-sum entries: amounts ending in 000/0000, above a value threshold, by voucher type and user |
| F4 | Benford's law (first digit and first-two digit) on sales, purchases, expenses and journals, with χ²/MAD and the deviating digit groups — used as a direction indicator, never as a conclusion |
| F5 | Journal entries to unusual accounts: revenue, cash, inventory, related parties, reserves — posted by journal rather than the process voucher type |
| F6 | Same-day or near-day reversals; entries reversed in the next FY's first month |
| F7 | Entries posted on weekends, public holidays, or outside business hours (time from Edit Log) |
| F8 | Back-dated entries: created timestamp materially after the voucher date; entries dated before a period lock; entries to a closed month |
| F9 | Entries created and altered by the same single user with no second-person involvement, above materiality (segregation-of-duties failure) |
| F10 | Deleted vouchers (from Edit Log) — count, value ₹, user, whether replaced by another voucher |
| F11 | Altered vouchers where the **amount, party, ledger or date** changed after original entry — before/after and the value delta ₹ |
| F12 | Year-end concentration: value of manual journals in the last 5 days of the FY vs the monthly average |
| F13 | Split transactions just below a threshold: 40A(3) ₹10,000 cash, e-way bill ₹50,000, 269ST ₹2,00,000, approval limits, TDS section thresholds |
| F14 | New vendor/customer created and transacted on the same day, especially over materiality |
| F15 | Ghost vendor/employee indicators: shared bank account, address, PAN, mobile; vendor with no GSTIN receiving large payments; employee with no attendance but with salary |
| F16 | Negative balances that shouldn't exist: negative cash, negative stock, negative creditor with no advance, debit balance in a bank OD ledger inconsistent with sanction |
| F17 | Credit-note abuse: credit notes concentrated in the first month after year end against FY-end sales, or to specific customers |
| F18 | Expense ledgers with personal-consumption characteristics (travel, gifts, vehicle, mobile, medical) benchmarked per-employee and vs PY |
| F19 | Cash-in-hand pattern: daily balance vs the entity's scale, large cash receipts/payments, cash deposits immediately preceding cheque issues |
| F20 | Stock-based manipulation battery: value-creating stock journals (X15), production without consumption, consumption without production, transfers to external/third-party godowns near year end, physical-stock differences adjusted through stock journals rather than P&L |
| F21 | Kite-flying / circular funds: fund movement loops across related ledgers returning to origin within a short window (A→B→C→A), value ₹ |
| F22 | Revenue-recognition stress: invoices with no goods movement, invoices to parties with no subsequent collection, sale-and-return patterns |

For every test that produces exceptions, state whether it indicates **error**,
**control deficiency**, or **possible fraud**, and apply SA 240 escalation
(communicate to those charged with governance; consider s.143(12) and ADT-4
reporting thresholds for companies).

**Gate 7:** F1–F22 executed; each mapped to error / deficiency / fraud-risk with
₹ impact.

---

## 11. Phase 8 — Statutory checklists (statutory & tax audit)

Every item: conclusion + evidence reference + ₹ impact + the section/clause
cited, and the FY whose rule you applied (Appendix C).

### 11.1 Standards on Auditing — procedural spine
SA 200/210 (engagement acceptance and terms) · SA 220 + SQC 1 (quality) ·
SA 230 (documentation — every conclusion in this pack must have a working paper
reference) · SA 240 (fraud — §10) · SA 250 (laws and regulations — §11.2–11.5) ·
SA 260/265 (communication and control deficiencies) · SA 299 (joint auditors,
if any) · SA 315 (understanding the entity and its controls; the IT
environment — **Tally configuration, user rights and Edit Log are your ITGC
evidence**) · SA 320 (materiality) · SA 330 (responses) · SA 402 (service
organisations) · SA 450 (evaluation of misstatements — aggregate your exception
register against materiality) · SA 500/501 (evidence; inventory attendance,
litigation, segments) · SA 505 (external confirmations — R22) · SA 510 (opening
balances — G3, G14, X11) · SA 520 (analytics — X31–X36) · SA 530 (sampling —
§13) · SA 550 (related parties — R57, X43) · SA 560 (subsequent events — X36) ·
SA 570 (going concern — R10 ratios, negative net worth, defaults, cash flows) ·
SA 580 (written representations) · SA 600 (branch auditors) · SA 700/701/705/706
(opinion, KAM, modifications, EOM) · SA 710 (comparatives) · SA 720 (other
information).

### 11.2 Companies Act 2013
- s.128 — books of account, whether maintained on accrual and double-entry, and
  whether the **server/records are kept in India**; s.128(5) preservation of 8
  years.
- **Rule 3(1), Companies (Accounts) Rules 2014 — audit trail:** was Tally's Edit
  Log enabled throughout the FY, was it ever disabled, and were deletions
  logged? This is your Rule 11(g) reporting basis.
- s.129 + Schedule III — presentation, note disclosures, and the mandated
  ageing schedules and ratios.
- s.133 — AS/Ind AS compliance, and disclosure of accounting policies.
- s.134 — Board's report consistency with the financials.
- s.143(1) proviso enquiries; s.143(3) clauses (a)–(j); s.143(3)(i) internal
  financial controls with reference to financial statements; s.143(12) fraud
  reporting.
- Rule 11 of the Audit and Auditors Rules: (a) pending litigation, (b)
  foreseeable losses on long-term contracts and derivatives, (c) IEPF transfer,
  (d) **funds advanced/received with an "ultimate beneficiary" representation**,
  (e) dividend compliance with s.123, (f)/(g) audit-trail reporting.
- Section-specific: s.73–76 (deposits), s.180, s.185 (loans to directors),
  s.186 (loans and investments), s.188 (related-party transactions), s.192
  (non-cash transactions with directors), s.135 (CSR — spend, unspent transfer
  to the Schedule VII fund or Unspent CSR Account), s.148 (cost records and
  cost audit), s.203 (KMP), s.42/62 (private placement/preferential allotment
  usage), s.90 (SBO), s.89, MSME Form I / MSME-1 half-yearly return.
- ROC filings in the year: AOC-4, MGT-7/7A, DPT-3, DIR-3 KYC, ADT-1, MSME-1,
  BEN-2, charges (CHG-1/4) — filed vs due, with late fee exposure.

### 11.3 CARO 2020 — clause by clause
Report each clause with the data backing it:
(i) PPE and intangibles — register with full particulars, physical verification
programme and results, **title deeds** of immovable property not in the
company's name, revaluation, **benami** proceedings ·
(ii)(a) inventory physical verification, coverage and **discrepancies of 10% or
more per class** (use R33) · (ii)(b) working-capital limits **exceeding ₹5 crore
in aggregate** from banks/FIs on security of current assets — quarterly returns
vs books ·
(iii) loans, advances, guarantees, security given: aggregate, terms, repayment
schedule, overdue >90 days, evergreening, loans repayable on demand or without
terms ·
(iv) compliance with s.185 and s.186 ·
(v) deposits and deemed deposits — s.73–76 and the Rules ·
(vi) cost records u/s 148 ·
(vii)(a) undisputed statutory dues (GST, PF, ESI, income tax, TDS, customs,
cess) outstanding for more than six months from the due date; (vii)(b) disputed
dues with forum and amount ·
(viii) transactions not recorded in the books that were surrendered or disclosed
as income in income-tax assessments/search ·
(ix)(a) default in repayment of loans or interest, lender-wise; (ix)(b) wilful
defaulter; (ix)(c) term loans applied for the purpose obtained; (ix)(d)
short-term funds used for long-term purposes; (ix)(e) funds raised to meet
obligations of subsidiaries/associates/JVs; (ix)(f) loans raised on the pledge
of securities held in subsidiaries/JVs/associates ·
(x)(a) IPO/FPO application of money; (x)(b) preferential allotment/private
placement compliance with s.42/62 and utilisation ·
(xi)(a) fraud by or on the company noticed or reported; (xi)(b) ADT-4 filed;
(xi)(c) whistle-blower complaints considered ·
(xii) Nidhi-specific ratios (if applicable) ·
(xiii) related-party transactions — s.188 compliance and AS 18/Ind AS 24
disclosure ·
(xiv)(a) internal audit system commensurate with size and nature; (xiv)(b)
whether the internal audit reports were considered ·
(xv) non-cash transactions with directors — s.192 ·
(xvi) RBI registration requirement / NBFC / HFC / CIC status and group CICs ·
(xvii) cash losses in the current and immediately preceding FY ·
(xviii) resignation of the statutory auditors and issues taken into
consideration ·
(xix) material uncertainty over meeting liabilities existing at the balance
sheet date as they fall due within one year — use ageing, ratios and cash flow ·
(xx) CSR — unspent amount transferred to the Fund / Unspent CSR Account within
the prescribed time ·
(xxi) qualifications or adverse remarks in the CARO reports of companies
included in the consolidated financial statements.

### 11.4 Form 3CD (tax audit) — data pack per clause
Clause 12 (presumptive income) · **13 (method of accounting, change, ICDS
adjustments)** · **14 (stock valuation and s.145A)** — R35 is the evidence ·
16 (amounts not credited to P&L) · 17 (transfer of land/building below stamp
value, s.43CA/50C) · 18 (depreciation block-wise — R51) · 19 (specified
deductions) · 20 (bonus/commission to employees; employee contributions u/s
36(1)(va) — R54) · **21(a)** capital/personal/advertisement/penalty expenses ·
**21(b)** s.40(a) — TDS not deducted/not paid, s.40(a)(ia)/(i), and 40(a)(ii)
· 21(d) **s.40A(3) cash payments over the limit** · 21(e) 40A(7) gratuity
provision · 21(f)–(g) s.40A(9), contingent liabilities · **22 s.23 of MSMED —
interest inadmissible** · **23 s.40A(2) payments to specified persons — R57** ·
24 (s.32AC/33AB/33ABA deemed income) · 26 (**s.43B** sums payable — statutory
dues paid before the due date of filing) · 27 (CENVAT/GST credit availed and
utilised, prior-period items) · 28/29 (s.56(2)(viia)/(viib)) · 29A/29B
(s.56(2)(ix)/(x)) · 30 (hundi) · 30A (secondary transfer-pricing adjustment) ·
30B (interest deduction limit, s.94B) · 30C (GAAR — impermissible avoidance
arrangement) · **31 (s.269SS/269T loans and deposits, and 269ST receipts)** ·
32 (brought-forward losses and depreciation) · 33 (Chapter VI-A/10AA
deductions) · **34(a)/(b)/(c) TDS/TCS compliance, returns, and interest u/s
201(1A)/206C(7) — R47/R48** · 36A (deemed dividend u/s 2(22)(e)) · 40
(prescribed ratios) · 41 (demands/refunds under other tax laws) · 42 (Form
61/61A/61B) · 43 (Country-by-Country reporting) · **44 (break-up of total
expenditure — GST-registered vs unregistered entities)** — this clause is built
straight from the ledger-wise expenditure crossed with vendor GSTIN status,
so build it from R42/R45 data.
Also: s.44AB applicability computation (turnover and the 5%-cash test), and
s.44AD/44ADA/44AE where relevant.

### 11.5 GST
Registration and amendments · outward liability (R39–R41) · **ITC eligibility:
s.16(2)(a)–(d) including invoice possession, receipt of goods/services, tax
actually paid by the supplier (2B-based, s.16(2)(aa)/(ba)), and return filed;
s.16(4) time limit (30 November of the following FY, or the annual return date,
whichever is earlier)** · s.17(5) blocked credits (R44) · Rules 42/43
(common-credit reversal for exempt/personal use, capital goods) · Rule 37
(ITC reversal where the supplier is not paid within 180 days) · Rule 37A
(reversal where the supplier hasn't filed GSTR-3B) · RCM s.9(3)/9(4) and
self-invoicing (R45) · place of supply and CGST+SGST vs IGST correctness ·
exports/SEZ — LUT, refunds, realisation · e-invoice and e-way bill (R46) ·
credit/debit notes u/s 34 and the time limit · interest u/s 50 and late fee
u/s 47 · GSTR-9/9C reconciliation (X25) · cross-charge and ISD where
multi-GSTIN.

### 11.6 TDS/TCS and other direct-tax
Section-wise applicability and rate (R47) · lower/nil deduction certificates ·
PAN-inoperative higher rate · 194Q vs 206C(1H) interaction · 194R (benefits
and perquisites) · 194-IA/IB/IC · 195 and Form 15CA/15CB for foreign
remittances, treaty rate and Form 10F/TRC · quarterly returns and corrections ·
Form 16/16A issuance · interest u/s 201(1A) and fee u/s 234E · 43B(h) MSME
payment timelines · advance tax and 234A/B/C (R52).

### 11.7 Other laws touching the books
PF/ESI/PT/LWF · Shops & Establishments · MSMED Act (vendor classification,
45-day payment, Form MSME-1) · FEMA (ECB, FDI, ODI, export realisation) ·
Stamp duty on instruments · SEBI LODR where listed · industry-specific (RBI,
IRDAI, FSSAI, drugs, environmental).

**Gate 8:** every applicable checklist item concluded with evidence and ₹
impact; every N-A carries a reason.

---

## 12. Phase 9 — Internal audit specifics (if ENGAGEMENT_TYPE = Internal Audit)

Follow the ICAI Standards on Internal Audit (SIA), especially SIA 110
(nature of assurance), SIA 120 (internal controls), SIA 130 (risk assessment),
SIA 140 (governance), SIA 210/220 (managing the engagement and conducting the
work), SIA 310 (planning), SIA 320 (risk and materiality), SIA 330
(documentation), SIA 350 (reporting), SIA 360 (communication), SIA 370
(management responses and follow-up).

**Build a Risk and Control Matrix (RCM) per process**, each row: process → sub-
process → risk → control → control type (preventive/detective, manual/
automated) → test performed on the Tally population → population size →
exceptions → control conclusion (effective / partially effective / ineffective)
→ ₹ exposure → recommendation → management response → owner → target date.

Process cycles to cover, each driven by the reports and relations already built:

1. **Order to Cash** — customer master changes, credit limit and credit period
   discipline (compare invoices against the ledger's credit limit), order →
   delivery → invoice completeness (L6), pricing vs price list, discount
   authorisation, credit-note approvals, collection and ageing (R19/R21),
   write-offs, cash-sale controls.
2. **Procure to Pay** — vendor onboarding and duplicates (X39/X40), PO
   discipline (purchases without a PO, PO after invoice date), three-way match
   PO↔GRN↔invoice quantity and rate (L7), rate reasonableness across vendors
   per item, advance management, payment authorisation, duplicate payments
   (F2), vendor concentration (X38).
3. **Inventory and warehouse** — receipt to issue traceability, godown
   discipline, negative stock (R28), stock journal governance (X15/F20),
   physical verification programme and adjustment approvals (R33), slow/
   non-moving and expiry (R29/R34), valuation (R35), scrap disposal, insurance
   coverage vs stock value, third-party stock (R38).
4. **Production/conversion** — BOM accuracy and variance (R32), yield, scrap
   and rework norms, cost of production build-up, WIP existence and valuation,
   job-work reconciliation (L22).
5. **Fixed assets** — capitalisation vs revenue expenditure (test expense
   ledgers for capital items over a threshold), CWIP ageing (Schedule III),
   physical verification, disposals and scrapping authorisation, depreciation
   policy application (R51), title deeds, idle assets.
6. **Payroll and HR** — headcount reconciliation (R55), joiners/leavers timing,
   salary revision authorisation, attendance-to-pay linkage, statutory
   deposits (R54), reimbursement policy compliance, F&F settlements, ghost
   employees (F15).
7. **Treasury, banking and cash** — bank mandates and signatory limits, BRS
   discipline and stale items (R24/R25), cash handling and imprest, fund
   utilisation vs sanction terms, borrowing covenants and default (CARO
   3(ix)), investment authorisation, forex exposure (R60).
8. **Statutory compliance monitoring** — a due-date calendar vs actual filings
   and payments for GST, TDS, PF, ESI, PT, advance tax and ROC, with delay days
   and interest/penalty ₹ (LexComply's rule set is the reference here).
9. **IT general controls in Tally** — user list vs current employees, shared
   logins, rights vs role, **Edit Log enabled**, period lock, backup and
   restore evidence, remote access, data-path and server control, versions and
   licence.
10. **Governance and entity-level controls** — delegation of authority matrix vs
    actual approvals, related-party governance (R57), whistle-blower
    mechanism, budget discipline (R59), prior-period observation closure
    (PRIOR_YEAR_OBS re-testing).

**Gate 9:** RCM complete for every in-scope process, every control tested
against the Tally population, and every open observation carried into the
report with an owner and a date.

---

## 13. Phase 10 — Materiality, sampling and evidence

1. **Materiality** (SA 320): set overall, performance and clearly-trivial
   thresholds in ₹, state the benchmark and %, and revisit them after Phase 5 if
   the data changes the picture.
2. **Full-population first.** Everything computable runs at 100%. Say so
   explicitly — "tested 100% of 48,912 vouchers" is a stronger statement than
   any sample.
3. **Sampling only for document/human inspection** (SA 530): state the
   population size and value ₹, the sampling unit, the method (monetary-unit,
   systematic with a random start, or judgemental for targeted risk), the
   sample size and its basis, the selection seed, the coverage % by value, and
   the projection method for errors found. Never extrapolate a judgemental
   sample to the population.
4. **Evidence index.** Every exception line carries: voucher GUID, voucher
   number, date, party, ledger/item, ₹ amount, the test ID that found it, the
   query or script that produced it, and the document requested or inspected.
5. **Written representations** (SA 580) for matters not verifiable from data:
   completeness of related parties, litigation, subsequent events, fraud
   awareness, and the ultimate-beneficiary representation for Rule 11(e).
6. **What data cannot tell you.** Maintain an explicit list: physical existence,
   title, third-party confirmation, valuation judgement, intent, and management
   estimates. Each becomes a procedure outside the MCP pull, or a scope
   limitation to disclose.

---

## 14. Phase 11 — Exception register

One register, one row per exception, these columns:

```
exception_id | test_id (R/L/X/N/F/S ref or CAE rule code) | phase
voucher_guid | voucher_number | voucher_date | voucher_type | user
party / ledger / item | quantity (base unit) | amount_₹
title (one line) | description (what, where, why it matters)
severity: Critical | High | Medium | Low
category: Error | Control deficiency | Fraud risk | Compliance | Disclosure | Data quality
financial_impact_₹ (and how computed) | tax/interest/penalty exposure_₹ with section
assertion affected: Existence | Completeness | Accuracy | Cut-off | Classification | Valuation | Presentation
evidence_ref | management_response | agreed_action | owner | target_date | status
label: Observed | Concluded | Assumed
```

**Severity rubric** (state the thresholds you used):

- **Critical** — quantified impact above overall materiality, or any suspected
  fraud, or a statutory non-compliance attracting prosecution/disqualification,
  or a matter affecting the audit opinion.
- **High** — impact above performance materiality, a pervasive control failure,
  or non-compliance attracting interest/penalty above a stated ₹ threshold.
- **Medium** — impact below performance materiality but systemic or repeating.
- **Low** — isolated, below clearly-trivial, or presentation/data-quality only.

**Aggregation (SA 450):** total uncorrected misstatements by nature
(factual/judgemental/projected), compare against materiality, and state the
effect on the opinion. Fraud indicators are **scored**, not severity-graded —
report the score and the corroborating tests, never a bare label.

---

## 15. Phase 12 — Deliverables

1. **Extraction dossier** — coverage matrix, manifests, ALTERID watermarks,
   raw-pull inventory, and the Phase 2 tie-out sheet.
2. **Report pack R1–R62** — each as its own sheet/file, each with its control
   total and tie-out status.
3. **Relationship and integrity pack** — the linkage model plus L1–L22 results.
4. **Analytics pack** — X1–X44, narration analysis, fraud battery F1–F22, each
   with its exception list.
5. **Compliance pack** — SA/CARO/3CD/GST/TDS checklists with conclusions and ₹
   exposures; or, for internal audit, the RCM per process.
6. **Exception register** (§14) plus a one-page summary of the top 20 by ₹.
7. **Draft report** — for statutory audit: opinion section, basis, KAM (if
   applicable), s.143(3) clauses, CARO annexure, IFC annexure; for internal
   audit: executive summary, process-wise observations, RCM, and the follow-up
   tracker on prior observations.
8. **Management letter** — control deficiencies (SA 265) and the improvement
   recommendations, each with the ₹ exposure it addresses.
9. **Open items and scope limitations** — what couldn't be obtained or tested,
   and the audit impact.
10. **Reproducibility file** — every query/script used, so any figure can be
    regenerated from the raw pulls without re-touching Tally.

---

## 16. Definition of done

Do not report the engagement complete until **all** of these hold:

- [ ] Gate 0–9 each recorded as passed, with evidence.
- [ ] Trial Balance, Stock Summary and bill-wise tie-outs all ₹0.00 / zero qty.
- [ ] Every voucher type present in Tally appears in the extract — including
      stock journals, physical stock, optional, post-dated and cancelled — and
      each is either in the books population or reconciled outside it.
- [ ] Narration captured for 100% of vouchers that have one, with the blank-
      narration population quantified.
- [ ] Every report R1–R62 marked PASS / FAIL / N-A with a reason.
- [ ] Every relation L1–L22 built, with orphans quantified.
- [ ] Every comparison X1–X44 executed or explicitly not performed with the
      missing input named.
- [ ] Narration battery (§9) and fraud battery (§10) complete.
- [ ] Every applicable checklist item in §11 (or §12 for internal audit)
      concluded and cited.
- [ ] Exception register complete, aggregated against materiality, with ₹
      impact on every line.
- [ ] Every number in every deliverable traceable to a shown query — no figure
      produced by narrative.
- [ ] Scope limitations and open items stated plainly.

---

## Appendix A — Tally data-model traps that cause wrong audit conclusions

1. **Sign convention.** Credits carry a negative `AMOUNT`; `ISDEEMEDPOSITIVE`
   records the Dr/Cr intent. Resolve both together — using either alone flips
   entries. Verify by proving debits = credits per voucher (G1).
2. **`ALTERID` is your incremental key**, `MASTERID`/`GUID` your identity key.
   A changing `ALTERID` mid-extraction means the books moved under you.
3. **Optional vouchers don't affect books** but look like real vouchers in a
   raw pull. So do **scenario-only** vouchers and **post-dated** vouchers.
   Segregate them or you will overstate everything.
4. **Cancelled vouchers retain their number** and carry zero value —
   they explain voucher-number gaps but must not enter the population.
5. **Deleted vouchers vanish entirely** from a normal pull. Only the Edit Log
   proves they existed. An audit that skips the Edit Log cannot detect deletion.
6. **`BILLEDQTY` ≠ `ACTUALQTY`.** Actual is what moved, billed is what was
   charged. The difference is free-of-cost supply, shortage, or a manipulation
   — quantify it item-wise.
7. **Bill types matter.** `New Ref` creates an outstanding, `Agst Ref` settles
   one, `Advance` is unearned, `On Account` is unallocated. Unallocated
   `On Account` balances break ageing and are a finding in their own right.
8. **Stock journals can move value without touching the P&L.** A transfer
   journal should be value-neutral; a manufacturing journal's destination value
   equals source value plus additional cost. Any other outcome silently changes
   inventory valuation and therefore profit. Test every one (X15).
9. **Physical Stock vouchers overwrite the book quantity** without a value
   entry — the shortage/excess is absorbed in valuation, not shown as a loss.
   Always compare counted vs book and ask where the difference went (R33).
10. **Zero-value and zero-quantity lines are legal in Tally** and are used to
    hide movements. Don't filter them out.
11. **Item valuation method is per item**, can be "At Cost", "Avg. Cost",
    "FIFO", "Last Purchase Cost", "Standard Cost" or "At Market Rate", and can
    be changed mid-year — which retroactively changes closing value. Check for
    method changes (AS 1/AS 2 disclosure, and 3CD clause 13/14).
12. **Multi-godown and batch features can be enabled mid-year**, so earlier
    vouchers carry no godown/batch. Don't read that as missing data without
    checking the feature-activation date.
13. **Alternate units and compound units** make quantities non-additive. Always
    convert to the base unit before summing, and state the unit.
14. **Rounding ledgers** absorb differences; a large rounding-off balance is a
    symptom, not a policy.
15. **Same ledger name under a different group across companies** — never join
    on name across companies without the company key.
16. **Narration length limits and line-level narrations.** Voucher narration and
    per-entry narration are separate fields; pull both or you lose the reason
    for half the postings.
17. **Voucher date vs effective date vs created timestamp** are three different
    dates. Cut-off and back-dating tests need all three.
18. **`ISDEEMEDPOSITIVE` on tax lines** plus inclusive-of-tax rates can make
    recomputing tax from the taxable value look wrong. Recompute from the
    invoice's own taxable base.
19. **Forex vouchers** carry `FOREXAMOUNT` and `RATEOFEXCHANGE`; the base-
    currency `AMOUNT` is derived. Revaluation entries at year end are separate
    vouchers — don't double count.
20. **Godowns flagged external** are third-party locations. Stock there is a
    disclosure item and a favourite year-end parking spot.

## Appendix B — Read-only request patterns (when only a generic XML tool exists)

If the MCP server exposes a generic "send Tally XML request" tool, use only
these shapes. `TALLYREQUEST` must be `Export`. **Never** `Import`.

```xml
<!-- Report export: any Tally report by name, e.g. Trial Balance, Day Book,
     Stock Summary, Bills Receivable, Group Summary -->
<ENVELOPE>
  <HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Data</TYPE><ID><!-- report name --></ID></HEADER>
  <BODY><DESC><STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
    <SVCURRENTCOMPANY><!-- company --></SVCURRENTCOMPANY>
    <SVFROMDATE>YYYYMMDD</SVFROMDATE><SVTODATE>YYYYMMDD</SVTODATE>
  </STATICVARIABLES></DESC></BODY>
</ENVELOPE>

<!-- Collection export: masters or vouchers with chosen fields -->
<ENVELOPE>
  <HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Collection</TYPE><ID><!-- collection name --></ID></HEADER>
  <BODY><DESC><STATICVARIABLES>
      <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      <SVFROMDATE>YYYYMMDD</SVFROMDATE><SVTODATE>YYYYMMDD</SVTODATE>
    </STATICVARIABLES>
    <TDL><TDLMESSAGE><!-- COLLECTION / FETCH / FILTER definitions -->
    </TDLMESSAGE></TDL>
  </DESC></BODY>
</ENVELOPE>
```

Practical notes: fetch `ALLLEDGERENTRIES.LIST`, `ALLINVENTORYENTRIES.LIST`,
`BATCHALLOCATIONS.LIST`, `BILLALLOCATIONS.LIST`,
`COSTCENTREALLOCATIONS.LIST`, `SOURCEDESTINATIONLIST` and `NARRATION`
explicitly — they are not returned by default. Chunk by month; a full-FY
voucher collection on a large company times out. Set the company explicitly on
every request; never rely on the "current" company. If a response is truncated
or malformed, re-request that chunk rather than patching the XML.

## Appendix C — Thresholds to re-verify for the FY under audit

Thresholds and due dates change with each Finance Act and notification. **Verify
each against the law as applicable to {FINANCIAL_YEAR} before using it, and
state in the working paper which year's rule you applied.** The list below is
the set of thresholds the tests reference:

| Item | Reference | Verify |
|---|---|---|
| Tax audit applicability | s.44AB (₹1 crore; ₹10 crore where cash receipts and payments ≤5%) | limit and the 5% test for the FY |
| Presumptive taxation | s.44AD / 44ADA / 44AE | limits for the FY |
| Cash expenditure disallowance | s.40A(3) — ₹10,000 (₹35,000 goods carriage) | unchanged? |
| Cash receipt bar | s.269ST — ₹2,00,000 | mode and aggregation rules |
| Loans/deposits in cash | s.269SS / 269T — ₹20,000 | — |
| MSME payment disallowance | s.43B(h) — 15/45 days, from AY 2024-25 | applicability to the FY |
| TDS on purchase of goods | s.194Q — ₹50 lakh, 0.1% | rate/threshold |
| TCS on sale of goods | s.206C(1H) — ₹50 lakh, 0.1% | interaction with 194Q |
| TDS interest / fee | s.201(1A) 1%/1.5% per month; s.234E ₹200/day | — |
| E-invoicing | AATO threshold (₹5 crore from 01-Aug-2023) and the 30-day reporting window for larger AATO | threshold and window for the FY |
| E-way bill | ₹50,000 consignment value (state variations apply) | state rules |
| ITC time limit | s.16(4) — 30 November of the following FY or annual-return date, whichever earlier | — |
| ITC on unpaid supplier | Rule 37 — 180 days; Rule 37A — supplier's 3B default | — |
| GST interest / late fee | s.50, s.47 | rates |
| CARO applicability | CARO 2020, from FY 2021-22 | exemptions for small/private companies (paid-up capital + reserves, borrowings, turnover tests) |
| CARO working-capital clause | 3(ii)(b) — limits over ₹5 crore | — |
| Audit trail | Rule 3(1), Companies (Accounts) Rules 2014, from 01-Apr-2023; reporting under Rule 11(g) | — |
| Schedule III ageing & ratios | from FY 2021-22 | Division applicable |
| CSR | s.135 — net worth ₹500 crore / turnover ₹1,000 crore / net profit ₹5 crore; 2% of average net profit | — |
| Depreciation | Schedule II (companies) vs s.32 blocks (tax) | rates/useful lives |

## Appendix D — Model discipline (why this prompt is built this way)

The model's job in this pipeline is **narrative, not arithmetic**. It decides
what to test, writes the query, reads the result, and explains the finding in
reviewable language. It never produces a figure, a due date, an applicability
conclusion or an ITC number by reasoning alone. If a number appears in a
deliverable, a shown query produced it.

That split is what makes the output defensible in front of a reviewer, a
regulator, or a tribunal — and it is the same rule the Continuous Audit Engine
in this repository enforces in code (see `CLAUDE.md`, "Deterministic code
computes every number; the model only explains").
