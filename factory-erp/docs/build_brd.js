const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, AlignmentType, BorderStyle, PageBreak, TableOfContents,
  Header, Footer, PageNumber, VerticalAlign,
} = require("docx");
const fs = require("fs");

// ---------------------------------------------------------------------------
// Page: US Letter. Table width budget: 12240 - 2*1080 (0.75" margins) = 10080 DXA.
// ---------------------------------------------------------------------------
const PAGE_WIDTH = 12240;
const PAGE_HEIGHT = 15840;
const MARGIN = 1080; // 0.75"
const TABLE_WIDTH = PAGE_WIDTH - 2 * MARGIN; // 10080

const NAVY = "1F2937";
const SLATE = "475569";
const LIGHT = "F1F5F9";
const AMBER = "FEF3C7";
const RED = "FECACA";
const GREEN = "DCFCE7";

const FONT = "Calibri";

function h1(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_1, spacing: { before: 400, after: 200 } });
}
function h2(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_2, spacing: { before: 300, after: 150 } });
}
function h3(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_3, spacing: { before: 200, after: 100 } });
}
function body(text, opts = {}) {
  return new Paragraph({
    children: [new TextRun({ text, font: FONT, size: 21, ...opts })],
    spacing: { after: 160 },
  });
}
function note(text) {
  return new Paragraph({
    children: [new TextRun({ text, italics: true, color: SLATE, font: FONT, size: 19 })],
    spacing: { after: 160 },
  });
}
function bullet(text, level = 0) {
  return new Paragraph({
    children: [new TextRun({ text, font: FONT, size: 21 })],
    bullet: { level },
    spacing: { after: 80 },
  });
}
function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}

function cell(text, { width, header = false, shade = null, bold = false, color = null, align = AlignmentType.LEFT } = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: shade ? { type: ShadingType.CLEAR, fill: shade } : undefined,
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    children: [
      new Paragraph({
        alignment: align,
        children: [
          new TextRun({
            text,
            bold: header || bold,
            color: header ? "FFFFFF" : color || "000000",
            font: FONT,
            size: header ? 19 : 19,
          }),
        ],
      }),
    ],
  });
}

// rows: array of arrays of strings; widths: array of DXA widths summing to TABLE_WIDTH
function makeTable(headerRow, dataRows, widths, opts = {}) {
  const rows = [];
  rows.push(
    new TableRow({
      tableHeader: true,
      cantSplit: true,
      children: headerRow.map((t, i) => cell(t, { width: widths[i], header: true, shade: NAVY })),
    })
  );
  dataRows.forEach((r, idx) => {
    const stripe = idx % 2 === 1 ? LIGHT : null;
    rows.push(
      new TableRow({
        cantSplit: true,
        children: r.map((t, i) => {
          const rowOpts = opts.cellShade ? opts.cellShade(r, i) : null;
          return cell(String(t), { width: widths[i], shade: rowOpts || stripe });
        }),
      })
    );
  });
  return new Table({
    width: { size: TABLE_WIDTH, type: WidthType.DXA },
    columnWidths: widths,
    rows,
    borders: {
      top: { style: BorderStyle.SINGLE, size: 2, color: "CBD5E1" },
      bottom: { style: BorderStyle.SINGLE, size: 2, color: "CBD5E1" },
      left: { style: BorderStyle.SINGLE, size: 2, color: "CBD5E1" },
      right: { style: BorderStyle.SINGLE, size: 2, color: "CBD5E1" },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 1, color: "E2E8F0" },
      insideVertical: { style: BorderStyle.SINGLE, size: 1, color: "E2E8F0" },
    },
  });
}

// ===========================================================================
// CONTENT
// ===========================================================================

const children = [];

// --- Title page ---------------------------------------------------------
children.push(
  new Paragraph({ spacing: { before: 1800 }, children: [] }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "BUSINESS REQUIREMENT DOCUMENT", bold: true, size: 44, color: NAVY, font: FONT })],
    spacing: { after: 200 },
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Factory ERP — Sales & Planning (PPC) Module", size: 30, color: SLATE, font: FONT })],
    spacing: { after: 100 },
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Phase 1 of the Manufacturing Operations & Control System roadmap", size: 22, italics: true, color: SLATE, font: FONT })],
    spacing: { after: 1200 },
  })
);

