"""Property-based and fuzz testing suite using Hypothesis to verify security invariants."""

from datetime import date
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from src.app.core.security import validate_password_strength
from src.app.schemas.transaction import TransactionCreate, TransactionFilterParams
from src.app.services.reporting_service import FORMULA_TRIGGERS, sanitize_csv_cell


@given(st.text(min_size=0, max_size=300))
def test_property_csv_formula_injection_sanitization_invariant(text_val: str):
    """
    SECURITY INVARIANT (CWE-1236):
    For ANY arbitrary string, the sanitized output must NEVER start with an unescaped
    formula trigger character ('=', '+', '-', '@', '\\t', '\\r').
    """
    sanitized = sanitize_csv_cell(text_val)

    if text_val and text_val.startswith(FORMULA_TRIGGERS):
        # Must prepend single quote
        assert sanitized.startswith("'")
        assert sanitized[1:] == text_val
    else:
        assert sanitized == text_val


@given(st.text(min_size=0, max_size=200))
def test_property_password_strength_validator_resilience_and_soundness(pwd: str):
    """
    ROBUSTNESS & SOUNDNESS INVARIANT (CWE-20 / CWE-521):
    The password validator must never raise unexpected exceptions on arbitrary Unicode,
    and if it returns valid (True), the password must strictly satisfy NIST complexity.
    """
    is_valid = validate_password_strength(pwd)
    assert isinstance(is_valid, bool)

    if is_valid:
        assert len(pwd) >= 10
        assert any(c.isupper() for c in pwd)
        assert any(c.islower() for c in pwd)
        assert any(c.isdigit() for c in pwd)
        assert any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in pwd)


@given(
    d1=st.dates(min_value=date(2000, 1, 1), max_value=date(2035, 12, 31)),
    d2=st.dates(min_value=date(2000, 1, 1), max_value=date(2035, 12, 31)),
)
def test_property_date_range_validation_boundary_invariants(d1: date, d2: date):
    """
    QUERY BOUNDARY INVARIANT (CWE-20 / SEC-017):
    For any pair of dates:
    - If d1 > d2: Must reject inverted range with ValidationError.
    - If (d2 - d1).days > 1826: Must reject excessive span (> 5 years) with ValidationError.
    - Otherwise: Must validate and construct cleanly.
    """
    if d1 > d2:
        with pytest.raises((ValueError, ValidationError), match="start_date cannot be later than end_date"):
            TransactionFilterParams(start_date=d1, end_date=d2)
    elif (d2 - d1).days > 1826:
        with pytest.raises((ValueError, ValidationError), match="Date range cannot exceed 5 years"):
            TransactionFilterParams(start_date=d1, end_date=d2)
    else:
        params = TransactionFilterParams(start_date=d1, end_date=d2)
        assert params.start_date == d1
        assert params.end_date == d2


@given(
    amount=st.decimals(min_value=Decimal("-1000.00"), max_value=Decimal("2000000.00"), places=2)
)
def test_property_transaction_amount_invariants(amount: Decimal):
    """
    FINANCIAL INTEGRITY INVARIANT (CWE-840):
    Transactions can only be created with amounts strictly between $0.01 and $1,000,000.00.
    """
    payload = {
        "category_id": 1,
        "amount": amount,
        "type": "EXPENSE",
        "transaction_date": date(2026, 10, 8),
    }

    if Decimal("0.00") < amount <= Decimal("1000000.00"):
        obj = TransactionCreate(**payload)
        assert obj.amount == amount
    else:
        with pytest.raises(ValidationError):
            TransactionCreate(**payload)
