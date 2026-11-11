import json
import sqlite3
from typing import Dict, Any, List, Optional
from src.db import get_connection

AVAILABLE_EXCEL_SKILLS = [
    "Basic formulas",
    "IF, SUMIF, COUNTIF",
    "XLOOKUP / VLOOKUP",
    "Pivot Tables",
    "Charts",
    "Dashboards",
    "Data cleaning",
    "MIS reporting",
    "Excel automation",
    "Power Query",
    "VBA"
]

AVAILABLE_OTHER_TOOLS = [
    "Microsoft Excel",
    "Google Sheets",
    "Power BI",
    "SQL",
    "Python"
]

EXPERIENCE_LEVELS = [
    "Beginner",
    "Intermediate",
    "Advanced"
]

DEFAULT_PROFILE = {
    "excel_skills": ["Basic formulas", "IF, SUMIF, COUNTIF", "Data cleaning"],
    "other_tools": ["Microsoft Excel"],
    "experience_level": "Beginner",
    "work_experience_desc": "Hands-on experience organizing spreadsheets, standardizing columns, and writing Excel formulas.",
    "completed_projects_desc": "Built personal finance trackers and sales summary sheets using basic formulas.",
    "industry_knowledge": "Small business operations and general retail sales reporting.",
    "hours_per_week": 15.0,
    "preferred_duration": "1-2 weeks",
    "min_budget": 1500.0
}

def get_user_profile(conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
    """
    Retrieves the confirmed user skills profile.
    If no profile is recorded yet, initializes and returns the honest beginner baseline.
    Never invents unconfirmed skills.
    """
    close_at_end = False
    if conn is None:
        conn = get_connection()
        close_at_end = True

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_profile WHERE id = 1")
        row = cursor.fetchone()

        if not row:
            # Seed default profile safely
            save_user_profile(DEFAULT_PROFILE, conn=conn)
            cursor.execute("SELECT * FROM user_profile WHERE id = 1")
            row = cursor.fetchone()

        data = dict(row)
        # Parse JSON fields
        try:
            data["excel_skills"] = json.loads(data.get("excel_skills") or "[]")
        except Exception:
            data["excel_skills"] = []

        try:
            data["other_tools"] = json.loads(data.get("other_tools") or "[]")
        except Exception:
            data["other_tools"] = []

        return data
    finally:
        if close_at_end:
            conn.close()

def save_user_profile(profile_data: Dict[str, Any], conn: Optional[sqlite3.Connection] = None) -> bool:
    """
    Updates the confirmed user skills profile.
    Only stores confirmed user input.
    """
    close_at_end = False
    if conn is None:
        conn = get_connection()
        close_at_end = True

    try:
        cursor = conn.cursor()
        excel_skills_json = json.dumps(profile_data.get("excel_skills", []))
        other_tools_json = json.dumps(profile_data.get("other_tools", []))
        experience_level = profile_data.get("experience_level", "Beginner")
        work_exp = (profile_data.get("work_experience_desc") or "").strip()
        comp_proj = (profile_data.get("completed_projects_desc") or "").strip()
        ind_know = (profile_data.get("industry_knowledge") or "").strip()
        hours_pw = float(profile_data.get("hours_per_week", 15.0))
        pref_dur = profile_data.get("preferred_duration", "1-2 weeks")
        min_bud = float(profile_data.get("min_budget", 1500.0))

        cursor.execute("""
            INSERT INTO user_profile (
                id, excel_skills, other_tools, experience_level,
                work_experience_desc, completed_projects_desc, industry_knowledge,
                hours_per_week, preferred_duration, min_budget, updated_at
            ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                excel_skills = excluded.excel_skills,
                other_tools = excluded.other_tools,
                experience_level = excluded.experience_level,
                work_experience_desc = excluded.work_experience_desc,
                completed_projects_desc = excluded.completed_projects_desc,
                industry_knowledge = excluded.industry_knowledge,
                hours_per_week = excluded.hours_per_week,
                preferred_duration = excluded.preferred_duration,
                min_budget = excluded.min_budget,
                updated_at = CURRENT_TIMESTAMP
        """, (
            excel_skills_json, other_tools_json, experience_level,
            work_exp, comp_proj, ind_know,
            hours_pw, pref_dur, min_bud
        ))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        if close_at_end:
            conn.close()

def get_portfolio_projects(conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
    """Returns confirmed portfolio projects."""
    close_at_end = False
    if conn is None:
        conn = get_connection()
        close_at_end = True

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_portfolio ORDER BY id DESC")
        rows = cursor.fetchall()
        projects = []
        for r in rows:
            p = dict(r)
            projects.append(p)
        return projects
    finally:
        if close_at_end:
            conn.close()

def add_portfolio_project(
    project_title: str,
    project_description: str,
    skills_used: str,
    portfolio_link: str = "",
    completion_status: str = "Completed",
    conn: Optional[sqlite3.Connection] = None
) -> Optional[int]:
    """Adds a new verified portfolio item entered by user."""
    close_at_end = False
    if conn is None:
        conn = get_connection()
        close_at_end = True

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_portfolio (
                project_title, project_description, skills_used,
                portfolio_link, completion_status
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            project_title.strip(),
            project_description.strip(),
            skills_used.strip(),
            portfolio_link.strip(),
            completion_status
        ))
        conn.commit()
        return cursor.lastrowid
    except Exception:
        return None
    finally:
        if close_at_end:
            conn.close()

def delete_portfolio_project(project_id: int, conn: Optional[sqlite3.Connection] = None) -> bool:
    """Deletes a portfolio project."""
    close_at_end = False
    if conn is None:
        conn = get_connection()
        close_at_end = True

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_portfolio WHERE id = ?", (project_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        if close_at_end:
            conn.close()
