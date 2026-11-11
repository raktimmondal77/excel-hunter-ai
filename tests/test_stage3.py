import pytest
from pathlib import Path
from datetime import datetime, timedelta
from src.db import init_db, get_connection
import src.user_profile as up
import src.suitability_analyser as sa
import src.pricing_assistant as pa
import src.proposal_intelligence as pi
import src.application_tracker as at
import src.earnings_tracker as et
import src.job_manager as jm

@pytest.fixture
def test_db(tmp_path: Path, monkeypatch):
    db_file = tmp_path / "test_stage3.db"
    init_db(db_file)
    monkeypatch.setattr(up, "get_connection", lambda: get_connection(db_file))
    monkeypatch.setattr(at, "get_connection", lambda: get_connection(db_file))
    monkeypatch.setattr(et, "get_connection", lambda: get_connection(db_file))
    monkeypatch.setattr(jm, "get_connection", lambda: get_connection(db_file))
    return db_file

# 1. Test User Skills Profile CRUD & Default Baseline
def test_user_profile_crud(test_db):
    # Fetch default profile
    prof = up.get_user_profile()
    assert prof["experience_level"] == "Beginner"
    assert "Basic formulas" in prof["excel_skills"]

    # Update profile with confirmed skills
    updated_data = {
        "excel_skills": ["Basic formulas", "Pivot Tables", "Dashboards"],
        "other_tools": ["Microsoft Excel", "Google Sheets"],
        "experience_level": "Intermediate",
        "work_experience_desc": "2 years managing sales spreadsheets.",
        "completed_projects_desc": "Retail KPI dashboard.",
        "industry_knowledge": "E-commerce and Retail.",
        "hours_per_week": 25.0,
        "preferred_duration": "1-2 weeks",
        "min_budget": 2000.0
    }
    assert up.save_user_profile(updated_data) is True

    loaded = up.get_user_profile()
    assert loaded["experience_level"] == "Intermediate"
    assert "Dashboards" in loaded["excel_skills"]
    assert "Google Sheets" in loaded["other_tools"]
    assert loaded["min_budget"] == 2000.0

# 2. Test Portfolio Management
def test_portfolio_management(test_db):
    proj_id = up.add_portfolio_project(
        project_title="Retail Sales Dashboard",
        project_description="Interactive slicers and monthly summaries",
        skills_used="Dashboards, Pivot Tables",
        portfolio_link="https://github.com/example/retail-dashboard"
    )
    assert proj_id is not None
    projects = up.get_portfolio_projects()
    assert len(projects) == 1
    assert projects[0]["project_title"] == "Retail Sales Dashboard"

    # Delete portfolio project
    assert up.delete_portfolio_project(proj_id) is True
    assert len(up.get_portfolio_projects()) == 0

# 3. Test Missing Skill Detection & Suitability Analyzer
def test_suitability_analyzer_and_missing_skills(test_db):
    # Profile with Beginner formulas only
    beginner_profile = {
        "excel_skills": ["Basic formulas", "Data cleaning"],
        "other_tools": ["Microsoft Excel"],
        "experience_level": "Beginner",
        "min_budget": 1000.0,
        "hours_per_week": 15.0
    }

    # Job requiring advanced VBA and Power BI
    advanced_job = {
        "title": "Automate Excel with VBA and Power BI DAX Dashboard",
        "description": "Need an expert to write macros and build a complex Power BI pipeline with SQL queries.",
        "budget": 15000.0,
        "currency": "INR",
        "client_info": "Verified Client"
    }

    analysis = sa.analyse_suitability(advanced_job, beginner_profile)
    assert "VBA" in analysis["missing_skills"]
    assert "Power BI" in analysis["missing_skills"]
    assert analysis["recommendation"] == "Avoid"
    assert analysis["recommendation_code"] == "C"
    assert analysis["is_beginner_friendly"] is False

    # Job matching beginner skills
    beginner_job = {
        "title": "Clean and format messy product spreadsheet",
        "description": "I have an excel file with duplicate rows and irregular formatting. Need formulas to calculate totals cleanly.",
        "budget": 2500.0,
        "currency": "INR",
        "client_info": "Verified Client"
    }

    analysis_beg = sa.analyse_suitability(beginner_job, beginner_profile)
    assert len(analysis_beg["missing_skills"]) == 0
    assert analysis_beg["recommendation"] == "Apply"
    assert analysis_beg["recommendation_code"] == "A"
    assert analysis_beg["is_beginner_friendly"] is True
    assert analysis_beg["suitability_score"] >= 70

