"""
EXCEL HUNTER AI — Automation Runner
Designed for manual execution and Windows Task Scheduler automated runs.
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
    print("🎯 EXCEL HUNTER AI — JOB DISCOVERY RUNNER")
    print("Zero-Cost Windows Automation Worker")
    print("=" * 60)

    # Initialize tables and safe migrations
    init_db()

    print("[1/2] Initializing source adapters...")
    engine = DiscoveryEngine()
    print(f"      Active adapters: {[a.source_name for a in engine.adapters if a.is_enabled]}")

    print("\n[2/2] Scanning for Excel freelance opportunities...")
    result = engine.run_discovery_scan()

    print("\n" + "-" * 60)
    print(f"Scan Completed: {result['timestamp']}")
    print(f"Status:         {result['status'].upper()}")
    print(f"New Imported:   {result['jobs_imported']}")
    print(f"Duplicates:     {result['duplicates_skipped']} skipped")
    print(f"Issues/Errors:  {result['errors_count']}")
    print(f"Summary:        {result['summary']}")
    print("-" * 60)

    if result["error_logs"]:
        print("\nWarnings / Logged Notices:")
        for log in result["error_logs"]:
            print(f"  • {log}")

    print("\n✅ Run finished successfully. Records saved to local SQLite database.")

if __name__ == "__main__":
    main()
