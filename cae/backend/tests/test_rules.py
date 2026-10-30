"""Each rule gets data that must fire and data that must not."""
from datetime import date, datetime

import pytest

from app.rules import get_rule_fn, registered_codes
from app.rules.catalogue import CATALOGUE_BY_CODE
from conftest import CID, build_conn, rule


def run(code, conn, **params):
    return get_rule_fn(code)(conn, CID, rule(**params))


def titles(results):
    return [r["title"] for r in results]


def test_catalogue_and_registry_match():
    assert set(CATALOGUE_BY_CODE) == registered_codes()


def test_every_rule_runs_on_empty_data():
    conn = build_conn()
    for code in registered_codes():
        assert run(code, conn) == [], code


# ---------------- sales ----------------

def test_sal_001_duplicates_only_within_a_financial_year():
    conn = build_conn(sales_invoices=[
        dict(invoice_number="INV/1", invoice_date=date(2025, 3, 31), total_amount=100, taxable_amount=100),
        dict(invoice_number="INV/1", invoice_date=date(2025, 4, 1), total_amount=100, taxable_amount=100),   # new FY
        dict(invoice_number="INV/2", invoice_date=date(2025, 5, 1), total_amount=100, taxable_amount=100),
        dict(invoice_number="INV/2", invoice_date=date(2026, 2, 1), total_amount=100, taxable_amount=100),   # same FY
    ])
    out = run("SAL-001", conn)
    assert len(out) == 1 and "INV/2" in out[0]["title"] and "2025-26" in out[0]["title"]


def test_sal_002_round_amount():
    conn = build_conn(sales_invoices=[
        dict(invoice_number="A", invoice_date=date(2025, 5, 1), total_amount=200000, taxable_amount=1),
        dict(invoice_number="B", invoice_date=date(2025, 5, 1), total_amount=200999.6, taxable_amount=1),
    ])
    assert [r["evidence"]["invoice_number"] for r in run("SAL-002", conn)] == ["A"]


def test_sal_004_cut_off():
    conn = build_conn(sales_invoices=[
        dict(invoice_number="LATE", invoice_date=date(2025, 3, 28), created_at=datetime(2025, 4, 20), total_amount=500000, taxable_amount=1),
        dict(invoice_number="OK", invoice_date=date(2025, 3, 28), created_at=datetime(2025, 4, 3), total_amount=500000, taxable_amount=1),
    ])
    assert [r["evidence"]["invoice_number"] for r in run("SAL-004", conn)] == ["LATE"]


def test_sal_005_discount_impact_is_the_discount():
    conn = build_conn(sales_invoices=[
        dict(invoice_number="D", invoice_date=date(2025, 5, 1), gross_amount=100000, discount_amount=20000, total_amount=80000, taxable_amount=1),
        dict(invoice_number="N", invoice_date=date(2025, 5, 1), gross_amount=100000, discount_amount=10000, total_amount=90000, taxable_amount=1),
    ])
    out = run("SAL-005", conn)
    assert len(out) == 1 and out[0]["financial_impact"] == 20000


def test_sal_009_null_source_is_not_manual_by_default():
    conn = build_conn(sales_invoices=[
        dict(invoice_number="M", invoice_date=date(2025, 5, 1), total_amount=200000, taxable_amount=1, erp_source="manual"),
        dict(invoice_number="U", invoice_date=date(2025, 5, 1), total_amount=200000, taxable_amount=1, erp_source=None),
    ])
    assert len(run("SAL-009", conn)) == 1
    assert len(run("SAL-009", conn, treat_null_source_as_manual=True)) == 2


def test_sal_010_credit_limit():
    conn = build_conn(
        customers=[dict(id="c1", name="Over", credit_limit=100000), dict(id="c2", name="Under", credit_limit=500000)],
        sales_invoices=[
            dict(customer_id="c1", invoice_number="1", invoice_date=date(2025, 5, 1), total_amount=150000, taxable_amount=1, outstanding_amount=150000),
            dict(customer_id="c2", invoice_number="2", invoice_date=date(2025, 5, 1), total_amount=150000, taxable_amount=1, outstanding_amount=150000),
        ])
    out = run("SAL-010", conn)
    assert len(out) == 1 and out[0]["financial_impact"] == 50000


