# Premium Fixed Asset Register (FAR) — Companies Act, 2013 (Schedule II)

`FAR_Schedule_II.xlsx` is a fully formula-driven Fixed Asset Register that
computes **year-wise depreciation** under **Schedule II of the Companies Act,
2013**, supporting both **SLM** (Straight Line) and **WDV** (Written Down
Value) methods. Change one cell and the entire register, reports and summary
recalculate.

> Open in **Microsoft Excel** or **Google Sheets**. The file is standard
> `.xlsx`; all cells are live formulas (no macros).

## Workbook structure

| Sheet | Purpose |
|-------|---------|
| **Input** | Control panel. The yellow cells drive everything: global depreciation **Method (SLM/WDV)**, default **residual %**, **first FY-end** (anchor for the year columns) and the **reporting FY-end**. Holds the **Schedule II useful-life master** (with each category mapped to its **Income-Tax block & rate**) and the **Income-Tax block master** (Sec. 32 / Appendix I WDV rates). |
| **FAR** | The single **Register of Fixed Assets** — one row per asset with master details, cost basis, **year-wise pro-rata depreciation + closing WDV** for each financial year, the position as on the reporting FY, plus **Schedule II extra-shift** (Single/Double/Triple/NESD) and **CARO 2020** compliance fields (physical-verification date, title-deed flag, remarks/components). |
| **Reports** | Year-wise total depreciation & net-block movement, and a **Category × Year** depreciation matrix. |
| **Summary** | Category-wise **Gross Block / Depreciation for the year / Accumulated Depreciation / Net Block** as on the reporting FY, a reconciliation check, and a disposals section. |
| **Income-Tax Dep Chart** | **Block-of-assets depreciation chart under Section 32** (WDV, Appendix I rates). Additions auto-flow from the FAR and are split by the **180-day rule**; you enter Opening WDV and any **additional depreciation u/s 32(1)(iia)**. Computes normal + half-rate + additional depreciation and closing WDV, and flags blocks that turn negative (short-term capital gain u/s 50). |
| **Book vs Tax (Def. Tax)** | **Deferred tax working (AS 22 / Ind AS 12)** reconciling Schedule II (book) vs Section 32 (tax) depreciation. A per-asset tax-WDV roll-forward (Appendix I rates + 180-day rule) gives year-wise tax depreciation; the sheet shows the year-wise difference, the deferred-tax charge/(credit), and the closing **DTL/(DTA)** = (Book WDV − Tax WDV) × tax rate. Headline deferred tax as on the reporting year sits at the top. |
| **Schedule III PPE Note** | The **Note to the financial statements for Property, Plant & Equipment** in Schedule III format — a movement schedule of Gross Block (Opening / Additions / Disposals / Closing), Depreciation (Opening / For the year / On disposals / Closing) and Net Block (current year vs previous year), by class of asset, with built-in reconciliation checks. Auto-built from the FAR for the selected reporting year. |
| **Notes & Compliance** | Plain-language notes on Schedule II, Income-Tax Sec. 32, and the **CARO 2020 clause 3(i)(a)–(e)** checklist, with sources and a disclaimer. |

## How to use

1. **Set the method** on `Input` → *Depreciation Method (Global)* = `SLM` or
   `WDV`. The whole workbook switches instantly.
2. **Set residual %** and the **First / Reporting FY-end** dates. The reporting
   date must equal one of the year columns (they step yearly from the first
   FY-end).
3. **Enter assets** on `FAR`: pick the **Asset Category** from the dropdown —
   the **useful life** and **WDV rate** fill in automatically from Schedule II.
   Fill cost, *Date Put to Use*, and (if sold) *Date of Sale/Disposal*.
4. Read off the year-wise depreciation across the green/gold columns, or jump to
   **Reports** / **Summary**.

## Depreciation logic (per Schedule II)

- **Depreciable amount** = Cost − Residual value (Residual = Cost × Residual %).
- **WDV rate** = `1 − (Residual ÷ Cost) ^ (1 ÷ Useful Life)`.
- **SLM charge** = Depreciable amount ÷ Useful Life.
- **Pro-rata by days**: each FY's charge is scaled by days the asset was *in
  use* during that year (from *Date Put to Use*, and only up to the disposal
  date in the year of sale).
