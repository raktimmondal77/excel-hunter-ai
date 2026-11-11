import re
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.discovery.base_adapter import BaseSourceAdapter, StandardJob
from src.evaluation import is_excel_job

# Multiple search terms: "excel" alone misses "spreadsheet" listings
REMOTIVE_SEARCH_TERMS = ["excel", "spreadsheet"]


class PublicFeedAdapter(BaseSourceAdapter):
    """
    Public Remote Feeds Adapter — Remotive API (Stage 3).
    Endpoint: https://remotive.com/api/remote-jobs
    Attribution: Powered by Remotive Remote Jobs API (https://remotive.com).

    Strictly filters for genuine contract, freelance, or part-time
    spreadsheet work (full-time corporate vacancies are rejected).
    Salaries on Remotive are usually ANNUAL — they are recorded in
    client_info as context, never misrepresented as a per-gig budget.
    """

    def __init__(self):
        super().__init__(
            source_id="remotive_public_api",
            source_name="Remotive (Permitted Public Remote API)",
            is_enabled=True
        )
        self.feed_url = "https://remotive.com/api/remote-jobs"

    def test_connection(self) -> Dict[str, Any]:
        """Tests live connectivity to Remotive API."""
        try:
            resp = requests.get(f"{self.feed_url}?limit=1", timeout=6)
            if resp.status_code == 200:
                return {
                    "status": "Connected",
                    "message": "Remotive Public API is live and responding.",
                    "healthy": True
                }
            else:
                return {
                    "status": "Warning",
                    "message": f"Remotive API returned HTTP {resp.status_code}",
                    "healthy": False
                }
        except Exception as e:
            return {
                "status": "Temporarily unavailable",
                "message": f"Network exception: {str(e)}",
                "healthy": False
            }

    def fetch_jobs(self, search_terms: List[str], max_results: int = 10) -> List[StandardJob]:
        """
        Fetches live remote jobs matching Excel/spreadsheet terms from Remotive.
        - searches multiple relevant terms (not just "excel")
        - keeps only contract / freelance / part-time engagements
        - applies the strict Excel-tool relevance gate
        - never invents budgets; annual salaries are noted, not scored
        """
        jobs: List[StandardJob] = []
        seen_urls = set()
        self.filtered_count = 0

        terms = [t.strip() for t in (search_terms or []) if t and t.strip()][:2]
        if not terms:
            terms = REMOTIVE_SEARCH_TERMS

        for term in terms:
            if len(jobs) >= max_results:
                break
            try:
                resp = requests.get(
                    self.feed_url, params={"search": term, "limit": 50}, timeout=10
                )
                if resp.status_code != 200:
                    continue

                remote_jobs = resp.json().get("jobs", [])

                for rj in remote_jobs:
                    if len(jobs) >= max_results:
                        break

                    job_type = (rj.get("job_type") or "").lower()

                    # Only contract, freelance, or part-time engagements
                    if job_type in ["full_time", "full-time", "permanent"]:
                        continue
                    if job_type not in ["contract", "freelance", "part_time", "part-time", "contractor"]:
                        continue

                    title = (rj.get("title") or "").strip()
                    desc = (rj.get("description") or "").strip()
                    url = (rj.get("url") or "").strip()
                    if url in seen_urls:
                        continue

                    # Strict Excel / spreadsheet tool relevance
                    if not is_excel_job(title, desc):
                        self.filtered_count += 1
                        continue
                    seen_urls.add(url)

                    company = (rj.get("company_name") or "Remote Employer").strip()
                    raw_salary = (rj.get("salary") or "").strip()
                    pub_date = (
                        (rj.get("publication_date") or "")[:10]
                        or datetime.now().strftime("%Y-%m-%d")
                    )

                    client_desc = f"Company: {company} | Remotive (Type: {job_type})"
                    if raw_salary:
                        # Remotive salaries are typically ANNUAL figures —
                        # record as context, do NOT fake a per-gig budget.
                        client_desc += f" | Stated pay: {raw_salary} (usually annual)"

                    jobs.append(StandardJob(
                        title=title,
                        description=desc[:1500],
                        platform="Remotive (Remote Public Feed)",
                        url=url,
                        budget=0.0,  # never invent a project budget from a salary string
                        currency="INR",
                        date_posted=pub_date,
                        client_info=client_desc,
                        skills_required=["Excel", "Remote Contract"],
                        discovery_source="remotive_public_api",
                        is_sample=0
                    ))

            except Exception:
                continue

        return jobs[:max_results]
