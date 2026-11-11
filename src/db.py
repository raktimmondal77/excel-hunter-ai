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

    conn.commit()
    conn.close()
