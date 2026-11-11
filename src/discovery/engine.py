import sqlite3
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.db import get_connection
from src.job_manager import add_job
from src.config import SEARCH_TERMS
from src.evaluation import is_excel_job
from src.discovery.base_adapter import BaseSourceAdapter, StandardJob
from src.discovery.freelancer_adapter import FreelancerAdapter
from src.discovery.public_feed_adapter import PublicFeedAdapter
from src.discovery.remoteok_adapter import RemoteOkAdapter
from src.discovery.jobicy_adapter import JobicyAdapter
from src.discovery.workingnomads_adapter import WorkingNomadsAdapter
from src.discovery.upwork_adapter import UpworkManualAdapter


class DiscoveryEngine:
    """
    Central Job Discovery Coordinator — Stage 3.

    Coordinates 6 source adapters with fault tolerance:
      1. Freelancer.com (Official API, fresh + relevance filtered)
      2. Remotive (public remote-jobs API)
      3. RemoteOK (public remote-jobs API)          [NEW in Stage 3]
      4. Jobicy (public remote-jobs API)            [NEW in Stage 3]
      5. Working Nomads (public jobs API)           [NEW in Stage 3]
      6. Upwork (compliant manual ingestion only)

    Engine-level guarantees:
      - STRICT relevance gate: any non-Excel posting is skipped and counted
        (never imported, never scored as if it were relevant).
      - Per-source statistics returned for transparent scan reports.
      - Every imported job is returned in `new_jobs` so the UI/CLI can
        immediately show what a scan found.
    """

    def __init__(self, adapters: Optional[List[BaseSourceAdapter]] = None):
        if adapters is not None:
            self.adapters = adapters
        else:
            self.adapters = [
                FreelancerAdapter(),
                PublicFeedAdapter(),
                RemoteOkAdapter(),
                JobicyAdapter(),
                WorkingNomadsAdapter(),
                UpworkManualAdapter()
            ]

    def run_discovery_scan(
        self,
        search_terms: Optional[List[str]] = None,
        max_per_source: int = 20
    ) -> Dict[str, Any]:
        """
        Executes a discovery scan across all enabled sources.
        Fault-tolerant: an error in one source never crashes the others.
        """
        terms = search_terms or SEARCH_TERMS[:4]
        scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        total_imported = 0
        total_duplicates = 0
        total_errors = 0
        total_irrelevant = 0
        sources_scanned: List[str] = []
        error_logs: List[str] = []
        new_jobs: List[Dict[str, Any]] = []
        per_source: Dict[str, Dict[str, int]] = {}

        conn = get_connection()

        for adapter in self.adapters:
            if not adapter.is_enabled:
                continue

            sources_scanned.append(adapter.source_name)
            stats = {"found": 0, "imported": 0, "duplicates": 0, "irrelevant": 0, "errors": 0}

            try:
                found_jobs = adapter.fetch_jobs(terms, max_results=max_per_source)

                # Junk the adapter itself rejected (relevance / engagement filters)
                adapter_filtered = int(getattr(adapter, "filtered_count", 0) or 0)
                stats["found"] = len(found_jobs) + adapter_filtered  # raw candidates seen
                stats["irrelevant"] += adapter_filtered
                total_irrelevant += adapter_filtered

                for job in found_jobs:
                    job_dict = job.to_dict()

                    # ---- Engine-level STRICT relevance gate ----
                    # Adapters already filter, but the engine double-checks so
                    # junk can never reach the repository, even from a new
                    # or custom adapter.
                    if not is_excel_job(job_dict.get("title", ""), job_dict.get("description", "")):
                        stats["irrelevant"] += 1
                        total_irrelevant += 1
                        continue

                    success, job_id, msg = add_job(job_dict, conn=conn, auto_evaluate=True)
                    if success:
                        total_imported += 1
                        stats["imported"] += 1
                        new_jobs.append({
                            "job_id": job_id,
                            "title": job_dict.get("title", ""),
                            "platform": job_dict.get("platform", ""),
                            "budget": job_dict.get("budget", 0.0),
                            "url": job_dict.get("url", "")
                        })
                    else:
                        if "Duplicate" in (msg or ""):
                            total_duplicates += 1
                            stats["duplicates"] += 1
                        else:
                            total_errors += 1
                            stats["errors"] += 1
                            error_logs.append(f"[{adapter.source_name}] {msg}")
            except Exception as e:
                total_errors += 1
                stats["errors"] += 1
                error_logs.append(f"[{adapter.source_name}] Scan exception: {str(e)}")

            per_source[adapter.source_name] = stats

        # Log scan summary to discovery_runs table
        cursor = conn.cursor()
        summary_text = (
            f"Imported {total_imported} new jobs; skipped {total_duplicates} duplicates; "
            f"filtered {total_irrelevant} non-Excel postings; logged {total_errors} issues."
        )
        status = "completed" if total_errors == 0 else "completed_with_warnings"

        cursor.execute("""
            INSERT INTO discovery_runs (
                run_timestamp, sources_scanned, jobs_found,
                duplicates_skipped, errors_logged, status, summary_notes, irrelevant_skipped
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            scan_time,
            ", ".join(sources_scanned),
            total_imported,
            total_duplicates,
            total_errors,
            status,
            summary_text,
            total_irrelevant
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
            "irrelevant_skipped": total_irrelevant,
            "errors_count": total_errors,
            "error_logs": error_logs,
            "status": status,
            "summary": summary_text,
            "per_source": per_source,
            "new_jobs": new_jobs
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
