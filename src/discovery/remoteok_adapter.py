import re
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.discovery.base_adapter import BaseSourceAdapter, StandardJob
from src.evaluation import is_excel_job


class RemoteOkAdapter(BaseSourceAdapter):
    """
    RemoteOK Public API Adapter (Stage 3 — NEW SOURCE).
    Endpoint: https://remoteok.com/api
    Attribution: Powered by the RemoteOK public jobs API (https://remoteok.com).

    - One request per scan (courtesy of their free-API terms).
    - Keeps only contract / freelance engagements, or untitled-type posts
      whose title explicitly names Excel.
    - Applies the strict Excel-tool relevance gate.
    - Annual salary figures are recorded as context, never as a gig budget.
    """

    def __init__(self):
        super().__init__(
            source_id="remoteok_public_api",
            source_name="RemoteOK (Public Remote Jobs API)",
            is_enabled=True
        )
        self.api_url = "https://remoteok.com/api"

    def test_connection(self) -> Dict[str, Any]:
        try:
            resp = requests.get(self.api_url, timeout=8, headers=self._headers())
            if resp.status_code == 200:
                return {
                    "status": "Connected",
                    "message": "RemoteOK public API is live and responding.",
                    "healthy": True
                }
            return {
                "status": "Warning",
                "message": f"RemoteOK API returned HTTP {resp.status_code}",
                "healthy": False
            }
        except Exception as e:
            return {
                "status": "Temporarily unavailable",
                "message": f"Network exception: {str(e)}",
                "healthy": False
            }

    @staticmethod
    def _headers() -> Dict[str, str]:
        return {"User-Agent": "ExcelHunterAI/3.0 (freelance job research; attribution to remoteok.com)"}

    def fetch_jobs(self, search_terms: List[str], max_results: int = 10) -> List[StandardJob]:
        jobs: List[StandardJob] = []
        self.filtered_count = 0

        try:
            resp = requests.get(self.api_url, timeout=12, headers=self._headers())
            if resp.status_code != 200:
                return []

            entries = resp.json()
            for entry in entries:
                if len(jobs) >= max_results:
                    break
                if not isinstance(entry, dict) or not entry.get("position"):
                    continue  # skips the legal/notice block at index 0

                title = (entry.get("position") or "").strip()
                desc_html = entry.get("description") or ""
                desc = re.sub(r"<[^>]+>", " ", desc_html)
                desc = re.sub(r"\s+", " ", desc).strip()[:1500]

                # Strict relevance gate (position + tags + cleaned description)
                tags = [str(t) for t in (entry.get("tags") or [])]
                relevance_blob = f"{title} {' '.join(tags)} {desc}"
                if not is_excel_job(title, relevance_blob):
                    self.filtered_count += 1
                    continue

                job_type = (entry.get("type") or "").lower()
                title_names_excel = bool(re.search(r"\bexcel\b|spreadsheet", title, re.IGNORECASE))
                # Accept contract/freelance roles; untyped roles only when the
                # TITLE itself explicitly names Excel/spreadsheets.
                if job_type not in ("contract", "freelance", "part_time", "part-time") \
                        and not (job_type == "" and title_names_excel):
                    self.filtered_count += 1
                    continue
                if job_type in ("full_time", "full-time"):
                    continue

                url = (entry.get("url") or "").strip()
                company = (entry.get("company") or "Remote Employer").strip()
                pub_date = (entry.get("date") or "")[:10] or datetime.now().strftime("%Y-%m-%d")

                salary_min = entry.get("salary_min")
                salary_max = entry.get("salary_max")
                salary_note = ""
                if salary_min or salary_max:
                    try:
                        lo = int(salary_min or 0)
                        hi = int(salary_max or 0)
                        salary_note = f" | Stated pay: ${lo:,}-${hi:,}/yr (annual, not a gig budget)"
                    except (ValueError, TypeError):
                        salary_note = ""

                client_desc = f"Company: {company} | RemoteOK (Type: {job_type or 'unspecified'}" \
                              f"{', contract-friendly' if job_type else ''}){salary_note}"

                jobs.append(StandardJob(
                    title=title,
                    description=desc,
                    platform="RemoteOK (Remote Public Feed)",
                    url=url,
                    budget=0.0,  # salary is annual context, never a fake budget
                    currency="INR",
                    date_posted=pub_date,
                    client_info=client_desc,
                    skills_required=["Excel", "Remote Contract"],
                    discovery_source="remoteok_public_api",
                    is_sample=0
                ))

        except Exception:
            return []

        return jobs[:max_results]
