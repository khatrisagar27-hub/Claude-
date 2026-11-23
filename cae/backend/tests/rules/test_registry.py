"""Tests for the rule registry and SQL validity of every registered rule."""
import pytest

import app.rules as rules
from tests.rules.schema import RULES_COMPANY

# Importing app.rules triggers registration of all rule modules.
ALL_RULE_CODES = sorted(rules._REGISTRY)


def test_registry_is_populated():
    # Sales/purchase/journal/payroll/treasury/inventory modules all register rules.
    assert len(ALL_RULE_CODES) >= 40


def test_get_rule_fn_resolves_known_codes():
    for code in ["SAL-001", "PUR-001", "JE-009", "PAY-001", "TRE-001", "INV-001"]:
        fn = rules.get_rule_fn(code)
        assert callable(fn), f"{code} did not resolve to a callable"


def test_get_rule_fn_returns_none_for_unknown_code():
    assert rules.get_rule_fn("NOPE-999") is None


def test_every_rule_code_maps_to_a_distinct_callable():
    fns = [rules._REGISTRY[c] for c in ALL_RULE_CODES]
    # No two codes should accidentally point at the same function object.
    assert len(set(fns)) == len(fns)


@pytest.mark.parametrize("code", ALL_RULE_CODES)
def test_rule_sql_executes_against_empty_schema(duck, code):
    """Every rule's SQL must parse and run; with no data it yields no exceptions.

    This is a regression net: a rule referencing a non-existent column (the class
    of bug previously found in the GST engine) fails here instead of in production.
    """
    fn = rules.get_rule_fn(code)
    result = fn(duck, RULES_COMPANY, None)
    assert isinstance(result, list)
    assert result == []