def test_sal_019_weekend_is_saturday_and_sunday():
    conn = build_conn(sales_invoices=[
        dict(invoice_number="SAT", invoice_date=date(2025, 10, 25), total_amount=900000, taxable_amount=1),
        dict(invoice_number="SUN", invoice_date=date(2025, 10, 26), total_amount=900000, taxable_amount=1),
        dict(invoice_number="MON", invoice_date=date(2025, 10, 27), total_amount=900000, taxable_amount=1),
    ])
    assert sorted(r["evidence"]["invoice_number"] for r in run("SAL-019", conn)) == ["SAT", "SUN"]


def test_sal_021_e_invoice_depends_on_preceding_year_turnover():
    big = [dict(customer_id="b2b", invoice_number=f"P{i}", invoice_date=date(2024, 6, 1), taxable_amount=6_000_000,
                total_amount=7_080_000) for i in range(10)]   # FY 2024-25 turnover Rs.6 cr
    conn = build_conn(
        customers=[dict(id="b2b", name="Buyer", gstin="24AAAAA0000A1Z5"), dict(id="b2c", name="Consumer", gstin=None)],
        sales_invoices=big + [
            dict(customer_id="b2b", invoice_number="NOIRN", invoice_date=date(2025, 6, 1), taxable_amount=1000, total_amount=1180, e_invoice_irn=None),
            dict(customer_id="b2c", invoice_number="B2C", invoice_date=date(2025, 6, 1), taxable_amount=1000, total_amount=1180, e_invoice_irn=None),
            dict(customer_id="b2b", invoice_number="FIRSTYR", invoice_date=date(2024, 7, 1), taxable_amount=1000, total_amount=1180, e_invoice_irn=None),
        ])
    out = run("SAL-021", conn)
    assert [r["evidence"]["invoice_number"] for r in out] == ["NOIRN"]   # small value still caught; B2C and no-prior-year skipped


def test_sal_022_cash_receipt_aggregated_per_person_per_day():
    conn = build_conn(bank_transactions=[
        dict(transaction_date=date(2026, 5, 1), transaction_type="credit", transaction_mode="cash", amount=150000, counterparty_name="Ravi"),
        dict(transaction_date=date(2026, 5, 1), transaction_type="credit", transaction_mode="cash", amount=60000, counterparty_name="Ravi"),
        dict(transaction_date=date(2026, 5, 1), transaction_type="credit", transaction_mode="cash", amount=190000, counterparty_name="Mehul"),
    ])
    out = run("SAL-022", conn)
    assert len(out) == 1 and out[0]["evidence"]["total"] == 210000
    assert "s.186 of the Income-tax Act, 2025" in out[0]["evidence"]["statutory_ref"]


# ---------------- purchases ----------------

def test_pur_001_normalised_number_same_fy():
    conn = build_conn(purchase_invoices=[
        dict(vendor_id="v1", invoice_number="GST/001", invoice_date=date(2025, 6, 1), total_amount=1000, taxable_amount=1),
        dict(vendor_id="v1", invoice_number="GST-001", invoice_date=date(2025, 7, 1), total_amount=1000, taxable_amount=1),
        dict(vendor_id="v2", invoice_number="GST/001", invoice_date=date(2025, 6, 1), total_amount=1000, taxable_amount=1),
    ])
    out = run("PUR-001", conn)
    assert len(out) == 1 and out[0]["evidence"]["count"] == 2


def test_pur_002_reads_po_value_from_json_text():
    conn = build_conn(purchase_invoices=[
        dict(invoice_number="X", invoice_date=date(2025, 6, 1), total_amount=120000, taxable_amount=1, raw_data='{"po_value": 100000}'),
        dict(invoice_number="Y", invoice_date=date(2025, 6, 1), total_amount=102000, taxable_amount=1, raw_data='{"po_value": 100000}'),
    ])
    assert [r["evidence"]["invoice_number"] for r in run("PUR-002", conn)] == ["X"]


