import pytest
from pathlib import Path
from src.db import init_db, get_connection
from src.job_manager import add_job, is_duplicate_job, normalize_title, normalize_url

@pytest.fixture
def temp_conn(tmp_path: Path):
    db_file = tmp_path / "test_dup.db"
    init_db(db_file)
    conn = get_connection(db_file)
    yield conn
    conn.close()

def test_normalize_title():
    assert normalize_title("URGENT: Need Excel Expert for Dashboard!") == "excel dashboard"
    assert normalize_title("Looking for hiring an Excel Specialist") == "an excel"
    assert normalize_title("Excel formulas repair") == "excel formulas repair"

def test_normalize_url():
    assert normalize_url("https://upwork.com/jobs/123/") == "https://upwork.com/jobs/123"
    assert normalize_url(" HTTPS://UPWORK.COM/jobs/123 ") == "https://upwork.com/jobs/123"

def test_duplicate_detection_by_url(temp_conn):
    job1 = {
        "title": "Excel Dashboard Creator",
        "platform": "Upwork",
        "url": "https://upwork.com/jobs/sample123",
        "budget": 5000
    }
    success, job_id, msg = add_job(job1, conn=temp_conn)
    assert success is True
    assert job_id is not None

    # Exact duplicate URL with trailing slash and whitespace
    job2 = {
        "title": "Different Title Same URL",
        "platform": "Upwork",
        "url": " https://upwork.com/jobs/sample123/ ",
        "budget": 5000
    }
    is_dup, reason = is_duplicate_job(temp_conn, job2["title"], job2["platform"], job2["url"])
    assert is_dup is True
    assert "Matching URL" in reason

    success2, _, msg2 = add_job(job2, conn=temp_conn)
    assert success2 is False
    assert "Duplicate detected" in msg2

def test_duplicate_detection_by_normalized_title(temp_conn):
    job1 = {
        "title": "Excel MIS Dashboard Automation",
        "platform": "Freelancer",
        "url": "https://freelancer.com/projects/mis-01",
        "budget": 8000
    }
    success, _, _ = add_job(job1, conn=temp_conn)
    assert success is True

    # Same platform, similar wording that normalizes identically
    job2 = {
        "title": "Need Excel MIS Dashboard Automation urgently!",
        "platform": "Freelancer",
        "url": "https://freelancer.com/projects/different-url",
        "budget": 8000
    }
    is_dup, reason = is_duplicate_job(temp_conn, job2["title"], job2["platform"], job2["url"])
    assert is_dup is True
    assert "Matching Title" in reason
