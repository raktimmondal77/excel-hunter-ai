import sqlite3
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.db import get_connection
from src.config import INTEGRATION_STATES

DEFAULT_PLATFORMS = [
    {
        "platform_name": "Freelancer.com",
        "profile_url": "https://www.freelancer.com",
        "account_status": "Active",
        "integration_mode": "Official API available",
        "connection_status": "API access pending",
        "policy_notes": "Official Freelancer REST API permits active project search. Scraping and bot bidding are strictly prohibited by terms. All bids remain human-controlled.",
        "notes": "Target: Excel formulas, dashboards, data cleaning, and spreadsheet automation."
    },
    {
        "platform_name": "Fiverr",
        "profile_url": "https://www.fiverr.com",
        "account_status": "Active",
        "integration_mode": "Manual",
        "connection_status": "Connected",
        "policy_notes": "Fiverr Terms of Service forbid automated scraping and third-party bots. Manual Gig management and buyer request ingestion only.",
        "notes": "Gigs: Excel Dashboards, Financial Models, MIS Reporting, Formula Repair."
    },
    {
        "platform_name": "Upwork",
        "profile_url": "https://www.upwork.com",
        "account_status": "Active",
        "integration_mode": "Manual",
        "connection_status": "Connected",
        "policy_notes": "Upwork Developer API requires enterprise approval. Automated bidding or scraping violates Terms of Use. Supports manual job URL entry and CSV/email alert imports.",
        "notes": "Hourly and fixed-price contracts for Excel reporting and spreadsheet automation."
    },
    {
        "platform_name": "PeoplePerHour",
        "profile_url": "https://www.peopleperhour.com",
        "account_status": "Active",
        "integration_mode": "Manual",
        "connection_status": "Connected",
        "policy_notes": "Manual proposal submission only. Web scraping or automated proposals violate Terms.",
        "notes": "Project work and Hourly offers for UK/EU Excel clients."
    },
    {
        "platform_name": "Truelancer",
        "profile_url": "https://www.truelancer.com",
        "account_status": "Active",
        "integration_mode": "Manual",
        "connection_status": "Connected",
        "policy_notes": "Indian and global freelance marketplace. Manual proposal submission required.",
        "notes": "Competitive Excel data entry, MIS dashboards, and formula troubleshooting."
    },
    {
        "platform_name": "Guru",
        "profile_url": "https://www.guru.com",
        "account_status": "Active",
        "integration_mode": "Manual",
        "connection_status": "Connected",
        "policy_notes": "Public project browsing permitted. API restricted. Manual quoting required.",
        "notes": "Enterprise and SME Excel spreadsheet systems."
    },
    {
        "platform_name": "Direct Client",
        "profile_url": "",
        "account_status": "Active",
        "integration_mode": "Manual",
        "connection_status": "Connected",
        "policy_notes": "Direct client engagements via email, referral, or WhatsApp. 100% human-operated.",
        "notes": "Higher margins, zero platform commissions."
    },
    {
        "platform_name": "LinkedIn",
        "profile_url": "https://www.linkedin.com",
        "account_status": "Active",
        "integration_mode": "Manual",
        "connection_status": "Connected",
        "policy_notes": "Scraping profiles or messaging leads automatically triggers account restrictions. Use browser to message job posters directly.",
        "notes": "Direct outreach to SME business owners and finance managers."
    }
]

ACCOUNT_STATUSES = [
    "Active",
    "Pending Verification",
    "Under Review",
    "Inactive"
]

CONNECTION_STATUSES = [
    "Connected",
    "Not Connected",
    "API access pending",
    "Temporarily unavailable",
    "Disabled"
]

def seed_default_platforms() -> int:
    """Pre-seeds standard freelance platform records if they do not already exist."""
    conn = get_connection()
    cursor = conn.cursor()
    added_count = 0
    today_str = datetime.now().strftime("%Y-%m-%d")

    for p in DEFAULT_PLATFORMS:
        cursor.execute("SELECT id FROM platform_accounts WHERE platform_name = ?", (p["platform_name"],))
        row = cursor.fetchone()
        if row is None:
            cursor.execute("""
                INSERT INTO platform_accounts (
                    platform_name, profile_url, account_status,
                    integration_mode, connection_status, last_checked_date,
                    policy_notes, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p["platform_name"], p["profile_url"], p["account_status"],
                p["integration_mode"], p.get("connection_status", "Connected"),
                today_str, p["policy_notes"], p["notes"]
            ))
            added_count += 1
        else:
            # Safe migration: ensure integration_mode matches valid state if it was legacy
            pass

    conn.commit()
    conn.close()
    return added_count

def get_platform_accounts() -> pd.DataFrame:
    """Returns all configured platform accounts."""
    seed_default_platforms()
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM platform_accounts ORDER BY id ASC", conn)
    conn.close()
    return df

def update_platform_account(
    platform_id: int,
    profile_url: str,
    account_status: str,
    integration_mode: str,
    connection_status: str = "Connected",
    policy_notes: str = "",
    notes: str = ""
) -> bool:
    """Updates account and integration settings for a specific platform."""
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute("""
        UPDATE platform_accounts
        SET profile_url = ?,
            account_status = ?,
            integration_mode = ?,
            connection_status = ?,
            last_checked_date = ?,
            policy_notes = ?,
            notes = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (profile_url, account_status, integration_mode, connection_status, now_str, policy_notes, notes, platform_id))
    conn.commit()
    rows = cursor.rowcount
    conn.close()
    return rows > 0

def add_custom_platform(
    platform_name: str,
    profile_url: str = "",
    account_status: str = "Active",
    integration_mode: str = "Manual",
    connection_status: str = "Connected",
    policy_notes: str = "Manual submission only.",
    notes: str = ""
) -> Optional[int]:
    """Adds a new platform account safely. No password or session fields."""
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d")
    try:
        cursor.execute("""
            INSERT INTO platform_accounts (
                platform_name, profile_url, account_status,
                integration_mode, connection_status, last_checked_date,
                policy_notes, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (platform_name.strip(), profile_url.strip(), account_status, integration_mode, connection_status, now_str, policy_notes, notes))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()
