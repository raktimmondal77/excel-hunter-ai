import sqlite3
from typing import Optional
from pathlib import Path
from src.config import DB_PATH

def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Returns a SQLite connection with row_factory enabled."""
    target_db = db_path or DB_PATH
    conn = sqlite3.connect(str(target_db))
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Optional[Path] = None) -> None:
    """Initializes tables for jobs and earnings."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Table: jobs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        platform TEXT NOT NULL,
        url TEXT,
        budget REAL,
        currency TEXT DEFAULT 'INR',
        date_posted TEXT,
        client_info TEXT,
        status TEXT DEFAULT 'discovered',
        score INTEGER DEFAULT 0,
        priority TEXT DEFAULT 'Medium',
        risk_flags TEXT,
        is_sample INTEGER DEFAULT 0,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Indexes for fast lookup and duplicate checks
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_url ON jobs(url);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_platform ON jobs(platform);")

    # Table: earnings
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS earnings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER,
        project_name TEXT NOT NULL,
        platform TEXT,
        date_received TEXT,
        gross_amount REAL NOT NULL,
        platform_fee REAL DEFAULT 0.0,
        net_amount REAL NOT NULL,
        currency TEXT DEFAULT 'INR',
        status TEXT DEFAULT 'received',
        is_sample INTEGER DEFAULT 0,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE SET NULL
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_earnings_date ON earnings(date_received);")

    # Table: platform_accounts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS platform_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform_name TEXT NOT NULL UNIQUE,
        profile_url TEXT,
        account_status TEXT DEFAULT 'Active',
        integration_mode TEXT DEFAULT 'Manual (Human-Controlled)',
        policy_notes TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Table: applications
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        platform TEXT NOT NULL,
        job_url TEXT,
        proposal_text TEXT NOT NULL,
        bid_amount REAL,
        currency TEXT DEFAULT 'INR',
        applied_date TEXT NOT NULL,
        status TEXT DEFAULT 'applied',
        follow_up_date TEXT,
        follow_up_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_applications_job ON applications(job_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_applications_followup ON applications(follow_up_date);")

    # Table: fiverr_gigs (Stage 2)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fiverr_gigs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gig_title TEXT NOT NULL,
        gig_url TEXT,
        target_keywords TEXT,
        status TEXT DEFAULT 'Active',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Table: discovery_runs (Stage 2, extended in Stage 3)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS discovery_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        sources_scanned TEXT NOT NULL,
        jobs_found INTEGER DEFAULT 0,
        duplicates_skipped INTEGER DEFAULT 0,
        errors_logged INTEGER DEFAULT 0,
        status TEXT DEFAULT 'completed',
        summary_notes TEXT,
        irrelevant_skipped INTEGER DEFAULT 0
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_discovery_runs_time ON discovery_runs(run_timestamp);")

    # Table: user_profile (Stage 3)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_profile (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        excel_skills TEXT NOT NULL DEFAULT '[]',
        other_tools TEXT NOT NULL DEFAULT '[]',
        experience_level TEXT DEFAULT 'Beginner',
        work_experience_desc TEXT DEFAULT '',
        completed_projects_desc TEXT DEFAULT '',
        industry_knowledge TEXT DEFAULT '',
        hours_per_week REAL DEFAULT 15.0,
        preferred_duration TEXT DEFAULT '1-2 weeks',
        min_budget REAL DEFAULT 1500.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Table: user_portfolio (Stage 3)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_portfolio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_title TEXT NOT NULL,
        project_description TEXT,
        skills_used TEXT,
        portfolio_link TEXT,
        completion_status TEXT DEFAULT 'Completed',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Safe Schema Migrations (Adding Stage 2 & 3 columns to existing tables if missing)
    def add_col_if_missing(table_name: str, col_name: str, col_type: str):
        cursor.execute(f"PRAGMA table_info({table_name});")
        existing_cols = [r["name"].lower() for r in cursor.fetchall()]
        if col_name.lower() not in existing_cols:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type};")

    # jobs table extensions
    add_col_if_missing("jobs", "deadline", "TEXT")
    add_col_if_missing("jobs", "skills_required", "TEXT")
    add_col_if_missing("jobs", "discovery_source", "TEXT")
    add_col_if_missing("jobs", "date_discovered", "TEXT")
    add_col_if_missing("jobs", "category", "TEXT")

    # platform_accounts table extensions
    add_col_if_missing("platform_accounts", "connection_status", "TEXT DEFAULT 'Not Connected'")
    add_col_if_missing("platform_accounts", "last_checked_date", "TEXT")

    # discovery_runs table extensions (Stage 3)
    add_col_if_missing("discovery_runs", "irrelevant_skipped", "INTEGER DEFAULT 0")

    # applications table extensions (Stage 3)
    add_col_if_missing("applications", "project_title", "TEXT")
    add_col_if_missing("applications", "client_name", "TEXT")
    add_col_if_missing("applications", "proposed_amount", "REAL")
    add_col_if_missing("applications", "date_prepared", "TEXT")
    add_col_if_missing("applications", "date_submitted", "TEXT")
    add_col_if_missing("applications", "next_follow_up_date", "TEXT")
    add_col_if_missing("applications", "client_response", "TEXT")
    add_col_if_missing("applications", "interview_date", "TEXT")
    add_col_if_missing("applications", "final_outcome", "TEXT")
    add_col_if_missing("applications", "notes", "TEXT")

    # Unique index for duplicate application prevention on same platform
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_applications_job_platform ON applications(job_id, platform);")

    conn.commit()
    conn.close()
