"""Rule registry — maps rule_code strings to Python callables."""
from typing import Callable, Optional


_REGISTRY: dict[str, Callable] = {}


def register(rule_code: str):
    def decorator(fn: Callable) -> Callable:
        _REGISTRY[rule_code] = fn
        return fn
    return decorator


def get_rule_fn(rule_code: str) -> Optional[Callable]:
    return _REGISTRY.get(rule_code)


# Import all rule modules to trigger registration
from app.rules import sales_rules, purchase_rules, inventory_rules, journal_rules, payroll_rules, treasury_rules  # noqa: F401, E402
