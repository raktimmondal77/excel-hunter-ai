import re
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse
from src.job_manager import add_job
from src.discovery.base_adapter import StandardJob

def detect_platform_from_url(url: str) -> str:
    """Detects freelance platform from URL domain."""
    if not url:
        return "Direct Client"
    domain = urlparse(url).netloc.lower()
    if "upwork.com" in domain:
        return "Upwork"
    elif "freelancer.com" in domain:
        return "Freelancer.com"
    elif "fiverr.com" in domain:
        return "Fiverr"
    elif "peopleperhour.com" in domain:
        return "PeoplePerHour"
    elif "truelancer.com" in domain:
        return "Truelancer"
    elif "guru.com" in domain:
        return "Guru"
    elif "linkedin.com" in domain:
        return "LinkedIn"
    else:
        return "Direct Client"

def import_job_from_url(
    job_url: str,
    title: str = "",
    budget: float = 0.0,
    description: str = "",
    client_info: str = ""
) -> Tuple[bool, Optional[int], str]:
    """
    Imports a job manually from a pasted opportunity URL.
    Auto-detects platform and applies evaluation and deduplication.
    """
    url_clean = job_url.strip()
    if not url_clean:
        return False, None, "A valid job URL is required."

    platform = detect_platform_from_url(url_clean)
    final_title = title.strip() if title.strip() else f"{platform} Excel Opportunity"

    job_dict = {
        "title": final_title,
        "description": description.strip() or f"Discovered job on {platform} at {url_clean}",
        "platform": platform,
        "url": url_clean,
        "budget": budget,
        "currency": "INR",
        "client_info": client_info.strip() or f"{platform} Buyer",
        "discovery_source": "manual_url",
        "date_posted": datetime.now().strftime("%Y-%m-%d")
    }

    return add_job(job_dict, auto_evaluate=True)

def import_job_from_pasted_text(
    raw_text: str,
    platform: str = "Direct Client",
    job_url: str = "",
    custom_budget: Optional[float] = None,
    custom_title: Optional[str] = None
) -> Tuple[bool, Optional[int], str]:
    """
    Parses unstructured pasted text (from a client chat, email alert, or forum post).
    Extracts title, description, and budget signals automatically.
    """
    if not raw_text or len(raw_text.strip()) < 15:
        return False, None, "Pasted text is too short to extract a job opportunity."

    lines = [l.strip() for l in raw_text.strip().split("\n") if l.strip()]
    if custom_title and custom_title.strip():
        title = custom_title.strip()
    else:
        title = lines[0] if lines else "Excel Freelance Project"
    
    # Ensure title isn't excessively long
    if len(title) > 100:
        title = title[:97] + "..."

    # Extract budget if not explicitly provided
    budget_val = custom_budget if custom_budget is not None and custom_budget > 0 else 0.0
    if budget_val == 0.0:
        budget_match = re.search(r"(\$|₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)", raw_text, re.IGNORECASE)
        if budget_match:
            symbol = budget_match.group(1).lower()
            val = float(budget_match.group(2).replace(",", ""))
            budget_val = val * 85.0 if "$" in symbol else val

    job_dict = {
        "title": title,
        "description": raw_text.strip(),
        "platform": platform or detect_platform_from_url(job_url),
        "url": job_url.strip() or None,
        "budget": budget_val,
        "currency": "INR",
        "client_info": "Extracted from client message/alert",
        "discovery_source": "pasted_text",
        "date_posted": datetime.now().strftime("%Y-%m-%d")
    }

    return add_job(job_dict, auto_evaluate=True)

def parse_email_alert(
    subject: str,
    body: str,
    sender_platform: Optional[str] = None
) -> Tuple[bool, Optional[int], str]:
    """
    Parses an email alert notification (e.g. Upwork Job Alert, Freelancer Project Notification).
    """
    platform = sender_platform or "Email Alert"
    # Extract any links from the email body
    url_match = re.search(r"https?://[^\s<>\"']+", body)
    found_url = url_match.group(0) if url_match else ""

    if not sender_platform and found_url:
        platform = detect_platform_from_url(found_url)

    title = subject.strip() if subject.strip() else f"{platform} Alert Project"
    # Clean standard email alert prefixes
    title = re.sub(r"^(re:\s*|fwd:\s*|new job alert:\s*|new job:\s*|new project:\s*)", "", title, flags=re.IGNORECASE).strip()

    return import_job_from_pasted_text(
        raw_text=body,
        platform=platform,
        job_url=found_url,
        custom_title=title
    )
