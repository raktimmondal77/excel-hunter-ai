"""
EXCEL HUNTER AI — Automation Runner (Stage 3)
Designed for manual execution and Windows Task Scheduler automated runs.

Scans 5 live sources (Freelancer API + 4 free public remote-job feeds),
filters non-Excel junk, converts budgets to INR, scores every opportunity,
and prints the best fresh leads at the end.
"""
import sys
import os
from pathlib import Path

# Ensure root directory is on Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.db import init_db
from src.discovery.engine import DiscoveryEngine

def main():
    print("=" * 60)
    print("🎯 EXCEL HUNTER AI — JOB DISCOVERY RUNNER (Stage 3)")
    print("Zero-Cost Windows Automation Worker")
    print("=" * 60)

    # Initialize tables and safe migrations
    init_db()

    print("[1/2] Initializing source adapters...")
    engine = DiscoveryEngine()
    print(f"      Active adapters: {len([a for a in engine.adapters if a.is_enabled])}")
    for a in engine.adapters:
        if a.is_enabled:
            print(f"        • {a.source_name}")

    print("\n[2/2] Scanning for Excel freelance opportunities...")
    result = engine.run_discovery_scan(max_per_source=20)

    print("\n" + "-" * 60)
    print(f"Scan Completed: {result['timestamp']}")
    print(f"Status:         {result['status'].upper()}")
    print(f"New Imported:   {result['jobs_imported']}")
    print(f"Duplicates:     {result['duplicates_skipped']} skipped")
    print(f"Junk Filtered:  {result['irrelevant_skipped']} non-Excel postings rejected")
    print(f"Issues/Errors:  {result['errors_count']}")
    print("-" * 60)

    # Per-source breakdown
    print("\nPer-source results:")
    for name, s in result.get("per_source", {}).items():
        print(
            f"  • {name}: found {s['found']} | imported {s['imported']} | "
            f"junk filtered {s['irrelevant']} | duplicates {s['duplicates']} | errors {s['errors']}"
        )

    # Top fresh opportunities from this run
    new_jobs = result.get("new_jobs", [])
    if new_jobs:
        print("\n⭐ Top fresh opportunities from this scan:")
        # Fetch scores for the new jobs
        try:
            import sqlite3
            from src.db import get_connection
            from src.config import DB_PATH
            conn = get_connection()
            ids = [j["job_id"] for j in new_jobs]
            placeholders = ",".join("?" * len(ids))
            rows = conn.execute(
                f"SELECT id, title, score, priority, budget, url FROM jobs WHERE id IN ({placeholders})",
                ids
            ).fetchall()
            conn.close()
            scored = sorted(rows, key=lambda r: -(r["score"] or 0))[:5]
            for r in scored:
                budget_str = f"₹{r['budget']:,.0f}" if (r["budget"] or 0) > 0 else "budget TBD"
                print(f"  [{r['score']}/100 | {r['priority']}] {r['title'][:60]} ({budget_str})")
                print(f"      {r['url']}")
        except Exception:
            for j in new_jobs[:5]:
                print(f"  • {j['title'][:70]} ({j['platform']})")

    if result["error_logs"]:
        print("\nWarnings / Logged Notices:")
        for log in result["error_logs"]:
            print(f"  • {log}")

    print("\n✅ Run finished successfully. Records saved to local SQLite database.")

if __name__ == "__main__":
    main()
