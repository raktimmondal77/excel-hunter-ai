import sqlite3
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, List
from src.db import get_connection
from src.config import TARGET_MIN_INR, TARGET_MAX_INR

def add_earning(
    project_name: str,
    gross_amount: float,
    platform_fee: float = 0.0,
    platform: str = "Direct Client",
    date_received: Optional[str] = None,
    currency: str = "INR",
    job_id: Optional[int] = None,
    status: str = "received",
    is_sample: int = 0,
    notes: str = ""
) -> int:
    """Records an earnings entry."""
    if not date_received:
        date_received = datetime.now().strftime("%Y-%m-%d")

    net_amount = float(gross_amount) - float(platform_fee)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO earnings (
            job_id, project_name, platform, date_received,
            gross_amount, platform_fee, net_amount, currency,
            status, is_sample, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_id, project_name, platform, date_received,
        gross_amount, platform_fee, net_amount, currency,
        status, is_sample, notes
    ))
    conn.commit()
    earning_id = cursor.lastrowid
    conn.close()
    return earning_id

def update_earning(
    earning_id: int,
    project_name: str,
    gross_amount: float,
    platform_fee: float = 0.0,
    platform: str = "Direct Client",
    date_received: Optional[str] = None,
    status: str = "received",
    notes: str = ""
) -> bool:
    """Updates an existing earnings record."""
    net_amount = float(gross_amount) - float(platform_fee)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE earnings
        SET project_name = ?,
            gross_amount = ?,
            platform_fee = ?,
            net_amount = ?,
            platform = ?,
            date_received = COALESCE(?, date_received),
            status = ?,
            notes = ?
        WHERE id = ?
    """, (
        project_name, gross_amount, platform_fee, net_amount,
        platform, date_received, status, notes, earning_id
    ))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0

def delete_earning(earning_id: int) -> bool:
    """Deletes an earning record by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM earnings WHERE id = ?", (earning_id,))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0

def get_earnings(include_samples: bool = True) -> pd.DataFrame:
    """Returns all earnings records."""
    conn = get_connection()
    query = "SELECT * FROM earnings WHERE 1=1"
    if not include_samples:
        query += " AND is_sample = 0"
    query += " ORDER BY date_received DESC, id DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_monthly_summary(target_month: Optional[str] = None, include_samples: bool = True) -> Dict[str, Any]:
    """
    Computes earnings metrics for a specified month (format 'YYYY-MM') or the current month.
    Includes target comparison against ₹10,000 and ₹20,000.
    """
    if not target_month:
        target_month = datetime.now().strftime("%Y-%m")

    conn = get_connection()
    query = """
        SELECT
            COALESCE(SUM(CASE WHEN status = 'received' THEN gross_amount ELSE 0 END), 0) AS total_gross,
            COALESCE(SUM(CASE WHEN status = 'received' THEN platform_fee ELSE 0 END), 0) AS total_fees,
            COALESCE(SUM(CASE WHEN status = 'received' THEN net_amount ELSE 0 END), 0) AS total_net,
            COALESCE(SUM(CASE WHEN status = 'expected' THEN net_amount ELSE 0 END), 0) AS expected_net,
            COUNT(*) AS total_entries
        FROM earnings
        WHERE date_received LIKE ?
    """
    if not include_samples:
        query += " AND is_sample = 0"

    cursor = conn.cursor()
    cursor.execute(query, (f"{target_month}%",))
    row = cursor.fetchone()
    conn.close()

    total_gross = float(row["total_gross"] or 0)
    total_fees = float(row["total_fees"] or 0)
    total_net = float(row["total_net"] or 0)
    expected_net = float(row["expected_net"] or 0)
    total_entries = int(row["total_entries"] or 0)

    progress_min = min(round((total_net / TARGET_MIN_INR) * 100, 1), 100.0) if TARGET_MIN_INR > 0 else 0.0
    progress_max = min(round((total_net / TARGET_MAX_INR) * 100, 1), 100.0) if TARGET_MAX_INR > 0 else 0.0

    return {
        "month": target_month,
        "total_gross": total_gross,
        "total_fees": total_fees,
        "total_net": total_net,
        "expected_net": expected_net,
        "entries_count": total_entries,
        "target_min": TARGET_MIN_INR,
        "target_max": TARGET_MAX_INR,
        "progress_min_pct": progress_min,
        "progress_max_pct": progress_max,
        "target_min_reached": total_net >= TARGET_MIN_INR,
        "target_max_reached": total_net >= TARGET_MAX_INR,
        "gap_to_min": max(TARGET_MIN_INR - total_net, 0.0),
        "gap_to_max": max(TARGET_MAX_INR - total_net, 0.0),
    }

