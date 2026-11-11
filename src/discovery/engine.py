import json
import sqlite3
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.db import get_connection
from src.job_manager import add_job
from src.config import SEARCH_TERMS
from src.discovery.base_adapter import BaseSourceAdapter, StandardJob
from src.discovery.freelancer_adapter import FreelancerAdapter
from src.discovery.public_feed_adapter import PublicFeedAdapter
from src.discovery.upwork_adapter import UpworkManualAdapter

class DiscoveryEngine:
    """
    Central Job Discovery Coordinator.
    Coordinates source adapters, fault tolerance, deduplication, and persistence.
    """

    def __init__(self, adapters: Optional[List[BaseSourceAdapter]] = None):
        if adapters is not None:
            self.adapters = adapters
        else:
            self.adapters = [
                FreelancerAdapter(),
                PublicFeedAdapter(),
                UpworkManualAdapter()
            ]

    def run_discovery_scan(
        self,
        search_terms: Optional[List[str]] = None,
        max_per_source: int = 10
    ) -> Dict[str, Any]:
        """
        Executes a discovery scan across all enabled sources.
        Fault-tolerant: error in one source does not crash others.
        Saves progress after each source.
        """
        terms = search_terms or SEARCH_TERMS[:4]
        scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        total_imported = 0
        total_duplicates = 0
        total_errors = 0
        sources_scanned: List[str] = []
        error_logs: List[str] = []

        conn = get_connection()

        for adapter in self.adapters:
            if not adapter.is_enabled:
                continue

            sources_scanned.append(adapter.source_name)
            try:
                found_jobs = adapter.fetch_jobs(terms, max_results=max_per_source)
                for job in found_jobs:
                    job_dict = job.to_dict()
                    success, _, msg = add_job(job_dict, conn=conn, auto_evaluate=True)
                    if success:
                        total_imported += 1
                    else:
                        if "Duplicate" in (msg or ""):
                            total_duplicates += 1
                        else:
                            total_errors += 1
                            error_logs.append(f"[{adapter.source_name}] {msg}")
            except Exception as e:
                total_errors += 1
                error_logs.append(f"[{adapter.source_name}] Scan exception: {str(e)}")

        # Log scan summary to discovery_runs table
        cursor = conn.cursor()
        summary_text = f"Imported {total_imported} new jobs; skipped {total_duplicates} duplicates; logged {total_errors} issues."
        status = "completed" if total_errors == 0 else "completed_with_warnings"

        cursor.execute("""
            INSERT INTO discovery_runs (
                run_timestamp, sources_scanned, jobs_found,
                duplicates_skipped, errors_logged, status, summary_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            scan_time,
            ", ".join(sources_scanned),
            total_imported,
            total_duplicates,
            total_errors,
            status,
            summary_text
        ))
        conn.commit()
        run_id = cursor.lastrowid
        conn.close()

        return {
            "run_id": run_id,
            "timestamp": scan_time,
            "sources_scanned": sources_scanned,
            "jobs_imported": total_imported,
            "duplicates_skipped": total_duplicates,
            "errors_count": total_errors,
            "error_logs": error_logs,
            "status": status,
            "summary": summary_text
        }

def get_last_discovery_run() -> Optional[Dict[str, Any]]:
    """Returns the most recent discovery run log."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM discovery_runs ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)

def get_discovery_history(limit: int = 10) -> pd.DataFrame:
    """Returns recent discovery run history."""
    conn = get_connection()
    df = pd.read_sql_query(
        f"SELECT * FROM discovery_runs ORDER BY id DESC LIMIT {limit}",
        conn
    )
    conn.close()
    return df
