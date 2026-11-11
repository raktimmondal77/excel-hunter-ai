"""Stage 3 tests — the three NEW public-source adapters (RemoteOK, Jobicy,
Working Nomads). HTTP calls are monkeypatched with canned payloads so the
tests run offline and deterministically."""
import pytest
from src.discovery.remoteok_adapter import RemoteOkAdapter
from src.discovery.jobicy_adapter import JobicyAdapter, strip_html
from src.discovery.workingnomads_adapter import WorkingNomadsAdapter


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


# ---------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------
def test_strip_html():
    assert strip_html("<p>Hello <b>world</b>!</p>") == "Hello world!"
    assert strip_html("  A\n  B  ") == "A B"
    assert strip_html("") == ""


# ---------------------------------------------------------------
# RemoteOK
# ---------------------------------------------------------------
REMOTEOK_PAYLOAD = [
    {"legal": "Usage terms notice — must be skipped"},
    {
        "position": "Excel Data Analyst (Contract)",
        "company": "Acme Corp",
        "url": "https://remoteok.com/remote-jobs/excel-analyst-1",
        "description": "<p>Advanced <b>Excel</b> dashboards, pivot tables and spreadsheet automation.</p>",
        "tags": ["excel", "data"],
        "type": "contract",
        "date": "2026-11-10T00:00:00+00:00",
        "salary_min": 90000,
        "salary_max": 110000,
    },
    {
        "position": "Senior React Developer",   # junk: not Excel
        "company": "Beta LLC",
        "url": "https://remoteok.com/remote-jobs/react-dev-2",
        "description": "<p>React, TypeScript, Node.js frontend engineering.</p>",
        "tags": ["react", "frontend"],
        "type": "full_time",
        "date": "2026-11-10T00:00:00+00:00",
    },
    {
        "position": "Full-time Accountant",      # full-time → rejected
        "company": "Gamma Inc",
        "url": "https://remoteok.com/remote-jobs/accountant-3",
        "description": "<p>Accounting with Excel spreadsheets and reconciliation.</p>",
        "tags": ["excel", "accounting"],
        "type": "full_time",
        "date": "2026-11-10T00:00:00+00:00",
    },
]


def test_remoteok_filters_junk_and_full_time(monkeypatch):
    adapter = RemoteOkAdapter()
    monkeypatch.setattr(
        "src.discovery.remoteok_adapter.requests.get",
        lambda *a, **k: FakeResponse(REMOTEOK_PAYLOAD)
    )
    jobs = adapter.fetch_jobs(["excel"], max_results=10)

    assert len(jobs) == 1
    job = jobs[0]
    assert "Excel Data Analyst" in job.title
    assert job.platform == "RemoteOK (Remote Public Feed)"
    assert job.budget == 0.0  # annual salary never fakes a gig budget
    assert "annual" in job.client_info
    assert job.date_posted == "2026-11-10"
    assert job.is_sample == 0


def test_remoteok_network_failure_returns_empty(monkeypatch):
    def boom(*a, **k):
        raise ConnectionError("network down")

    adapter = RemoteOkAdapter()
    monkeypatch.setattr("src.discovery.remoteok_adapter.requests.get", boom)
    assert adapter.fetch_jobs(["excel"]) == []


# ---------------------------------------------------------------
# Jobicy
# ---------------------------------------------------------------
JOBICY_PAYLOAD = {
    "jobs": [
        {
            "id": 101,
            "url": "https://jobicy.com/jobs/excel-reporting-specialist",
            "jobTitle": "Excel Reporting Specialist (Contract)",
            "companyName": "Delta Data",
            "jobType": ["Contract"],
            "jobExcerpt": "Excel reporting and spreadsheet automation for finance teams.",
            "jobDescription": "<p>Build <b>Excel</b> reports and maintain spreadsheets.</p>",
            "pubDate": "2026-11-09T10:00:00+00:00",
            "salaryMin": 60000,
            "salaryMax": 80000,
        },
        {
            "id": 102,
            "url": "https://jobicy.com/jobs/fulltime-devops",
            "jobTitle": "Senior DevOps Engineer",          # not Excel → rejected
            "companyName": "Epsilon",
            "jobType": ["Full-time"],
            "jobExcerpt": "Kubernetes and cloud infrastructure.",
            "jobDescription": "<p>DevOps all day.</p>",
            "pubDate": "2026-11-09T10:00:00+00:00",
        },
        {
            "id": 103,
            "url": "https://jobicy.com/jobs/mis-manager",
            "jobTitle": "MIS Reporting Manager",           # full-time → rejected
            "companyName": "Zeta Corp",
            "jobType": ["Full-time"],
            "jobExcerpt": "MIS reports in Excel for management.",
            "jobDescription": "<p>Excel MIS reporting, full time role.</p>",
            "pubDate": "2026-11-09T10:00:00+00:00",
        },
    ]
}


