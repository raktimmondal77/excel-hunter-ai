"""Stage 3 tests — central currency utilities."""
import pytest
from src.currency import (
    to_inr, normalize_currency_code, format_inr,
    parse_money_text_to_inr, looks_like_annual_salary, FX_TO_INR
)


def test_usd_to_inr():
    assert to_inr(400, "USD") == 400 * FX_TO_INR["USD"]
    assert to_inr(400, "usd") == 400 * FX_TO_INR["USD"]
    assert to_inr(400, "$") == 400 * FX_TO_INR["USD"]


def test_eur_gbp_to_inr():
    assert to_inr(100, "EUR") == 100 * FX_TO_INR["EUR"]
    assert to_inr(100, "GBP") == 100 * FX_TO_INR["GBP"]


def test_inr_passthrough():
    assert to_inr(5000, "INR") == 5000.0
    assert to_inr(5000, None) == 5000.0
    assert to_inr(5000, "") == 5000.0


def test_invalid_amounts_never_crash():
    assert to_inr(None, "USD") == 0.0
    assert to_inr(0, "USD") == 0.0
    assert to_inr(-100, "USD") == 0.0
    assert to_inr("not-a-number", "USD") == 0.0


def test_unknown_currency_is_conservative():
    # Unknown codes must NOT be multiplied by a guessed rate
    assert to_inr(250, "XYZ") == 250.0


def test_normalize_currency_aliases():
    assert normalize_currency_code("$") == "USD"
    assert normalize_currency_code("rs.") == "INR"
    assert normalize_currency_code("Rs") == "INR"
    assert normalize_currency_code("USD (approx)") == "USD"
    assert normalize_currency_code("") == "INR"
    assert normalize_currency_code(None) == "INR"


def test_format_inr():
    assert format_inr(12500) == "₹12,500"
    assert format_inr(None) == "₹0"


def test_parse_money_text():
    assert parse_money_text_to_inr("$100") == 100 * FX_TO_INR["USD"]
    assert parse_money_text_to_inr("₹5,000") == 5000.0
    assert parse_money_text_to_inr("USD 250") == 250 * FX_TO_INR["USD"]
    # k-suffix expansion: $60k = 60,000 USD
    assert parse_money_text_to_inr("$60k - $100k") == 60000 * FX_TO_INR["USD"]
    assert parse_money_text_to_inr("no money here") == 0.0


def test_annual_salary_detection():
    assert looks_like_annual_salary(90000 * FX_TO_INR["USD"]) is True   # $90k
    assert looks_like_annual_salary(5000, "$60k - $100k /year") is True
    assert looks_like_annual_salary(5000.0) is False
