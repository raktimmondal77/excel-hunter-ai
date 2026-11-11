import pytest
from pathlib import Path
from src.db import init_db, get_connection
import src.job_manager as jm
import src.application_tracker as at

@pytest.fixture
def override_db(tmp_path: Path, monkeypatch):
    db_file = tmp_path / "test_app_tracker.db"
    init_db(db_file)
    monkeypatch.setattr(jm, "get_connection", lambda: get_connection(db_file))
    monkeypatch.setattr(at, "get_connection", lambda: get_connection(db_file))
    return db_file

def test_record_application_syncs_job_status(override_db):
    # Add a job first
    success, job_id, _ = jm.add_job({
        "title": "Excel Commission Calculator",
        "platform": "Freelancer",
        "budget": 4500,
        "status": "shortlisted"
    })
    assert success is True

    # Record application
    app_success, app_id, msg = at.record_application(
        job_id=job_id,
        platform="Freelancer",
        proposal_text="Sample customized proposal",
        bid_amount=4500.0,
        applied_date="2026-11-11",
        follow_up_date="2026-11-14",
        follow_up_notes="Check for client reply"
    )
    assert app_success is True
    assert app_id is not None

    # Verify job status in jobs table transitioned to 'applied'
    jobs_df = jm.get_jobs()
    job_row = jobs_df[jobs_df["id"] == job_id].iloc[0]
    assert job_row["status"] == "applied"

    # Verify application recorded in applications table
    apps_df = at.get_applications()
    assert len(apps_df) == 1
    assert apps_df.iloc[0]["job_title"] == "Excel Commission Calculator"
    assert apps_df.iloc[0]["bid_amount"] == 4500.0

def test_update_application_status_and_sync(override_db):
    # Setup job and application
    _, job_id, _ = jm.add_job({
        "title": "Inventory Audit Spreadsheet",
        "platform": "Upwork",
        "budget": 6000
    })
    _, app_id, _ = at.record_application(
        job_id=job_id,
        platform="Upwork",
        proposal_text="Proposal text",
        bid_amount=6000.0
    )

    # Client replies
    updated = at.update_application_status(app_id, "replied", follow_up_notes="Client asked for sample file")
    assert updated is True

    # Check status synced to job
    jobs_df = jm.get_jobs()
    assert jobs_df[jobs_df["id"] == job_id].iloc[0]["status"] == "replied"

    # Won contract
    won_updated = at.update_application_status(app_id, "won", follow_up_notes="Contract started!")
    assert won_updated is True
    jobs_df2 = jm.get_jobs()
    assert jobs_df2[jobs_df2["id"] == job_id].iloc[0]["status"] == "won"

def test_get_follow_ups_due(override_db):
    # Add application due in the past/today
    _, j1, _ = jm.add_job({"title": "Job Due Today", "platform": "Fiverr", "budget": 3000})
    at.record_application(
        job_id=j1,
        platform="Fiverr",
        proposal_text="Prop 1",
        bid_amount=3000,
        follow_up_date="2026-11-10" # Yesterday/due
    )

    # Add application due in the future
    _, j2, _ = jm.add_job({"title": "Job Due Later", "platform": "Fiverr", "budget": 5000})
    at.record_application(
        job_id=j2,
        platform="Fiverr",
        proposal_text="Prop 2",
        bid_amount=5000,
        follow_up_date="2026-11-25" # Far future
    )

    # Check due follow-ups as of 2026-11-11
    due_df = at.get_follow_ups_due("2026-11-11")
    assert len(due_df) == 1
    assert due_df.iloc[0]["job_title"] == "Job Due Today"
