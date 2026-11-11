import pytest
from pathlib import Path
from src.db import init_db, get_connection
import src.fiverr_manager as fm
import src.job_manager as jm

@pytest.fixture
def override_db(tmp_path: Path, monkeypatch):
    db_file = tmp_path / "test_fiverr.db"
    init_db(db_file)
    monkeypatch.setattr(fm, "get_connection", lambda: get_connection(db_file))
    monkeypatch.setattr(jm, "get_connection", lambda: get_connection(db_file))
    return db_file

def test_fiverr_gigs_crud(override_db):
    fm.seed_default_fiverr_gigs()
    df = fm.get_fiverr_gigs()
    assert len(df) >= 3
    assert "Excel Dashboard" in df.iloc[0]["gig_title"]

    # Add custom gig
    new_gid = fm.add_fiverr_gig(
        gig_title="Financial Model & Working Capital Forecasting",
        gig_url="https://fiverr.com/s/finance-model",
        target_keywords="Financial model, DCF, Balance sheet, Cash flow",
        status="Active",
        notes="High ticket service"
    )
    assert new_gid is not None

    # Update gig
    up_ok = fm.update_fiverr_gig(
        gig_id=new_gid,
        gig_title="Financial Model & Valuation Forecast",
        gig_url="https://fiverr.com/s/finance-model-v2",
        target_keywords="Financial model, Valuation",
        status="Active",
        notes="Updated pricing"
    )
    assert up_ok is True

def test_add_fiverr_buyer_request(override_db):
    success, j_id, msg = fm.add_fiverr_buyer_request(
        title="Custom Excel Quoting Template with VBA",
        description="Need a quoting workbook that exports PDF invoices automatically.",
        budget=4500.0,
        buyer_info="Fiverr US Buyer, Level 2",
        request_url="https://fiverr.com/buyer/req/123"
    )
    assert success is True
    assert j_id is not None

    df = jm.get_jobs()
    job = df[df["id"] == j_id].iloc[0]
    assert job["platform"] == "Fiverr"
    assert job["discovery_source"] == "fiverr_manual_request"
    assert job["budget"] == 4500.0
