# Planning documents

Consulting-style planning artifacts for factory-erp, produced before the
corresponding build — per the methodology in `BRD_Sales_Planning_Phase1.docx`
itself (§ "Out of Scope"): BRD → process flow → data model → control matrix
→ architecture notes, reviewed before code.

## Sales & Planning (PPC) — Phase 1

`BRD_Sales_Planning_Phase1.docx` — the Sales Order → Master Production Plan →
Material Requirement Plan flow that sits upstream of the already-built
Inventory/Production/Machine modules. Covers: process flow, functional
requirements, data model (new tables + the one field added to the existing
WorkOrder), a control matrix tagged by enforcement layer (Excel-and-backend
vs. backend-only), and an architecture note on where each piece lands in
`factory-erp/backend` and `factory-erp/excel`. Appendices carry the full
eight-module roadmap and the complete control-layer reference for context
beyond this phase.

This document is the plan, not the build — no code or workbook changes were
made against it yet.

### Regenerating it

```bash
cd factory-erp/docs
npm install docx      # not committed — package.json/package-lock.json are
node build_brd.js     # writes BRD_Sales_Planning_Phase1.docx
```
