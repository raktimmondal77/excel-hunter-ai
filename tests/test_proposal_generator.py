import pytest
import src.proposal_generator as pg

def test_detect_primary_category():
    assert pg.detect_primary_category("Interactive Executive KPI Dashboard with Slicers") == "dashboard"
    assert pg.detect_primary_category("Build VBA Macro to automate reporting") == "vba"
    assert pg.detect_primary_category("Monthly MIS Report consolidation sheet") == "mis"
    assert pg.detect_primary_category("Clean up customer list and remove duplicate rows") == "data_cleaning"
    assert pg.detect_primary_category("Repair broken VLOOKUP formula and balance sheet") == "formula"

def test_generate_honest_proposal():
    proposal = pg.generate_honest_proposal(
        job_title="Retail Sales Dashboard with Pivot Tables",
        job_description="Need an Excel specialist to create a dashboard from raw sales CSV",
        platform="Freelancer.com",
        client_name="Alex",
        freelancer_name="Rakesh",
        turnaround_estimate="2 days"
    )

    # Verifications
    assert "Hi Alex," in proposal
    assert "Freelancer.com" in proposal
    assert "Retail Sales Dashboard" in proposal
    assert "2 days" in proposal
    assert "Rakesh" in proposal
    assert "pivot tables and slicers" in proposal.lower()

    # Zero fabrication check: should not claim fake certifications or fake companies
    assert "google certified" not in proposal.lower()
    assert "fortune 500" not in proposal.lower()
