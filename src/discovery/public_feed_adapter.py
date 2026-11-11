import re
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.discovery.base_adapter import BaseSourceAdapter, StandardJob

# Pattern distinguishing actual Microsoft Excel spreadsheet work from generic verb "excel"
EXCEL_TOOL_PATTERN = re.compile(
    r"\b(microsoft\s+excel|ms\s+excel|advanced\s+excel|excel\s+(?:dashboard|formula|sheet|file|vba|macro|tracker|model|reporting)|spreadsheet|spreadsheets|google\s+sheets|pivot\s+tables?|vba|xlookup|vlookup|mis\s+report)\b",
    re.I
)

class PublicFeedAdapter(BaseSourceAdapter):
    """
    Public Remote Feeds Adapter — Remotive API.
    Endpoint: https://remotive.com/api/remote-jobs
    Attribution: Powered by Remotive Remote Jobs API (https://remotive.com).
    Strictly filters for genuine contract, freelance, or part-time Excel spreadsheet work.
    Rejects full-time corporate employment vacancies to prevent misrepresentation.
    Never invents missing salary/budget figures.
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
        Fetches live remote jobs matching Excel/spreadsheet terms from Remotive API.
        Filters strictly for freelance, contract, or part-time work.
        Rejects full-time employment vacancies.
        Rejects listings where 'excel' is merely used as a generic verb.
        """
        jobs: List[StandardJob] = []

        try:
            resp = requests.get(f"{self.feed_url}?search=excel&limit=30", timeout=10)
            if resp.status_code != 200:
                return []

            data = resp.json()
            remote_jobs = data.get("jobs", [])

            for rj in remote_jobs:
                job_type = (rj.get("job_type") or "").lower()
                
                # Exclude full-time permanent corporate employment
                if job_type in ["full_time", "full-time", "permanent"]:
                    continue

                # Must be contract, freelance, or part-time
                if job_type not in ["contract", "freelance", "part_time", "part-time", "contractor"]:
                    continue

                title = (rj.get("title") or "").strip()
                desc = (rj.get("description") or "").strip()
                company = (rj.get("company_name") or "Remote Employer").strip()
                url = (rj.get("url") or "").strip()
                raw_salary = (rj.get("salary") or "").strip()
                pub_date = rj.get("publication_date", "")[:10] if rj.get("publication_date") else datetime.now().strftime("%Y-%m-%d")

                # Verify actual Excel / spreadsheet tool requirement (not generic verb)
                text_corpus = f"{title} {desc}".lower()
                if not EXCEL_TOOL_PATTERN.search(text_corpus):
                    continue

                # Parse actual numeric budget/salary if available without inventing figures
                budget_val = 0.0
                currency = "INR"

                if raw_salary:
                    num_match = re.search(r"(\$|₹|inr|usd|€|£)?\s*([\d,]+)", raw_salary)
                    if num_match:
                        raw_num = float(num_match.group(2).replace(",", ""))
                        curr_symbol = num_match.group(1) or "$"
                        if "$" in curr_symbol or "usd" in curr_symbol.lower():
                            budget_val = raw_num * 85.0 # USD to INR
                        else:
                            budget_val = raw_num

                client_desc = f"Company: {company} | Remotive Source (Type: {job_type})"
                if raw_salary:
                    client_desc += f" | Stated Pay: {raw_salary}"

                jobs.append(StandardJob(
                    title=title,
                    description=desc[:1500],
                    platform="Remotive (Remote Public Feed)",
                    url=url,
                    budget=budget_val, # Real parsed amount or 0.0 (Unstated)
                    currency=currency,
                    date_posted=pub_date,
                    client_info=client_desc,
                    skills_required=["Excel", "Remote Contract"],
                    discovery_source="remotive_public_api",
                    is_sample=0 # Real data
                ))

            return jobs[:max_results]
        except Exception:
            return []
