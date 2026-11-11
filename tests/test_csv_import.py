import io
import pytest
from pathlib import Path
from src.db import init_db, get_connection
import src.job_manager as jm

@pytest.fixture
def override_db(tmp_path: Path, monkeypatch):
    db_file = tmp_path / "test_csv.db"
    init_db(db_file)
    monkeypatch.setattr(jm, "get_connection", lambda: get_connection(db_file))
    return db_file

def test_csv_import_valid(override_db):
    csv_data = """title,description,platform,url,budget,currency
"Excel Inventory Dashboard","Automate stock replenishment with formulas","Upwork","https://upwork.com/jobs/inv-01",6000,INR
"VBA Automation Macro","Consolidate 10 workbooks into one","Fiverr","https://fiverr.com/orders/vba-01",3500,INR
"""
    buf = io.StringIO(csv_data)
    result = jm.import_jobs_from_csv(buf, is_sample=False)
    
    assert result["success"] is True
    assert result["imported_count"] == 2
    assert result["duplicate_count"] == 0

    # Verify jobs stored in DB
    df = jm.get_jobs()
    assert len(df) == 2
    assert "Excel Inventory Dashboard" in df["title"].values

def test_csv_import_duplicate_skipping(override_db):
    csv_data = """title,description,platform,url,budget
"Excel Dashboard Pro","Description text","Upwork","https://upwork.com/jobs/dup-01",5000
"Excel Dashboard Pro","Different description","Upwork","https://upwork.com/jobs/dup-01",5000
"""
    buf = io.StringIO(csv_data)
    result = jm.import_jobs_from_csv(buf, is_sample=False)
    
    assert result["success"] is True
    assert result["imported_count"] == 1
    assert result["duplicate_count"] == 1

def test_csv_import_fraud_detection(override_db):
    csv_data = """title,description,platform,url,budget
"Easy Excel Copy Work","Pay registration fee of 500 INR and message on Telegram","Other","https://scam.example.com",25000
"""
    buf = io.StringIO(csv_data)
    result = jm.import_jobs_from_csv(buf, is_sample=False)
    
    assert result["success"] is True
    assert result["imported_count"] == 1

    df = jm.get_jobs()
    scam_job = df.iloc[0]
    assert scam_job["priority"] == "Low"
    assert "registration fee" in scam_job["risk_flags"].lower()
