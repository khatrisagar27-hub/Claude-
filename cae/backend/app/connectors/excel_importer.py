"""Parse uploaded Excel/CSV files into transaction tables."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


_SIGNALS: dict[str, list[str]] = {
    "sales_invoices":    ["invoice", "customer", "sale", "revenue", "irn", "eway", "e_way", "taxable", "cgst", "sgst", "igst"],
    "purchase_invoices": ["vendor", "supplier", "purchase", "po_no", "grn", "itc", "receipt", "payable"],
    "journal_entries":   ["debit", "credit", "gl_account", "voucher", "narration", "ledger", "je_", "journal"],
    "bank_transactions": ["bank", "transaction", "transfer", "upi", "neft", "rtgs", "balance", "cheque", "remit"],
    "inventory":         ["warehouse", "stock", "material", "quantity", "movement", "sku", "item_code", "goods"],
    "payroll":           ["salary", "employee", "payroll", "pf_", "esi", "tds", "deduction", "net_pay", "gross_pay"],
}

_FIELD_ALIASES: dict[str, list[str]] = {
    # sales / purchase shared
    "invoice_number":  ["invoice_no", "invoice_number", "inv_no", "inv_number", "bill_no", "bill_number"],
    "invoice_date":    ["invoice_date", "inv_date", "bill_date", "date"],
    "total_amount":    ["total_amount", "total_value", "invoice_value", "amount", "net_amount"],
    "taxable_amount":  ["taxable_amount", "taxable_value", "taxable"],
    "cgst_amount":     ["cgst_amount", "cgst"],
    "sgst_amount":     ["sgst_amount", "sgst"],
    "igst_amount":     ["igst_amount", "igst"],
    "customer_id":     ["customer_id", "customer_code", "customer"],
    "vendor_id":       ["vendor_id", "vendor_code", "vendor", "supplier_id", "supplier"],
    # journal entries
    "voucher_number":  ["voucher_number", "je_no", "voucher_no", "journal_no"],
    "entry_date":      ["entry_date", "je_date", "posting_date", "date"],
    "total_debit":     ["total_debit", "debit", "dr_amount"],
    "total_credit":    ["total_credit", "credit", "cr_amount"],
    "narration":       ["narration", "description", "remarks", "notes"],
    # bank
    "transaction_date":   ["transaction_date", "txn_date", "value_date", "date"],
    "amount":             ["amount", "txn_amount", "transaction_amount"],
    "transaction_type":   ["transaction_type", "txn_type", "dr_cr", "type"],
    "reference_number":   ["reference_number", "reference_no", "ref_no", "cheque_no", "utr"],
    "counterparty_name":  ["counterparty_name", "party_name", "beneficiary", "sender", "payee"],
    "transaction_mode":   ["transaction_mode", "channel", "mode", "payment_mode"],
    # inventory
    "movement_date":   ["movement_date", "date", "posting_date"],
    "item_code":       ["item_code", "material_code", "sku", "product_code"],
    "item_name":       ["item_name", "material_name", "product_name", "description"],
    "warehouse_from":  ["warehouse_from", "warehouse", "location", "store"],
    "movement_type":   ["movement_type", "type", "transaction_type"],
    "quantity":        ["quantity", "qty", "units"],
    "unit_cost":       ["unit_cost", "uom_rate", "rate", "price"],
    "total_value":     ["total_value", "value", "amount"],
    # payroll
    "employee_id":     ["employee_id", "emp_id", "staff_id"],
    "gross_earnings":  ["gross_earnings", "gross_pay", "gross_salary", "ctc"],
    "total_deductions":["total_deductions", "deductions", "total_deduction"],
    "net_pay":         ["net_pay", "net_salary", "take_home"],
    "pay_period_year": ["pay_period_year", "period_year", "year"],
    "pay_period_month":["pay_period_month", "period_month", "month"],
}

_TYPE_LABELS = {
    "sales_invoices":    "Sales Invoices",
    "purchase_invoices": "Purchase / Vendor Invoices",
    "journal_entries":   "Journal Entries",
    "bank_transactions": "Bank Transactions",
    "inventory":         "Inventory Movements",
    "payroll":           "Payroll Records",
}


def _fuzzy_match_column(target_aliases: list[str], candidates: list[str]) -> str | None:
    c_lower = {c: c.lower().replace(" ", "_").replace("-", "_") for c in candidates}
    for alias in target_aliases:
        alias_n = alias.lower().replace(" ", "_").replace("-", "_")
        for orig, norm in c_lower.items():
            if alias_n == norm or alias_n in norm or norm in alias_n:
                return orig
    return None


class ExcelImporter:
    def __init__(self, db: "Session", company_id: str):
        self.db = db
        self.company_id = uuid.UUID(company_id)

    @staticmethod
    def detect_schema(file_path: str) -> dict:
        """Auto-detect data type and map columns from any file structure."""
        import pandas as pd
        import math

        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path, nrows=5)
        else:
            df = pd.read_excel(file_path, nrows=5)

        columns_found = list(df.columns)
        cols_lower = [str(c).lower().replace(" ", "_").replace("-", "_") for c in columns_found]

        # Score each data type
        scores: dict[str, int] = {}
        for dtype, signals in _SIGNALS.items():
            score = 0
            for signal in signals:
                for col in cols_lower:
                    if signal in col:
                        score += 1
                        break
            scores[dtype] = score

        best_type = max(scores, key=lambda k: scores[k])
        best_score = scores[best_type]
        total_signals = len(_SIGNALS[best_type])
        confidence = round(best_score / total_signals, 2) if total_signals else 0.0

        # Map known fields to actual columns
        column_mapping: dict[str, str] = {}
        for field, aliases in _FIELD_ALIASES.items():
            match = _fuzzy_match_column(aliases, columns_found)
            if match:
                column_mapping[field] = match

        mapped_cols = set(column_mapping.values())
        unmapped = [c for c in columns_found if c not in mapped_cols]

        # Preview rows (first 3, convert NaN to None)
        preview_rows = []
        for _, row in df.head(3).iterrows():
            clean = {}
            for k, v in row.items():
                if isinstance(v, float) and math.isnan(v):
                    clean[str(k)] = None
                else:
                    clean[str(k)] = str(v) if v is not None else None
            preview_rows.append(clean)

        return {
            "detected_type": best_type,
            "detected_label": _TYPE_LABELS.get(best_type, best_type),
            "confidence": confidence,
            "confidence_pct": int(confidence * 100),
            "all_scores": scores,
            "columns_found": columns_found,
            "column_mapping": column_mapping,
            "unmapped_columns": unmapped,
            "preview_rows": preview_rows,
            "total_rows": len(df),
        }

    def import_file(self, file_path: str, file_type: str, detected_type: str | None = None) -> dict:
        import pandas as pd
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        resolved_type = file_type
        if file_type == "auto":
            resolved_type = detected_type or self.detect_schema(file_path)["detected_type"]

        importers = {
            "sales_invoices": self._import_sales,
            "purchase_invoices": self._import_purchases,
            "journal_entries": self._import_journal_entries,
            "bank_transactions": self._import_bank,
            "inventory": self._import_inventory,
            "payroll": self._import_payroll,
        }
        fn = importers.get(resolved_type)
        if not fn:
            return {"error": f"Unknown file type: {resolved_type}", "rows_imported": 0}
        result = fn(df)
        result["detected_type"] = resolved_type
        return result

    def _import_sales(self, df) -> dict:
        from app.models.transaction import SalesInvoice
        imported = 0
        errors = []
        for _, row in df.iterrows():
            try:
                total = self._decimal(row.get("total_amount", row.get("total_value", 0)))
                inv = SalesInvoice(
                    id=uuid.uuid4(),
                    company_id=self.company_id,
                    invoice_number=str(row.get("invoice_number", row.get("invoice_no", ""))),
                    invoice_date=self._parse_date(row.get("invoice_date")),
                    customer_id=self._get_uuid(row, "customer_id"),
                    gross_amount=self._decimal(row.get("gross_amount", total)),
                    discount_amount=self._decimal(row.get("discount_amount", 0)),
                    taxable_amount=self._decimal(row.get("taxable_amount", row.get("taxable_value", total))),
                    cgst_amount=self._decimal(row.get("cgst_amount", row.get("cgst", 0))),
                    sgst_amount=self._decimal(row.get("sgst_amount", row.get("sgst", 0))),
                    igst_amount=self._decimal(row.get("igst_amount", row.get("igst", 0))),
                    total_amount=total,
                    outstanding_amount=self._decimal(row.get("outstanding_amount", total)),
                    status=str(row.get("status", "confirmed")),
                    e_way_bill_number=self._get_str(row, "e_way_bill_number"),
                    e_invoice_irn=self._get_str(row, "e_invoice_irn"),
                    erp_source=self._get_str(row, "erp_source") or "excel_import",
                )
                self.db.add(inv)
                imported += 1
            except Exception as e:
                errors.append(str(e))
        self.db.commit()
        return {"rows_imported": imported, "errors": errors[:10]}

    def _import_purchases(self, df) -> dict:
        from app.models.transaction import PurchaseInvoice
        imported = 0
        errors = []
        for _, row in df.iterrows():
            try:
                total = self._decimal(row.get("total_amount", row.get("total_value", 0)))
                inv = PurchaseInvoice(
                    id=uuid.uuid4(),
                    company_id=self.company_id,
                    vendor_id=self._get_uuid(row, "vendor_id"),
                    invoice_number=str(row.get("invoice_number", row.get("invoice_no", ""))),
                    our_po_number=self._get_str(row, "our_po_number") or self._get_str(row, "po_no"),
                    invoice_date=self._parse_date(row.get("invoice_date")),
                    receipt_date=self._parse_date(row.get("receipt_date")),
                    gross_amount=self._decimal(row.get("gross_amount", total)),
                    discount_amount=self._decimal(row.get("discount_amount", 0)),
                    taxable_amount=self._decimal(row.get("taxable_amount", row.get("taxable_value", total))),
                    cgst_amount=self._decimal(row.get("cgst_amount", row.get("cgst", 0))),
                    sgst_amount=self._decimal(row.get("sgst_amount", row.get("sgst", 0))),
                    igst_amount=self._decimal(row.get("igst_amount", row.get("igst", 0))),
                    total_amount=total,
                    outstanding_amount=self._decimal(row.get("outstanding_amount", total)),
                    itc_eligible=bool(row.get("itc_eligible", True)),
                    status=str(row.get("status", "pending")),
                    erp_source=self._get_str(row, "erp_source") or "excel_import",
                )
                self.db.add(inv)
                imported += 1
            except Exception as e:
                errors.append(str(e))
        self.db.commit()
        return {"rows_imported": imported, "errors": errors[:10]}

    def _import_journal_entries(self, df) -> dict:
        from app.models.transaction import JournalEntry
        imported = 0
        errors = []
        for _, row in df.iterrows():
            try:
                total_debit = self._decimal(row.get("total_debit", 0))
                je = JournalEntry(
                    id=uuid.uuid4(),
                    company_id=self.company_id,
                    voucher_number=str(row.get("voucher_number", row.get("je_no", ""))),
                    entry_date=self._parse_date(row.get("entry_date", row.get("je_date"))),
                    voucher_type=str(row.get("voucher_type", row.get("je_type", "journal"))),
                    narration=self._get_str(row, "narration"),
                    total_debit=total_debit,
                    total_credit=self._decimal(row.get("total_credit", total_debit)),
                    is_reversed=bool(row.get("is_reversed", row.get("is_reversal", False))),
                    status=str(row.get("status", "posted")),
                    erp_source=self._get_str(row, "erp_source") or "excel_import",
                )
                self.db.add(je)
                imported += 1
            except Exception as e:
                errors.append(str(e))
        self.db.commit()
        return {"rows_imported": imported, "errors": errors[:10]}

    def _import_bank(self, df) -> dict:
        from app.models.transaction import BankTransaction
        imported = 0
        errors = []
        for _, row in df.iterrows():
            try:
                bt = BankTransaction(
                    id=uuid.uuid4(),
                    company_id=self.company_id,
                    transaction_date=self._parse_date(row.get("transaction_date", row.get("txn_date"))),
                    amount=self._decimal(row.get("amount", 0)),
                    transaction_type=str(row.get("transaction_type", row.get("txn_type", "debit"))),
                    reference_number=self._get_str(row, "reference_number") or self._get_str(row, "reference_no"),
                    description=self._get_str(row, "description") or self._get_str(row, "narration"),
                    counterparty_name=self._get_str(row, "counterparty_name") or self._get_str(row, "party_name"),
                    transaction_mode=self._get_str(row, "transaction_mode") or self._get_str(row, "channel"),
                    erp_source=self._get_str(row, "erp_source") or "excel_import",
                )
                self.db.add(bt)
                imported += 1
            except Exception as e:
                errors.append(str(e))
        self.db.commit()
        return {"rows_imported": imported, "errors": errors[:10]}

    def _import_inventory(self, df) -> dict:
        from app.models.transaction import InventoryMovement
        imported = 0
        errors = []
        for _, row in df.iterrows():
            try:
                mv = InventoryMovement(
                    id=uuid.uuid4(),
                    company_id=self.company_id,
                    movement_date=self._parse_date(row.get("movement_date")),
                    item_code=str(row.get("item_code", row.get("material_code", ""))),
                    item_name=self._get_str(row, "item_name"),
                    warehouse_from=self._get_str(row, "warehouse_from") or self._get_str(row, "warehouse"),
                    movement_type=str(row.get("movement_type", "goods_receipt")),
                    quantity=self._decimal(row.get("quantity", 0)),
                    unit_of_measure=str(row.get("unit_of_measure", row.get("unit", "NOS"))),
                    unit_cost=self._decimal(row.get("unit_cost", row.get("uom_rate", 0))),
                    total_value=self._decimal(row.get("total_value", row.get("value", 0))),
                    reference_document_number=self._get_str(row, "reference_document_number") or self._get_str(row, "reference_doc"),
                    erp_source=self._get_str(row, "erp_source") or "excel_import",
                )
                self.db.add(mv)
                imported += 1
            except Exception as e:
                errors.append(str(e))
        self.db.commit()
        return {"rows_imported": imported, "errors": errors[:10]}

    def _import_payroll(self, df) -> dict:
        from app.models.transaction import PayrollRecord
        imported = 0
        errors = []
        for _, row in df.iterrows():
            try:
                gross = self._decimal(row.get("gross_earnings", row.get("gross_pay", 0)))
                deductions = self._decimal(row.get("total_deductions", row.get("deductions", 0)))
                pr = PayrollRecord(
                    id=uuid.uuid4(),
                    company_id=self.company_id,
                    employee_id=uuid.UUID(str(row["employee_id"])),
                    pay_period_year=int(row.get("pay_period_year", row.get("period_year", date.today().year))),
                    pay_period_month=int(row.get("pay_period_month", row.get("period_month", 1))),
                    gross_earnings=gross,
                    total_deductions=deductions,
                    net_pay=self._decimal(row.get("net_pay", float(gross) - float(deductions))),
                    pf_employee=self._decimal(row.get("pf_employee", 0)),
                    pf_employer=self._decimal(row.get("pf_employer", 0)),
                    esic_employee=self._decimal(row.get("esic_employee", 0)),
                    esic_employer=self._decimal(row.get("esic_employer", row.get("esi_employer", 0))),
                    tds_income_tax=self._decimal(row.get("tds_income_tax", row.get("tds", 0))),
                    payment_date=self._parse_date(row.get("payment_date")),
                    payment_mode=self._get_str(row, "payment_mode") or "bank_transfer",
                    status=str(row.get("status", "paid")),
                    erp_source=self._get_str(row, "erp_source") or "excel_import",
                )
                self.db.add(pr)
                imported += 1
            except Exception as e:
                errors.append(str(e))
        self.db.commit()
        return {"rows_imported": imported, "errors": errors[:10]}

    @staticmethod
    def _parse_date(val):
        if val is None:
            return date.today()
        if hasattr(val, "date"):
            return val.date()
        try:
            from datetime import datetime
            return datetime.fromisoformat(str(val)).date()
        except Exception:
            return date.today()

    @staticmethod
    def _decimal(val) -> Decimal:
        try:
            return Decimal(str(val))
        except Exception:
            return Decimal("0")

    @staticmethod
    def _get_str(row, key) -> str | None:
        val = row.get(key)
        if val is None or (isinstance(val, float) and str(val) == "nan"):
            return None
        return str(val)

    @staticmethod
    def _get_uuid(row, key) -> uuid.UUID | None:
        val = row.get(key)
        if val is None or (isinstance(val, float) and str(val) == "nan"):
            return None
        try:
            return uuid.UUID(str(val))
        except Exception:
            return None
