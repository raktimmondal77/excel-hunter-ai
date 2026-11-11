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
