# 🎯 EXCEL HUNTER AI — Stage 2: Job Discovery Engine & Multi-Platform Manager

> **A Zero-Cost, Windows-Based Excel Freelance Job Hunting Assistant**  
> Target Monthly Income: **₹10,000 – ₹20,000** | Budget: **₹0** (No paid APIs or recurring subscriptions)

---

## 📌 1. Project Overview

**EXCEL HUNTER AI** is built specifically for Excel freelancers seeking legitimate client contracts in:
- **Excel Dashboards & KPI Summaries**
- **Excel Automation & VBA Macros**
- **Advanced Formulas (XLOOKUP, INDEX/MATCH, Dynamic Arrays)**
- **MIS & Executive Reporting**
- **Data Cleaning & Deduplication**
- **Spreadsheet Formatting & Templates**
- **Excel Trackers (Inventory, Attendance, Budget)**
- **Business & Operations Reporting**
- **Custom Excel Workflow Systems**

### Stage 2 Capabilities:
- **Modular Job Discovery Engine**: Scans active sources (Freelancer.com REST API, Permitted Public Feeds, Upwork manual feeds) with instant duplicate suppression.
- **Universal Job Importer**: Ingest opportunities via pasted URLs, raw pasted client messages, email alert notifications, or CSV files.
- **Job Intelligence & 100-Point Weighted Scoring**: Calibrated specifically for ₹10k–₹20k monthly milestones with automated fraud screening.
- **Platform Account Manager**: Manage Freelancer.com, Fiverr, Upwork, PeoplePerHour, Truelancer, and Guru settings with strict **Zero-Credential Security** (no passwords or tokens stored).
- **Fiverr Gig & Buyer Request Manager**: Track your live Fiverr Gigs and manually ingest client inquiries without violating marketplace terms.
- **Windows Task Scheduler Automation**: Standalone worker (`run_discovery.py`) runs on-demand or on schedule, logging results to SQLite.

---

## 💻 2. Prerequisites & Installation

### Checked on Your Windows System:
- **Operating System:** Windows 10/11
- **Python:** Python 3.14.5 is installed
- **Pip:** pip 26.1.1 is installed

### Required Packages:
Standard open-source libraries (`streamlit`, `pandas`, `openpyxl`, `requests`, `pytest`).  
Install or update anytime:
```powershell
pip install -r requirements.txt
```

---

## 🚀 3. Quick Start: Launching the App

### Option A: 1-Click Launcher
Double-click [`run_dashboard.bat`](file:///d:/PROJECTS/EXCE%20FINDING%20AI/run_dashboard.bat) in the project folder.

### Option B: From PowerShell or Command Prompt
```powershell
cd "d:\PROJECTS\EXCE FINDING AI"
python -m streamlit run app.py
```
Open your browser to: `http://localhost:8501`

---

## 🔍 4. Running the Job Discovery Scanner

### Method 1: From the Streamlit Dashboard
1. Open the **"🔍 Job Discovery & Scanner"** module in the sidebar.
2. Select your target keywords (e.g. `Excel dashboard`, `Excel automation`, `MIS executive freelance`).
3. Click **"🚀 Run Discovery Scan Now"**.
4. The scanner evaluates opportunities, skips duplicates, and updates your repository.

### Method 2: Running via Command Line (Windows Automation)
You can run a scan directly without opening a browser:
```powershell
python run_discovery.py
```

### Method 3: Scheduling via Windows Task Scheduler
1. Open Windows **Task Scheduler** (`taskschd.msc`).
2. Click **Create Basic Task** ➔ Name: `Excel Hunter AI Discovery`.
3. Trigger: **When I log on** or **Daily at 9:00 AM**.
4. Action: **Start a program** ➔ Program: `python.exe` ➔ Arguments: `run_discovery.py` ➔ Start in: `d:\PROJECTS\EXCE FINDING AI`.
5. Progress is saved after every scan and resumes safely after computer restarts.

---

## 📂 5. Project Architecture

```
EXCE FINDING AI/
├── app.py                      # Streamlit Command Center (10 complete modules)
├── run_dashboard.bat           # 1-Click Windows dashboard launcher
├── run_discovery.py            # Standalone discovery automation runner
├── requirements.txt            # Free open-source Python dependencies
├── README.md                   # Complete documentation and user guide
├── data/
│   ├── excel_hunter.db         # Local SQLite database (restart-safe persistence)
│   └── sample_jobs.csv         # Sample CSV file for testing batch imports
├── src/
│   ├── config.py               # 10 categories, search terms, integration states, targets
│   ├── db.py                   # SQLite tables, indexes, and safe migrations
│   ├── evaluation.py           # 100-point weighted scoring engine & fraud screening
│   ├── job_manager.py          # Job repository CRUD, deduplication, CSV import/export
│   ├── earnings_tracker.py     # Monthly targets (₹10k / ₹20k), fee deductions, net ledger
│   ├── platform_manager.py     # Multi-platform accounts (Freelancer, Fiverr, Upwork, etc.)
│   ├── fiverr_manager.py       # Fiverr Gig manager & manual buyer request ingestion
│   ├── proposal_generator.py   # Truthful, skill-matched tailored proposal generator
│   ├── application_tracker.py  # Application submissions, status sync & follow-up scheduler
│   └── discovery/
│       ├── __init__.py
│       ├── base_adapter.py     # StandardJob dataclass & BaseSourceAdapter
│       ├── freelancer_adapter.py # Official Freelancer REST API adapter
│       ├── upwork_adapter.py   # Upwork manual URL & email alert parser
│       ├── public_feed_adapter.py # Permitted public remote feeds (Remotive / Open RSS)
│       ├── universal_importer.py # Pasted URLs, raw text briefs & email alert parser
│       └── engine.py           # Multi-source discovery orchestrator & audit logger
└── tests/
    ├── test_application_tracker.py
    ├── test_csv_import.py
    ├── test_db.py
    ├── test_discovery_adapters.py
    ├── test_discovery_engine.py
    ├── test_duplicates.py
    ├── test_earnings.py
    ├── test_evaluation_v2.py
    ├── test_fiverr_manager.py
    ├── test_platform_manager.py
    ├── test_proposal_generator.py
    ├── test_safety.py
    └── test_universal_importer.py
```

---

## 🧭 6. Platform Access & Compliance Guide

| Platform | Integration Mode | Compliance Status & How It Works |
|---|---|---|
| **Freelancer.com** | `Official API available` | Compliant with official Freelancer REST API. Free Developer Token can be generated at [freelancer.com/developers](https://www.freelancer.com/developers). If unconfigured, safe demonstrative records load without web scraping. |
| **Fiverr** | `Manual` | Dedicated Gig and Buyer Request Manager. Terms strictly prohibit bot scraping; manual ingestion of buyer requirements keeps your seller account 100% compliant. |
| **Upwork** | `Manual` | Upwork Developer API restricts public job searches to vetted enterprise partners. Upwork integration operates via manual job URL entry, raw text pasting, and CSV/email alerts. |
| **PeoplePerHour** | `Manual` | Profile tracking and manual opportunity entry. No unauthorized web scrapers. |
| **Truelancer** | `Manual` | Indian and international freelance opportunities tracked via manual ingestion. |
| **Guru** | `Manual` | Project tracking and manual quoting. |
| **Public Feeds** | `Connected` | Pulls legitimate public remote job listings via permitted open feeds (e.g. Remotive Public API). Zero cost, no API keys needed. |

---

## 🧪 7. Running Automated Tests

To run the complete test suite:

```powershell
python -m pytest -v
```

All **38 unit tests** will run and pass green in ~10 seconds.
