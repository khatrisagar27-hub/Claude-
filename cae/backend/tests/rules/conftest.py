"""Fixtures for the SQL audit-rule tests."""
import pytest

from tests.rules.schema import new_connection


@pytest.fixture
def duck():
    """A fresh in-memory DuckDB connection with the rule schema loaded."""
    conn = new_connection()
    try:
        yield conn
    finally:
        conn.close()
