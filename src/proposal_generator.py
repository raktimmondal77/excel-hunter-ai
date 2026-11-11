from typing import Dict, Any, List

# Verified skills catalog
VERIFIED_SKILLS_PROFILES = {
    "dashboard": {
        "title": "Interactive Excel Dashboards & KPI Trackers",
        "approach": [
            "Structure raw data tables cleanly to ensure error-free dynamic aggregations.",
            "Build interactive pivot tables and slicers to let you filter results by date, region, or category seamlessly.",
            "Design modern visual cards and KPI summary charts for fast executive decisions.",
            "Protect underlying calculation sheets to prevent accidental formula overwrites."
        ]
    },
    "mis": {
        "title": "MIS Reporting Automation",
        "approach": [
            "Standardize multiple input workbooks into a unified reporting structure.",
            "Automate recurring consolidation routines to eliminate tedious manual copy-pasting.",
            "Implement automated reconciliation checks so discrepancies are flagged instantly.",
            "Deliver an intuitive refresh workflow so daily/weekly reports update in seconds."
        ]
    },
    "formula": {
        "title": "Advanced Formula Engineering & Error Resolution",
        "approach": [
            "Audit current worksheet references and resolve #N/A, #REF!, and circular dependency errors.",
            "Upgrade legacy nested formulas to robust XLOOKUP, INDEX/MATCH, and dynamic array calculations.",
            "Optimize calculation speed for large data sets by minimizing volatile formula functions.",
            "Document formula logic clearly so your team can maintain the workbook effortlessly."
        ]
    },
    "vba": {
        "title": "Excel VBA Macro & Workflow Automation",
        "approach": [
            "Map your step-by-step repetitive manual process into a clean, well-commented VBA module.",
            "Add safety error handling and confirmation prompts before executing batch changes.",
            "Include a simple 1-click execution button directly on your master Excel sheet.",
            "Provide clear documentation on macro permissions and maintenance."
        ]
    },
    "data_cleaning": {
        "title": "Data Cleaning & Deduplication",
        "approach": [
            "Sanitize raw data: trim whitespace, standardize text casing, and harmonize date/phone formats.",
            "Isolate and remove duplicate entries with validation auditing.",
            "Split, merge, or transform columns using robust Excel formulas and Power Query where applicable.",
            "Deliver cleanly formatted master sheets along with an audit summary of records corrected."
        ]
    }
}

def detect_primary_category(text: str) -> str:
    """Classifies job text into one of the verified skill tracks."""
    t = text.lower()
    if any(k in t for k in ["vba", "macro", "macros", "script", "automate workflow"]):
        return "vba"
    elif any(k in t for k in ["dashboard", "kpi", "slicer", "visual", "pivot table"]):
        return "dashboard"
    elif any(k in t for k in ["mis", "management report", "consolidation", "weekly report", "monthly report"]):
        return "mis"
    elif any(k in t for k in ["clean", "dedup", "duplicate", "format list", "standardize"]):
        return "data_cleaning"
    else:
        return "formula"

def generate_honest_proposal(
    job_title: str,
    job_description: str,
    platform: str = "Freelancer",
    client_name: str = "there",
    freelancer_name: str = "Excel Freelancer",
    turnaround_estimate: str = "1-2 days"
) -> str:
    """
    Generates a structured, tailored, and 100% truthful proposal draft.
    Does not invent fake experience or client testimonials.
    """
    combined_text = f"{job_title} {job_description}"
    category = detect_primary_category(combined_text)
    profile = VERIFIED_SKILLS_PROFILES.get(category, VERIFIED_SKILLS_PROFILES["formula"])

    # Greeting
    greeting = f"Hi {client_name}," if client_name and client_name.lower() != "there" else "Hi there,"

    # Approach bullet points
    approach_lines = "\n".join([f"  {idx+1}. {step}" for idx, step in enumerate(profile["approach"])])

    proposal = f"""{greeting}

I noticed your posting regarding "{job_title.strip()}" on {platform}. I specialize in practical Excel solutions—specifically in {profile['title'].lower()}—and I can help you solve this efficiently and accurately.

Here is the exact approach I will take for your project:
{approach_lines}

Why this approach works for you:
- Accuracy first: All calculations and data structures are tested thoroughly to prevent errors.
- Clean design: Your spreadsheet will be organized, well-documented, and easy for anyone on your team to operate.
- Realistic timeline: I can deliver a working version for your review within {turnaround_estimate}.

If you have sample files or specific format requirements, feel free to share them so I can inspect the data structure and provide immediate feedback.

Looking forward to helping you with your spreadsheet!

Best regards,
{freelancer_name}"""

    return proposal