def test_pur_006_split_within_window():
    rows = [dict(vendor_id="v1", invoice_number=str(i), invoice_date=date(2025, 6, 1 + i), total_amount=90000, taxable_amount=1) for i in range(3)]
    rows += [dict(vendor_id="v2", invoice_number=f"s{i}", invoice_date=date(2025, 6, 1 + 10 * i), total_amount=90000, taxable_amount=1) for i in range(3)]
    out = run("PUR-006", build_conn(purchase_invoices=rows))
    assert len(out) == 1 and out[0]["evidence"]["vendor_id"] == "v1"


def test_pur_010_payment_to_other_account():
    conn = build_conn(
        vendors=[dict(id="v1", name="Steel Co", bank_account_number="1111 2222")],
        bank_transactions=[
            dict(transaction_date=date(2025, 6, 1), transaction_type="debit", amount=50000, counterparty_name="steel co", counterparty_account="99998888"),
            dict(transaction_date=date(2025, 6, 2), transaction_type="debit", amount=50000, counterparty_name="Steel Co", counterparty_account="11112222"),
        ])
    assert len(run("PUR-010", conn)) == 1


def test_pur_016_needs_different_invoice_numbers_close_in_time():
    conn = build_conn(purchase_invoices=[
        dict(vendor_id="v1", invoice_number="A", invoice_date=date(2025, 6, 1), total_amount=75000, taxable_amount=1, status="paid"),
        dict(vendor_id="v1", invoice_number="B", invoice_date=date(2025, 6, 10), total_amount=75000, taxable_amount=1, status="paid"),
        dict(vendor_id="v2", invoice_number="RENT-APR", invoice_date=date(2025, 4, 1), total_amount=50000, taxable_amount=1, status="paid"),
        dict(vendor_id="v2", invoice_number="RENT-JUN", invoice_date=date(2025, 6, 1), total_amount=50000, taxable_amount=1, status="paid"),
    ])
    out = run("PUR-016", conn)
    assert len(out) == 1 and out[0]["evidence"]["vendor_id"] == "v1"


def test_pur_022_links_on_bank_account_or_pan_not_address():
    conn = build_conn(
        vendors=[dict(id="v1", name="Ghost Traders", bank_account_number="123456789", pan="ABCDE1234F"),
                 dict(id="v2", name="Real Co", bank_account_number="555555555", pan="ZZZZZ9999Z")],
        employees=[dict(id="e1", full_name="Clerk", bank_account_number="123456789", pan="QQQQQ1111Q")])
    out = run("PUR-022", conn)
    assert len(out) == 1 and out[0]["evidence"]["matched_on"] == "bank account"


def test_pur_031_msme_micro_small_only_with_s16_interest():
    conn = build_conn(
        vendors=[dict(id="m", name="Micro Ltd", msme_status="Micro"), dict(id="med", name="Medium Ltd", msme_status="Medium")],
        purchase_invoices=[
            dict(vendor_id="m", invoice_number="M1", invoice_date=date(2025, 4, 1), total_amount=100000, taxable_amount=1, outstanding_amount=100000),
            dict(vendor_id="med", invoice_number="D1", invoice_date=date(2025, 4, 1), total_amount=100000, taxable_amount=1, outstanding_amount=100000),
            dict(vendor_id="m", invoice_number="M2", invoice_date=date(2025, 7, 1), total_amount=10, taxable_amount=1, outstanding_amount=0, status="paid"),
        ])
    out = run("PUR-031", conn, as_on="2025-07-01")
    assert [r["evidence"]["invoice_number"] for r in out] == ["M1"]
    ev = out[0]["evidence"]
    assert ev["credit_days_applied"] == 15 and ev["appointed_day"] == "2025-04-16"
    assert ev["rate_pa"] == pytest.approx(3 * 6.25)    # bank rate on 16-04-2025
    assert 0 < ev["interest"] < 100000 * 0.1875 * 76 / 365 * 1.05


# ---------------- GST ----------------