# 4. Test Pricing When Client Budget is Missing vs Stated
def test_pricing_assistant_budget_specified_and_missing(test_db):
    profile = {
        "experience_level": "Beginner",
        "min_budget": 1500.0
    }

    # Case A: Budget not specified (budget=0 or None)
    job_no_budget = {
        "title": "Excel Commission Formulas",
        "description": "Need formulas written for sales tiers.",
        "platform": "Freelancer.com",
        "budget": 0.0,
        "currency": "INR"
    }
    pricing_a = pa.calculate_pricing_recommendation(job_no_budget, profile)
    assert pricing_a["budget_stated"] is False
    assert pricing_a["budget_display"] == "Budget not specified"
    assert pricing_a["suggested_quotation_inr"] >= 1500.0 # Respects minimum acceptable budget
    assert pricing_a["platform_fee_rate_percent"] == 10

    # Case B: Stated budget
    job_with_budget = {
        "title": "Excel Commission Formulas",
        "description": "Need formulas written for sales tiers.",
        "platform": "Upwork",
        "budget": 100.0, # USD
        "currency": "USD"
    }
    pricing_b = pa.calculate_pricing_recommendation(job_with_budget, profile)
    assert pricing_b["budget_stated"] is True
    assert "100.00 USD" in pricing_b["budget_display"]
    assert pricing_b["suggested_quotation_job_currency"] > 0
    assert pricing_b["platform_fee_rate_percent"] == 10

    # Case C: Manual Override
    pricing_override = pa.calculate_pricing_recommendation(job_with_budget, profile, manual_quote_override=80.0)
    assert pricing_override["final_quotation_job_currency"] == 80.0

# 5. Test AI Proposal Generator 3 Versions & Strict Verified Skills
def test_proposal_generator_versions_and_strict_skills(test_db):
    # Profile WITHOUT VBA or Python
    profile_without_vba = {
        "excel_skills": ["Basic formulas", "Data cleaning", "Pivot Tables"],
        "other_tools": ["Microsoft Excel"],
        "experience_level": "Beginner"
    }

    job = {
        "title": "Need help formatting Excel data and creating pivot table summary",
        "description": "Please organize our inventory sheet and create a clean summary pivot table.",
        "platform": "Freelancer.com"
    }

    proposals = pi.generate_three_proposal_versions(job, profile_without_vba, freelancer_name="Raktim")
    assert "version_a" in proposals
    assert "version_b" in proposals
    assert "version_c" in proposals

    # Strict Rule: VBA or Python must NOT appear in proposals because user did NOT confirm them
    for ver in ["version_a", "version_b", "version_c"]:
        text = proposals[ver].lower()
        assert "vba" not in text
        assert "python" not in text
        assert "power bi" not in text
        assert "raktim" in text

# 6. Test Duplicate Application Prevention on Same Platform
def test_duplicate_application_prevention(test_db):
    # Create a job
    _, job_id, _ = jm.add_job({
        "title": "Excel MIS Report Setup",
        "platform": "Upwork",
        "budget": 5000.0
    })

    # Record first application
    success1, app_id1, _ = at.record_application(
        job_id=job_id,
        platform="Upwork",
        proposal_text="First customized proposal",
        bid_amount=5000.0,
        status="Submitted"
    )
    assert success1 is True
    assert app_id1 is not None

    # Try submitting duplicate application for same job on same platform
    success2, app_id2, msg2 = at.record_application(
        job_id=job_id,
        platform="Upwork",
        proposal_text="Duplicate attempt",
        bid_amount=5000.0
    )
    assert success2 is False
    assert app_id2 is None
    assert "already exists" in msg2

