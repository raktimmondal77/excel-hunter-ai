import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional
from src.db import get_connection
from src.job_manager import add_job

DEFAULT_FIVERR_GIGS = [
    {
        "gig_title": "Design Interactive Excel Dashboard & KPI Reporting System",
        "gig_url": "https://www.fiverr.com/s/excel-dashboard-gig",
        "target_keywords": "Excel dashboard, KPI summary, Pivot tables, Slicers, Visual charts",
        "status": "Active",
        "notes": "Core Gig. High conversion for business reporting and executive summaries."
    },
    {
        "gig_title": "Excel Formula Repair, XLOOKUP Optimization & Spreadsheet Audit",
        "gig_url": "https://www.fiverr.com/s/excel-formula-repair",
        "target_keywords": "Formula repair, XLOOKUP, INDEX MATCH, Circular errors, Audit",
        "status": "Active",
        "notes": "Fast turnaround gig for urgent client bug fixes."
    },
    {
        "gig_title": "Automate Excel Workflows & Data Cleaning with VBA Macros",
        "gig_url": "https://www.fiverr.com/s/excel-vba-automation",
        "target_keywords": "VBA, Macro, Automation, Data cleaning, Deduplication",
        "status": "Active",
        "notes": "Higher value gig ($50-$150) for recurring business reporting automation."
    }
]

def seed_default_fiverr_gigs() -> int:
    """Pre-seeds default Excel gigs if none exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM fiverr_gigs")
    count = cursor.fetchone()[0]
    added = 0
    if count == 0:
        for g in DEFAULT_FIVERR_GIGS:
            cursor.execute("""
                INSERT INTO fiverr_gigs (
                    gig_title, gig_url, target_keywords, status, notes
                ) VALUES (?, ?, ?, ?, ?)
            """, (g["gig_title"], g["gig_url"], g["target_keywords"], g["status"], g["notes"]))
            added += 1
        conn.commit()
    conn.close()
    return added

def get_fiverr_gigs() -> pd.DataFrame:
    """Returns all configured Fiverr gigs."""
    seed_default_fiverr_gigs()
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM fiverr_gigs ORDER BY id ASC", conn)
    conn.close()
    return df

def add_fiverr_gig(
    gig_title: str,
    gig_url: str = "",
    target_keywords: str = "",
    status: str = "Active",
    notes: str = ""
) -> int:
    """Creates a new Gig profile record."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO fiverr_gigs (
            gig_title, gig_url, target_keywords, status, notes
        ) VALUES (?, ?, ?, ?, ?)
    """, (gig_title.strip(), gig_url.strip(), target_keywords.strip(), status, notes.strip()))
    conn.commit()
    gig_id = cursor.lastrowid
    conn.close()
    return gig_id

def update_fiverr_gig(
    gig_id: int,
    gig_title: str,
    gig_url: str,
    target_keywords: str,
    status: str,
    notes: str
) -> bool:
    """Updates an existing Gig profile."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE fiverr_gigs
        SET gig_title = ?,
            gig_url = ?,
            target_keywords = ?,
            status = ?,
            notes = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (gig_title, gig_url, target_keywords, status, notes, gig_id))
    conn.commit()
    rows = cursor.rowcount
    conn.close()
    return rows > 0

def add_fiverr_buyer_request(
    title: str,
    description: str,
    budget: float,
    buyer_info: str = "",
    request_url: str = "",
    deadline: str = ""
) -> Tuple[bool, Optional[int], str]:
    """
    Manually ingests a Fiverr buyer request or client message into the unified jobs repository.
    Enforces compliance: 100% human-managed, zero automated scraping.
    """
    job_dict = {
        "title": title,
        "description": description,
        "platform": "Fiverr",
        "url": request_url or "https://www.fiverr.com",
        "budget": budget,
        "currency": "INR",
        "client_info": buyer_info or "Fiverr Buyer",
        "deadline": deadline,
        "discovery_source": "fiverr_manual_request"
    }
    return add_job(job_dict, auto_evaluate=True)