def test_gst_001_removed_slab_after_gst2():
    conn = build_conn(sales_invoices=[
        dict(invoice_number="OLD12", invoice_date=date(2025, 10, 1), taxable_amount=1000, cgst_amount=60, sgst_amount=60, total_amount=1120),
        dict(invoice_number="NEW18", invoice_date=date(2025, 10, 1), taxable_amount=1000, igst_amount=180, total_amount=1180),
        dict(invoice_number="PRE", invoice_date=date(2025, 9, 1), taxable_amount=1000, cgst_amount=60, sgst_amount=60, total_amount=1120),
    ])
    assert [r["evidence"]["invoice_number"] for r in run("GST-001", conn)] == ["OLD12"]


def test_gst_002_rule_37_proportionate_reversal():
    conn = build_conn(purchase_invoices=[
        dict(invoice_number="OLD", invoice_date=date(2025, 1, 1), taxable_amount=100000, igst_amount=18000, total_amount=118000, outstanding_amount=59000),
        dict(invoice_number="NEW", invoice_date=date(2025, 6, 1), taxable_amount=100000, igst_amount=18000, total_amount=118000, outstanding_amount=118000),
        dict(invoice_number="RCM", invoice_date=date(2025, 1, 1), taxable_amount=100000, igst_amount=18000, total_amount=118000, outstanding_amount=118000, reverse_charge=True),
    ])
    out = run("GST-002", conn, as_on="2025-08-01")
    assert len(out) == 1 and out[0]["financial_impact"] == pytest.approx(9000)


def test_gst_003_s16_4_time_limit():
    conn = build_conn(purchase_invoices=[
        dict(invoice_number="LATE", invoice_date=date(2024, 6, 1), created_at=datetime(2025, 12, 5), taxable_amount=1, igst_amount=500, total_amount=1),
        dict(invoice_number="OK", invoice_date=date(2024, 6, 1), created_at=datetime(2025, 11, 30), taxable_amount=1, igst_amount=500, total_amount=1),
    ])
    assert [r["evidence"]["invoice_number"] for r in run("GST-003", conn)] == ["LATE"]


# ---------------- TDS ----------------

def test_tds_001_goods_threshold_only_on_excess_and_big_buyer():
    sales = [dict(invoice_number=f"S{i}", invoice_date=date(2024, 6, 1), taxable_amount=60_000_000, total_amount=1) for i in range(2)]
    purchases = [dict(vendor_id="v1", invoice_number=f"P{i}", invoice_date=date(2025, 5, 1 + i), taxable_amount=2_000_000, total_amount=1) for i in range(3)]
    out = run("TDS-001", build_conn(sales_invoices=sales, purchase_invoices=purchases))
    assert len(out) == 1
    assert out[0]["evidence"]["excess_over_threshold"] == pytest.approx(1_000_000)
    assert out[0]["financial_impact"] == pytest.approx(1000)
    # buyer below Rs.10 cr in the preceding year -> no obligation
    assert run("TDS-001", build_conn(purchase_invoices=purchases)) == []


def test_tds_002_short_deduction_uses_new_act_reference():
    conn = build_conn(purchase_invoices=[
        dict(invoice_number="J", invoice_date=date(2026, 5, 1), taxable_amount=100000, tds_section="194J", tds_amount=1000, total_amount=1),
        dict(invoice_number="C", invoice_date=date(2026, 5, 1), taxable_amount=100000, tds_section="194C", tds_amount=1000, total_amount=1),
    ])
    out = run("TDS-002", conn)
    assert len(out) == 1 and out[0]["evidence"]["invoice_number"] == "J"
    assert "s.393(1) Table Sl.6(iii)" in out[0]["evidence"]["statutory_ref"]


# ---------------- treasury ----------------

def test_tre_001_aggregates_per_day_and_uses_transport_limit():
    conn = build_conn(bank_transactions=[
        dict(transaction_date=date(2025, 6, 1), transaction_type="debit", transaction_mode="cash", amount=6000, counterparty_name="Vendor A"),
        dict(transaction_date=date(2025, 6, 1), transaction_type="debit", transaction_mode="cash", amount=6000, counterparty_name="Vendor A"),
        dict(transaction_date=date(2025, 6, 1), transaction_type="debit", transaction_mode="cash", amount=30000, counterparty_name="Ram Transport"),
        dict(transaction_date=date(2025, 6, 1), transaction_type="debit", transaction_mode="cash", amount=90000, counterparty_name="self"),
    ])
    out = run("TRE-001", conn)
    assert [r["evidence"]["party"] for r in out] == ["Vendor A"]
    assert "s.40A(3) of the Income-tax Act, 1961" in out[0]["evidence"]["statutory_ref"]


