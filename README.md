# 🎯 EXCEL HUNTER AI

> **A Zero-Cost, Windows-Based Excel Freelance Job Hunting Assistant**  
> Target Monthly Income: **₹10,000 – ₹20,000** | Budget: **₹0** (No paid APIs or recurring fees)

---

## 📌 1. Project Overview

**EXCEL HUNTER AI** is designed specifically for Excel freelancers who want to discover legitimate client projects, score opportunities, screen out fraudulent posts, manage application pipelines, and track their monthly income targets towards ₹10,000 and ₹20,000.

### Key Highlights for Stage 1:
- **100% Free & Local**: Operates completely on your Windows computer with zero API costs.
- **Offline Persistence**: Uses a local SQLite database (`data/excel_hunter.db`). Your data is preserved even when your PC is turned off or restarted.
- **Smart Scoring & Risk Detection**: Evaluates match quality for core Excel skills (Dashboards, MIS reporting, Formulas, XLOOKUP, VBA/Macros, Data Cleaning) and flags suspicious posts (registration fees, crypto, telegram off-platform contact).
- **Intelligent Deduplication**: Automatically blocks identical URLs and normalized titles so you never review duplicate posts.
- **Interactive Streamlit Dashboard**: Clean visual interface with pipeline tracking, filters, and earnings progress bars.
- **CSV Import & Export**: Import freelance leads from CSV or export filtered job lists for offline review.

---

## 💻 2. Windows Environment & Prerequisites

### Checked on Your System:
- **Operating System:** Windows 10/11
- **Python:** Python 3.14.5 is installed
- **Pip:** pip 26.1.1 is installed

### Required Libraries:
The project uses standard, open-source Python packages:
- `streamlit` (interactive web UI dashboard)
- `pandas` (tabular data manipulation)
- `openpyxl` (Excel workbook handling)
- `pytest` (automated testing framework)

To install or verify them anytime, run:
```powershell
pip install -r requirements.txt
```

---

## 🚀 3. Quick Start: How to Run

### Step 1: Open Terminal in the Project Folder
Open PowerShell or Command Prompt, and navigate to the project directory:
```powershell
cd "d:\PROJECTS\EXCE FINDING AI"
```

### Step 2: Launch the Streamlit Dashboard
Run:
```powershell
python -m streamlit run app.py
```
> **Tip for Beginners:** Using `python -m streamlit run app.py` avoids any PATH configuration issues on Windows.

Your default web browser will automatically open to:
```
http://localhost:8501
```

---

## 📂 4. Project Structure

```
EXCE FINDING AI/
├── app.py                      # Main Streamlit command center dashboard
├── requirements.txt            # Python dependencies (Streamlit, Pandas, OpenPyXL, Pytest)
├── README.md                   # Beginner's documentation and guide
├── data/
│   ├── excel_hunter.db         # Local SQLite database (auto-created on launch)
│   └── sample_jobs.csv         # Sample CSV file for testing manual import
├── src/
│   ├── __init__.py
│   ├── config.py               # Constants, monthly income goals, status types
│   ├── db.py                   # SQLite database initialization & connection helper
│   ├── evaluation.py           # Skill matching score (0-100) & risk/fraud detection
│   ├── job_manager.py          # Job CRUD, deduplication, CSV import/export
│   ├── earnings_tracker.py     # Monthly income calculations, fees, and targets
│   ├── platform_manager.py     # Multi-platform accounts & policy compliance
│   ├── proposal_generator.py   # Honest tailored proposal generation engine
│   ├── application_tracker.py  # Application submissions, client replies & follow-ups
│   └── sample_data.py          # Clearly-labeled demonstration records
└── tests/
    ├── __init__.py
    ├── test_db.py              # Tests for database tables and schema
    ├── test_duplicates.py      # Tests for URL and title deduplication
    ├── test_csv_import.py      # Tests for CSV import and scam detection
    ├── test_earnings.py        # Tests for fee calculation & monthly targets
    ├── test_safety.py          # Tests for data safety, persistence & CSV resilience
    ├── test_platform_manager.py# Tests for platform settings & zero-credential security
    ├── test_proposal_generator.py # Tests for truthful tailored proposals
    └── test_application_tracker.py# Tests for application lifecycle & follow-up alerts
```

