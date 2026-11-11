import re
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.discovery.base_adapter import BaseSourceAdapter, StandardJob
from src.evaluation import is_excel_job

# Jobicy exposes a free public API with tag search. The tag match is fuzzy,
# so results are always post-filtered with the strict relevance gate.
JOBICY_ACCEPTED_TYPES = {"contract", "freelance", "part-time", "part_time"}


def strip_html(text: str) -> str:
    """Removes HTML tags and collapses whitespace (no space before punctuation)."""
    if not text:
        return ""
    cleaned = re.sub(r"<[^>]+>", " ", str(text))
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # squeeze spaces that tags introduced before punctuation: "world !" -> "world!"
    cleaned = re.sub(r"\s+([,.!?;:%])", r"\1", cleaned)
    return cleaned


class JobicyAdapter(BaseSourceAdapter):
    """
    Jobicy Public Remote Jobs API Adapter (Stage 3 — NEW SOURCE).
    Endpoint: https://jobicy.com/api/v2/remote-jobs?tag=excel
    Attribution: Powered by the Jobicy public remote jobs API (https://jobicy.com).

    - Free, no API key, official public API.
    - Keeps only Contract / Freelance / Part-time engagements.
    - Applies the strict Excel-tool relevance gate.
    - Annual salary fields are recorded as context, never as a gig budget.
    """

    def __init__(self):
        super().__init__(
            source_id="jobicy_public_api",
            source_name="Jobicy (Public Remote Jobs API)",
            is_enabled=True
        )
        self.api_url = "https://jobicy.com/api/v2/remote-jobs"

    def test_connection(self) -> Dict[str, Any]:
        try:
            resp = requests.get(
                self.api_url, params={"tag": "excel", "count": 1}, timeout=8,
                headers={"User-Agent": "ExcelHunterAI/3.0"}
            )
            if resp.status_code == 200:
                return {
                    "status": "Connected",
                    "message": "Jobicy public API is live and responding.",
                    "healthy": True
                }
            return {
                "status": "Warning",
                "message": f"Jobicy API returned HTTP {resp.status_code}",
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
        seen_urls = set()
        self.filtered_count = 0

        try:
            resp = requests.get(
                self.api_url,
                params={"tag": "excel", "count": 50},
                timeout=12,
                headers={"User-Agent": "ExcelHunterAI/3.0"}
            )
            if resp.status_code != 200:
                return []

            entries = resp.json().get("jobs", [])

            for entry in entries:
                if len(jobs) >= max_results:
                    break

                title = (entry.get("jobTitle") or "").strip()
                desc = strip_html(entry.get("jobDescription") or entry.get("jobExcerpt") or "")[:1500]
                url = (entry.get("url") or "").strip()
                if not title or url in seen_urls:
                    continue

                # Job types arrive as a list e.g. ['Contract']
                raw_types = entry.get("jobType") or []
                if isinstance(raw_types, str):
                    raw_types = [raw_types]
                types_lower = {str(t).strip().lower() for t in raw_types if t}

                # Only contract / freelance / part-time engagements
                if types_lower and not (types_lower & JOBICY_ACCEPTED_TYPES):
                    continue
                if not types_lower and "full-time" in (entry.get("jobExcerpt") or "").lower():
                    continue

                # Strict Excel-tool relevance gate
                if not is_excel_job(title, desc):
                    self.filtered_count += 1
                    continue
                seen_urls.add(url)

                company = (entry.get("companyName") or "Remote Employer").strip()
                pub_date = (entry.get("pubDate") or "")[:10] or datetime.now().strftime("%Y-%m-%d")

                salary_note = ""
                salary_min = entry.get("salaryMin")
                salary_max = entry.get("salaryMax")
                if salary_min or salary_max:
                    try:
                        lo = int(float(salary_min or 0))
                        hi = int(float(salary_max or 0))
                        salary_note = f" | Stated pay: ${lo:,}-${hi:,}/yr (annual, not a gig budget)"
                    except (ValueError, TypeError):
                        salary_note = ""

                type_str = "/".join(sorted(types_lower)) if types_lower else "unspecified"
                client_desc = f"Company: {company} | Jobicy (Type: {type_str}){salary_note}"

                jobs.append(StandardJob(
                    title=title,
                    description=desc,
                    platform="Jobicy (Remote Public Feed)",
                    url=url,
                    budget=0.0,
                    currency="INR",
                    date_posted=pub_date,
                    client_info=client_desc,
                    skills_required=["Excel", "Remote Contract"],
                    discovery_source="jobicy_public_api",
                    is_sample=0
                ))

        except Exception:
            return []

        return jobs[:max_results]
