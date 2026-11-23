"""Statutory functions, the 2B matcher and the fraud statistics."""
from datetime import date

import pytest

from app.engines import gst_match
from app.engines.fraud_engine import benford_first_digit, first_digit
from app.statutory import clause44, companies, gst, income_tax, labour, msme, sampling


def test_section_ref_switches_on_1_april_2026():
    assert income_tax.section_ref("cash_expenditure", date(2026, 3, 31)) == "s.40A(3) of the Income-tax Act, 1961"
    assert income_tax.section_ref("cash_expenditure", date(2026, 4, 1)).startswith("s.36(4) of the Income-tax Act, 2025")
    assert income_tax.section_ref("msme_disallowance", date(2026, 4, 1)).startswith("s.37(2)(g)")
    assert income_tax.tax_year(date(2026, 3, 31)) == "2025-26"
    assert income_tax.tax_year(date(2026, 4, 1)) == "2026-27"


def test_e_invoice_thresholds():
    assert gst.e_invoice_threshold(date(2023, 7, 31)) == 100_000_000
    assert gst.e_invoice_threshold(date(2023, 8, 1)) == 50_000_000
    assert gst.e_invoice_applicable(50_000_001, date(2025, 1, 1))
    assert not gst.e_invoice_applicable(50_000_000, date(2025, 1, 1))     # "exceeds"
    assert gst.irp_30_day_limit_applies(100_000_000, date(2025, 4, 1))      # "10 crore and above"
    assert not gst.irp_30_day_limit_applies(100_000_000, date(2025, 3, 31))


def test_gst2_rates_and_itc_time_limit():
    assert 12.0 in gst.valid_rates(date(2025, 9, 21)) and 12.0 not in gst.valid_rates(date(2025, 9, 22))
    assert 40.0 in gst.valid_rates(date(2025, 9, 22))
    assert gst.itc_time_limit(date(2025, 3, 31)) == date(2025, 11, 30)
    assert gst.itc_time_limit(date(2025, 4, 1)) == date(2026, 11, 30)


def test_msme_classification_uses_2025_limits():
    assert msme.classify(20_000_000, 90_000_000, date(2025, 4, 1)) == "micro"
    assert msme.classify(20_000_000, 90_000_000, date(2025, 3, 31)) == "small"
    assert msme.classify(1_300_000_000, 1, date(2025, 6, 1)) is None


def test_msme_appointed_day_and_compound_interest():
    due, credit = msme.appointed_day(date(2025, 4, 1), 60)
    assert credit == 45 and due == date(2025, 5, 16)
    due, credit = msme.appointed_day(date(2025, 4, 1), None)
    assert credit == 15
    interest, segs = msme.compound_interest(100_000, date(2025, 1, 1), date(2025, 3, 1), 18.0)
    simple = 100_000 * 0.18 * 59 / 365
    assert interest > simple and len(segs) == 2
    assert segs[1]["opening_balance"] == pytest.approx(100_000 + segs[0]["interest"], abs=0.01)
    assert msme.bank_rate_on(date(2026, 10, 7)) == 5.75 and msme.bank_rate_on(date(2026, 10, 6)) == 5.50


def test_small_company_and_caro():
    base = dict(balance_sheet_date=date(2026, 3, 31), paid_up_capital=8 * companies.CRORE,
                preceding_year_turnover=90 * companies.CRORE)
    assert companies.small_company(companies.CompanyFacts(**base)).applies          # Rs.10/100 cr limits
    old = dict(base, balance_sheet_date=date(2025, 3, 31))
    assert not companies.small_company(companies.CompanyFacts(**old)).applies       # Rs.4/40 cr then
    sub = companies.CompanyFacts(**base, is_subsidiary=True)
    assert not companies.small_company(sub).applies
    # small company beats the private-company test (GN para 12)
    small_but_big_reserves = companies.CompanyFacts(**base, reserves_and_surplus=50 * companies.CRORE)
    assert not companies.caro_2020(small_but_big_reserves).applies
    # not small, private, fails one para 1(2)(v) limb -> CARO applies
    big = companies.CompanyFacts(balance_sheet_date=date(2026, 3, 31), paid_up_capital=12 * companies.CRORE,
                                 preceding_year_turnover=1, total_revenue=1)
    assert companies.caro_2020(big).applies
    assert not companies.ifc_reporting(big).applies     # private, turnover < Rs.50 cr


