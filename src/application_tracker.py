import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from src.db import get_connection
from src.job_manager import update_job_status

APPLICATION_STATUSES = [
    "Interested",
    "Under Review",
    "Proposal Drafted",
    "Ready for Submission",
    "Submitted",
    "Client Replied",
    "Interview",
    "Negotiation",
    "Awarded",
    "Rejected",
    "Withdrawn",
    "No Response",
    "Completed"
]

# Legacy status mapping for backwards compatibility
LEGACY_STATUS_MAP = {
    "applied": "Submitted",
    "replied": "Client Replied",
    "interview": "Interview",
    "won": "Awarded",
    "lost": "Rejected"
}

def normalize_status(status: str) -> str:
    """Normalizes status strings to standard Stage 3 title-case."""
    s = (status or "Submitted").strip().lower()
    for std in APPLICATION_STATUSES:
        if std.lower() == s:
            return std
    return LEGACY_STATUS_MAP.get(s, "Submitted")

def record_application(
    job_id: int,
    platform: str,
    proposal_text: str,
    bid_amount: float,
    currency: str = "INR",
    job_url: Optional[str] = None,
    applied_date: Optional[str] = None,
    follow_up_date: Optional[str] = None,
    follow_up_notes: str = "",
    project_title: Optional[str] = None,
    client_name: Optional[str] = None,
    status: str = "Submitted",
    date_prepared: Optional[str] = None,
    client_response: Optional[str] = None,
    interview_date: Optional[str] = None,
    final_outcome: Optional[str] = None,
    notes: Optional[str] = None
) -> Tuple[bool, Optional[int], str]:
    """
    Records an application submission with strict duplicate prevention per platform.
    Never automatically submits applications without human confirmation.
    """
    clean_status = normalize_status(status)
    today_str = datetime.now().strftime("%Y-%m-%d")

    if not applied_date:
        applied_date = today_str
    if not date_prepared:
        date_prepared = today_str

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 1. Duplicate Application Prevention (Same job + same platform)
        cursor.execute(
            "SELECT id FROM applications WHERE job_id = ? AND LOWER(platform) = LOWER(?)",
            (job_id, platform.strip())
        )
        existing = cursor.fetchone()
        if existing:
            return False, None, f"An application for this project on {platform} already exists (Application #{existing['id']})."

        # Lookup project title and client name from jobs table if not provided
        if not project_title or not client_name:
            cursor.execute("SELECT title, client_info, url FROM jobs WHERE id = ?", (job_id,))
            j_row = cursor.fetchone()
            if j_row:
                project_title = project_title or j_row["title"]
                client_name = client_name or j_row["client_info"]
                job_url = job_url or j_row["url"]

        effective_notes = notes or follow_up_notes
        effective_followup = follow_up_date

        cursor.execute("""
            INSERT INTO applications (
                job_id, platform, job_url, proposal_text,
                bid_amount, currency, applied_date, status,
                follow_up_date, follow_up_notes,
                project_title, client_name, proposed_amount,
                date_prepared, date_submitted, next_follow_up_date,
                client_response, interview_date, final_outcome, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id, platform.strip(), job_url, proposal_text,
            float(bid_amount), currency, applied_date, clean_status,
            effective_followup, effective_notes,
            project_title, client_name, float(bid_amount),
            date_prepared, applied_date, effective_followup,
            client_response, interview_date, final_outcome, effective_notes
        ))
        conn.commit()
        app_id = cursor.lastrowid

        # Sync parent job status
        job_status = "applied"
        if clean_status in ["Awarded", "Completed"]:
            job_status = "won"
        elif clean_status == "Rejected":
            job_status = "lost"
        update_job_status(job_id, job_status, f"Application #{app_id} ({clean_status}) recorded on {platform}")

        return True, app_id, "Application successfully logged."
    except Exception as e:
        return False, None, f"Failed to record application: {str(e)}"
    finally:
        conn.close()

def update_application_status(
    application_id: int,
    new_status: str,
    follow_up_date: Optional[str] = None,
    follow_up_notes: Optional[str] = None,
    client_response: Optional[str] = None,
    interview_date: Optional[str] = None,
    final_outcome: Optional[str] = None
) -> bool:
    """Updates the status and follow-up details of an existing application."""
    clean_status = normalize_status(new_status)
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
            next_follow_up_date = COALESCE(?, next_follow_up_date, follow_up_date),
            follow_up_notes = COALESCE(?, follow_up_notes),
            notes = COALESCE(?, notes, follow_up_notes),
            client_response = COALESCE(?, client_response),
            interview_date = COALESCE(?, interview_date),
            final_outcome = COALESCE(?, final_outcome),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        clean_status,
        follow_up_date, follow_up_date,
        follow_up_notes, follow_up_notes,
        client_response, interview_date, final_outcome,
        application_id
    ))
    conn.commit()
    rows = cursor.rowcount

    # Sync corresponding job status
    if clean_status in ["Awarded", "Completed"]:
        update_job_status(job_id, "won", f"Contract awarded: status updated to {clean_status}")
    elif clean_status == "Rejected":
        update_job_status(job_id, "lost", "Application rejected")
    elif clean_status in ["Client Replied", "Interview", "Negotiation"]:
        update_job_status(job_id, "replied", f"Client activity: {clean_status}")

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
            COALESCE(a.project_title, j.title) AS job_title,
            a.platform,
            COALESCE(a.job_url, j.url) AS job_url,
            COALESCE(a.client_name, j.client_info) AS client_name,
            COALESCE(a.proposed_amount, a.bid_amount) AS bid_amount,
            a.currency,
            COALESCE(a.date_submitted, a.applied_date) AS applied_date,
            a.status,
            COALESCE(a.next_follow_up_date, a.follow_up_date) AS follow_up_date,
            COALESCE(a.notes, a.follow_up_notes) AS follow_up_notes,
            a.client_response,
            a.interview_date,
            a.final_outcome,
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
        # Match either exact or normalized
        clean_s = normalize_status(status)
        query += " AND (a.status = ? OR a.status = ?)"
        params.extend([status, clean_s])

    query += " ORDER BY a.id DESC"
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
            COALESCE(a.project_title, j.title) AS job_title,
            a.platform,
            COALESCE(a.client_name, j.client_info) AS client_name,
            COALESCE(a.proposed_amount, a.bid_amount) AS bid_amount,
            COALESCE(a.date_submitted, a.applied_date) AS applied_date,
            a.status,
            COALESCE(a.next_follow_up_date, a.follow_up_date) AS follow_up_date,
            COALESCE(a.notes, a.follow_up_notes) AS follow_up_notes,
            a.client_response
        FROM applications a
        LEFT JOIN jobs j ON a.job_id = j.id
        WHERE (a.next_follow_up_date IS NOT NULL AND a.next_follow_up_date != '' AND a.next_follow_up_date <= ?)
           OR (a.follow_up_date IS NOT NULL AND a.follow_up_date != '' AND a.follow_up_date <= ?)
          AND a.status NOT IN ('Awarded', 'Completed', 'Rejected', 'Withdrawn', 'won', 'lost')
        ORDER BY COALESCE(a.next_follow_up_date, a.follow_up_date) ASC
    """
    df = pd.read_sql_query(query, conn, params=(current_date, current_date))
    conn.close()
    return df

def get_follow_up_groups(current_date: Optional[str] = None) -> Dict[str, pd.DataFrame]:
    """
    Categorizes applications for the Follow-up Manager:
    - due_today: follow-up date == today
    - overdue: follow-up date < today
    - upcoming: follow-up date > today
    - no_response: submitted >= 3 days ago with no client reply
    """
    if not current_date:
        current_date = datetime.now().strftime("%Y-%m-%d")

    conn = get_connection()
    query = """
        SELECT
            a.id AS app_id,
            a.job_id,
            COALESCE(a.project_title, j.title) AS job_title,
            a.platform,
            COALESCE(a.client_name, j.client_info) AS client_name,
            COALESCE(a.proposed_amount, a.bid_amount) AS bid_amount,
            a.currency,
            COALESCE(a.date_submitted, a.applied_date) AS applied_date,
            a.status,
            COALESCE(a.next_follow_up_date, a.follow_up_date) AS follow_up_date,
            COALESCE(a.notes, a.follow_up_notes) AS follow_up_notes,
            a.client_response,
            COALESCE(a.job_url, j.url) AS job_url
        FROM applications a
        LEFT JOIN jobs j ON a.job_id = j.id
        WHERE a.status NOT IN ('Awarded', 'Completed', 'Rejected', 'Withdrawn', 'won', 'lost')
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        empty_df = pd.DataFrame(columns=[
            "app_id", "job_id", "job_title", "platform", "client_name",
            "bid_amount", "currency", "applied_date", "status",
            "follow_up_date", "follow_up_notes", "client_response", "job_url"
        ])
        return {"due_today": empty_df, "overdue": empty_df, "upcoming": empty_df, "no_response": empty_df}

    df["follow_up_date"] = df["follow_up_date"].fillna("")
    df["applied_date"] = df["applied_date"].fillna(current_date)

    due_today = df[df["follow_up_date"] == current_date]
    overdue = df[(df["follow_up_date"] != "") & (df["follow_up_date"] < current_date)]
    upcoming = df[(df["follow_up_date"] != "") & (df["follow_up_date"] > current_date)]

    # No response: status is Submitted/applied, submitted >= 3 days ago, and client_response is empty
    three_days_ago = (datetime.strptime(current_date, "%Y-%m-%d") - timedelta(days=3)).strftime("%Y-%m-%d")
    no_response = df[
        (df["status"].isin(["Submitted", "applied"])) &
        (df["applied_date"] <= three_days_ago) &
        (df["client_response"].isna() | (df["client_response"] == ""))
    ]

    return {
        "due_today": due_today,
        "overdue": overdue,
        "upcoming": upcoming,
        "no_response": no_response
    }

def generate_follow_up_message(
    project_title: str,
    client_name: Optional[str] = None,
    stage: int = 1,
    freelancer_name: str = "Excel Freelancer"
) -> str:
    """
    Generates polite, professional, and customizable follow-up messages.
    Never sent automatically.
    """
    c_name = client_name.strip() if client_name and client_name.strip().lower() not in ["there", "client", "unknown", ""] else ""
    greeting = f"Hi {c_name}," if c_name else "Hi there,"

    if stage == 1:
        # 3-4 days polite check-in
        return f"""{greeting}

I hope your week is going well. I am following up on the proposal I submitted for "{project_title}".

I wanted to check if you have had a chance to review candidates, or if you have any questions regarding my approach or timeline. I have sample workbook structures ready and would be glad to answer any questions or inspect your raw data layout.

Looking forward to hearing from you.

Best regards,
{freelancer_name}""".strip()
    else:
        # 6-8 days final polite touchpoint
        return f"""{greeting}

I hope you are doing well. Reaching out with a quick check-in regarding "{project_title}".

If this project is still open and you are finalizing details, I remain available to assist with your spreadsheet requirements and can deliver a clean turnaround. If you have already filled the position, no problem at all and I wish you success with the project.

Warm regards,
{freelancer_name}""".strip()

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
    cursor.execute("SELECT COUNT(*) FROM applications WHERE status IN ('Submitted', 'applied')")
    apps_submitted = cursor.fetchone()[0]

    # Client replies
    cursor.execute("SELECT COUNT(*) FROM applications WHERE status IN ('Client Replied', 'replied')")
    replies_count = cursor.fetchone()[0]

    # Interviews active
    cursor.execute("SELECT COUNT(*) FROM applications WHERE status IN ('Interview', 'interview')")
    interviews_count = cursor.fetchone()[0]

    # Won projects
    cursor.execute("SELECT COUNT(*) FROM applications WHERE status IN ('Awarded', 'Completed', 'won')")
    won_count = cursor.fetchone()[0]

    # Follow-ups due
    today_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT COUNT(*) FROM applications
        WHERE (next_follow_up_date IS NOT NULL AND next_follow_up_date != '' AND next_follow_up_date <= ?)
           OR (follow_up_date IS NOT NULL AND follow_up_date != '' AND follow_up_date <= ?)
          AND status NOT IN ('Awarded', 'Completed', 'Rejected', 'Withdrawn', 'won', 'lost')
    """, (today_str, today_str))
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