def get_performance_analytics(include_samples: bool = True) -> Dict[str, Any]:
    """
    Computes Stage 3 comprehensive performance analytics integrating
    the application pipeline and actual realized earnings.
    Strictly keeps project value, completed revenue, and money actually received separate.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Application Pipeline Counts
    cursor.execute("SELECT COUNT(*) FROM applications")
    total_applications = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM applications
        WHERE status IN ('Submitted', 'applied', 'Client Replied', 'Interview', 'Negotiation', 'Awarded', 'Completed', 'Rejected')
    """)
    proposals_submitted = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM applications
        WHERE status IN ('Client Replied', 'Interview', 'Negotiation', 'Awarded', 'Completed')
    """)
    client_replies = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM applications
        WHERE status IN ('Interview')
    """)
    interviews_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM applications
        WHERE status IN ('Awarded', 'Completed', 'won')
    """)
    projects_awarded = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM applications
        WHERE status IN ('Completed')
    """)
    projects_completed = cursor.fetchone()[0]

    # Total Project Value (Contract value of awarded/completed projects)
    cursor.execute("""
        SELECT COALESCE(SUM(COALESCE(proposed_amount, bid_amount)), 0)
        FROM applications
        WHERE status IN ('Awarded', 'Completed', 'won')
    """)
    total_project_value = float(cursor.fetchone()[0] or 0.0)

    # 2. Realized Earnings (Money actually received)
    earnings_query = """
        SELECT
            COALESCE(SUM(CASE WHEN status = 'received' THEN net_amount ELSE 0 END), 0) AS amount_received,
            COALESCE(SUM(CASE WHEN status = 'expected' THEN net_amount ELSE 0 END), 0) AS expected_earnings
        FROM earnings
        WHERE 1=1
    """
    if not include_samples:
        earnings_query += " AND is_sample = 0"

    cursor.execute(earnings_query)
    e_row = cursor.fetchone()
    amount_received = float(e_row["amount_received"] or 0.0)
    expected_earnings = float(e_row["expected_earnings"] or 0.0)

    # Outstanding payments = project value - amount received
    outstanding_payments = max(0.0, total_project_value - amount_received)

    # Conversion Rates
    success_rate = round((projects_awarded / proposals_submitted * 100), 1) if proposals_submitted > 0 else 0.0
    reply_rate = round((client_replies / proposals_submitted * 100), 1) if proposals_submitted > 0 else 0.0

    # 3. Distributions
    apps_df = pd.read_sql_query("SELECT status, platform, COALESCE(proposed_amount, bid_amount) as amount FROM applications", conn)
    
    earn_query = "SELECT platform, net_amount, date_received FROM earnings WHERE 1=1"
    if not include_samples:
        earn_query += " AND is_sample = 0"
    earn_df = pd.read_sql_query(earn_query, conn)

    conn.close()

    status_dist = apps_df["status"].value_counts().to_dict() if not apps_df.empty else {}
    platform_apps_dist = apps_df["platform"].value_counts().to_dict() if not apps_df.empty else {}
    platform_earn_dist = earn_df.groupby("platform")["net_amount"].sum().to_dict() if not earn_df.empty else {}

    return {
        "total_applications": total_applications,
        "proposals_submitted": proposals_submitted,
        "client_replies": client_replies,
        "interviews_count": interviews_count,
        "projects_awarded": projects_awarded,
        "projects_completed": projects_completed,
        "total_project_value": total_project_value,
        "amount_received": amount_received,
        "outstanding_payments": outstanding_payments,
        "expected_earnings": expected_earnings,
        "success_rate_pct": success_rate,
        "reply_rate_pct": reply_rate,
        "status_distribution": status_dist,
        "platform_apps_distribution": platform_apps_dist,
        "platform_earnings_distribution": platform_earn_dist
    }