const docControlRows = [
  ["Document", "BRD — Sales & Planning (PPC) Module, Phase 1"],
  ["Project", "Factory ERP — Stock, Machines & Production (factory-erp/)"],
  ["Phase", "1 of 4 — see Appendix A for the full roadmap and phase sequence"],
  ["Version", "1.0"],
  ["Date", "07 September 2026"],
  ["Status", "Draft — for review"],
  ["Prepared by", "Claude Code, on behalf of the project owner"],
  ["Distribution", "Internal — project owner"],
];
children.push(
  makeTable(
    ["Field", "Value"],
    docControlRows,
    [2400, TABLE_WIDTH - 2400]
  )
);
children.push(pageBreak());

// --- 1. Purpose & Scope --------------------------------------------------
children.push(h1("1. Purpose & Scope"));
children.push(body(
  "This document specifies the Sales and Planning (PPC — Production Planning & Control) module: " +
  "the upstream half of the factory-erp flow, from customer enquiry through to a Material Requirement " +
  "Plan handed off to production. It is Phase 1 of an eight-module roadmap (Sales, Planning, Inventory, " +
  "Production, Machine, Quality, Dispatch, MIS — full detail in Appendix A). Inventory, Production, and " +
  "Machine already exist in factory-erp/backend and factory-erp/excel; this document defines what gets " +
  "added upstream of them, and how the two connect."
));
children.push(body("Explicitly out of scope for this document (deferred to later-phase BRDs):"));
children.push(bullet("Procurement execution — PO issuance, vendor master, goods receipt, incoming quality inspection"));
children.push(bullet("Quality module (in-process/FG inspection, customer complaints, CAPA)"));
children.push(bullet("Dispatch, invoicing, delivery tracking"));
children.push(bullet("Consolidated MIS reporting beyond what the existing Dashboard already covers"));
children.push(note(
  "Phase 1 produces a Material Requirement Plan that flags a shortfall against on-hand stock — it does " +
  "not execute a purchase. Procurement is Phase 3 (Appendix A)."
));

// --- 2. Business Objectives -----------------------------------------------
children.push(h1("2. Business Objectives"));
children.push(bullet("No sales order is lost, duplicated, or actioned without a record."));
children.push(bullet("Delivery dates committed to customers are checked against real material, machine, and capacity constraints — not promised blind."));
children.push(bullet("Every confirmed order converts into a production plan the shop floor can execute, and that plan is what the existing Work Order module runs against."));
children.push(bullet("A shortfall between what production needs and what stock has is visible before the shop floor discovers it mid-run."));
children.push(bullet("Management can see order backlog and delivery risk without asking the shop floor for a status update."));

// --- 3. Process Flow -------------------------------------------------------
children.push(h1("3. Process Flow — Phase 1 Scope"));
children.push(body("Steps 1–8 are new in Phase 1. Step 9 (Production Work Order) is the existing Production module — this flow feeds it, not replaces it."));

const flowRows = [
  ["1", "Customer Enquiry", "Informal — logged for conversion tracking, not a transaction", "—", "Enquiry record"],
  ["2", "Sales Order", "Customer, product(s), quantity, requested delivery date captured against a unique order number", "Enquiry (optional)", "Sales Order (draft)"],
  ["3", "Order Confirmation", "Order reviewed and confirmed — status change, not a new record", "Sales Order (draft)", "Sales Order (confirmed)"],
  ["4", "Delivery Date Commitment", "Committed date set, which may differ from the customer's requested date; reason recorded if it does", "Confirmed order", "Committed delivery date"],
  ["5", "Order Prioritization", "Open confirmed orders ranked (delivery date, customer priority, order value)", "Confirmed orders", "Priority-ordered backlog"],
  ["6", "Master Production Plan", "Backlog aggregated into planned production by product, machine, and period", "Priority-ordered backlog", "Draft Production Plan"],
  ["7", "Material / Machine / Capacity Check", "Plan checked against on-hand stock (Analytics_Stock), machine calendar, and rated capacity — three checks, one gate", "Draft Production Plan", "Checked / flagged plan"],
  ["8", "Material Requirement Plan", "BOM explosion of the plan's quantities vs. on-hand stock; shortfall listed by SKU", "Checked plan + BOM + Stock", "MRP shortfall list"],
  ["9", "Production Work Order (existing module)", "Where stock is sufficient, a Work Order is created directly, referencing the Sales Order", "MRP output (no shortfall)", "Work Order"],
];
children.push(makeTable(
  ["#", "Process Step", "Description", "Input", "Output"],
  flowRows,
  [450, 1900, 4200, 1730, 1800]
));
children.push(note(
  "Where the MRP step finds a shortfall, the order is flagged for procurement rather than blocked silently " +
  "— Phase 1 produces that flag; Phase 3 (Procurement) is what acts on it."
));

