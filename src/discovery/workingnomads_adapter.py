import re
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.discovery.base_adapter import BaseSourceAdapter, StandardJob
from src.evaluation import is_excel_job
from src.discovery.jobicy_adapter import strip_html

# Engagement signals accepted for a side-income freelancer
ENGAGEMENT_ACCEPT = re.compile(
    r"\b(contract(?:or)?|freelance|freelancer|part[- ]time|gig|project[- ]based)\b",
    re.IGNORECASE
)
ENGAGEMENT_REJECT = re.compile(r"\bfull[- ]time\b", re.IGNORECASE)


class WorkingNomadsAdapter(BaseSourceAdapter):
    """
    Working Nomads Public Jobs API Adapter (Stage 3 — NEW SOURCE).
    Endpoint: https://www.workingnomads.com/api/exposed_jobs/
    Attribution: Powered by the Working Nomads public jobs API (https://www.workingnomads.com).

    - Free, no API key, official public API.
    - Accepts only postings that explicitly look like contract / freelance /
      part-time engagements (full-time vacancies are rejected).
    - Applies the strict Excel-tool relevance gate.
    """

    def __init__(self):
        super().__init__(
            source_id="workingnomads_public_api",
            source_name="Working Nomads (Public Jobs API)",
            is_enabled=True
        )
        self.api_url = "https://www.workingnomads.com/api/exposed_jobs/"

    def test_connection(self) -> Dict[str, Any]:
        try:
            resp = requests.get(self.api_url, timeout=10, headers={"User-Agent": "ExcelHunterAI/3.0"})
            if resp.status_code == 200:
                return {
                    "status": "Connected",
                    "message": "Working Nomads public API is live and responding.",
                    "healthy": True
                }
            return {
                "status": "Warning",
                "message": f"Working Nomads API returned HTTP {resp.status_code}",
                "healthy": False
            }
        except Exception as e:
            return {
                "status": "Temporarily unavailable",
                "message": f"Network exception: {str(e)}",
                "healthy": False
            }

    def fetch_jobs(self, search_terms: List[str], max_results: int = 10) -> List[StandardJob]:
        jobs: List[StandardJob] = []
        self.filtered_count = 0

        try:
            resp = requests.get(self.api_url, timeout=15, headers={"User-Agent": "ExcelHunterAI/3.0"})
            if resp.status_code != 200:
                return []

            entries = resp.json()

            for entry in entries:
                if len(jobs) >= max_results:
                    break
                if not isinstance(entry, dict):
                    continue

                title = (entry.get("title") or "").strip()
                desc = strip_html(entry.get("description") or "")[:1500]
                url = (entry.get("url") or "").strip()
                if not title or not url:
                    continue

                category = (entry.get("category_name") or "").strip()
                tags = " ".join(str(t) for t in (entry.get("tags") or []) if t)

                # Strict Excel-tool relevance gate
                if not is_excel_job(title, f"{desc} {tags}"):
                    self.filtered_count += 1
                    continue

                # Engagement filter: must look like contract/freelance work
                engagement_blob = f"{title} {desc[:400]} {tags} {category}"
                if ENGAGEMENT_REJECT.search(engagement_blob):
                    self.filtered_count += 1
                    continue
                if not ENGAGEMENT_ACCEPT.search(engagement_blob):
                    self.filtered_count += 1
                    continue

                company = (entry.get("company_name") or "Remote Employer").strip()
                pub_date = (entry.get("pub_date") or "")[:10] or datetime.now().strftime("%Y-%m-%d")

                client_desc = f"Company: {company} | Working Nomads (Category: {category or 'General'})"

                jobs.append(StandardJob(
                    title=title,
                    description=desc,
                    platform="Working Nomads (Remote Public Feed)",
                    url=url,
                    budget=0.0,
                    currency="INR",
                    date_posted=pub_date,
                    client_info=client_desc,
                    skills_required=["Excel", "Remote Contract"],
                    discovery_source="workingnomads_public_api",
                    is_sample=0
                ))

        except Exception:
            return []

        return jobs[:max_results]
