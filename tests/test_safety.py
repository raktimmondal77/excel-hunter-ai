import io
import pytest
from pathlib import Path
from src.db import init_db, get_connection
import src.job_manager as jm
import src.earnings_tracker as et

@pytest.fixture
def clean_db(tmp_path: Path, monkeypatch):
    db_file = tmp_path / "safety_test.db"
    init_db(db_file)
    monkeypatch.setattr(jm, "get_connection", lambda: get_connection(db_file))
    monkeypatch.setattr(et, "get_connection", lambda: get_connection(db_file))
    return db_file

def test_clearing_sample_data_preserves_real_records(clean_db):
    """Verifies clearing sample data NEVER deletes real user jobs or real user earnings."""
    # Add real job (is_sample = 0)
    real_job = {
        "title": "Real Client Custom MIS System",
        "description": "Important real client project",
        "platform": "Direct Client",
        "budget": 15000,
        "is_sample": 0
    }
    s1, r_id, _ = jm.add_job(real_job)
    assert s1 is True

    # Add sample job (is_sample = 1)
    sample_job = {
        "title": "Sample Demo Dashboard Job",
        "description": "Demo project",
        "platform": "Upwork",
        "budget": 5000,
        "is_sample": 1
    }
    s2, s_id, _ = jm.add_job(sample_job)
    assert s2 is True

    # Add real earning
    et.add_earning(
        project_name="Real Paid Project",
        gross_amount=10000.0,
        platform_fee=0.0,
        is_sample=0
    )

    # Add sample earning
    et.add_earning(
        project_name="Sample Demo Payment",
        gross_amount=5000.0,
        platform_fee=500.0,
        is_sample=1
    )

    # Clear sample data
    jobs_del, earnings_del = jm.delete_sample_data()
    assert jobs_del == 1
    assert earnings_del == 1

    # Check remaining jobs
    remaining_jobs = jm.get_jobs(include_samples=True)
    assert len(remaining_jobs) == 1
    assert remaining_jobs.iloc[0]["id"] == r_id
    assert remaining_jobs.iloc[0]["title"] == "Real Client Custom MIS System"
    assert remaining_jobs.iloc[0]["is_sample"] == 0

    # Check remaining earnings
    remaining_earnings = et.get_earnings(include_samples=True)
    assert len(remaining_earnings) == 1
    assert remaining_earnings.iloc[0]["project_name"] == "Real Paid Project"
    assert remaining_earnings.iloc[0]["is_sample"] == 0

def test_persistence_across_restart(tmp_path):
    """Simulates computer shutdown / app restart and verifies SQLite disk persistence."""
    db_file = tmp_path / "persist_test.db"
    
    # Session 1: Initialize and store records
    init_db(db_file)
    conn1 = get_connection(db_file)
    jm.add_job({
        "title": "Persistent Excel Project",
        "description": "Testing data survival",
        "platform": "Upwork",
        "budget": 7500
    }, conn=conn1)
    conn1.close() # Connection cleanly terminated

    # Session 2: Fresh start simulation
    conn2 = get_connection(db_file)
    cursor = conn2.cursor()
    cursor.execute("SELECT title, budget, status FROM jobs WHERE title = 'Persistent Excel Project'")
    row = cursor.fetchone()
    conn2.close()

    assert row is not None
    assert row["title"] == "Persistent Excel Project"
    assert row["budget"] == 7500.0
    assert row["status"] == "discovered"

def test_job_status_transition_lifecycle(clean_db):
    """Tests updating a job through the entire pipeline: discovered -> shortlisted -> applied -> won -> paid."""
    job = {
        "title": "Pipeline Lifecycle Excel Test",
        "platform": "Freelancer",
        "budget": 8000
    }
    _, job_id, _ = jm.add_job(job)

    statuses = ["shortlisted", "proposal_drafted", "applied", "interview", "won", "paid"]
    for st in statuses:
        updated = jm.update_job_status(job_id, st, notes=f"Moved to {st}")
        assert updated is True
        
        # Verify
        df = jm.get_jobs()
        current_st = df[df["id"] == job_id].iloc[0]["status"]
        assert current_st == st

def test_invalid_csv_handling(clean_db):
    """Verifies that invalid, empty, or corrupted CSV files are safely handled without crash."""
    # 1. Empty buffer
    empty_buf = io.StringIO("")
    res_empty = jm.import_jobs_from_csv(empty_buf)
    assert res_empty["success"] is False
    assert "empty" in res_empty["error"].lower()

    # 2. CSV missing title column
    no_title_buf = io.StringIO("category,budget,link\nExcel,5000,http://example.com")
    res_no_title = jm.import_jobs_from_csv(no_title_buf)
    assert res_no_title["success"] is False
    assert "title" in res_no_title["error"].lower()

    # 3. CSV with headers only (no rows)
    headers_only = io.StringIO("title,description,platform,budget\n")
    res_headers = jm.import_jobs_from_csv(headers_only)
    assert res_headers["success"] is False
    assert "no job rows" in res_headers["error"].lower()

def test_earnings_update_and_delete(clean_db):
    """Tests adding, updating and deleting earnings."""
    e_id = et.add_earning(
        project_name="Old Project Name",
        gross_amount=5000.0,
        platform_fee=500.0,
        platform="Upwork"
    )

    # Verify initial
    df1 = et.get_earnings()
    assert df1[df1["id"] == e_id].iloc[0]["net_amount"] == 4500.0

    # Update
    up_ok = et.update_earning(
        earning_id=e_id,
        project_name="Updated Project Name",
        gross_amount=6000.0,
        platform_fee=600.0,
        platform="Upwork",
        status="received",
        notes="Updated notes"
    )
    assert up_ok is True

    # Verify updated
    df2 = et.get_earnings()
    up_row = df2[df2["id"] == e_id].iloc[0]
    assert up_row["project_name"] == "Updated Project Name"
    assert up_row["gross_amount"] == 6000.0
    assert up_row["net_amount"] == 5400.0

    # Delete
    del_ok = et.delete_earning(e_id)
    assert del_ok is True
    df3 = et.get_earnings()
    assert len(df3[df3["id"] == e_id]) == 0