children.push(pageBreak());

// --- 4. Functional Requirements --------------------------------------------
children.push(h1("4. Functional Requirements"));

function frTable(rows) {
  return makeTable(
    ["ID", "Requirement", "Business Rule", "Priority"],
    rows,
    [1000, 3800, 4180, 1100]
  );
}

children.push(h2("4.1 Sales"));
children.push(frTable([
  ["FR-SAL-01", "Capture a Customer Master", "Code, name, contact, credit terms. Referenced by every Sales Order.", "Must"],
  ["FR-SAL-02", "Capture a Sales Order", "Unique order number, customer, one or more product lines with quantity, requested delivery date.", "Must"],
  ["FR-SAL-03", "Reject duplicate order numbers", "See Control Matrix CTL-SAL-01. Enforced at the database in the backend edition; formula-flagged in Excel.", "Must"],
  ["FR-SAL-04", "Support an Order Confirmation status distinct from draft", "A draft order can be edited freely; a confirmed order changing quantity/date is a tracked amendment, not a silent edit.", "Must"],
  ["FR-SAL-05", "Record a Committed Delivery Date separate from the customer's Requested Delivery Date", "If they differ, a reason is required (see CTL-SAL-02).", "Should"],
]));

children.push(h2("4.2 Planning (PPC)"));
children.push(frTable([
  ["FR-PLN-01", "Rank open confirmed orders", "Sort key configurable: delivery date, customer priority tier, or order value — not hardcoded to one.", "Must"],
  ["FR-PLN-02", "Generate a Master Production Plan", "Aggregates ranked orders into planned Work Orders by product, machine, and period (day/week).", "Must"],
  ["FR-PLN-03", "Check material availability per planned line", "Against Analytics_Stock on-hand qty (existing) — reuses factory-erp/backend/app/analytics/stock.py, not a new calculation.", "Must"],
  ["FR-PLN-04", "Check machine availability per planned line", "Against the Machine master and existing/other planned bookings in the same window — avoids double-booking a machine.", "Must"],
  ["FR-PLN-05", "Check capacity per planned line", "Planned hours vs. machine rated_capacity_per_hour (existing field) within the period.", "Must"],
  ["FR-PLN-06", "Compute a Material Requirement Plan", "BOM explosion (existing BOMItem table) of planned quantities, netted against on-hand stock; output is a shortfall list by SKU, not a purchase order.", "Must"],
  ["FR-PLN-07", "Create a Work Order directly where stock is sufficient", "Reuses the existing Production module unchanged — Phase 1 adds a sales_order_line_id reference on Work Order, nothing else.", "Must"],
  ["FR-PLN-08", "Flag a Purchase Requirement where stock is insufficient", "List only in Phase 1 — no PO is generated; Phase 3 (Procurement) consumes this list.", "Should"],
  ["FR-PLN-09", "A plan cannot generate Work Orders until its status is Approved", "See CTL-PLN-01 — backend-only; not enforceable in the Excel edition (see §7).", "Must"],
]));

children.push(pageBreak());

// --- 5. Data Model ----------------------------------------------------------
children.push(h1("5. Data Model — Phase 1"));
children.push(body("New tables only. Nothing below duplicates or modifies Product, BOMItem, Machine, StockMovement, or the existing analytics — Phase 1 sits upstream of them and links in via foreign key."));