- **Residual floor**: accumulated depreciation never reduces the carrying value
  below the residual value.
- **Disposal**: depreciation is charged up to the disposal date; the asset's
  closing WDV becomes 0 and it is excluded from the closing block in Summary.

## Income-Tax depreciation (Block of Assets — Section 32)

The **Income-Tax Dep Chart** is separate from the book (Companies Act) depreciation:

- Depreciation is on the **WDV of a block of assets**, not asset-by-asset. Rates
  (Appendix I): Buildings 10% (residential 5%, temporary 40%), Furniture 10%,
  Plant & Machinery 15%, Motor vehicles 15% (commercial/hire 30%), Computers &
  software 40%, Intangibles 25%, Books 40%, Ships 20%.
- **180-day rule**: an asset put to use for `< 180 days` in its year of
  acquisition gets only **50%** of the rate. The chart classifies every addition
  automatically from the FAR *Date Put to Use*.
- **Additional depreciation u/s 32(1)(iia)** (20% on eligible new plant &
  machinery) is an input column.
- `Closing WDV = Opening WDV + Additions − Sale proceeds − Depreciation`; if sale
  proceeds exceed the block, the value goes negative and is flagged for **STCG
  u/s 50**.

Set the **Income-Tax Computation FY** cell on that sheet to pick the year.

## Schedule II additions in this version

- **Extra-shift depreciation** — set *Shift Basis* per asset (Single / Double /
  Triple / NESD); double shift adds 50% and triple adds 100% to the charge.
- **CARO 2020 clause 3(i)** fields — physical-verification date, title-deed-in-
  company-name flag (auto-applies for immovables), and remarks for
  componentisation, revaluation or benami disclosures.

## Deferred tax (Book vs Tax — AS 22 / Ind AS 12)

The **Book vs Tax (Def. Tax)** sheet quantifies the timing difference between
book and tax depreciation:

- A per-asset **tax-WDV roll-forward** computes Section 32 depreciation for every
  year (full rate, or 50% in the year of acquisition if used `< 180 days`), held
  at cost until the asset is put to use and written off on disposal.
- For each year it shows: **Book Dep vs Tax Dep → Difference → Deferred Tax
  charge/(credit)**, and the closing **DTL/(DTA) = (Book WDV − Tax WDV) × tax
  rate**.
- Set the **applicable tax rate** at the top (default 25.168% u/s 115BAA; change
  for 115BAB / 25% / 30% + surcharge & cess).
- Book WDV > Tax WDV ⇒ **Deferred Tax Liability**; the reverse ⇒ **Deferred Tax
  Asset** (recognise only with reasonable/virtual certainty).

> The deferred-tax engine uses an asset-level approximation of the tax block. For
> the formal block computation (additional depreciation, disposals, STCG u/s 50)
> use the **Income-Tax Dep Chart** sheet.

## Schedule III PPE Note (Note to the accounts)

The **Schedule III PPE Note** is the disclosure-ready movement schedule:

- **Gross Block**: Opening + Additions − Disposals = Closing
- **Depreciation**: Opening + For the year − On disposals = Closing
- **Net Block**: Closing (current year) and Closing (previous year)

…by class of asset, for the **reporting year** selected on Input. A per-asset
working below the note pulls additions, disposals, opening accumulated
depreciation and the year's charge from the FAR, and two checks confirm
`Net = Gross − Depreciation` and that the charge ties back to the FAR. Intangible
assets should be shown in a separate note in the same format (footnoted on the
sheet).

## Customising

- **Add/edit asset categories or useful lives** directly in the Schedule II
  table on `Input` — the dropdown and lookups follow automatically.
- **Override a single asset's method or residual %** by typing a value over the
  formula in the `Method` / `Residual %` column on `FAR`.
- **More years**: regenerate with a larger `N_YEARS` in `build_far.py`.
- **More asset rows**: the register is pre-formatted with blank, formula-ready
  rows; just keep typing.

## Regenerating

```bash
pip install openpyxl
python3 build_far.py      # writes FAR_Schedule_II.xlsx
```

`build_far.py` is the generator; the model was independently verified for SLM,
WDV, pro-rata timing, residual floor and disposal handling.