# 7. Test Application Status Changes Across 13 Statuses
def test_application_status_changes(test_db):
    _, job_id, _ = jm.add_job({
        "title": "Excel Cost Tracker",
        "platform": "Freelancer",
        "budget": 4000.0
    })

    success, app_id, _ = at.record_application(
        job_id=job_id,
        platform="Freelancer",
        proposal_text="Proposal text",
        bid_amount=4000.0,
        status="Interested"
    )
    assert success is True

    # Transition to Submitted
    assert at.update_application_status(app_id, "Submitted") is True
    app = at.get_applications()
    assert app.iloc[0]["status"] == "Submitted"

    # Transition to Client Replied
    assert at.update_application_status(app_id, "Client Replied", client_response="Can you start tomorrow?") is True
    app = at.get_applications()
    assert app.iloc[0]["status"] == "Client Replied"

    # Transition to Awarded
    assert at.update_application_status(app_id, "Awarded") is True
    app = at.get_applications()
    assert app.iloc[0]["status"] == "Awarded"

# 8. Test Follow-up Manager Date Calculations & Message Generation
def test_follow_up_groups_and_messages(test_db):
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    four_days_ago = (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d")

    # App 1: Due today
    _, j1, _ = jm.add_job({"title": "Job 1", "platform": "Upwork"})
    at.record_application(job_id=j1, platform="Upwork", proposal_text="p1", bid_amount=3000, follow_up_date=today)

    # App 2: Overdue
    _, j2, _ = jm.add_job({"title": "Job 2", "platform": "Freelancer"})
    at.record_application(job_id=j2, platform="Freelancer", proposal_text="p2", bid_amount=4000, follow_up_date=yesterday)

    # App 3: Upcoming
    _, j3, _ = jm.add_job({"title": "Job 3", "platform": "Truelancer"})
    at.record_application(job_id=j3, platform="Truelancer", proposal_text="p3", bid_amount=5000, follow_up_date=tomorrow)

    # App 4: No Response (> 3 days, no client response)
    _, j4, _ = jm.add_job({"title": "Job 4", "platform": "Direct"})
    at.record_application(job_id=j4, platform="Direct", proposal_text="p4", bid_amount=6000, applied_date=four_days_ago)

    groups = at.get_follow_up_groups(today)
    assert len(groups["due_today"]) == 1
    assert len(groups["overdue"]) == 1
    assert len(groups["upcoming"]) == 1
    assert len(groups["no_response"]) >= 1

    # Test template message generation
    msg = at.generate_follow_up_message("Sales Commission Sheet", client_name="Alex", stage=1)
    assert "Hi Alex," in msg
    assert "Sales Commission Sheet" in msg

# 9. Test Performance Analytics (Project Value vs Revenue Received)
def test_performance_analytics(test_db):
    # Add application with Awarded status (value = ₹8,000)
    _, j_id, _ = jm.add_job({"title": "Awarded Project", "platform": "Upwork", "budget": 8000})
    at.record_application(job_id=j_id, platform="Upwork", proposal_text="p", bid_amount=8000, status="Awarded")

    # Add realized earnings entry (received = ₹5,000)
    et.add_earning(project_name="Awarded Project Milestone 1", gross_amount=5500, platform_fee=500, status="received")

    analytics = et.get_performance_analytics()
    assert analytics["total_applications"] >= 1
    assert analytics["projects_awarded"] >= 1
    assert analytics["total_project_value"] == 8000.0
    assert analytics["amount_received"] == 5000.0
    assert analytics["outstanding_payments"] == 3000.0 # 8000 - 5000

# 10. Test No Automatic Submission (Human Approval Required)
def test_no_automatic_submission(test_db):
    # Application tracker requires explicit record_application call with human-specified parameters
    # A job can sit in 'shortlisted' or 'proposal_drafted' indefinitely until user submits
    _, job_id, _ = jm.add_job({"title": "Unapplied Job", "platform": "Upwork", "status": "proposal_drafted"})
    apps = at.get_applications()
    assert not any(a["job_id"] == job_id for _, a in apps.iterrows())
