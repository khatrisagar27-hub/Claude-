"""Parse uploaded Excel/CSV files into transaction tables."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class ExcelImporter:
    def __init__(self, db: "Session", company_id: str):
        self.db = db
        self.company_id = uuid.UUID(company_id)

    def import_file(self, file_path: str, file_type: str) -> dict:
        import pandas as pd
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        importers = {
            "sales_invoices": self._import_sales,
            "purchase_invoices": self._import_purchases,
            "journal_entries": self._import_journal_entries,
            "bank_transactions": self._import_bank,
            "inventory": self._import_inventory,
            "payroll": self._import_payroll,
        }
        fn = importers.get(file_type)
        if not fn:
            return {"error": f"Unknown file type: {file_type}", "rows_imported": 0}
        return fn(df)

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
