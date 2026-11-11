import pytest
from pathlib import Path
from src.db import init_db, get_connection
import src.earnings_tracker as et

@pytest.fixture
def override_db(tmp_path: Path, monkeypatch):
    db_file = tmp_path / "test_earnings.db"
    init_db(db_file)
    monkeypatch.setattr(et, "get_connection", lambda: get_connection(db_file))
    return db_file

def test_earnings_and_targets(override_db):
    # Add received earnings
    et.add_earning(
        project_name="Sales MIS Report",
        gross_amount=6000.0,
        platform_fee=600.0,
        date_received="2026-11-05",
        status="received"
    )
    # Add another received earning
    et.add_earning(
        project_name="Excel Formula Optimization",
        gross_amount=5000.0,
        platform_fee=0.0,
        date_received="2026-11-10",
        status="received"
    )
    # Add expected earning
    et.add_earning(
        project_name="VBA Pipeline",
        gross_amount=4000.0,
        platform_fee=400.0,
        date_received="2026-11-20",
        status="expected"
    )

    summary = et.get_monthly_summary(target_month="2026-11")

    # Net received: (6000 - 600) + 5000 = 5400 + 5000 = 10400
    assert summary["total_net"] == 10400.0
    assert summary["total_fees"] == 600.0
    # Expected net: 4000 - 400 = 3600
    assert summary["expected_net"] == 3600.0

    # Target checks (target min = 10,000, target max = 20,000)
    assert summary["target_min_reached"] is True
    assert summary["progress_min_pct"] == 100.0
    assert summary["target_max_reached"] is False
    assert summary["gap_to_max"] == 20000.0 - 10400.0
