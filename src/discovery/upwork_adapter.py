import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.discovery.base_adapter import BaseSourceAdapter, StandardJob
from src.currency import to_inr, normalize_currency_code

class UpworkManualAdapter(BaseSourceAdapter):
    """
    Upwork Compliant Adapter.
    Upwork Developer API requires organizational enterprise vetting and explicitly
    restricts automated public job searches for individual accounts.
    To maintain 100% compliance with Upwork Terms of Service:
    - Zero bot scraping or automated page scraping.
    - Supports manual job URL ingestion and alert text parsing.
    """

    def __init__(self):
        super().__init__(
            source_id="upwork_manual",
            source_name="Upwork (Manual & Alert Ingestion)",
            is_enabled=True
        )

    def test_connection(self) -> Dict[str, Any]:
        return {
            "status": "Manual",
            "message": "Compliant manual ingestion active. Upwork prohibits unauthorized scrapers.",
            "healthy": True
        }

    def fetch_jobs(self, search_terms: List[str], max_results: int = 10) -> List[StandardJob]:
        # Upwork does not permit unattended bot scraping; active jobs are imported via manual URL or alerts.
        return []

    def parse_upwork_text(self, text: str, job_url: str = "") -> Optional[StandardJob]:
        """
        Parses manually pasted Upwork job brief or email notification text.
        Extracts budget, client rating, and key descriptions cleanly.
        """
        if not text or len(text.strip()) < 10:
            return None

        lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
        title = lines[0] if lines else "Upwork Excel Opportunity"
        
        # Extract budget if present in text (e.g. "$50", "₹5,000", "Fixed-price: $100")
        budget_match = re.search(r"(\$|₹|rs\.?|inr|usd|eur|gbp)\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
        budget_val = 0.0
        currency = "INR"

        if budget_match:
            symbol = budget_match.group(1).lower()
            raw_amount = float(budget_match.group(2).replace(",", ""))
            code = normalize_currency_code(symbol)
            budget_val = to_inr(raw_amount, code)  # always stored in INR

        # Check for client rating
        client_info = "Upwork Client"
        rating_match = re.search(r"(Rating:\s*[\d\.]+|[\d\.]+\s*of\s*5\s*stars)", text, re.IGNORECASE)
        if rating_match:
            client_info = f"Upwork Client ({rating_match.group(1)})"

        return StandardJob(
            title=title[:120],
            description=text,
            platform="Upwork",
            url=job_url.strip() if job_url else "https://www.upwork.com",
            budget=budget_val,
            currency=currency,
            date_posted=datetime.now().strftime("%Y-%m-%d"),
            client_info=client_info,
            discovery_source="upwork_manual"
        )
