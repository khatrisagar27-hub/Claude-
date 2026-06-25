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
| **Input** | Control panel. The yellow cells drive everything: global depreciation **Method (SLM/WDV)**, default **residual %**, **first FY-end** (anchor for the year columns) and the **reporting FY-end**. Also holds the **Schedule II useful-life master table** used for lookups and the category dropdown. |
| **FAR** | The single **Register of Fixed Assets** — one row per asset with master details, cost basis, and **year-wise pro-rata depreciation + closing WDV** for each financial year, plus the position (Dep / Acc. Dep / WDV / Status) as on the reporting FY. |
| **Reports** | Year-wise total depreciation & net-block movement, and a **Category × Year** depreciation matrix. |
| **Summary** | Category-wise **Gross Block / Depreciation for the year / Accumulated Depreciation / Net Block** as on the reporting FY, a reconciliation check, and a disposals section. |

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
