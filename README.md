# 🎯 EXCEL HUNTER AI — Stage 3: Precision Discovery, Honest Scoring, 6 Live Sources

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

### Stage 3 Capabilities (NEW — this version):
- **6 discovery sources** (was 2): Freelancer.com Official API, Remotive, **RemoteOK**, **Jobicy**, **Working Nomads** (all free, no API keys), plus compliant manual Upwork ingestion.
- **Strict Excel relevance gate**: fuzzy API junk (marketing posts, SEO gigs, "excel" used as an English verb) is rejected before it ever reaches your repository. A live scan evaluates ~200 raw postings and imports only genuine spreadsheet work.
- **Fresh-leads-only Freelancer scan**: `from_time` + `sort=latest` filters mean only projects posted in the last 7 days are imported.
- **100% INR-normalized budgets**: USD/EUR/GBP budgets are converted once, at the repository boundary, so scoring against your ₹10k–₹20k goal is always accurate. Original amounts are preserved in the client notes.
- **Freshness-aware 100-point scoring**: brand-new postings outrank 3-week-old ones; stale postings are flagged. Severe fraud flags (-25 each) are now distinguished from soft quality warnings (rush deadline, tiny budget).
- **Real client-credibility signals**: escrow-funded, featured/urgent listings, live bid counts — no more fake "verified" credibility.
- **Proposals that close**: every generated proposal can embed your recommended fixed quote and delivery timeline straight from the pricing assistant (still 100% editable, still never inventing skills you don't have).
- **Dashboard upgrade**: score badges, priority badges, category chips, risk boxes, sorting (best match / newest / highest budget), priority filter, keyword search, "hide risky jobs" toggle, and a "Top Jobs to Apply for Right Now" panel on the home page.

### Stage 2 Capabilities (carried forward):
- Universal Job Importer (pasted URLs, raw client messages, email alerts, CSV files)
- Platform Account Manager with Zero-Credential Security
- Fiverr Gig & Buyer Request Manager
- Windows Task Scheduler Automation (`run_discovery.py`)
- Earnings tracker with platform-fee deductions and monthly goal progress

---

## 💻 2. Prerequisites & Installation

- **Operating System:** Windows 10/11 (also runs on macOS/Linux)
- **Python:** 3.10 or newer (tested up to 3.14)
- **Pip:** any recent version

Install the free open-source dependencies:
```powershell
pip install -r requirements.txt
```

---

## 🚀 3. Quick Start: Launching the App

### Option A: 1-Click Launcher
Double-click `run_dashboard.bat` in the project folder.

### Option B: From PowerShell or Command Prompt
```powershell
cd <project folder>
python -m streamlit run app.py
```
Open your browser to: `http://localhost:8501`

---

## 🔍 4. Running the Job Discovery Scanner

### Method 1: From the Streamlit Dashboard
1. Open the **"🔍 Find Excel Jobs"** page.
2. Click **"🚀 Find New Excel Jobs Now"**.
3. Review the scan report: new jobs imported, duplicates skipped, junk filtered — with a per-source breakdown.
4. Sort by **Best match (score)** and start applying.

### Method 2: Command Line (Windows Automation)
```powershell
python run_discovery.py
```
The runner prints per-source statistics and the **top fresh opportunities** from the scan.

### Method 3: Scheduling via Windows Task Scheduler
1. Open Windows **Task Scheduler** (`taskschd.msc`).
2. Click **Create Basic Task** ➔ Name: `Excel Hunter AI Discovery`.
3. Trigger: **Daily at 9:00 AM** (fresh Excel projects appear every morning).
4. Action: **Start a program** ➔ Program: `python.exe` ➔ Arguments: `run_discovery.py` ➔ Start in: your project folder.

---

## 🧭 5. Platform Access & Compliance Guide

| Platform | Integration Mode | How It Works |
|---|---|---|
| **Freelancer.com** | `Official API` | Read-only project search via the official REST API. Free developer token optional (public read-only works). Fresh-only (last 7 days), strict relevance filter, budgets converted to INR. |
| **Fiverr** | `Manual` | Gig manager + manual buyer-request ingestion. No scraping (Fiverr ToS). |
| **Upwork** | `Manual` | Manual job URL / text / email-alert ingestion (Upwork restricts public API job search to vetted partners). |
| **Remotive** | `Connected` | Public remote-jobs API. Contract/freelance/part-time spreadsheet roles only. |
| **RemoteOK** | `Connected` *(NEW)* | Public jobs API (attribution in every record). Contract roles or explicitly-Excel titles only. |
| **Jobicy** | `Connected` *(NEW)* | Public remote-jobs API. Contract/freelance/part-time engagements only. |
| **Working Nomads** | `Connected` *(NEW)* | Public jobs API. Explicit contract/freelance engagements only. |
| **PeoplePerHour / Truelancer / Guru** | `Manual` | Profile tracking and manual opportunity entry. |

All sources are fault-tolerant: one source failing never affects the others.

---

## 🧠 6. How Jobs Are Scored (100-Point Engine v3)

| Factor | Max Points | What it measures |
|---|---|---|
| Excel relevance & skill match | 30 | Is it genuinely spreadsheet work? Which of the 10 Excel categories? |
| Budget attractiveness (INR) | 20 | Value in ₹ against your monthly target — currency-normalized |
| Project clarity | 10 | How well-defined the scope is |
| Client credibility | 15 | Real signals: escrow, featured, ratings, hiring history |
| Deliverability | 15 | Stays inside core Excel skills (no C++/app development) |
| Freshness | 10 | Posted today vs. weeks ago |

**Penalties:** severe fraud flags (deposits, Telegram diversion, crypto, unpaid trials, off-platform payments) −25 each; soft warnings (rush deadline, tiny budget, stale posting) −5 each. Non-Excel postings are capped at 35 and flagged. Priority: **High ≥ 70**, Medium ≥ 50, otherwise Low.

---

## 📂 7. Project Architecture

```
EXCEL HUNTER AI/
├── app.py                          # Streamlit Command Center (6 pages, score badges, filters)
├── run_dashboard.bat               # 1-Click Windows dashboard launcher
├── run_discovery.py                # CLI discovery runner + top-opportunities report
├── requirements.txt                # streamlit, pandas, openpyxl, requests, pytest
├── README.md / CHANGELOG.md
├── data/
│   ├── excel_hunter.db             # Local SQLite database (auto-created)
│   └── sample_jobs.csv             # Sample CSV for testing imports
├── src/
│   ├── config.py                   # Categories, search terms, targets
│   ├── currency.py                 # (NEW) FX rates, to_inr(), money-text parsing
│   ├── db.py                       # Tables, indexes, safe migrations
│   ├── evaluation.py               # 100-pt scoring v3 + Excel relevance gate
│   ├── job_manager.py              # Repository CRUD, dedup, INR normalization, CSV import
│   ├── earnings_tracker.py         # Monthly targets, fees, net ledger
│   ├── platform_manager.py         # Multi-platform accounts
│   ├── fiverr_manager.py           # Fiverr gigs & buyer requests
│   ├── proposal_generator.py       # Legacy tailored-proposal generator
│   ├── proposal_intelligence.py    # 3-version proposals + honest pricing block
│   ├── application_tracker.py      # Submissions, statuses, follow-up scheduler
│   ├── pricing_assistant.py        # Quotes, hours, platform fees, net earnings
│   ├── suitability_analyser.py     # Personal 100-pt match vs your skills
│   ├── user_profile.py             # Skills, experience, budget preferences
│   ├── sample_data.py              # Demo seeding
│   └── discovery/
│       ├── base_adapter.py         # StandardJob + BaseSourceAdapter (+ filtered_count)
│       ├── freelancer_adapter.py   # Official API, fresh-only, relevance-filtered
│       ├── public_feed_adapter.py  # Remotive
│       ├── remoteok_adapter.py     # (NEW) RemoteOK
│       ├── jobicy_adapter.py       # (NEW) Jobicy
│       ├── workingnomads_adapter.py# (NEW) Working Nomads
│       ├── upwork_adapter.py       # Manual Upwork ingestion
│       ├── universal_importer.py   # Pasted URLs, text, email alerts
│       └── engine.py               # 6-source orchestrator + junk gate + scan reports
└── tests/                          # 76 automated tests
```

---

## 🧪 8. Running Automated Tests

```powershell
python -m pytest -v
```

All **76 unit tests** run and pass in ~3 seconds — covering currency conversion, the relevance gate, currency-aware scoring, freshness, all new adapters (offline with canned payloads), fraud detection, deduplication, and data safety.
