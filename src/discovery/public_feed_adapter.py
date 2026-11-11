import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.discovery.base_adapter import BaseSourceAdapter, StandardJob

class PublicFeedAdapter(BaseSourceAdapter):
    """
    Public Remote Feeds Adapter.
    Pulls legitimate public remote job listings from permitted public feeds
    (e.g., Remotive Public API: https://remotive.com/api/remote-jobs?search=excel).
    Free, zero API key needed, permitted terms.
    """

    def __init__(self):
        super().__init__(
            source_id="public_feed",
            source_name="Permitted Public Remote Feeds (Remotive/Open)",
            is_enabled=True
        )
        self.feed_url = "https://remotive.com/api/remote-jobs"

    def test_connection(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.feed_url}?limit=1", timeout=5)
            if resp.status_code == 200:
                return {"status": "Connected", "message": "Public remote job feed is online.", "healthy": True}
            else:
                return {"status": "Warning", "message": f"Feed returned HTTP {resp.status_code}", "healthy": False}
        except Exception as e:
            return {"status": "Temporarily unavailable", "message": str(e), "healthy": False}

    def fetch_jobs(self, search_terms: List[str], max_results: int = 10) -> List[StandardJob]:
        jobs: List[StandardJob] = []
        try:
            resp = requests.get(f"{self.feed_url}?search=excel&limit={max_results}", timeout=8)
            if resp.status_code != 200:
                return []

            data = resp.json()
            remote_jobs = data.get("jobs", [])

            for rj in remote_jobs:
                title = rj.get("title", "")
                desc = rj.get("description", "")
                url = rj.get("url", "")
                company = rj.get("company_name", "Remote Employer")
                salary = rj.get("salary", "")
                pub_date = rj.get("publication_date", "")[:10] if rj.get("publication_date") else datetime.now().strftime("%Y-%m-%d")

                # Only include jobs that are relevant to Excel or Spreadsheets
                if not any(term in (title + " " + desc).lower() for term in ["excel", "spreadsheet", "reporting", "dashboard", "data"]):
                    continue

                jobs.append(StandardJob(
                    title=title,
                    description=desc[:1500], # Store clean excerpt
                    platform="Public Remote Feed",
                    url=url,
                    budget=12000.0 if "contract" in (title + desc).lower() else 8000.0,
                    currency="INR",
                    date_posted=pub_date,
                    client_info=f"Company: {company}",
                    skills_required=["Excel", "Reporting", "Analytics"],
                    discovery_source="public_feed"
                ))

            return jobs[:max_results]
        except Exception:
            # Gracefully return empty list on network or parse error
            return []