def test_jobicy_keeps_only_excel_contracts(monkeypatch):
    adapter = JobicyAdapter()
    monkeypatch.setattr(
        "src.discovery.jobicy_adapter.requests.get",
        lambda *a, **k: FakeResponse(JOBICY_PAYLOAD)
    )
    jobs = adapter.fetch_jobs(["excel"], max_results=10)

    assert len(jobs) == 1
    job = jobs[0]
    assert "Excel Reporting Specialist" in job.title
    assert "<" not in job.description          # HTML stripped
    assert job.budget == 0.0
    assert "Jobicy" in job.client_info


def test_jobicy_http_error_returns_empty(monkeypatch):
    adapter = JobicyAdapter()
    monkeypatch.setattr(
        "src.discovery.jobicy_adapter.requests.get",
        lambda *a, **k: FakeResponse({}, status_code=500)
    )
    assert adapter.fetch_jobs(["excel"]) == []


# ---------------------------------------------------------------
# Working Nomads
# ---------------------------------------------------------------
WORKINGNOMADS_PAYLOAD = [
    {
        "title": "Freelance Excel Automation Expert",
        "url": "https://www.workingnomads.com/jobs/excel-automation-expert",
        "description": "<p>Automate reporting with <b>Excel</b> VBA macros, contract position.</p>",
        "company_name": "Eta Analytics",
        "category_name": "Data",
        "tags": ["excel", "automation"],
        "pub_date": "2026-11-08T00:00:00+00:00",
    },
    {
        "title": "Remote Customer Service Representative",
        "url": "https://www.workingnomads.com/jobs/customer-service",
        "description": "<p>Answer tickets; candidates who excel at empathy wanted. Full-time.</p>",
        "company_name": "Theta Support",
        "category_name": "Customer Success",
        "tags": ["support"],
        "pub_date": "2026-11-08T00:00:00+00:00",
    },
    {
        "title": "Senior Java Backend Engineer",       # not Excel → rejected
        "url": "https://www.workingnomads.com/jobs/java-engineer",
        "description": "<p>Java microservices, freelance contract.</p>",
        "company_name": "Iota Systems",
        "category_name": "Development",
        "tags": ["java"],
        "pub_date": "2026-11-08T00:00:00+00:00",
    },
]


def test_workingnomads_keeps_excel_contracts_only(monkeypatch):
    adapter = WorkingNomadsAdapter()
    monkeypatch.setattr(
        "src.discovery.workingnomads_adapter.requests.get",
        lambda *a, **k: FakeResponse(WORKINGNOMADS_PAYLOAD)
    )
    jobs = adapter.fetch_jobs(["excel"], max_results=10)

    assert len(jobs) == 1
    job = jobs[0]
    assert "Excel Automation Expert" in job.title
    assert job.budget == 0.0
    assert "Working Nomads" in job.client_info


def test_workingnomads_exception_returns_empty(monkeypatch):
    def boom(*a, **k):
        raise TimeoutError("timeout")

    adapter = WorkingNomadsAdapter()
    monkeypatch.setattr("src.discovery.workingnomads_adapter.requests.get", boom)
    assert adapter.fetch_jobs(["excel"]) == []


# ---------------------------------------------------------------
# Proposal pricing block (Stage 3)
# ---------------------------------------------------------------
def test_proposal_includes_pricing_when_provided(tmp_path, monkeypatch):
    from src.db import init_db, get_connection
    import src.user_profile as up
    import src.proposal_intelligence as pi

    db_file = tmp_path / "proposal.db"
    init_db(db_file)
    monkeypatch.setattr(up, "get_connection", lambda: get_connection(db_file))

    job = {
        "title": "Excel Sales Dashboard",
        "description": "Build a KPI Excel dashboard from our sales spreadsheet.",
        "platform": "Upwork",
    }
    pricing = {"final_quotation_inr": 4200.0, "delivery_time_recommendation": "2-3 days"}

    proposals = pi.generate_three_proposal_versions(
        job, client_name="Ravi", freelancer_name="Test User", pricing_info=pricing
    )
    for key in ("version_a", "version_b", "version_c"):
        assert "₹4,200" in proposals[key], f"{key} missing the quote"
        assert "2-3 days" in proposals[key], f"{key} missing the timeline"


def test_proposal_without_pricing_has_no_fake_numbers(tmp_path, monkeypatch):
    from src.db import init_db, get_connection
    import src.user_profile as up
    import src.proposal_intelligence as pi

    db_file = tmp_path / "proposal2.db"
    init_db(db_file)
    monkeypatch.setattr(up, "get_connection", lambda: get_connection(db_file))

    job = {
        "title": "Excel Data Cleaning",
        "description": "Clean and deduplicate our customer spreadsheet.",
        "platform": "Fiverr",
    }
    proposals = pi.generate_three_proposal_versions(job, client_name="Anna")
    for key in ("version_a", "version_b", "version_c"):
        assert "₹" not in proposals[key], f"{key} must not contain invented prices"
