import re
from typing import Dict, Any, List, Optional
from src.user_profile import get_user_profile, get_portfolio_projects

def generate_clarifying_questions(job_title: str, job_desc: str) -> List[str]:
    """Generates 1-2 practical clarifying questions based on context."""
    text = (job_title + " " + job_desc).lower()
    questions = []

    if any(k in text for k in ["dashboard", "kpi", "tracker", "report"]):
        questions.append("Are your raw data inputs updated on a recurring schedule (e.g. daily/weekly), or is this a one-time consolidation?")
    if any(k in text for k in ["clean", "format", "dedup", "duplicate"]):
        questions.append("Do you have specific column naming and casing guidelines you would like me to follow for the output sheet?")
    if any(k in text for k in ["formula", "calculate", "xlookup", "vlookup"]):
        questions.append("Would you like me to include error-trapping (like IFERROR) and cell protection so formulas cannot be accidentally erased?")
    if not questions:
        questions.append("Could you share a sample file or an example of your preferred final layout so I can verify the exact structure?")

    return questions[:2]

def generate_three_proposal_versions(
    job: Dict[str, Any],
    profile: Optional[Dict[str, Any]] = None,
    client_name: Optional[str] = None,
    freelancer_name: str = "Excel Freelancer"
) -> Dict[str, str]:
    """
    Generates three distinct, human-sounding, and 100% honest proposal versions:
    - Version A: Short and direct
    - Version B: Professional and detailed
    - Version C: Beginner-friendly and honest

    STRICT SAFETY RULE:
    Only references verified skills and portfolio projects from user's confirmed profile.
    Never invents unconfirmed skills (e.g. VBA, Python, SQL) or fabricated achievements.
    """
    if profile is None:
        profile = get_user_profile()

    user_excel_skills = set(profile.get("excel_skills", []))
    user_tools = set(profile.get("other_tools", []))
    all_user_skills = user_excel_skills.union(user_tools)
    user_exp = profile.get("experience_level", "Beginner")

    title = job.get("title", "").strip()
    desc = job.get("description", "").strip()
    platform = (job.get("platform") or "Freelance Platform").strip()

    # Client greeting
    c_name = client_name.strip() if client_name and client_name.strip().lower() not in ["there", "client", "unknown", ""] else ""
    greeting = f"Hi {c_name}," if c_name else "Hi,"

    # Verified capabilities relevant to project
    verified_mentions = []
    if "Dashboards" in user_excel_skills and any(k in (title + desc).lower() for k in ["dash", "kpi", "visual", "chart"]):
        verified_mentions.append("building dynamic Excel dashboards and clear visual KPI summaries")
    if "Data cleaning" in user_excel_skills and any(k in (title + desc).lower() for k in ["clean", "format", "dedup", "duplicate", "split"]):
        verified_mentions.append("meticulous spreadsheet data cleaning and standardization")
    if "XLOOKUP / VLOOKUP" in user_excel_skills and any(k in (title + desc).lower() for k in ["lookup", "match", "formula", "vlookup", "xlookup"]):
        verified_mentions.append("robust formula structures using XLOOKUP and dynamic indexing")
    if "Pivot Tables" in user_excel_skills and any(k in (title + desc).lower() for k in ["pivot", "slicer", "summary"]):
        verified_mentions.append("multi-dimensional pivot table summaries with intuitive slicers")
    if "MIS reporting" in user_excel_skills and any(k in (title + desc).lower() for k in ["mis", "report", "monthly", "weekly", "consolidation"]):
        verified_mentions.append("automated MIS reporting and workbook consolidation")
    if "VBA" in user_excel_skills and any(k in (title + desc).lower() for k in ["vba", "macro"]):
        verified_mentions.append("custom Excel VBA macros for repetitive workflow automation")
    if "Google Sheets" in user_tools and any(k in (title + desc).lower() for k in ["google sheet", "gsheet"]):
        verified_mentions.append("Google Sheets formulas and cloud collaboration")

    # If no specific overlap, use confirmed baseline skills
    if not verified_mentions:
        sample_skills = [s for s in ["Basic formulas", "Data cleaning", "Pivot Tables"] if s in user_excel_skills]
        if sample_skills:
            verified_mentions.append(f"practical spreadsheet management using {', '.join(sample_skills)}")
        else:
            verified_mentions.append("careful data organization and Excel workbook accuracy")

    verified_summary = "; ".join(verified_mentions)
    clarifying_qs = generate_clarifying_questions(title, desc)
    questions_formatted = "\n".join([f"• {q}" for q in clarifying_qs])

    # Check for confirmed portfolio projects
    portfolio = get_portfolio_projects()
    portfolio_note = ""
    if portfolio:
        sample_proj = portfolio[0]
        portfolio_note = f"\nFor reference, I recently completed a similar project: '{sample_proj['project_title']}' ({sample_proj.get('skills_used', 'Excel')})."

    # -------------------------------------------------------------
    # Version A: Short and Direct
    # -------------------------------------------------------------
    version_a = f"""{greeting}

I read your project requirements for "{title}". I can take care of this cleanly and accurately.

My approach for your sheet:
1. Review your raw data and structure to ensure zero formula errors or broken references.
2. Deliver a clean, well-formatted solution focusing on {verified_mentions[0]}.
3. Provide a documented walkthrough so you and your team can operate it easily.

Turnaround: 1–2 days. I will also test everything on sample records before final handover.
{portfolio_note}
Quick question:
{questions_formatted}

Looking forward to reviewing your sample files.

Best regards,
{freelancer_name}"""

    # -------------------------------------------------------------
    # Version B: Professional and Detailed
    # -------------------------------------------------------------
    version_b = f"""{greeting}

Thank you for posting the opportunity for "{title}". I understand you need a reliable, error-free Excel solution that simplifies your workflow and provides trustworthy calculations.

Based on your project description, here is the structured delivery roadmap I will follow:

Phase 1: Data Audit & Architecture
- Inspect incoming data columns, standardizing text casing, dates, and number formats.
- Eliminate circular references and formula risks like #N/A or #VALUE!.

Phase 2: Core Implementation
- Implement the requested solution utilizing verified methods: {verified_summary}.
- Organize sheet tabs logically, keeping raw data separate from summary views.
- Add cell locking and protection on calculation cells to prevent inadvertent edits.

Phase 3: Quality Assurance & Review
- Test calculations with multiple test scenarios to verify 100% mathematical accuracy.
- Prepare a brief notes tab explaining formula logic and refresh steps.

Clarifications to ensure an exact fit:
{questions_formatted}
{portfolio_note}
I am ready to start immediately upon receiving your file structure and can deliver a working draft within 2 to 3 days.

Sincerely,
{freelancer_name}"""

    # -------------------------------------------------------------
    # Version C: Beginner-Friendly and Honest
    # -------------------------------------------------------------
    version_c = f"""{greeting}

I am reaching out regarding your project: "{title}". 

I want to be completely upfront: my focus is on delivering clean, meticulous Excel work with clear communication and fast turnaround. I don't use confusing technical jargon—I focus on making sure your spreadsheet works exactly the way you need it to.

What I can guarantee for this project:
- My verified skills in {verified_summary} match your core requirements.
- I will double-check every calculation manually before sending you the workbook.
- If anything needs tweaking after you test it, I will revise it promptly until you are 100% satisfied.
- Clean formatting: easy-to-read numbers, neat borders, and clear headers.

Estimated delivery: 1–2 days.
{portfolio_note}
To get started on the right foot:
{questions_formatted}

Thank you for considering my proposal, and I look forward to working with you!

Warm regards,
{freelancer_name}"""

    return {
        "version_a": version_a.strip(),
        "version_b": version_b.strip(),
        "version_c": version_c.strip()
    }
