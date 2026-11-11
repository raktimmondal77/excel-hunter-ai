import pytest
from pathlib import Path
from src.db import init_db, get_connection
import src.platform_manager as pm

@pytest.fixture
def override_db(tmp_path: Path, monkeypatch):
    db_file = tmp_path / "test_platform.db"
    init_db(db_file)
    monkeypatch.setattr(pm, "get_connection", lambda: get_connection(db_file))
    return db_file

def test_default_platform_seeding(override_db):
    added = pm.seed_default_platforms()
    assert added >= 5

    df = pm.get_platform_accounts()
    assert len(df) >= 5
    platform_names = df["platform_name"].tolist()
    assert "Freelancer.com" in platform_names
    assert "Fiverr" in platform_names
    assert "Upwork" in platform_names
    assert "LinkedIn" in platform_names
    assert "Direct Client" in platform_names

def test_no_passwords_or_tokens_in_schema(override_db):
    """Verifies security requirement: zero password or token columns exist in the database."""
    conn = pm.get_connection()
    c = conn.cursor()
    c.execute("PRAGMA table_info(platform_accounts);")
    col_names = [r["name"].lower() for r in c.fetchall()]
    conn.close()

    forbidden = ["password", "token", "secret", "cookie", "session"]
    for f in forbidden:
        assert not any(f in col for col in col_names), f"Found sensitive column matching '{f}' in platform_accounts!"

def test_update_platform_account(override_db):
    pm.seed_default_platforms()
    df = pm.get_platform_accounts()
    freelancer_id = int(df[df["platform_name"] == "Freelancer.com"].iloc[0]["id"])

    updated = pm.update_platform_account(
        platform_id=freelancer_id,
        profile_url="https://www.freelancer.com/u/excelpro",
        account_status="Active",
        integration_mode="Manual (Human-Controlled)",
        policy_notes="Confirmed human-in-the-loop compliance.",
        notes="Targeting Excel formula repair bids."
    )
    assert updated is True

    df2 = pm.get_platform_accounts()
    row = df2[df2["id"] == freelancer_id].iloc[0]
    assert row["profile_url"] == "https://www.freelancer.com/u/excelpro"
    assert "formula repair" in row["notes"]

def test_add_custom_platform(override_db):
    new_id = pm.add_custom_platform(
        platform_name="Guru.com",
        profile_url="https://guru.com/pro",
        account_status="Active",
        integration_mode="Manual (Human-Controlled)",
        notes="Excel data cleaning"
    )
    assert new_id is not None

    df = pm.get_platform_accounts()
    assert "Guru.com" in df["platform_name"].values
