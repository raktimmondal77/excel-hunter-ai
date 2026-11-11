import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional
from src.db import get_connection

DEFAULT_PLATFORMS = [
    {
        "platform_name": "Freelancer.com",
        "profile_url": "https://www.freelancer.com",
        "account_status": "Active",
        "integration_mode": "Manual (Human-Controlled)",
        "policy_notes": "Terms prohibit unauthorized scraping and automated bidding bots. All applications must be human-reviewed and submitted via the official website.",
        "notes": "Target: Excel formulas, data cleaning, and spreadsheet automation contests/projects."
    },
    {
        "platform_name": "Fiverr",
        "profile_url": "https://www.fiverr.com",
        "account_status": "Active",
        "integration_mode": "Manual (Human-Controlled)",
        "policy_notes": "Buyer requests and custom offers require direct seller review. Automated messaging or account access via third-party scripts is strictly forbidden.",
        "notes": "Gigs: Excel Dashboards, Financial Models, Dynamic Templates."
    },
    {
        "platform_name": "Upwork",
        "profile_url": "https://www.upwork.com",
        "account_status": "Active",
        "integration_mode": "Manual (Human-Controlled)",
        "policy_notes": "Official API requires enterprise partner approval. Scraping or bot bidding violates Terms of Use. Human-in-the-loop manual proposal submission.",
        "notes": "Hourly and fixed-price Excel reporting and MIS contracts."
    },
    {
        "platform_name": "LinkedIn",
        "profile_url": "https://www.linkedin.com",
        "account_status": "Active",
        "integration_mode": "Manual (Human-Controlled)",
        "policy_notes": "Scraping profiles or messaging leads automatically triggers account restrictions. Use browser to message job posters or connections directly.",
        "notes": "Direct outreach to SME business owners and finance managers."
    },
    {
        "platform_name": "Direct Client",
        "profile_url": "",
        "account_status": "Active",
        "integration_mode": "Manual (Human-Controlled)",
        "policy_notes": "Direct client engagements via email, referral, or WhatsApp. 100% human-operated.",
        "notes": "Higher margins, zero platform commissions."
    }
]

INTEGRATION_MODES = [
    "Manual (Human-Controlled)",
    "Official API (Not Configured)",
    "Unavailable"
]

ACCOUNT_STATUSES = [
    "Active",
    "Pending Verification",
    "Under Review",
    "Inactive"
]

def seed_default_platforms() -> int:
    """Pre-seeds standard freelance platform records if they do not already exist."""
    conn = get_connection()
    cursor = conn.cursor()
    added_count = 0

    for p in DEFAULT_PLATFORMS:
        cursor.execute("SELECT id FROM platform_accounts WHERE platform_name = ?", (p["platform_name"],))
        if cursor.fetchone() is None:
            cursor.execute("""
                INSERT INTO platform_accounts (
                    platform_name, profile_url, account_status,
                    integration_mode, policy_notes, notes
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                p["platform_name"], p["profile_url"], p["account_status"],
                p["integration_mode"], p["policy_notes"], p["notes"]
            ))
            added_count += 1

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
    policy_notes: str,
    notes: str
) -> bool:
    """Updates account settings for a specific platform."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE platform_accounts
        SET profile_url = ?,
            account_status = ?,
            integration_mode = ?,
            policy_notes = ?,
            notes = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (profile_url, account_status, integration_mode, policy_notes, notes, platform_id))
    conn.commit()
    rows = cursor.rowcount
    conn.close()
    return rows > 0

def add_custom_platform(
    platform_name: str,
    profile_url: str = "",
    account_status: str = "Active",
    integration_mode: str = "Manual (Human-Controlled)",
    policy_notes: str = "Manual submission only.",
    notes: str = ""
) -> Optional[int]:
    """Adds a new platform account safely. No password fields supported."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO platform_accounts (
                platform_name, profile_url, account_status,
                integration_mode, policy_notes, notes
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (platform_name.strip(), profile_url.strip(), account_status, integration_mode, policy_notes, notes))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()
