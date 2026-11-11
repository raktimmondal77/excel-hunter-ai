import pytest
from src.evaluation import evaluate_job, detect_job_category

def test_detect_10_categories():
    assert detect_job_category("Executive Sales Dashboard with Slicers", "") == "Excel dashboards"
    assert detect_job_category("Automate report with VBA Macro", "") == "Excel automation"
    assert detect_job_category("Fix broken XLOOKUP and nested formulas", "") == "Excel formulas and functions"
    assert detect_job_category("Weekly MIS Executive reporting", "") == "MIS reporting"
    assert detect_job_category("Data cleaning and deduplicate 50k rows", "") == "Data cleaning"
    assert detect_job_category("Format and beautify invoice template", "") == "Spreadsheet formatting"
    assert detect_job_category("Create Inventory and attendance tracker", "") == "Excel trackers"
    assert detect_job_category("Quarterly P&L Business Reporting model", "") == "Business reporting"
    assert detect_job_category("Warehouse dispatch operations report", "") == "Operations reporting"
    assert detect_job_category("Custom Excel commission calculator system", "") == "Custom Excel systems"

def test_100_point_scoring_formula():
    title = "High Budget Excel KPI Dashboard with Dynamic Arrays"
    desc = """We need an advanced Excel dashboard designed for our management team.
    Key deliverables:
    - Interactive slicers filtering by date and division
    - Dynamic XLOOKUP formulas and error auditing
    - Automated refresh summary for executive review
    - Clean visual formatting and chart cards
    Looking for a reliable spreadsheet freelancer.
    """
    score, priority, risks, category = evaluate_job(
        title=title,
        description=desc,
        budget=12000.0,
        client_info="Verified 5-star repeat client, 40+ hires"
    )

    # Verifications:
    assert score >= 75
    assert priority == "High"
    assert len(risks) == 0
    assert category == "Excel dashboards"

def test_fraud_and_risk_detections():
    # 1. Registration fee scam
    s1, p1, r1, _ = evaluate_job(
        title="Data Entry in Excel",
        description="Earn 50,000 INR weekly! Before starting you must deposit a registration fee of 1,000 INR.",
        budget=50000.0
    )
    assert p1 == "Low"
    assert any("registration fee" in r.lower() for r in r1)
    assert any("inflated budget" in r.lower() for r in r1)

    # 2. Telegram off-platform diversion
    s2, p2, r2, _ = evaluate_job(
        title="Copy Paste Excel Work",
        description="Contact HR manager directly on Telegram @work_hr for assignment files.",
        budget=15000.0
    )
    assert p2 == "Low"
    assert any("telegram" in r.lower() for r in r2)

    # 3. Disqualifying outside tech (C++ / Java backend)
    s3, p3, r3, _ = evaluate_job(
        title="Excel Add-in with C++ DLL",
        description="Build native C++ custom DLL library and integrate with spreadsheet.",
        budget=8000.0
    )
    assert any("outside core excel" in r.lower() for r in r3)

    # 4. Vague description (<35 chars)
    s4, p4, r4, _ = evaluate_job(
        title="Do excel",
        description="Help with excel",
        budget=500.0
    )
    assert any("vague" in r.lower() for r in r4)
