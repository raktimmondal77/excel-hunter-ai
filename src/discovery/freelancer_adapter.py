import os
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.discovery.base_adapter import BaseSourceAdapter, StandardJob

class FreelancerAdapter(BaseSourceAdapter):
    """
    Official Freelancer.com REST API Adapter.
    Uses official endpoint: https://www.freelancer.com/api/projects/0.1/projects/active/
    Read-only project discovery compliant with Freelancer Developer Terms.
    No scraping, no automated bidding.
    Never inserts fake or demonstration projects.
    """

    def __init__(self, auth_token: Optional[str] = None):
        super().__init__(
            source_id="freelancer_api",
            source_name="Freelancer.com (Official API)",
            is_enabled=True
        )
        self.auth_token = auth_token or os.environ.get("FREELANCER_DEV_TOKEN", "").strip()
        self.api_url = "https://www.freelancer.com/api/projects/0.1/projects/active/"

    def test_connection(self) -> Dict[str, Any]:
        """Tests connectivity to official Freelancer API."""
        headers = {"User-Agent": "ExcelHunterAI/2.5"}
        if self.auth_token:
            headers["Freelancer-Developer-Auth-V1"] = self.auth_token

        try:
            resp = requests.get(f"{self.api_url}?compact=true&limit=1&query=excel", headers=headers, timeout=6)
            if resp.status_code == 200:
                auth_mode = "Authorized Token" if self.auth_token else "Public Read-Only"
                return {
                    "status": "Connected",
                    "message": f"Freelancer REST API is responding ({auth_mode}).",
                    "healthy": True
                }
            elif resp.status_code == 401 or resp.status_code == 403:
                return {
                    "status": "Not Connected",
                    "message": "Authentication required. Generate a free developer token at https://www.freelancer.com/developers",
                    "healthy": False
                }
            else:
                return {
                    "status": "Not Connected",
                    "message": f"HTTP {resp.status_code}: {resp.text[:100]}",
                    "healthy": False
                }
        except Exception as e:
            return {
                "status": "Not Connected",
                "message": f"Network exception: {str(e)}",
                "healthy": False
            }

    def fetch_jobs(self, search_terms: List[str], max_results: int = 10) -> List[StandardJob]:
        """
        Fetches genuine active Excel projects from Freelancer API.
        Never returns simulated or fake fallback data. If no projects exist or call fails, returns [].
        """
        jobs: List[StandardJob] = []

        headers = {"User-Agent": "ExcelHunterAI/2.5"}
        if self.auth_token:
            headers["Freelancer-Developer-Auth-V1"] = self.auth_token

        # Use clean search terms (e.g. "Excel", "Excel VBA", "Excel spreadsheet")
        query_kw = search_terms[0] if search_terms else "excel"
        params = {
            "query": query_kw,
            "compact": "true",
            "limit": min(max_results, 20)
        }

        try:
            resp = requests.get(self.api_url, headers=headers, params=params, timeout=10)
            if resp.status_code != 200:
                return []

            data = resp.json()
            projects = data.get("result", {}).get("projects", [])

            for p in projects:
                title = (p.get("title") or "").strip()
                if not title:
                    continue

                desc = (p.get("preview_description") or p.get("description") or "").strip()
                proj_id = p.get("id")
                seo_url = p.get("seo_url")
                url = f"https://www.freelancer.com/projects/{seo_url}" if seo_url else f"https://www.freelancer.com/projects/{proj_id}"
                
                budget_info = p.get("budget", {})
                minimum = budget_info.get("minimum", 0)
                maximum = budget_info.get("maximum", 0)
                
                # Real budget calculation without inventing missing values
                if minimum and maximum:
                    avg_budget = (float(minimum) + float(maximum)) / 2.0
                elif minimum:
                    avg_budget = float(minimum)
                elif maximum:
                    avg_budget = float(maximum)
                else:
                    avg_budget = 0.0

                currency = p.get("currency", {}).get("code", "INR")
                time_submitted = p.get("time_submitted")
                date_posted = datetime.fromtimestamp(time_submitted).strftime("%Y-%m-%d") if time_submitted else datetime.now().strftime("%Y-%m-%d")

                jobs.append(StandardJob(
                    title=title,
                    description=desc,
                    platform="Freelancer.com",
                    url=url,
                    budget=avg_budget,
                    currency=currency,
                    date_posted=date_posted,
                    client_info="Freelancer Client",
                    skills_required=["Excel", "Data Processing"],
                    discovery_source="freelancer_api",
                    is_sample=0 # 100% Genuine live project
                ))

            return jobs
        except Exception:
            return []
