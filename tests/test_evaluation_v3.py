"""Stage 3 tests — evaluation engine v3: relevance gate, currency-aware
budget scoring, freshness scoring, and INR normalization at the repository
boundary."""
import pytest
from datetime import date, timedelta
from src.evaluation import evaluate_job, is_excel_job
from src.job_manager import add_job

TODAY = date.today().strftime("%Y-%m-%d")
YESTERDAY = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
THREE_DAYS_AGO = (date.today() - timedelta(days=3)).strftime("%Y-%m-%d")
FORTY_DAYS_AGO = (date.today() - timedelta(days=40)).strftime("%Y-%m-%d")


# ---------------------------------------------------------------
# Relevance gate
# ---------------------------------------------------------------
def test_relevance_gate_accepts_real_excel_jobs():
    assert is_excel_job("Excel Sales Dashboard", "Build a KPI dashboard from sales data")
    assert is_excel_job("Contact Details Data Entry", "copy records into a single Excel or Google Sheets file")
    assert is_excel_job("VBA macro to clean workbook", "Automate weekly reporting with a macro")
    assert is_excel_job("Pivot table summary needed", "spreadsheet with pivots")


def test_relevance_gate_rejects_verb_usage_and_junk():
    # "excel" as an English verb must NOT count
    assert not is_excel_job("Candidates who excel at communication", "fast-paced marketing team")
    assert not is_excel_job("Marketing associates recruitment", "energetic field associates needed")
    assert not is_excel_job("Boost SaaS Trials via SEO", "grow organic traffic for B2B SaaS")
    assert not is_excel_job("Design Coastal Security Floating Marine Barrier", "engineering project")


def test_non_excel_job_score_capped_and_flagged():
    score, priority, risks, _ = evaluate_job(
        title="Marketing associates recruitment",
        description="We need energetic marketing associates in every district of Andhra Pradesh. Great pay, flexible hours, weekly incentives for top performers.",
        budget=20000.0,
        client_info="Freelancer.com client | 3 bids so far",
        date_posted=YESTERDAY
    )
    assert score <= 35
    assert priority == "Low"
    assert any("Not an Excel" in r for r in risks)


# ---------------------------------------------------------------
# Currency-aware budget scoring
# ---------------------------------------------------------------
def test_usd_budget_scores_as_its_inr_value():
    # Same job, two currencies: $400 (≈ ₹34,000) vs ₹34,000 —
    # scores must be identical because everything is normalized to INR.
    s_usd, _, _, _ = evaluate_job(
        "Excel Sales Dashboard with Pivot Tables",
        "Need an Excel dashboard built from our sales spreadsheet with pivot tables, slicers and clean formatting.",
        budget=400.0, currency="USD", date_posted=YESTERDAY
    )
    s_inr, _, _, _ = evaluate_job(
        "Excel Sales Dashboard with Pivot Tables",
        "Need an Excel dashboard built from our sales spreadsheet with pivot tables, slicers and clean formatting.",
        budget=400 * 85.0, currency="INR", date_posted=YESTERDAY
    )
    assert s_usd == s_inr
    assert s_usd >= 70  # a ₹34k budget project must look attractive


def test_tiny_usd_budget_scores_low():
    # $10 ≈ ₹850 — must NOT be scored as if it were ₹10,000+
    s_small, _, _, _ = evaluate_job(
        "Quick Excel formula fix",
        "Fix one VLOOKUP formula in our Excel sheet, quick job for an expert.",
        budget=10.0, currency="USD", date_posted=YESTERDAY
    )
    s_real, _, _, _ = evaluate_job(
        "Quick Excel formula fix",
        "Fix one VLOOKUP formula in our Excel sheet, quick job for an expert.",
        budget=10.0 * 85.0, currency="INR", date_posted=YESTERDAY
    )
    assert s_small == s_real
    assert s_small < 70  # small money stays small


# ---------------------------------------------------------------
# Freshness scoring
# ---------------------------------------------------------------
def test_fresh_job_outscores_stale_job():
    base_title = "Excel Inventory Tracker with Alerts"
    base_desc = ("Build an Excel tracker with conditional formatting alerts, "
                 "dropdown lists and a summary dashboard for stock levels.")
    s_fresh, p_fresh, _, _ = evaluate_job(base_title, base_desc, budget=6000.0, date_posted=YESTERDAY)
    s_stale, p_stale, risks_stale, _ = evaluate_job(base_title, base_desc, budget=6000.0, date_posted=FORTY_DAYS_AGO)

    assert s_fresh > s_stale
    assert any("Stale posting" in r for r in risks_stale)


def test_rush_deadline_is_warned_not_hidden():
    _, _, risks, _ = evaluate_job(
        "Excel data cleanup — urgent",
        "Need this spreadsheet cleaned and deduplicated ASAP, within 24 hours please. Excel file attached.",
        budget=3000.0,
        date_posted=TODAY
    )
    assert any("Rush deadline" in r for r in risks)


# ---------------------------------------------------------------
# INR normalization at the repository boundary
# ---------------------------------------------------------------
def test_add_job_converts_usd_budget_to_inr(tmp_path, monkeypatch):
    from src.db import init_db, get_connection
    import src.job_manager as jm

    db_file = tmp_path / "normalize.db"
    init_db(db_file)
    monkeypatch.setattr(jm, "get_connection", lambda: get_connection(db_file))

    success, job_id, _ = jm.add_job({
        "title": "Excel Dashboard for Sales Team (USD client)",
        "description": "Create an Excel dashboard with pivot tables and slicers from our sales spreadsheet data.",
        "platform": "Freelancer.com",
        "url": "https://example.com/usd-job-1",
        "budget": 500.0,
        "currency": "USD",
        "client_info": "Overseas client",
        "date_posted": THREE_DAYS_AGO
    })
    assert success is True

    stored = jm.get_jobs().iloc[0]
    assert stored["currency"] == "INR"
    assert stored["budget"] == pytest.approx(500 * 85.0)
    assert "Original budget: 500" in stored["client_info"]
    assert "USD" in stored["client_info"]
    # A $500 (₹42,500) job should score as an attractive budget
    assert stored["score"] >= 70


def test_soft_warning_vs_severe_flag_classification():
    from src.evaluation import is_soft_warning
    assert is_soft_warning("Rush deadline — confirm feasibility before bidding") is True
    assert is_soft_warning("Stale posting (45 days old) — likely already awarded") is True
    assert is_soft_warning("Posting is 25 days old — may already be awarded") is True
    assert is_soft_warning("Very small budget (₹850) — barely worth the effort") is True
    # Severe flags are NOT soft warnings
    assert is_soft_warning("Demands security deposit from freelancer") is False
    assert is_soft_warning("Directs communication to off-platform Telegram account") is False
    assert is_soft_warning("Not an Excel/spreadsheet project — outside your service catalogue") is False
    assert is_soft_warning("") is False
