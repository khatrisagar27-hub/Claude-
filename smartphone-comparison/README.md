# Smartphone comparison workbook

A one-off deliverable, unrelated to the CAE and LexComply projects in this repo.

`Smartphone_Comparison_Aug2026.xlsx` compares the Galaxy Z Fold 7/6/5, Galaxy
S26/S25/S24/S23 Ultra and iPhone 17/16/15 for an India purchase decision, with
street prices captured on 26 August 2026, a weighted scorecard and a
recommendation.

Six sheets: **Read Me**, **Recommendation**, **Spec Comparison**,
**Price and Value**, **Scorecard**, **Best and Unique**.

## Rebuilding

```bash
pip install openpyxl
python build_comparison.py
python /root/.claude/skills/synced/xlsx/scripts/recalc.py Smartphone_Comparison_Aug2026.xlsx
```

`data.py` holds every device fact, price and rating; `build_comparison.py` only
does layout and formulas. Edit prices in `data.py` (or in column D of the
Price and Value sheet) and everything downstream recalculates.

Prices are a snapshot from public retail and price-tracker listings and go stale
quickly — re-check before quoting them.
