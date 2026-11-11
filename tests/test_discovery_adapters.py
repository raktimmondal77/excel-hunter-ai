import pytest
from src.discovery.base_adapter import StandardJob
from src.discovery.freelancer_adapter import FreelancerAdapter
from src.discovery.upwork_adapter import UpworkManualAdapter
from src.discovery.public_feed_adapter import PublicFeedAdapter

def test_standard_job_to_dict():
    job = StandardJob(
        title="Excel Inventory Dashboard",
        description="Build formulas and slicers",
        platform="Freelancer.com",
        budget=5000.0,
        currency="INR",
        discovery_source="test"
    )
    d = job.to_dict()
    assert d["title"] == "Excel Inventory Dashboard"
    assert d["budget"] == 5000.0
    assert d["platform"] == "Freelancer.com"
    assert "date_posted" in d
    assert d["discovery_source"] == "test"

def test_freelancer_adapter_fallback():
    adapter = FreelancerAdapter(auth_token="")
    conn_info = adapter.test_connection()
    assert conn_info["status"] == "API access pending"

    # Fetch jobs without token returns verified live sample schema
    jobs = adapter.fetch_jobs(["dashboard", "vba"])
    assert len(jobs) >= 2
    assert all(isinstance(j, StandardJob) for j in jobs)
    assert all(j.platform == "Freelancer.com" for j in jobs)

def test_upwork_manual_adapter_parsing():
    adapter = UpworkManualAdapter()
    conn_info = adapter.test_connection()
    assert conn_info["status"] == "Manual"

    raw_text = """Need Senior Excel Developer for MIS Automation
We are looking for someone to automate our daily sales sheet into a summary MIS.
Budget: $100.
Rating: 4.95 of 5 stars from 30 reviews.
"""
    parsed = adapter.parse_upwork_text(raw_text, job_url="https://www.upwork.com/jobs/~01abc")
    assert parsed is not None
    assert "MIS Automation" in parsed.title
    assert parsed.platform == "Upwork"
    assert parsed.budget == 100 * 85.0 # USD to INR conversion
    assert "4.95" in parsed.client_info

def test_public_feed_adapter_connection():
    adapter = PublicFeedAdapter()
    info = adapter.test_connection()
    assert "status" in info
    assert "healthy" in info
