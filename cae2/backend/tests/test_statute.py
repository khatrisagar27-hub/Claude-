from datetime import date

from app.money import inr
from app.statute import gstin_check_digit, gstin_valid, law_ref, pan_is_individual_or_huf, pan_valid, tds_version


def test_gstin_check_digit():
    assert gstin_valid("27AAPFU0939F1ZV")
    assert gstin_valid("29AABCU9603R1ZJ")
    assert gstin_valid(" 27aapfu0939f1zv ")          # spacing and case are ignored
    assert not gstin_valid("27AAPFU0939F1ZX")        # wrong check digit
    assert not gstin_valid("27AAPFU0939F1Z")         # too short
    assert not gstin_valid("")
    assert gstin_check_digit("27AAPFU0939F1Z") == "V"


def test_pan():
    assert pan_valid("AAPFU0939F") and not pan_valid("AAPFU0939") and not pan_valid(None)
    assert pan_is_individual_or_huf("ABCPK1234L") and pan_is_individual_or_huf("ABCHK1234L")
    assert not pan_is_individual_or_huf("AABCU9603R")


def test_tds_versions_follow_the_invoice_date():
    assert tds_version("professional", date(2025, 3, 31))["limit"] == 30_000
    assert tds_version("professional", date(2025, 4, 1))["limit"] == 50_000
    assert tds_version("commission", date(2024, 9, 30))["rate"] == 5.0
    assert tds_version("commission", date(2024, 10, 1))["rate"] == 2.0
    assert tds_version("rent", date(2025, 4, 1))["basis"] == "monthly"
    assert tds_version("goods", date(2021, 6, 30)) is None
    assert tds_version("other", date(2025, 4, 1)) is None


def test_law_reference_adds_2025_act_only_from_tax_year_2026_27():
    assert law_ref("s.40A(3)", date(2025, 4, 1)) == "Income-tax Act, 1961 s.40A(3)"
    assert "Income-tax Act, 2025" in law_ref("s.40A(3)", date(2026, 4, 1))
    assert "(verify)" in law_ref("s.40A(3)", date(2026, 4, 1))


def test_inr_uses_indian_grouping():
    assert inr(12345678.9) == "₹1,23,45,678.90"
    assert inr(100000) == "₹1,00,000.00"
    assert inr(999) == "₹999.00"
    assert inr(-1500.5) == "-₹1,500.50"
    assert inr(None) == "₹0.00"