def test_tre_001_reference_switches_to_2025_act():
    conn = build_conn(bank_transactions=[
        dict(transaction_date=date(2026, 6, 1), transaction_type="debit", transaction_mode="cash", amount=12000, counterparty_name="Vendor A")])
    assert run("TRE-001", conn)[0]["evidence"]["statutory_ref"].startswith("s.36(4) of the Income-tax Act, 2025")


def test_tre_002_same_day_round_trip():
    conn = build_conn(bank_transactions=[
        dict(transaction_date=date(2025, 6, 1), transaction_type="debit", amount=1_000_000, counterparty_name="Group Co"),
        dict(transaction_date=date(2025, 6, 1), transaction_type="credit", amount=1_000_000, counterparty_name="Group Co"),
    ])
    assert len(run("TRE-002", conn)) == 1


def test_tre_003_cash_loan():
    conn = build_conn(bank_transactions=[
        dict(transaction_date=date(2026, 6, 1), transaction_type="credit", transaction_mode="cash", amount=25000, counterparty_name="Friend", description="unsecured loan"),
        dict(transaction_date=date(2026, 6, 1), transaction_type="credit", transaction_mode="cash", amount=25000, counterparty_name="Customer", description="sale"),
    ])
    out = run("TRE-003", conn)
    assert len(out) == 1 and out[0]["evidence"]["statutory_ref"].startswith("s.185")


# ---------------- journals ----------------

def test_je_005_only_uncleared_suspense():
    conn = build_conn(
        journal_entries=[dict(id="j1", voucher_number="1", entry_date=date(2025, 1, 1), total_debit=1),
                         dict(id="j2", voucher_number="2", entry_date=date(2025, 1, 5), total_debit=1),
                         dict(id="j3", voucher_number="3", entry_date=date(2025, 1, 1), total_debit=1)],
        journal_entry_lines=[
            dict(journal_entry_id="j1", account_name="Suspense A/c", debit_amount=80000, credit_amount=0),
            dict(journal_entry_id="j2", account_name="Suspense A/c", debit_amount=0, credit_amount=80000),
            dict(journal_entry_id="j3", account_code="SUSP2", account_name="Bank Suspense", debit_amount=90000, credit_amount=0),
        ])
    out = run("JE-005", conn, as_on="2025-03-31")
    assert len(out) == 1 and out[0]["financial_impact"] == 90000


def test_je_015_uses_financial_year_not_calendar_year():
    conn = build_conn(journal_entries=[
        dict(voucher_number="SAMEFY", entry_date=date(2025, 12, 20), posted_at=datetime(2026, 1, 5), total_debit=500000),
        dict(voucher_number="PRIOR", entry_date=date(2026, 3, 30), posted_at=datetime(2026, 4, 10), total_debit=500000),
    ])
    assert [r["evidence"]["voucher_number"] for r in run("JE-015", conn)] == ["PRIOR"]


# ---------------- payroll ----------------

def test_pay_001_and_004_do_not_double_count():
    conn = build_conn(
        employees=[dict(id="ghost", full_name="Ghost", is_active=False, date_of_leaving=None),
                   dict(id="left", full_name="Leaver", is_active=False, date_of_leaving=date(2025, 5, 31))],
        payroll_records=[
            dict(employee_id="ghost", pay_period_year=2025, pay_period_month=5, gross_earnings=50000, net_pay=45000),
            dict(employee_id="left", pay_period_year=2025, pay_period_month=5, gross_earnings=50000, net_pay=45000),
            dict(employee_id="left", pay_period_year=2025, pay_period_month=7, gross_earnings=50000, net_pay=45000),
        ])
    assert [r["evidence"]["name"] for r in run("PAY-001", conn)] == ["Ghost"]
    out = run("PAY-004", conn)
    assert len(out) == 1 and out[0]["financial_impact"] == 45000


