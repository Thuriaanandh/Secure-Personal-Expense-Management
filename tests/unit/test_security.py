from datetime import timedelta

from src.app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    validate_password_strength,
    verify_password,
)
from src.app.services.reporting_service import sanitize_csv_cell


def test_password_hashing():
    raw = "SuperSecretP@ss123"
    hashed = get_password_hash(raw)
    assert hashed != raw
    assert hashed.startswith("$argon2id$")
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_password_strength_validation():
    # Too short (< 10 chars)
    assert validate_password_strength("Short1!") is False

    # Missing uppercase
    assert validate_password_strength("lowercase12345!") is False

    # Missing lowercase
    assert validate_password_strength("UPPERCASE12345!") is False

    # Missing digit
    assert validate_password_strength("NoDigitsHere!@#") is False

    # Missing special character
    assert validate_password_strength("NoSpecialChar123") is False

    # Valid password
    assert validate_password_strength("StrongPassw0rd!2026") is True


def test_jwt_token_creation_and_decoding():
    token_dict = create_access_token(subject=42, expires_delta=timedelta(minutes=15))
    assert isinstance(token_dict["access_token"], str)

    payload = decode_access_token(token_dict["access_token"])
    assert payload is not None
    assert payload["sub"] == "42"
    assert "jti" in payload
    assert "exp" in payload


def test_jwt_token_expiration():
    token_dict = create_access_token(subject=42, expires_delta=timedelta(seconds=-5))
    payload = decode_access_token(token_dict["access_token"])
    assert payload is None


def test_jwt_token_tampered():
    token_dict = create_access_token(subject=42)
    token = token_dict["access_token"]
    tampered = token[:-4] + "fake"
    payload = decode_access_token(tampered)
    assert payload is None


def test_csv_formula_injection_sanitization():
    # Formulas with trigger symbols (CWE-1236)
    assert sanitize_csv_cell("=1+1") == "'=1+1"
    assert sanitize_csv_cell("=cmd|' /C calc'!A0") == "'=cmd|' /C calc'!A0"
    assert sanitize_csv_cell("@SUM(A1:A10)") == "'@SUM(A1:A10)"
    assert sanitize_csv_cell("+441234567") == "'+441234567"
    assert sanitize_csv_cell("-500.00") == "'-500.00"
    assert sanitize_csv_cell("\tTABBED") == "'\tTABBED"

    # Benign financial text and amounts
    assert sanitize_csv_cell("Grocery Shopping") == "Grocery Shopping"
    assert sanitize_csv_cell("Salary October 2026") == "Salary October 2026"
    assert sanitize_csv_cell("1250.75") == "1250.75"
    assert sanitize_csv_cell(None) == ""
