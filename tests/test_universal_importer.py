import pytest
from pathlib import Path
from src.db import init_db, get_connection
import src.job_manager as jm
from src.discovery.universal_importer import (
    detect_platform_from_url,
    import_job_from_url,
    import_job_from_pasted_text,
    parse_email_alert
)

@pytest.fixture
def override_db(tmp_path: Path, monkeypatch):
    db_file = tmp_path / "test_importer.db"
    init_db(db_file)
    monkeypatch.setattr(jm, "get_connection", lambda: get_connection(db_file))
    return db_file

def test_detect_platform_from_url():
    assert detect_platform_from_url("https://www.upwork.com/jobs/~01xyz") == "Upwork"
    assert detect_platform_from_url("https://www.freelancer.com/projects/excel/123") == "Freelancer.com"
    assert detect_platform_from_url("https://www.fiverr.com/orders/fo123") == "Fiverr"
    assert detect_platform_from_url("https://www.peopleperhour.com/freelance-jobs/excel") == "PeoplePerHour"
    assert detect_platform_from_url("https://www.truelancer.com/freelance-job/excel-456") == "Truelancer"
    assert detect_platform_from_url("https://www.guru.com/jobs/excel-formula/789") == "Guru"
    assert detect_platform_from_url("https://example.com/project") == "Direct Client"

def test_import_job_from_url(override_db):
    success, j_id, msg = import_job_from_url(
        job_url="https://www.guru.com/jobs/excel-dashboard-automation/101",
        title="Custom Excel Financial Dashboard",
        budget=8000.0,
        description="Build executive financial dashboard with KPI graphs."
    )
    assert success is True
    assert j_id is not None

    # Verify duplicate URL rejection
    s2, _, msg2 = import_job_from_url(
        job_url="https://www.guru.com/jobs/excel-dashboard-automation/101",
        title="Duplicate Attempt",
        budget=8000.0
    )
    assert s2 is False
    assert "Duplicate" in msg2

def test_import_job_from_pasted_text(override_db):
    text = """Automate Retail Sales Reconciliation Sheet
Looking for an Excel expert to write formulas to reconcile daily cash registers against bank statement CSV.
Budget: ₹6,500
Turnaround needed within 2 days.
"""
    success, j_id, msg = import_job_from_pasted_text(
        raw_text=text,
        platform="Direct Client"
    )
    assert success is True
    assert j_id is not None

    df = jm.get_jobs()
    job = df[df["id"] == j_id].iloc[0]
    assert "Retail Sales Reconciliation" in job["title"]
    assert job["budget"] == 6500.0

def test_parse_email_alert(override_db):
    subject = "New Job Alert: Urgent Excel Formula Expert Required"
    body = """Hi Rakesh, a new project matches your Excel skills:
Title: Fix #N/A and circular references in sales sheet
Link: https://www.freelancer.com/projects/excel/fix-formulas-urgent
Budget: ₹3500 INR
Please submit proposal.
"""
    success, j_id, msg = parse_email_alert(subject, body, sender_platform="Freelancer.com")
    assert success is True
    assert j_id is not None

    df = jm.get_jobs()
    job = df[df["id"] == j_id].iloc[0]
    assert "Urgent Excel Formula Expert" in job["title"]
    assert job["platform"] == "Freelancer.com"
