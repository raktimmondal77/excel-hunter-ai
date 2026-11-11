import pytest
from pathlib import Path
from src.db import init_db, get_connection
import src.job_manager as jm
import src.discovery.engine as de
from src.discovery.base_adapter import BaseSourceAdapter, StandardJob

class MockTestAdapter(BaseSourceAdapter):
    def __init__(self, source_id: str, jobs_to_return: list, should_fail: bool = False):
        super().__init__(source_id=source_id, source_name=f"Mock Adapter {source_id}")
        self.jobs_to_return = jobs_to_return
        self.should_fail = should_fail

    def test_connection(self):
        return {"status": "Connected", "healthy": True}

    def fetch_jobs(self, search_terms, max_results=10):
        if self.should_fail:
            raise ConnectionError("Mock network drop test")
        return self.jobs_to_return

@pytest.fixture
def override_db(tmp_path: Path, monkeypatch):
    db_file = tmp_path / "test_engine.db"
    init_db(db_file)
    monkeypatch.setattr(jm, "get_connection", lambda: get_connection(db_file))
    monkeypatch.setattr(de, "get_connection", lambda: get_connection(db_file))
    return db_file

def test_discovery_engine_fault_tolerance_and_logging(override_db):
    job1 = StandardJob(
        title="Mock Job 1 - Dashboard",
        description="Detailed dashboard description with formulas",
        platform="Freelancer.com",
        url="https://mock.com/job1",
        budget=6000.0
    )
    job2 = StandardJob(
        title="Mock Job 2 - MIS Report",
        description="Detailed MIS automation description",
        platform="Upwork",
        url="https://mock.com/job2",
        budget=8000.0
    )

    ad1 = MockTestAdapter("ad1", [job1], should_fail=False)
    ad2 = MockTestAdapter("ad2", [], should_fail=True) # Fails intentionally
    ad3 = MockTestAdapter("ad3", [job2], should_fail=False)

    engine = de.DiscoveryEngine(adapters=[ad1, ad2, ad3])
    res = engine.run_discovery_scan()

    # Fault tolerance check: ad2 threw exception, but ad1 and ad3 still succeeded!
    assert res["jobs_imported"] == 2
    assert res["errors_count"] == 1
    assert "completed_with_warnings" in res["status"]

    # Deduplication check: running again must skip both jobs
    res2 = engine.run_discovery_scan()
    assert res2["jobs_imported"] == 0
    assert res2["duplicates_skipped"] == 2

    # Verification of discovery_runs table
    last_run = de.get_last_discovery_run()
    assert last_run is not None
    assert last_run["duplicates_skipped"] == 2
    assert "Mock Adapter" in last_run["sources_scanned"]
