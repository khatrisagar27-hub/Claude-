# Declaration of Income — Generator

A self-contained, browser-based tool that turns a **computation of income**
(in *any* structure) into a formal, printable **Declaration of Income** signed
by the assessee — built for Indian income-tax practice (Income-tax Act, 1961).

No install, no build, no server, no data leaves the browser. Just open
`index.html`.

## What it does

1. **Upload the computation PDF** (the **Upload Computation** button) and the
   tool reads it *in the browser* (via pdf.js) and auto-extracts the assessee's
   identity — Name, PAN, Father's Name, Status, Address, A.Y./F.Y. — together
   with every head of income and the Chapter VI-A deductions. The raw extracted
   text is also loaded into the box so you can verify it. Tested against
   Express-ITR / Winman-style computations; layout changes are tolerated via
   label matching, with a generic parser as fallback. (Head totals are read
   whether they sit on the head's own line or wrap to the next line.)
   *(Alternatively)* **Paste a computation of income in any format** — a table,
   a bullet list, text copied from a PDF/Excel, dot-leader lines
   (`Salary ...... 9,50,000`), etc. Each line that contains an amount is detected.
2. **Auto-classifies** every line into the five heads of income, Chapter VI-A
   deductions, or informational rows, using keyword rules
   (salary, house property, business/PGBP, capital gains, other sources,
   80C/80D/80TTA…).
3. **Review & edit** — fix any label, re-classify a head, correct an amount,
   add or delete rows. Gross Total Income, total deductions and Total Income
   (rounded off under **Sec. 288A**) recompute live.
4. **Generates the declaration letter** with the assessee's particulars, the
   computation table, amount in words, the customary true-and-correct
   declaration clause, and a signature block.
5. **Print / Save as PDF** or copy the text.

## Usage

Open `index.html` in any modern browser. Then:

- Click **Upload Computation (PDF)** and pick the computation file — assessee
  details and income heads fill in automatically. (Or fill the **Assessee
  Details** by hand and paste the computation, then **Parse pasted text**;
  **Load sample** shows a worked example.)
- Review the figures in panel 3 — edit, re-classify or add rows as needed.
- Click **Generate Declaration**, then **Print / Save as PDF**.

> PDF reading uses Mozilla's pdf.js (v3.11.174, Apache-2.0), embedded directly
> inside `index.html` as base64. There are **no external files and no internet
> needed** — open or share the single HTML file anywhere. On `file://` pages the
> library runs on the main thread (a harmless "fake worker" console note);
> parsing a few-page computation is instant. Scanned/image-only PDFs have no
> selectable text — paste the figures in that case.

## Notes on the parsing

- Amounts may use `Rs.`, `₹`, `/-`, Indian comma grouping (`9,50,000`),
  decimals, brackets/`-`/"loss" for negatives.
- Lines that are computed totals (`Gross Total Income`, `Total Income`,
  `Tax payable`, `TDS`, `Cess`…) are skipped from the line items — the tool
  recomputes them so the declaration is internally consistent.
- Anything mis-classified is one dropdown away from being fixed; nothing is
  locked.

## Disclaimer

This tool assists in drafting a declaration from figures you provide. It does
**not** compute tax liability and is not a substitute for professional
judgement. Always verify the generated figures and wording before the assessee
signs.