children.push(h2("5.1 New Entities"));

const entityRows = [
  ["Customer", "code (unique), name, contact, credit_terms", "—", "Master data, mirrors the existing Product/Machine pattern."],
  ["SalesOrder", "order_number (unique), customer_id, order_date, requested_delivery_date, committed_delivery_date, priority, status", "customer_id → Customer", "status: draft / confirmed / in_production / completed / cancelled."],
  ["SalesOrderLine", "sales_order_id, product_id, quantity, notes", "sales_order_id → SalesOrder; product_id → Product (existing)", "One row per product on an order — reuses the existing Product master."],
  ["ProductionPlan", "plant_id, period_start, period_end, status", "plant_id → Plant (existing)", "status: draft / approved. Work Orders cannot be generated from a draft plan — CTL-PLN-01."],
  ["ProductionPlanLine", "plan_id, sales_order_line_id, product_id, machine_id, planned_qty, planned_start, planned_end", "plan_id → ProductionPlan; sales_order_line_id → SalesOrderLine; machine_id → Machine (existing)", "On plan approval, each line generates one WorkOrder row (existing table) carrying this line's reference forward."],
];
children.push(makeTable(
  ["Entity", "Key Fields", "Relationships", "Notes"],
  entityRows,
  [1700, 2900, 2600, 2880]
));

children.push(h2("5.2 One Change to an Existing Table"));
children.push(body("WorkOrder (factory-erp/backend/app/models/production.py) gains one nullable field:"));
children.push(bullet("sales_order_line_id — nullable FK to SalesOrderLine. Nullable because a Work Order created outside this flow (as today) has no order to trace back to; one created by Phase 1's planning flow always sets it."));
children.push(note("This is the only change to already-shipped code in this document. Everything else is additive."));

children.push(pageBreak());

// --- 6. Control Matrix -------------------------------------------------------
children.push(h1("6. Control Matrix — Phase 1"));
children.push(body(
  "Each control is tagged by where it can actually be enforced. \"Both\" means a real formula/validation check " +
  "works in either edition. \"Backend only\" means the control requires code that runs before a save — approval " +
  "gates, role checks, change logs — which the macro-free Excel edition structurally cannot do (see the workbook's " +
  "own README sheet). Reopening VBA in Excel was considered and declined to preserve OneDrive/SharePoint " +
  "co-authoring; the trade-off is that these specific controls live in the backend edition only."
));

const ctlRows = [
  ["CTL-SAL-01", "Sales Order", "No duplicate order numbers", "Both", "Backend: DB unique constraint. Excel: COUNTIF flag on entry — a soft warning, not a hard block."],
  ["CTL-SAL-02", "Sales Order", "Reason required when committed date differs from requested date", "Both", "A required-field check, not a workflow gate — achievable with data validation in Excel."],
  ["CTL-PLN-01", "Production Plan", "Work Orders cannot be generated from a plan that isn't Approved", "Backend only", "This is a workflow gate on an action (creating rows), not a data check — Excel cannot block an action."],
  ["CTL-PLN-02", "Production Plan", "Approval required above a value/quantity threshold", "Backend only", "Requires a role check at approval time — RBAC, not a formula."],
  ["CTL-PLN-03", "MRP", "Shortfall list is read-only, recalculates from source data only", "Both", "A calculated view, not a permission — already the pattern used throughout the Excel edition."],
  ["CTL-USR-01", "Users", "Role-based access; protected masters", "Backend only", "Sheet/workbook passwords in Excel are trivially removable — not real access control. Backend already has User.role and a require_role dependency (factory-erp/backend/app/api/v1/deps.py) — Phase 1 extends its use to plan approval."],
  ["CTL-AUD-01", "All records", "Automatic change log with who/when", "Backend only", "created_at/updated_at already exist on every model. A field-level change log (what changed, by whom) does not exist yet — new in Phase 1's backend work, not present today."],
];
children.push(makeTable(
  ["ID", "Process", "Control", "Layer", "Notes"],
  ctlRows,
  [1150, 1400, 2900, 1400, 3230]
));

children.push(pageBreak());

