"""
Central currency utilities for EXCEL HUNTER AI.

All budgets stored in the local database are normalized to INR so that the
100-point scoring engine, the pricing assistant and the monthly income goals
(₹10,000 – ₹20,000) always compare apples to apples.

FX rates are approximate, editable constants — no paid FX API is used
(zero-cost constraint). Adjust them anytime; nothing else needs to change.
"""
from typing import Optional

# Approximate conversion rates -> INR (edit as needed; zero-cost project)
FX_TO_INR = {
    "INR": 1.0,
    "USD": 85.0,   # 1 US Dollar  ≈ ₹85
    "EUR": 92.0,   # 1 Euro        ≈ ₹92
    "GBP": 108.0,  # 1 Pound       ≈ ₹108
    "AUD": 56.0,   # 1 Aus Dollar  ≈ ₹56
    "CAD": 62.0,   # 1 Can Dollar  ≈ ₹62
    "SGD": 64.0,   # 1 Sg Dollar   ≈ ₹64
    "AED": 23.0,   # 1 UAE Dirham  ≈ ₹23
    "ZAR": 4.7,    # 1 SA Rand     ≈ ₹4.7
    "PHP": 1.5,    # 1 Peso        ≈ ₹1.5
    "MYR": 19.0,   # 1 Malay Ringgit ≈ ₹19
    "NGN": 0.055,  # 1 Naira       ≈ ₹0.055
}

# Common currency symbol / word aliases -> ISO code
CURRENCY_ALIASES = {
    "₹": "INR", "rs": "INR", "rs.": "INR", "rupees": "INR", "inr": "INR",
    "$": "USD", "usd": "USD", "dollar": "USD", "dollars": "USD",
    "€": "EUR", "eur": "EUR", "euro": "EUR", "euros": "EUR",
    "£": "GBP", "gbp": "GBP", "pound": "GBP",
    "aud": "AUD", "cad": "CAD", "sgd": "SGD", "aed": "AED",
}


def to_inr(amount: Optional[float], currency: Optional[str]) -> float:
    """Converts an amount from the given currency to INR.

    Unknown currencies are treated as INR (conservative, never inflates a
    budget by wrongly multiplying). Returns 0.0 for empty/invalid amounts.
    """
    if amount is None:
        return 0.0
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return 0.0
    if amount <= 0:
        return 0.0

    code = normalize_currency_code(currency)
    rate = FX_TO_INR.get(code)
    if rate is None:
        # Unknown code: do NOT guess a multiplier — keep the raw number as INR.
        return round(amount, 2)
    return round(amount * rate, 2)


def normalize_currency_code(currency: Optional[str]) -> str:
    """Normalizes a currency string ('usd', '$', 'Rs.' ...) to an ISO code."""
    if not currency:
        return "INR"
    raw = str(currency).strip().lower()
    if not raw:
        return "INR"
    if raw in CURRENCY_ALIASES:
        return CURRENCY_ALIASES[raw]
    upper = raw.upper()
    if upper in FX_TO_INR:
        return upper
    # e.g. 'usd (approx)' -> 'USD'
    for token in upper.split():
        if token in FX_TO_INR:
            return token
    return "INR"


def format_inr(amount: Optional[float]) -> str:
    """Formats a number as a readable INR string, e.g. ₹12,500."""
    try:
        val = float(amount or 0)
    except (TypeError, ValueError):
        val = 0.0
    return f"₹{val:,.0f}"


def parse_money_text_to_inr(text: str) -> float:
    """Extracts the first money amount from free text and converts it to INR.

    Handles '$100', '₹5,000', 'USD 250', '$60k - $100k' (uses first value,
    expands the k suffix). Returns 0.0 when nothing numeric is found.
    """
    import re
    if not text:
        return 0.0
    match = re.search(
        r"(\$|₹|€|£|rs\.?|inr|usd|eur|gbp)?\s*([\d,]+(?:\.\d+)?)\s*(k\b)?",
        str(text), re.IGNORECASE
    )
    if not match:
        return 0.0
    symbol = (match.group(1) or "").lower()
    try:
        value = float(match.group(2).replace(",", ""))
    except ValueError:
        return 0.0
    if match.group(3):  # 'k' suffix, e.g. $60k
        value *= 1000.0
    code = CURRENCY_ALIASES.get(symbol, "INR") if symbol else "INR"
    return to_inr(value, code)


def looks_like_annual_salary(amount_inr: float, raw_text: str = "") -> bool:
    """Heuristic: detects annual-salary figures (feeds often publish yearly pay,
    not per-gig budgets). Used to avoid treating a $90k/year salary as a
    per-project budget, which would wildly distort scoring."""
    raw = (raw_text or "").lower()
    if "/year" in raw or "per year" in raw or "annual" in raw or "yearly" in raw:
        return True
    # Anything above ~₹8,00,000 (≈ $9.5k) per gig is almost certainly a salary.
    if amount_inr >= 800000:
        return True
    return False