def test_labour_due_dates_and_tax_switch():
    assert labour.contribution_due_date(2025, 12) == date(2026, 1, 15)
    assert labour.employee_contribution_tax_test(date(2026, 3, 31)) == "labour_due_date"
    assert labour.employee_contribution_tax_test(date(2026, 4, 30)) == "return_due_date"


def test_sampling_is_deterministic_and_order_independent():
    pop = [{"id": str(i), "amount": i * 1000} for i in range(1, 201)]
    a = sampling.select(pop, seed=7, n=10, high_value_threshold=190_000)
    b = sampling.select(list(reversed(pop)), seed=7, n=10, high_value_threshold=190_000)
    assert [s["id"] for s in a["sample"]] == [s["id"] for s in b["sample"]]
    assert a["key_items"] == 11 and a["random_items"] == 10
    assert sampling.select(pop, seed=8, n=10)["sample"] != sampling.select(pop, seed=7, n=10)["sample"]


def test_clause44_excludes_schedule_iii_and_non_cash():
    lines = [
        clause44.ExpenseLine("Purchases", 1000, "24AAAAA0000A1Z5", "Reg"),
        clause44.ExpenseLine("Purchases", 300, None, "Unreg"),
        clause44.ExpenseLine("Petrol expenses", 200, "24BBBBB0000B1Z5", "Pump"),
        clause44.ExpenseLine("Salaries and wages", 5000),
        clause44.ExpenseLine("Depreciation", 700),
        clause44.ExpenseLine("Repairs", 150),
    ]
    out = clause44.compute(lines)
    assert out["col2_total_expenditure"] == 7350
    assert out["col5_other_registered"] == 1000 and out["col3_exempt"] == 200
    assert out["col7_unregistered"] == 300 and out["unattributed"] == 150
    assert out["working_79_4"]["less_schedule_iii"] == 5000 and out["working_79_4"]["less_non_cash"] == 700
    assert out["tie_out_difference"] == 0


def test_gst_match_buckets():
    g = "24AAAAA0000A1Z5"
    b2 = [gst_match.record(g, "INV-001", "01-06-2025", 1000, 180),
          gst_match.record(g, "INV-002", "02-06-2025", 1000, 180),
          gst_match.record(g, "X-9", "03-06-2025", 500, 90),
          gst_match.record(g, "INV-005", "05-06-2025", 400, 72)]
    books = [gst_match.record(g, "inv/1", "2025-06-01", 1000, 180),          # same key after normalising
             gst_match.record(g, "INV-002", "2025-06-02", 1000, 170),        # tax differs
             gst_match.record(g, "INV-003", "2025-06-03", 500, 90),          # not in 2B, 2B has X-9 for same tax
             gst_match.record(g, "INV-004", "2025-06-04", 100, 18)]          # not in 2B
    out = gst_match.reconcile(b2, books, tolerance=1)
    s = out["summary"]
    assert s["matched_count"] == 1 and s["mismatch_count"] == 1
    assert s["missing_in_2b_count"] == 2 and s["review_probable_count"] == 1 and s["missing_in_books_count"] == 1
    assert s["itc_at_risk"] == pytest.approx(90 + 18)          # books not in 2B; INV-002 books lower -> no risk


def test_gst_match_pairs_duplicate_keys_one_to_one():
    g = "24AAAAA0000A1Z5"
    b2 = [gst_match.record(g, "7", "2025-06-01", 100, 18)]
    books = [gst_match.record(g, "7", "2025-06-01", 100, 18), gst_match.record(g, "007", "2025-06-01", 100, 18)]
    s = gst_match.reconcile(b2, books)["summary"]
    assert s["matched_count"] == 1 and s["missing_in_2b_count"] == 1


def test_benford_mad():
    assert first_digit(0.05) == 5 and first_digit(123_000) == 1 and first_digit(0) is None
    import math, random
    rng = random.Random(1)
    benford_like = [10 ** rng.uniform(2, 7) for _ in range(5000)]
    assert benford_first_digit(benford_like)["conformity"] in ("close conformity", "acceptable conformity")
    uniform = [rng.uniform(100_000, 999_999) for _ in range(5000)]
    assert benford_first_digit(uniform)["conformity"] == "nonconformity"
