import sqlite3
import pytest
from pathlib import Path
from src.db import init_db, get_connection

@pytest.fixture
def temp_db(tmp_path: Path):
    db_file = tmp_path / "test_hunter.db"
    init_db(db_file)
    return db_file

def test_db_initialization(temp_db):
    conn = get_connection(temp_db)
    cursor = conn.cursor()
    
    # Verify jobs table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs';")
    assert cursor.fetchone() is not None

    # Verify earnings table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='earnings';")
    assert cursor.fetchone() is not None

    conn.close()

def test_job_table_schema(temp_db):
    conn = get_connection(temp_db)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(jobs);")
    columns = {row["name"] for row in cursor.fetchall()}
    
    expected_cols = {
        "id", "title", "description", "platform", "url", "budget",
        "currency", "date_posted", "client_info", "status", "score",
        "priority", "risk_flags", "is_sample", "notes", "created_at", "updated_at"
    }
    assert expected_cols.issubset(columns)
    conn.close()
