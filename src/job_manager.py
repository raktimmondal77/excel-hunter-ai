import re
import string
import json
import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from src.db import get_connection
from src.evaluation import evaluate_job
from src.currency import to_inr, normalize_currency_code

def normalize_title(title: str) -> str:
    """Normalizes a title for deduplication: lowercase, strips punctuation, removes common filler words."""
    if not title:
        return ""
    text = title.lower()
    # Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))
    # Remove common filler words
    filler_words = {"need", "needed", "looking", "for", "urgent", "urgently", "wanted", "hiring", "expert", "specialist"}
    tokens = [w for w in text.split() if w not in filler_words]
    return " ".join(tokens)

def normalize_url(url: Optional[str]) -> str:
    """Normalizes a URL by trimming, lowercasing, and stripping trailing slashes."""
    if not url:
        return ""
    u = url.strip().lower()
    return u.rstrip("/")

def is_duplicate_job(
    conn: sqlite3.Connection,
    title: str,
    platform: str,
    url: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Checks if a job already exists based on URL or normalized title + platform.
    Returns (is_duplicate, duplicate_reason)
    """
    cursor = conn.cursor()

    # 1. Check URL match
    norm_url = normalize_url(url)
    if norm_url:
        cursor.execute("SELECT id, title, url FROM jobs WHERE LOWER(TRIM(url)) = ? OR LOWER(TRIM(url)) = ?", (norm_url, norm_url + "/"))
        row = cursor.fetchone()
        if row:
            return True, f"Matching URL with Job #{row['id']} ('{row['title']}')"

    # 2. Check Normalized Title + Platform
    norm_incoming_title = normalize_title(title)
    if norm_incoming_title:
        cursor.execute("SELECT id, title FROM jobs WHERE LOWER(platform) = LOWER(?)", (platform.strip(),))
        existing_jobs = cursor.fetchall()
        for row in existing_jobs:
            if normalize_title(row["title"]) == norm_incoming_title:
                return True, f"Matching Title on {platform} with Job #{row['id']} ('{row['title']}')"

    return False, None

def add_job(
    job_data: Dict[str, Any],
    conn: Optional[sqlite3.Connection] = None,
    auto_evaluate: bool = True
) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Adds a job to the database if not duplicate.
    Returns (success, job_id, message_or_reason)
    """
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True

    try:
        title = str(job_data.get("title", "")).strip()
        if not title:
            return False, None, "Job title is required."

        platform = str(job_data.get("platform", "Other")).strip()
        url = str(job_data.get("url", "")).strip() or None
        description = str(job_data.get("description", "")).strip()
        
        try:
            budget = float(job_data.get("budget", 0) or 0)
        except (ValueError, TypeError):
            budget = 0.0

        # ----------------------------------------------------------
        # Currency normalization (Stage 3): every budget stored in the
        # repository is converted to INR once, at the boundary, so that
        # scoring, pricing and the ₹10k-20k goal always compare like with
        # like. The original amount is preserved inside client_info.
        # ----------------------------------------------------------
        currency = normalize_currency_code(job_data.get("currency", "INR"))
        client_info = str(job_data.get("client_info", "") or "")
        if currency != "INR" and budget > 0:
            original_note = f"Original budget: {budget:,.2f} {currency}"
            client_info = f"{client_info} | {original_note}".strip(" |")
            budget = to_inr(budget, currency)
            currency = "INR"

        # Check duplicate
        is_dup, dup_reason = is_duplicate_job(conn, title, platform, url)
        if is_dup:
            return False, None, f"Duplicate detected: {dup_reason}"

        # Evaluate if requested or missing score
        score = job_data.get("score")
        priority = job_data.get("priority")
        risk_flags = job_data.get("risk_flags")
        category = job_data.get("category")

        deadline = job_data.get("deadline", "")
        date_posted = str(job_data.get("date_posted", "") or "")

        if auto_evaluate or score is None:
            eval_res = evaluate_job(
                title, description, budget,
                client_info=client_info, deadline_text=deadline,
                currency="INR",  # already normalized above
                date_posted=date_posted
            )
            if len(eval_res) == 4:
                eval_score, eval_priority, eval_risks, eval_cat = eval_res
                category = category or eval_cat
            else:
                eval_score, eval_priority, eval_risks = eval_res[:3]
            score = eval_score
            priority = eval_priority
            risk_flags = json.dumps(eval_risks) if eval_risks else ""
        elif isinstance(risk_flags, list):
            risk_flags = json.dumps(risk_flags)

        status = job_data.get("status", "discovered")
        is_sample = int(job_data.get("is_sample", 0))
        notes = job_data.get("notes", "")

        skills_required = job_data.get("skills_required", "")
        if isinstance(skills_required, list):
            skills_required = json.dumps(skills_required)

        discovery_source = job_data.get("discovery_source", "manual")
        date_discovered = job_data.get("date_discovered", "") or date_posted

        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO jobs (
                title, description, platform, url, budget, currency,
                date_posted, client_info, status, score, priority,
                risk_flags, is_sample, notes,
                deadline, skills_required, discovery_source, date_discovered, category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title, description, platform, url, budget, currency,
            date_posted, client_info, status, score, priority,
            risk_flags, is_sample, notes,
            deadline, skills_required, discovery_source, date_discovered, category
        ))
        conn.commit()
        job_id = cursor.lastrowid
        return True, job_id, "Job added successfully."
    finally:
        if should_close:
            conn.close()

