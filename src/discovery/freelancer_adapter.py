import os
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from src.discovery.base_adapter import BaseSourceAdapter, StandardJob
from src.evaluation import is_excel_job
from src.currency import to_inr, format_inr

# Curated high-signal queries for the Freelancer search API. The API's
# `query` parameter is fuzzy (it happily returns marketing or SEO posts),
# so results are ALWAYS post-filtered with the strict Excel relevance gate.
DEFAULT_QUERIES = ["excel", "excel vba", "spreadsheet", "excel dashboard"]

# Only projects submitted within this window are imported (fresh leads only).
MAX_AGE_DAYS = 7


class FreelancerAdapter(BaseSourceAdapter):
    """
    Official Freelancer.com REST API Adapter — Stage 3.

    Uses official endpoint: https://www.freelancer.com/api/projects/0.1/projects/active/
    Read-only project discovery compliant with Freelancer Developer Terms.
    No scraping, no automated bidding. Never inserts fake projects.

    Stage 3 improvements over Stage 2:
    - Searches MULTIPLE high-signal queries instead of only the first term.
    - Filters results to the last 7 days (from_time) so only fresh leads land.
    - Applies the strict Excel-relevance gate (junk like "Marketing associates
      recruitment" or "SaaS SEO" is rejected client-side).
    - Converts every budget to INR and keeps the original in client_info.
    - Extracts real client-credibility signals (escrow, featured, urgent, bids).
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
        headers = {"User-Agent": "ExcelHunterAI/3.0"}
        if self.auth_token:
            headers["Freelancer-Developer-Auth-V1"] = self.auth_token

        try:
            resp = requests.get(
                f"{self.api_url}?compact=true&limit=1&query=excel",
                headers=headers, timeout=6
            )
            if resp.status_code == 200:
                auth_mode = "Authorized Token" if self.auth_token else "Public Read-Only"
                return {
                    "status": "Connected",
                    "message": f"Freelancer REST API is responding ({auth_mode}).",
                    "healthy": True
                }
            elif resp.status_code in (401, 403):
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

    def fetch_jobs(self, search_terms: List[str], max_results: int = 20) -> List[StandardJob]:
        """
        Fetches genuine, FRESH, Excel-relevant active projects from the
        Freelancer API. Never returns simulated or fake fallback data.
        If the call fails or nothing relevant is found, returns [].
        """
        jobs: List[StandardJob] = []
        seen_ids = set()
        self.filtered_count = 0  # junk rejected this fetch (for the scan report)

        headers = {"User-Agent": "ExcelHunterAI/3.0"}
        if self.auth_token:
            headers["Freelancer-Developer-Auth-V1"] = self.auth_token

        # Build the query list: prefer caller-provided terms, fall back to curated
        if search_terms:
            queries = [t.strip() for t in search_terms if t and t.strip()][:4]
        else:
            queries = DEFAULT_QUERIES
        if not queries:
            queries = DEFAULT_QUERIES

        from_time = int((datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)).timestamp())

        for query_kw in queries:
            if len(jobs) >= max_results:
                break

            params = {
                "query": query_kw,
                "compact": "true",
                "limit": min(max_results, 20),
                "from_time": from_time,     # fresh projects only
                "sort": "latest",           # newest first
            }

            try:
                resp = requests.get(self.api_url, headers=headers, params=params, timeout=10)
                if resp.status_code != 200:
                    continue

                projects = resp.json().get("result", {}).get("projects", [])

                for p in projects:
                    if len(jobs) >= max_results:
                        break

                    proj_id = p.get("id")
                    if proj_id in seen_ids:
                        continue

                    title = (p.get("title") or "").strip()
                    if not title:
                        continue

                    desc = (p.get("preview_description") or p.get("description") or "").strip()

                    # ---- Filter out locked / deposit-gated projects ----
                    upgrades = p.get("upgrades", {}) or {}
                    if (
                        upgrades.get("featured") or upgrades.get("sealed") or
                        upgrades.get("nonpublic") or upgrades.get("NDA") or
                        upgrades.get("pf_only") or p.get("featured")
                    ):
                        seen_ids.add(proj_id)
                        self.filtered_count += 1
                        continue

                    # ---- STRICT Excel relevance gate (kills fuzzy junk) ----
                    if not is_excel_job(title, desc):
                        seen_ids.add(proj_id)
                        self.filtered_count += 1
                        continue
                    seen_ids.add(proj_id)

                    seo_url = p.get("seo_url")
                    url = (
                        f"https://www.freelancer.com/projects/{seo_url}"
                        if seo_url else f"https://www.freelancer.com/projects/{proj_id}"
                    )

                    # ---- Budget: average of min/max, converted to INR ----
                    budget_info = p.get("budget", {}) or {}
                    minimum = float(budget_info.get("minimum") or 0)
                    maximum = float(budget_info.get("maximum") or 0)
                    if minimum and maximum:
                        raw_budget = (minimum + maximum) / 2.0
                    elif minimum:
                        raw_budget = minimum
                    elif maximum:
                        raw_budget = maximum
                    else:
                        raw_budget = 0.0

                    currency_code = (p.get("currency", {}) or {}).get("code", "INR") or "INR"
                    budget_inr = to_inr(raw_budget, currency_code)

                    # ---- Real client credibility signals ----
                    signals = ["Freelancer.com client"]
                    if p.get("is_escrow_project"):
                        signals.append("Escrow funded")
                    if p.get("featured"):
                        signals.append("Featured listing")
                    if p.get("urgent"):
                        signals.append("Urgent")
                    bid_count = (p.get("bid_stats", {}) or {}).get("bid_count")
                    if bid_count is not None:
                        signals.append(f"{bid_count} bids so far")
                    if raw_budget > 0 and currency_code != "INR":
                        signals.append(f"Original budget: {raw_budget:,.0f} {currency_code}")
                    client_desc = " | ".join(signals)

                    time_submitted = p.get("time_submitted")
                    if time_submitted:
                        try:
                            date_posted = datetime.fromtimestamp(
                                time_submitted, tz=timezone.utc
                            ).strftime("%Y-%m-%d")
                        except (ValueError, OSError, OverflowError):
                            date_posted = datetime.now().strftime("%Y-%m-%d")
                    else:
                        date_posted = datetime.now().strftime("%Y-%m-%d")

                    jobs.append(StandardJob(
                        title=title,
                        description=desc,
                        platform="Freelancer.com",
                        url=url,
                        budget=budget_inr,          # INR-normalized
                        currency="INR",
                        date_posted=date_posted,
                        client_info=client_desc,
                        skills_required=["Excel"],
                        discovery_source="freelancer_api",
                        is_sample=0  # 100% genuine live project
                    ))

            except Exception:
                # Fault-tolerant per query: try the next term
                continue

        return jobs