---

## 🧭 5. How to Use the Modules

### 1. 📊 Dashboard & Overview
- Monitor progress towards **Goal 1 (₹10,000/month)** and **Goal 2 (₹20,000/month)**.
- **Application & Opportunity Pipeline**:
  - **Jobs Awaiting Applications**: Shortlisted jobs ready for proposal generation.
  - **Proposals Ready for Review**: Opportunities with drafted proposals.
  - **Applications Submitted**: Live proposals submitted to clients.
  - **Replies & Follow-ups Due**: Check-ins due today or client responses received.
- Check the **Fraud & Risk Detection Box** highlighting suspicious posts.
- Review top high-priority opportunities scored 70+/100.

### 2. 🚀 Job Application Assistant
- Inspect full job briefs, skill match breakdown, and client details.
- **1-Click Browser Launch**: Click `🌐 Open Original Job` to view the listing directly in your browser.
- **Honest Proposal Generator**: Automatically drafts structured, honest proposals matching your verified Excel skills (Dashboards, MIS automation, XLOOKUP/formulas, VBA macros, data cleaning). Zero fabricated claims.
- **Human Confirmation Gate**: Application logging requires checking:  
  `☑️ "I confirm that I have reviewed this proposal and manually submitted it through the official platform website."`
- Automatically updates job status to `applied` and schedules follow-up check-ins.

### 3. 📬 Application History & Follow-ups
- Comprehensive ledger of all submitted bids and application dates.
- Update client progress: `applied` ➔ `replied` ➔ `interview` ➔ `won` / `lost`.
- Automatic follow-up alerts when client check-ins are due.

### 4. 🌐 Platform Accounts & Policy Control
- Configure profiles for **Freelancer.com, Fiverr, Upwork, LinkedIn, and Direct Client**.
- Record profile URLs, account statuses, and compliance notes.
- **Zero-Credential Security**: No passwords, tokens, or cookies are ever requested or stored.
- Explicit integration capability modes: Defaulted to **Manual (Human-Controlled)**.

### 5. 📋 Job Repository & Pipeline
- Filter opportunities by Platform, Pipeline Status, or Priority.
- Search by keyword (`dashboard`, `vba`, `xlookup`).
- Export filtered jobs as CSV.

### 6. 💰 Earnings & Monthly Targets
- Record completed or expected Excel projects.
- Tracks Gross Billed, Platform Fees, and Net Take-Home (INR).
- Edit or delete payment entries anytime.

### 7. 📥 CSV Job Import
- Ingest job listings from email alerts or saved search exports.
- Intelligent deduplication automatically blocks matching URLs or normalized titles.

### 8. ⚙️ Database & Settings
- View current database statistics (Real vs Demonstration records).
- 1-click **Delete Sample Records** button to safely clear demo data while preserving real records.
- 1-click **Load Demonstration Records** button to explore features anytime.

---

## 🧪 6. Running Automated Tests

To verify that the database, deduplication logic, CSV ingestion, proposal generator, platform manager, and application tracker are working correctly:

```powershell
python -m pytest -v
```

All 24 unit tests will run and pass.

---

## 🛡️ 7. Safety & Ethical Rules Built-In

1. **No Automatic Proposals**: All proposals and client communication remain strictly under your control. The system will never message a client or apply without your manual review.
2. **Zero Financial Risk**: Never asks for credit cards, subscriptions, or paid API keys.
3. **No Credential Storage**: No passwords or account cookies are stored in plain text.
4. **Scam Prevention**: Proactively screens out fee-charging scams and off-platform diversions.

---

## 🗺️ 8. Next Stages Roadmap

- **Stage 2**: Permitted public job discovery feeds and email alert parsers.
- **Stage 3**: Local, template-based proposal draft generator tailored to your verified Excel portfolio without fabricating credentials.
- **Stage 4**: Windows Task Scheduler automation to periodically check feeds when your PC is online.
