from typing import Dict, Any, Optional
from src.user_profile import get_user_profile
from src.suitability_analyser import estimate_difficulty_and_hours, extract_required_skills

PLATFORM_FEE_RATES = {
    "upwork": 0.10,
    "freelancer": 0.10,
    "freelancer.com": 0.10,
    "fiverr": 0.20,
    "truelancer": 0.08,
    "peopleperhour": 0.20,
    "guru": 0.09,
    "direct client": 0.00
}

# Base hourly rates in INR by experience level
BASE_HOURLY_RATES = {
    "Beginner": 400.0,
    "Intermediate": 750.0,
    "Advanced": 1200.0
}

def calculate_pricing_recommendation(
    job: Dict[str, Any],
    profile: Optional[Dict[str, Any]] = None,
    manual_quote_override: Optional[float] = None
) -> Dict[str, Any]:
    """
    Computes pricing recommendations:
    - Client stated budget (never invented)
    - Estimated hours required
    - Suggested quotation
    - Minimum acceptable quotation
    - Estimated hourly earning (net of platform fee)
    - Delivery time recommendation
    """
    if profile is None:
        profile = get_user_profile()

    user_exp = profile.get("experience_level", "Beginner")
    user_min_budget = float(profile.get("min_budget", 1500.0))
    base_hourly = BASE_HOURLY_RATES.get(user_exp, 400.0)

    title = job.get("title", "")
    desc = job.get("description", "")
    platform = (job.get("platform") or "Direct Client").strip()
    raw_budget = job.get("budget")
    currency = (job.get("currency") or "INR").upper()

    # 1. Budget Display & Check (Never invent missing budget)
    if raw_budget is None or float(raw_budget) <= 0:
        budget_stated = False
        budget_display = "Budget not specified"
        client_budget = 0.0
    else:
        budget_stated = True
        client_budget = float(raw_budget)
        budget_display = f"{client_budget:,.2f} {currency}"

    # 2. Estimate hours based on complexity
    combined_text = f"{title} {desc}"
    required_skills = extract_required_skills(combined_text)
    difficulty, est_hours, delivery_rec = estimate_difficulty_and_hours(required_skills, len(desc))

    # Adjust hours slightly if user is beginner
    if user_exp == "Beginner" and difficulty != "Low":
        est_hours = round(est_hours * 1.25, 1)

    # 3. Base Quotation Calculation
    calculated_quote = round(base_hourly * est_hours, -1) # rounded to nearest 10

    # Ensure quote is at least user's minimum acceptable budget
    suggested_quote = max(calculated_quote, user_min_budget)

    # Calibrate against client stated budget if available
    client_budget_inr = client_budget * 85.0 if currency in ["USD", "EUR"] else client_budget
    if budget_stated and client_budget_inr > 0:
        if client_budget_inr >= user_min_budget:
            # If client budget is reasonable, anchor near client budget (85% to 100%)
            if client_budget_inr > suggested_quote * 1.5:
                # Client has generous budget, propose good value
                suggested_quote = round(min(client_budget_inr * 0.9, suggested_quote * 1.4), -1)
            elif client_budget_inr < suggested_quote:
                # Client budget is slightly tight, offer close to client budget if >= min budget
                suggested_quote = max(client_budget_inr, user_min_budget)

    # Convert suggested quote to job's currency
    fx_rate = 85.0 if currency in ["USD", "EUR"] else 1.0
    suggested_quote_job_currency = round(suggested_quote / fx_rate, 2)
    min_quote_job_currency = round(user_min_budget / fx_rate, 2)

    # Apply manual override if provided
    final_quote_job_currency = manual_quote_override if manual_quote_override is not None else suggested_quote_job_currency
    final_quote_inr = final_quote_job_currency * fx_rate

    # 4. Platform Fee Deduction
    platform_key = platform.lower()
    fee_rate = 0.10 # default 10%
    for k, rate in PLATFORM_FEE_RATES.items():
        if k in platform_key:
            fee_rate = rate
            break

    platform_fee_inr = round(final_quote_inr * fee_rate, 2)
    net_earnings_inr = round(final_quote_inr - platform_fee_inr, 2)
    net_hourly_inr = round(net_earnings_inr / max(1.0, est_hours), 2)

    return {
        "budget_stated": budget_stated,
        "budget_display": budget_display,
        "currency": currency,
        "estimated_hours": est_hours,
        "complexity": difficulty,
        "suggested_quotation_job_currency": suggested_quote_job_currency,
        "suggested_quotation_inr": suggested_quote,
        "minimum_acceptable_quotation": min_quote_job_currency,
        "final_quotation_job_currency": final_quote_job_currency,
        "final_quotation_inr": final_quote_inr,
        "platform_name": platform,
        "platform_fee_rate_percent": int(fee_rate * 100),
        "platform_fee_amount_inr": platform_fee_inr,
        "net_earnings_inr": net_earnings_inr,
        "estimated_hourly_earning_inr": net_hourly_inr,
        "delivery_time_recommendation": delivery_rec
    }
