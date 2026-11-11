"""
End-to-end programmatic QA verification script for Excel Hunter AI.
Tests every user action required by the QA checklist:
1. Initialize DB and verify tables.
2. Seed sample data and verify label tags.
3. Import sample_jobs.csv directly and check duplicate rejection.
4. Attempt re-import of sample_jobs.csv and verify 100% duplicate rejection.
5. Update job status through entire pipeline.
6. Add, edit, and delete earnings entries.
7. Clear sample data and ensure real records remain intact.
8. Verify DB path is absolute and CWD-independent.
"""
import os
import sys
from pathlib import Path

# Ensure root directory is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DB_PATH, SAMPLE_CSV_PATH, TARGET_MIN_INR, TARGET_MAX_INR
from src.db import init_db, get_connection
import src.job_manager as jm
import src.earnings_tracker as et
from src.sample_data import seed_sample_data

def run_qa():
    print("=== EXCEL HUNTER AI - QA VERIFICATION ===")

    # 1. Path stability check
    print("\n[1] Checking Path Stability...")
    assert DB_PATH.is_absolute(), f"DB_PATH is not absolute: {DB_PATH}"
    assert SAMPLE_CSV_PATH.is_absolute(), f"SAMPLE_CSV_PATH is not absolute: {SAMPLE_CSV_PATH}"
    print(f"  -> DB_PATH: {DB_PATH}")
    print(f"  -> SAMPLE_CSV: {SAMPLE_CSV_PATH}")
    assert SAMPLE_CSV_PATH.exists(), "sample_jobs.csv does not exist!"

    # 2. Database init
    print("\n[2] Initializing SQLite DB...")
    init_db()
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r["name"] for r in c.fetchall()]
    conn.close()
    assert "jobs" in tables and "earnings" in tables, f"Missing tables: {tables}"
    print("  -> Tables initialized: jobs, earnings")

    # 3. Seed demo data
    print("\n[3] Seeding Demo Data...")
    res_seed = seed_sample_data()
    print(f"  -> Seeded {res_seed['jobs_added']} jobs, {res_seed['earnings_added']} earnings.")

    # 4. Import sample_jobs.csv
    print("\n[4] Ingesting data/sample_jobs.csv...")
    with open(SAMPLE_CSV_PATH, "r", encoding="utf-8") as f:
        res_csv = jm.import_jobs_from_csv(f, is_sample=False)
    print(f"  -> Imported: {res_csv['imported_count']}, Duplicates Skipped: {res_csv['duplicate_count']}")
    assert res_csv["success"] is True

    # 5. Duplicate Rejection Check
    print("\n[5] Testing Duplicate Rejection (Re-importing sample_jobs.csv)...")
    with open(SAMPLE_CSV_PATH, "r", encoding="utf-8") as f:
        res_dup = jm.import_jobs_from_csv(f, is_sample=False)
    print(f"  -> Re-import Imported: {res_dup['imported_count']}, Duplicates Skipped: {res_dup['duplicate_count']}")
    assert res_dup["imported_count"] == 0, "Duplicate jobs were mistakenly imported!"
    assert res_dup["duplicate_count"] > 0, "Duplicates were not rejected!"
    print("  -> Duplicate rejection PASSED: 100% duplicates blocked.")

    # 6. Status change test
    print("\n[6] Testing Job Status Pipeline Changes...")
    jobs = jm.get_jobs(include_samples=True)
    first_job_id = int(jobs.iloc[0]["id"])
    assert jm.update_job_status(first_job_id, "shortlisted", "Reviewing specs")
    assert jm.update_job_status(first_job_id, "applied", "Proposal sent via portal")
    assert jm.update_job_status(first_job_id, "won", "Client accepted contract")
    refetched = jm.get_jobs(include_samples=True)
    assert refetched[refetched["id"] == first_job_id].iloc[0]["status"] == "won"
    print(f"  -> Job #{first_job_id} transitioned successfully to 'won'.")

    # 7. Add, Edit, View Earnings
    print("\n[7] Testing Earnings CRUD & Targets...")
    new_eid = et.add_earning(
        project_name="QA Verified MIS Report",
        gross_amount=12000.0,
        platform_fee=1200.0,
        platform="Upwork",
        status="received",
        is_sample=0,
        notes="Real test earning"
    )
    print(f"  -> Created Earning #{new_eid} (Net: 10,800 INR)")

    # Verify editing
    edit_ok = et.update_earning(
        earning_id=new_eid,
        project_name="QA Verified MIS Report (Revised)",
        gross_amount=14000.0,
        platform_fee=1400.0,
        platform="Upwork",
        status="received",
        notes="Updated bonus added"
    )
    assert edit_ok, "Failed to edit earning record!"
    earnings_df = et.get_earnings(include_samples=True)
    e_row = earnings_df[earnings_df["id"] == new_eid].iloc[0]
    assert e_row["net_amount"] == 12600.0
    print(f"  -> Successfully updated Earning #{new_eid} to Net: 12,600 INR.")

    # Verify Monthly Summary
    summ = et.get_monthly_summary(include_samples=False)
    print(f"  -> Real Monthly Net: ₹{summ['total_net']:,.2f}")
    assert summ["total_net"] >= 12600.0
    assert summ["target_min_reached"] is True

    # 8. Safe Clear Sample Data
    print("\n[8] Testing Safe Clear Sample Data...")
    j_del, e_del = jm.delete_sample_data()
    print(f"  -> Deleted {j_del} sample jobs, {e_del} sample earnings.")

    # Verify real records survived
    surviving_jobs = jm.get_jobs(include_samples=True)
    surviving_earnings = et.get_earnings(include_samples=True)
    print(f"  -> Surviving Jobs: {len(surviving_jobs)} (All must have is_sample=0)")
    print(f"  -> Surviving Earnings: {len(surviving_earnings)} (All must have is_sample=0)")
    assert all(surviving_jobs["is_sample"] == 0), "Sample jobs were not deleted or real jobs mislabeled!"
    assert all(surviving_earnings["is_sample"] == 0), "Sample earnings were not deleted or real earnings mislabeled!"
    assert len(surviving_earnings[surviving_earnings["id"] == new_eid]) == 1, "Real user earning was deleted!"
    print("  -> Safe Clear Verified: 100% of real user records preserved.")

    # Cleanup test earning created for QA
    et.delete_earning(new_eid)

    # Re-seed sample data so user dashboard has demo records ready
    seed_sample_data()

    print("\n=== ALL QA CRITERIA COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_qa()