// --- 7. System Architecture --------------------------------------------------
children.push(h1("7. System Architecture Notes"));

children.push(h2("7.1 Backend (factory-erp/backend)"));
children.push(bullet("New models: Customer, SalesOrder, SalesOrderLine, ProductionPlan, ProductionPlanLine — app/models/sales.py, app/models/planning.py."));
children.push(bullet("One added field: WorkOrder.sales_order_line_id (nullable)."));
children.push(bullet("New API modules: app/api/v1/sales.py, app/api/v1/planning.py, registered in router.py."));
children.push(bullet("New analytics: order backlog by priority, delivery performance (committed vs. actual) — app/analytics/planning.py, same pattern (plain functions over a DB session, pytest-covered against in-memory SQLite) as the existing OEE/stock/production modules."));
children.push(bullet("RBAC: extend the existing require_role dependency to the plan-approval endpoint (CTL-PLN-01/02) and add a change-log table for CTL-AUD-01."));
children.push(bullet("One Alembic migration covers all of the above."));

children.push(h2("7.2 Excel edition (factory-erp/excel)"));
children.push(bullet("New sheets: Customers, SalesOrders, SalesOrderLines, ProductionPlan, ProductionPlanLines — same append-only-table + dropdown-validation pattern as the existing Machines/Products/StockMovements sheets."));
children.push(bullet("New Analytics_MRP sheet: BOM explosion formula reusing the existing BOM sheet's ComponentStdCost/LineStdCost helper columns, netted against Analytics_Stock's OnHand column — no new calculation logic, a new arrangement of existing ones."));
children.push(bullet("Plan \"Approved\" status is a dropdown cell, same as Machine Status or Work Order Status today — a label, not a gate. CTL-PLN-01/02 are out of reach here by design (§6)."));

children.push(pageBreak());

// --- 8. Out of Scope ------------------------------------------------------
children.push(h1("8. Out of Scope — Deferred to Later Phases"));
const oosRows = [
  ["Procurement execution", "PO issuance, vendor master, goods receipt, incoming inspection", "Phase 3 (candidate)"],
  ["Quality module", "In-process/FG inspection, customer complaints, CAPA", "Phase 2 (candidate)"],
  ["Dispatch", "Ready-stock tracking, vehicle/LR, invoicing, delivery status", "Phase 3 (candidate)"],
  ["Consolidated MIS", "Daily/weekly/monthly management reporting beyond the existing Dashboard", "Phase 4"],
  ["VBA-based enforcement in Excel", "Reopening macros to make CTL-PLN-01/02/CTL-USR-01/CTL-AUD-01 enforceable in the workbook", "Declined — see §6"],
];
children.push(makeTable(["Item", "Covers", "When"], oosRows, [2500, 4900, 2680]));
children.push(note("Phase 2/3 order is not yet fixed — options put to the project owner were \"Quality + Machine + Control layer\" or \"Procurement + Dispatch\"; whichever is chosen gets its own BRD before build starts, per this same methodology."));

children.push(pageBreak());

// --- Appendix A ------------------------------------------------------------
children.push(h1("Appendix A — Full Eight-Module Roadmap"));
children.push(body("For context beyond Phase 1. Condensed from the project owner's original module breakdown."));
const roadmapRows = [
  ["1. Sales", "Capture demand", "Customer/order master, confirmed backlog", "Phase 1 — this document"],
  ["2. Planning (PPC)", "Convert demand into an executable, checked plan", "Master Production Plan, Material Requirement Plan", "Phase 1 — this document"],
  ["3. Inventory", "Raw material → consumables → packing → WIP → FG → scrap ledgers", "On-hand qty, ageing, reorder, valuation, turnover", "Built — factory-erp/backend/app/analytics/stock.py"],
  ["4. Production", "Execute work orders; track output, yield, rejection", "Work Order, RejectionLog, material yield/cost per unit", "Built — factory-erp/backend/app/models/production.py"],
  ["5. Machine", "Availability, downtime, maintenance", "OEE, downtime Pareto, utilization", "Built — factory-erp/backend/app/analytics/oee.py, downtime.py"],
  ["6. Quality", "Incoming/in-process/FG inspection, complaints, CAPA", "Inspection records, CAPA tracking", "Future"],
  ["7. Dispatch", "Ready stock → vehicle → invoice → delivery", "Dispatch schedule, invoice reference, delivery status", "Future"],
  ["8. MIS", "Daily/weekly/monthly management reporting", "Consolidated dashboards across all modules", "Partially built — Dashboard sheet/page; full cross-module MIS is future work"],
];
children.push(makeTable(
  ["Module", "Purpose", "Key Outputs", "Status"],
  roadmapRows,
  [1600, 2600, 3200, 2680]
));