def update_job_status(job_id: int, new_status: str, notes: Optional[str] = None) -> bool:
    """Updates job status and optional notes."""
    conn = get_connection()
    cursor = conn.cursor()
    if notes is not None:
        cursor.execute(
            "UPDATE jobs SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_status, notes, job_id)
        )
    else:
        cursor.execute(
            "UPDATE jobs SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_status, job_id)
        )
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0

def get_jobs(
    platform: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    search_keyword: Optional[str] = None,
    min_score: Optional[int] = None,
    min_budget: Optional[float] = None,
    include_samples: bool = True
) -> pd.DataFrame:
    """Fetches jobs matching filter criteria as a pandas DataFrame."""
    conn = get_connection()
    query = "SELECT * FROM jobs WHERE 1=1"
    params: List[Any] = []

    if not include_samples:
        query += " AND is_sample = 0"

    if platform and platform != "All":
        query += " AND platform = ?"
        params.append(platform)

    if status and status != "All":
        query += " AND status = ?"
        params.append(status)

    if priority and priority != "All":
        query += " AND priority = ?"
        params.append(priority)

    if category and category != "All":
        query += " AND category = ?"
        params.append(category)

    if min_score is not None and min_score > 0:
        query += " AND score >= ?"
        params.append(min_score)

    if min_budget is not None and min_budget > 0:
        query += " AND budget >= ?"
        params.append(min_budget)

    if search_keyword and search_keyword.strip():
        kw = f"%{search_keyword.strip()}%"
        query += " AND (title LIKE ? OR description LIKE ? OR client_info LIKE ? OR skills_required LIKE ?)"
        params.extend([kw, kw, kw, kw])

    query += " ORDER BY id DESC"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def import_jobs_from_csv(file_path_or_buffer: Any, is_sample: bool = False) -> Dict[str, Any]:
    """
    Imports jobs from a CSV file or buffer.
    Performs field mapping, validation, duplicate prevention, and auto-evaluation.
    Handles encoding, empty files, and parser errors safely.
    """
    # 1. Attempt reading CSV with encodings
    df = None
    read_error = None
    encodings_to_try = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

    for enc in encodings_to_try:
        try:
            if hasattr(file_path_or_buffer, "seek"):
                file_path_or_buffer.seek(0)
            df = pd.read_csv(file_path_or_buffer, encoding=enc)
            read_error = None
            break
        except pd.errors.EmptyDataError:
            return {
                "success": False,
                "error": "The selected CSV file is empty.",
                "imported_count": 0,
                "duplicate_count": 0,
                "errors": ["File contains no data."]
            }
        except UnicodeDecodeError:
            continue
        except Exception as e:
            read_error = str(e)
            break

    if df is None:
        return {
            "success": False,
            "error": f"Failed to parse CSV file: {read_error or 'Unsupported file format or encoding.'}",
            "imported_count": 0,
            "duplicate_count": 0,
            "errors": [read_error or "Parsing failed."]
        }

    if df.empty:
        return {
            "success": False,
            "error": "The CSV file contains column headers but no job rows.",
            "imported_count": 0,
            "duplicate_count": 0,
            "errors": ["Zero rows found."]
        }

    # Standardize column names (lowercase, stripped)
    col_map = {str(col).strip().lower(): col for col in df.columns}

    def find_col(*candidates: str) -> Optional[str]:
        for c in candidates:
            if c in col_map:
                return col_map[c]
        return None

    title_col = find_col("title", "job_title", "project_title", "name")
    desc_col = find_col("description", "desc", "details", "job_description")
    platform_col = find_col("platform", "source", "site")
    url_col = find_col("url", "link", "job_url")
    budget_col = find_col("budget", "price", "amount", "rate")
    currency_col = find_col("currency", "curr")
    date_col = find_col("date_posted", "date", "posted_date", "created")
    client_col = find_col("client_info", "client", "buyer", "posted_by")

    if not title_col:
        return {
            "success": False,
            "error": "CSV missing a required 'title' or 'job_title' column. Please check your column headers.",
            "imported_count": 0,
            "duplicate_count": 0,
            "errors": ["Missing title column."]
        }

    conn = get_connection()
    imported_count = 0
    duplicate_count = 0
    errors: List[str] = []

    try:
        for idx, row in df.iterrows():
            title_val = str(row[title_col]).strip() if pd.notna(row[title_col]) else ""
            if not title_val or title_val.lower() == "nan":
                continue

            desc_val = str(row[desc_col]).strip() if desc_col and pd.notna(row[desc_col]) else ""
            plat_val = str(row[platform_col]).strip() if platform_col and pd.notna(row[platform_col]) else "CSV Import"
            url_val = str(row[url_col]).strip() if url_col and pd.notna(row[url_col]) else ""
            curr_val = str(row[currency_col]).strip() if currency_col and pd.notna(row[currency_col]) else "INR"
            date_val = str(row[date_col]).strip() if date_col and pd.notna(row[date_col]) else ""
            client_val = str(row[client_col]).strip() if client_col and pd.notna(row[client_col]) else ""

            b_val = 0.0
            if budget_col and pd.notna(row[budget_col]):
                try:
                    # Clean currency symbols and commas if present
                    clean_b = re.sub(r"[^\d.]", "", str(row[budget_col]))
                    # Handle cases with multiple periods
                    if clean_b.count(".") > 1:
                        parts = clean_b.split(".")
                        clean_b = parts[0] + "." + "".join(parts[1:])
                    b_val = float(clean_b) if clean_b else 0.0
                except (ValueError, TypeError):
                    b_val = 0.0

            job_dict = {
                "title": title_val,
                "description": desc_val,
                "platform": plat_val,
                "url": url_val,
                "budget": b_val,
                "currency": curr_val,
                "date_posted": date_val,
                "client_info": client_val,
                "is_sample": 1 if is_sample else 0
            }

            success, _, msg = add_job(job_dict, conn=conn, auto_evaluate=True)
            if success:
                imported_count += 1
            else:
                if "Duplicate" in (msg or ""):
                    duplicate_count += 1
                else:
                    errors.append(f"Row {idx+1} ({title_val}): {msg}")

        return {
            "success": True,
            "imported_count": imported_count,
            "duplicate_count": duplicate_count,
            "errors": errors
        }
    finally:
        conn.close()

def delete_sample_data() -> Tuple[int, int]:
    """
    Safely deletes ONLY sample demonstration records (is_sample = 1).
    Guarantees that real opportunities and user earnings (is_sample = 0) are untouched.
    """
    conn = get_connection()
    cursor = conn.cursor()
    # Explicitly filter strictly is_sample = 1 (real records are never touched)
    cursor.execute("DELETE FROM jobs WHERE is_sample = 1")
    jobs_deleted = cursor.rowcount
    cursor.execute("DELETE FROM earnings WHERE is_sample = 1")
    earnings_deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return jobs_deleted, earnings_deleted
