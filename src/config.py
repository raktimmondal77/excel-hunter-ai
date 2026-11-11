import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Database and File Paths
DB_PATH = DATA_DIR / "excel_hunter.db"
SAMPLE_CSV_PATH = DATA_DIR / "sample_jobs.csv"

# Monthly Earning Targets (in INR)
TARGET_MIN_INR = 10000.0
TARGET_MAX_INR = 20000.0

# Supported Job Statuses
JOB_STATUSES = [
    "discovered",
    "shortlisted",
    "proposal_drafted",
    "applied",
    "replied",
    "interview",
    "won",
    "lost",
    "paid"
]

# Supported Priority Levels
PRIORITIES = ["High", "Medium", "Low"]

# Standard Platforms
PLATFORMS = [
    "Upwork",
    "Fiverr",
    "Freelancer",
    "LinkedIn",
    "Direct Client",
    "Internshala",
    "Other"
]