children.push(pageBreak());

// --- Appendix B --------------------------------------------------------
children.push(h1("Appendix B — Full Control Layer Reference"));
children.push(body("The project owner's complete control-layer proposal, tagged by enforcement layer. CTL-SAL-01 through CTL-AUD-01 above are the Phase 1 subset; the remainder apply to modules covered in later-phase BRDs and are listed here for continuity."));
const fullCtlRows = [
  ["Sales Order", "No duplicate order numbers", "Both", "CTL-SAL-01 above."],
  ["Production", "Cannot start without an approved production plan", "Backend only", "CTL-PLN-01 above."],
  ["Material Issue", "Cannot exceed available stock, or requires authorization", "Both (limit check) / Backend only (authorization override)", "The limit check is a formula in both editions; an override requiring a second approver is backend-only."],
  ["Purchase", "Approval required above a threshold", "Backend only", "Phase 3 (Procurement) scope."],
  ["Machine", "Downtime reason is mandatory", "Both", "Already enforced in the shipped Excel edition and backend — dropdown/required field, not free text."],
  ["Dispatch", "Cannot dispatch more than available finished goods", "Both", "Phase 3 (Dispatch) scope — same pattern as the Material Issue limit check."],
  ["Inventory", "Physical stock variance reporting", "Both", "A comparison calculation (counted vs. ledger), not a permission — buildable in either edition when a physical-count entry point exists."],
  ["Costing", "Standard vs. actual variance analysis", "Both", "Standard cost already exists on Product; actual-cost capture and the variance calculation are future scope."],
  ["Users", "Role-based access, protected masters", "Backend only", "CTL-USR-01 above."],
  ["Audit", "Automatic change log and timestamps", "Backend only", "CTL-AUD-01 above."],
];
children.push(makeTable(
  ["Process", "Control", "Layer", "Notes"],
  fullCtlRows,
  [1600, 3200, 2200, 3080]
));

// ===========================================================================
// Assemble document
// ===========================================================================
const doc = new Document({
  styles: {
    default: {
      document: { run: { font: FONT, size: 21 } },
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, color: NAVY, font: FONT },
        paragraph: { spacing: { before: 400, after: 200 }, border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: NAVY, space: 4 } } },
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 25, bold: true, color: NAVY, font: FONT },
        paragraph: { spacing: { before: 300, after: 150 } },
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, color: SLATE, font: FONT },
        paragraph: { spacing: { before: 200, after: 100 } },
      },
    ],
  },
  sections: [
    {
      properties: {
        page: {
          size: { width: PAGE_WIDTH, height: PAGE_HEIGHT },
          margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN },
        },
      },
      headers: {
        default: new Header({
          children: [
            new Paragraph({
              alignment: AlignmentType.RIGHT,
              children: [new TextRun({ text: "Factory ERP BRD — Sales & Planning, Phase 1", size: 16, color: SLATE, font: FONT })],
            }),
          ],
        }),
      },
      footers: {
        default: new Footer({
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              children: [
                new TextRun({ text: "Page ", size: 16, color: SLATE, font: FONT }),
                new TextRun({ children: [PageNumber.CURRENT], size: 16, color: SLATE, font: FONT }),
                new TextRun({ text: " of ", size: 16, color: SLATE, font: FONT }),
                new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 16, color: SLATE, font: FONT }),
              ],
            }),
          ],
        }),
      },
      children,
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync("BRD_Sales_Planning_Phase1.docx", buf);
  console.log("Wrote BRD_Sales_Planning_Phase1.docx");
});
