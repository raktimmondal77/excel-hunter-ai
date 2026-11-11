import sqlite3
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from src.db import get_connection
from src.job_manager import update_job_status

APPLICATION_STATUSES = [
    "applied",
    "replied",
    "interview",
    "won",
    "lost"
]

def record_application(
    job_id: int,
    platform: str,
    proposal_text: str,
    bid_amount: float,
    currency: str = "INR",
    job_url: Optional[str] = None,
    applied_date: Optional[str] = None,
    follow_up_date: Optional[str] = None,
    follow_up_notes: str = ""
) -> Tuple[bool, Optional[int], str]:
    """
    Records an application submission.
    Updates the parent job status to 'applied' and logs the application.
    """
    if not applied_date:
        applied_date = datetime.now().strftime("%Y-%m-%d")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO applications (
                job_id, platform, job_url, proposal_text,
                bid_amount, currency, applied_date, status,
                follow_up_date, follow_up_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'applied', ?, ?)
        """, (
            job_id, platform, job_url, proposal_text,
            float(bid_amount), currency, applied_date,
            follow_up_date, follow_up_notes
        ))
        conn.commit()
        app_id = cursor.lastrowid

        # Update parent job status to 'applied'
        update_job_status(job_id, "applied", f"Proposal submitted on {applied_date} via {platform}")

        return True, app_id, "Application successfully logged."
    except Exception as e:
        return False, None, f"Failed to record application: {str(e)}"
    finally:
        conn.close()

def update_application_status(
    application_id: int,
    new_status: str,
    follow_up_date: Optional[str] = None,
    follow_up_notes: Optional[str] = None
) -> bool:
    """Updates the status and follow-up details of an existing application."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT job_id FROM applications WHERE id = ?", (application_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False

    job_id = row["job_id"]

    cursor.execute("""
        UPDATE applications
        SET status = ?,
            follow_up_date = COALESCE(?, follow_up_date),
            follow_up_notes = COALESCE(?, follow_up_notes),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (new_status, follow_up_date, follow_up_notes, application_id))
    conn.commit()
    rows = cursor.rowcount

    # Sync corresponding job status
    if new_status in ["replied", "interview", "won", "lost"]:
        update_job_status(job_id, new_status, f"Status updated to {new_status}")

    conn.close()
    return rows > 0

def get_applications(
    platform: Optional[str] = None,
    status: Optional[str] = None
) -> pd.DataFrame:
    """Fetches application records with parent job details."""
    conn = get_connection()
    query = """
        SELECT
            a.id AS app_id,
            a.job_id,
            j.title AS job_title,
            a.platform,
            a.job_url,
            a.bid_amount,
            a.currency,
            a.applied_date,
            a.status,
            a.follow_up_date,
            a.follow_up_notes,
            a.proposal_text,
            a.created_at
        FROM applications a
        LEFT JOIN jobs j ON a.job_id = j.id
        WHERE 1=1
    """
    params: List[Any] = []

    if platform and platform != "All":
        query += " AND a.platform = ?"
        params.append(platform)

    if status and status != "All":
        query += " AND a.status = ?"
        params.append(status)

    query += " ORDER BY a.applied_date DESC, a.id DESC"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_follow_ups_due(current_date: Optional[str] = None) -> pd.DataFrame:
    """Returns applications with follow-ups due today or overdue, excluding won/lost contracts."""
    if not current_date:
        current_date = datetime.now().strftime("%Y-%m-%d")

    conn = get_connection()
    query = """
        SELECT
            a.id AS app_id,
            a.job_id,
            j.title AS job_title,
            a.platform,
            a.bid_amount,
            a.applied_date,
            a.status,
            a.follow_up_date,
            a.follow_up_notes
        FROM applications a
        LEFT JOIN jobs j ON a.job_id = j.id
        WHERE a.follow_up_date IS NOT NULL
          AND a.follow_up_date != ''
          AND a.follow_up_date <= ?
          AND a.status NOT IN ('won', 'lost')
        ORDER BY a.follow_up_date ASC
    """
    df = pd.read_sql_query(query, conn, params=(current_date,))
    conn.close()
    return df

def get_pipeline_kpis() -> Dict[str, int]:
    """Returns aggregated pipeline counts for the dashboard overview."""
    conn = get_connection()
    cursor = conn.cursor()

    # Jobs awaiting application (shortlisted)
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'shortlisted'")
    awaiting_apps = cursor.fetchone()[0]

    # Proposals ready for review
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'proposal_drafted'")
    proposals_drafted = cursor.fetchone()[0]

    # Applications submitted
    cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'applied'")
    apps_submitted = cursor.fetchone()[0]

    # Client replies
    cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'replied'")
    replies_count = cursor.fetchone()[0]

    # Interviews active
    cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'interview'")
    interviews_count = cursor.fetchone()[0]

    # Won projects
    cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'won'")
    won_count = cursor.fetchone()[0]

    # Follow-ups due
    today_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT COUNT(*) FROM applications
        WHERE follow_up_date IS NOT NULL
          AND follow_up_date != ''
          AND follow_up_date <= ?
          AND status NOT IN ('won', 'lost')
    """, (today_str,))
    follow_ups_due = cursor.fetchone()[0]

    conn.close()

    return {
        "awaiting_apps": awaiting_apps,
        "proposals_drafted": proposals_drafted,
        "apps_submitted": apps_submitted,
        "replies_count": replies_count,
        "interviews_count": interviews_count,
        "won_count": won_count,
        "follow_ups_due": follow_ups_due
    }
