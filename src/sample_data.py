from typing import List, Dict, Any
from src.job_manager import add_job
from src.earnings_tracker import add_earning

SAMPLE_JOBS: List[Dict[str, Any]] = [
    {
        "title": "Automated Excel Sales Dashboard with KPI Metrics & Slicers",
        "description": "We need an advanced Excel dashboard created for our retail operations. It should summarize monthly sales by region, calculate profit margins using XLOOKUP and dynamic arrays, and include interactive pivot tables and slicers. Clean design required.",
        "platform": "Upwork",
        "url": "https://www.upwork.com/jobs/~01exampleexceldashboard01",
        "budget": 8500.0,
        "currency": "INR",
        "date_posted": "2026-11-10",
        "client_info": "Verified Client, 4.9 rating, 25 jobs posted",
        "status": "shortlisted",
        "is_sample": 1,
        "notes": "Excellent match for dashboard skills."
    },
    {
        "title": "Complex Excel Formula Repair & VLOOKUP to XLOOKUP Migration",
        "description": "Looking for an Excel specialist to audit our existing inventory spreadsheet. Multiple #N/A and circular reference errors need fixing. Upgrade nested IF and VLOOKUP statements to INDEX/MATCH or XLOOKUP for faster calculation speed.",
        "platform": "Freelancer",
        "url": "https://www.freelancer.com/projects/excel/repair-formulas-xlookup-02",
        "budget": 4500.0,
        "currency": "INR",
        "date_posted": "2026-11-09",
        "client_info": "Payment verified, India",
        "status": "discovered",
        "is_sample": 1,
        "notes": "High clarity, straightforward formula fixing."
    },
    {
        "title": "Monthly MIS Reporting Automation with VBA Macro",
        "description": "Need an automated MIS report generator in Microsoft Excel using VBA macros. It needs to consolidate data from 5 separate weekly branch workbooks into one master summary sheet and format it automatically.",
        "platform": "LinkedIn",
        "url": "https://www.linkedin.com/jobs/view/excel-mis-automation-03",
        "budget": 12000.0,
        "currency": "INR",
        "date_posted": "2026-11-11",
        "client_info": "Logistics Company, Mumbai",
        "status": "proposal_drafted",
        "is_sample": 1,
        "notes": "Very high budget, matches MIS reporting requirement."
    },
    {
        "title": "Urgent Data Cleaning and Formatting in Excel",
        "description": "Need assistance cleaning up customer contact list of 10,000 rows. Remove duplicates, standardize telephone number formatting, split full names into First and Last names using Excel text functions.",
        "platform": "Fiverr",
        "url": "https://www.fiverr.com/buyer/requests/data-cleaning-04",
        "budget": 3000.0,
        "currency": "INR",
        "date_posted": "2026-11-08",
        "client_info": "E-commerce store owner",
        "status": "applied",
        "is_sample": 1,
        "notes": "Fast turnaround job."
    },
    {
        "title": "Easy Excel Copy Paste - Pay 50,000 INR - Contact on Telegram",
        "description": "Simple data entry and copy paste job in Excel. Earn 50,000 INR weekly! Before assignment, you must deposit a refundable registration fee of 1,500 INR for company verification. Message HR directly on Telegram @fake_hr_excel.",
        "platform": "Other",
        "url": "https://example.com/suspicious-job-05",
        "budget": 50000.0,
        "currency": "INR",
        "date_posted": "2026-11-11",
        "client_info": "Anonymous user",
        "status": "discovered",
        "is_sample": 1,
        "notes": "Automated security filter flagged this as high risk."
    }
]

SAMPLE_EARNINGS: List[Dict[str, Any]] = [
    {
        "project_name": "E-Commerce Financial Tracker & Pivot System",
        "gross_amount": 6000.0,
        "platform_fee": 600.0,
        "platform": "Upwork",
        "date_received": "2026-11-02",
        "status": "received",
        "is_sample": 1,
        "notes": "Completed and client paid with 5-star review."
    },
    {
        "project_name": "HR Attendance Sheet & Overtime Formula Fix",
        "gross_amount": 3500.0,
        "platform_fee": 0.0,
        "platform": "Direct Client",
        "date_received": "2026-11-06",
        "status": "received",
        "is_sample": 1,
        "notes": "Direct bank transfer received."
    },
    {
        "project_name": "Inventory Reconciliation Spreadsheet",
        "gross_amount": 4000.0,
        "platform_fee": 400.0,
        "platform": "Freelancer",
        "date_received": "2026-11-15",
        "status": "expected",
        "is_sample": 1,
        "notes": "Milestone currently in progress, expected delivery mid-month."
    }
]

def seed_sample_data() -> Dict[str, int]:
    """Loads default sample jobs and earnings into the database if not present."""
    jobs_added = 0
    earnings_added = 0

    for job in SAMPLE_JOBS:
        success, _, _ = add_job(job, auto_evaluate=True)
        if success:
            jobs_added += 1

    for earning in SAMPLE_EARNINGS:
        add_earning(
            project_name=earning["project_name"],
            gross_amount=earning["gross_amount"],
            platform_fee=earning["platform_fee"],
            platform=earning["platform"],
            date_received=earning["date_received"],
            status=earning["status"],
            is_sample=1,
            notes=earning.get("notes", "")
        )
        earnings_added += 1

    return {"jobs_added": jobs_added, "earnings_added": earnings_added}