def test_pay_002_handles_december_to_january():
    conn = build_conn(payroll_records=[
        dict(employee_id="e1", pay_period_year=2025, pay_period_month=12, gross_earnings=50000, net_pay=1),
        dict(employee_id="e1", pay_period_year=2026, pay_period_month=1, gross_earnings=90000, net_pay=1),
    ])
    assert len(run("PAY-002", conn)) == 1


def test_pay_005_late_and_missing_deposits_with_tax_year_switch():
    payroll = [
        dict(employee_id="e1", pay_period_year=2025, pay_period_month=4, gross_earnings=1, net_pay=1, pf_employee=1800, pf_employer=1800),
        dict(employee_id="e1", pay_period_year=2025, pay_period_month=5, gross_earnings=1, net_pay=1, pf_employee=1800, pf_employer=1800),
        dict(employee_id="e1", pay_period_year=2026, pay_period_month=4, gross_earnings=1, net_pay=1, pf_employee=1800, pf_employer=1800),
    ]
    bank = [
        dict(transaction_date=date(2025, 5, 14), transaction_type="debit", amount=3650, description="EPFO challan Apr"),   # on time
        dict(transaction_date=date(2025, 6, 25), transaction_type="debit", amount=3650, description="EPFO challan May"),   # late
        dict(transaction_date=date(2026, 6, 30), transaction_type="debit", amount=10, description="other"),
    ]
    out = run("PAY-005", build_conn(payroll_records=payroll, bank_transactions=bank))
    assert [r["evidence"]["period"] for r in out] == ["2025-05", "2026-04"]
    late, missing = out
    assert late["evidence"]["paid_on"] == "2025-06-25" and late["financial_impact"] == 1800      # 1961 Act: disallowed
    assert missing["evidence"]["paid_on"] is None and missing["financial_impact"] == 0          # 2025 Act: return due date test
    assert missing["evidence"]["tax_test"] == "return_due_date"


# ---------------- inventory ----------------

def test_inv_001_and_007_use_netted_quantities():
    conn = build_conn(inventory_movements=[
        dict(item_code="NEG", movement_date=date(2025, 5, 1), movement_type="goods_receipt", quantity=10, unit_cost=100, total_value=1000),
        dict(item_code="NEG", movement_date=date(2025, 5, 2), movement_type="goods_issue", quantity=15, unit_cost=100, total_value=1500),
        dict(item_code="BIG", movement_date=date(2025, 5, 1), movement_type="goods_receipt", quantity=100, unit_cost=10000, total_value=1_000_000),
        dict(item_code="BIG", movement_date=date(2025, 5, 3), movement_type="transfer", quantity=100, unit_cost=10000, total_value=1_000_000),
    ])
    assert [r["evidence"]["item_code"] for r in run("INV-001", conn)] == ["NEG"]
    assert [r["evidence"]["item_code"] for r in run("INV-007", conn)] == ["BIG"]


def test_inv_005_ages_against_data_date_and_values_on_hand():
    conn = build_conn(inventory_movements=[
        dict(item_code="IDLE", movement_date=date(2024, 1, 1), movement_type="goods_receipt", quantity=10, unit_cost=500, total_value=5000),
        dict(item_code="IDLE", movement_date=date(2024, 1, 2), movement_type="goods_issue", quantity=4, unit_cost=500, total_value=2000),
        dict(item_code="LIVE", movement_date=date(2024, 12, 1), movement_type="goods_receipt", quantity=10, unit_cost=500, total_value=5000),
    ])
    out = run("INV-005", conn)
    assert [r["evidence"]["item_code"] for r in out] == ["IDLE"]
    assert out[0]["financial_impact"] == 3000 and out[0]["evidence"]["as_on"] == "2024-12-01"


def test_inv_010_weekend():
    conn = build_conn(inventory_movements=[
        dict(item_code="X", movement_date=date(2025, 10, 25), movement_type="goods_issue", quantity=1, total_value=300000),
        dict(item_code="Y", movement_date=date(2025, 10, 27), movement_type="goods_issue", quantity=1, total_value=300000),
    ])
    assert [r["evidence"]["item_code"] for r in run("INV-010", conn)] == ["X"]
