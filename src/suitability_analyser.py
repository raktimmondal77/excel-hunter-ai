import re
from typing import Dict, Any, List, Tuple, Optional
from src.user_profile import get_user_profile

SKILL_PATTERNS = {
    "Basic formulas": [r"\bformulas?\b", r"\bsum\b", r"\baverage\b", r"\bcount\b"],
    "IF, SUMIF, COUNTIF": [r"\bif\b", r"\bsumif\b", r"\bcountif\b", r"\bsumifs\b", r"\bcountifs\b"],
    "XLOOKUP / VLOOKUP": [r"\bxlookup\b", r"\bvlookup\b", r"\bhlookup\b", r"\bindex\s+match\b", r"\bindex/match\b"],
    "Pivot Tables": [r"\bpivot\s+tables?\b", r"\bpivots?\b", r"\bslicers?\b"],
    "Charts": [r"\bcharts?\b", r"\bgraphs?\b", r"\bvisualizations?\b"],
    "Dashboards": [r"\bdashboards?\b", r"\bkpi\b", r"\bscorecards?\b"],
    "Data cleaning": [r"\bdata\s+clean\w*\b", r"\bclean\w*\s+data\b", r"\bdedup\w*\b", r"\bduplicates?\b", r"\bformatting\b"],
    "MIS reporting": [r"\bmis\b", r"\bmonthly\s+report\w*\b", r"\bweekly\s+report\w*\b", r"\bconsolidation\b", r"\bmanagement\s+report\w*\b"],
    "Excel automation": [r"\bautomati\w*\b", r"\bworkflow\b", r"\brecurring\b"],
    "Power Query": [r"\bpower\s*query\b", r"\betl\b", r"\bm\s+code\b"],
    "VBA": [r"\bvba\b", r"\bmacros?\b", r"\bexcel\s+script\b"],
    "Google Sheets": [r"\bgoogle\s+sheets?\b", r"\bgsheets?\b"],
    "Power BI": [r"\bpower\s*bi\b", r"\bdax\b"],
    "SQL": [r"\bsql\b", r"\bdatabase\s+query\b"],
    "Python": [r"\bpython\b", r"\bpandas\b"]
}

def extract_required_skills(text: str) -> List[str]:
    """Extracts required skills from job text using predefined patterns."""
    text_lower = text.lower()
    matched = []
    for skill, patterns in SKILL_PATTERNS.items():
        if any(re.search(pat, text_lower) for pat in patterns):
            matched.append(skill)
    # Default to Basic formulas if no specific skill mentioned but it is an Excel task
    if not matched:
        matched.append("Basic formulas")
    return matched

def estimate_difficulty_and_hours(skills_required: List[str], desc_len: int) -> Tuple[str, float, str]:
    """Estimates difficulty level, working hours, and expected turnaround."""
    high_skills = {"VBA", "Power BI", "SQL", "Python", "Power Query"}
    med_skills = {"Dashboards", "MIS reporting", "Excel automation", "XLOOKUP / VLOOKUP", "Pivot Tables"}

    has_high = any(s in high_skills for s in skills_required)
    has_med = any(s in med_skills for s in skills_required)

    if has_high:
        return "High", 10.0, "3-5 days"
    elif has_med or desc_len > 800:
        return "Medium", 5.0, "2-3 days"
    else:
        return "Low", 2.5, "1-2 days"

def analyse_suitability(
    job: Dict[str, Any],
    profile: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Computes a 100-point suitability score matching the job to the user's confirmed skills profile:
    - Skill match: 30 pts
    - Budget suitability: 15 pts
    - Project clarity: 15 pts
    - Client credibility: 15 pts
    - Delivery feasibility: 15 pts
    - Deadline feasibility: 10 pts
    """
    if profile is None:
        profile = get_user_profile()

    user_excel_skills = set(profile.get("excel_skills", []))
    user_tools = set(profile.get("other_tools", []))
    user_all_skills = user_excel_skills.union(user_tools)
    user_exp = profile.get("experience_level", "Beginner")
    user_min_budget = float(profile.get("min_budget", 1500.0))
    user_weekly_hours = float(profile.get("hours_per_week", 15.0))

    title = job.get("title", "")
    desc = job.get("description", "")
    client_info = job.get("client_info", "")
    budget = float(job.get("budget", 0) or 0)
    currency = job.get("currency", "INR")
    combined_text = f"{title} {desc}"

    # 1. Skill Extraction & Matching (30 points)
    skills_required = extract_required_skills(combined_text)
    skills_possessed = [s for s in skills_required if s in user_all_skills]
    missing_skills = [s for s in skills_required if s not in user_all_skills]

    if len(skills_required) == 0 or len(skills_possessed) == len(skills_required):
        skill_score = 30
    elif len(skills_possessed) / len(skills_required) >= 0.7:
        skill_score = 24
    elif len(skills_possessed) / len(skills_required) >= 0.4:
        skill_score = 16
    elif len(skills_possessed) > 0:
        skill_score = 10
    else:
        skill_score = 4

    # 2. Budget Suitability (15 points)
    # Convert USD/EUR to INR estimate if necessary
    budget_inr = budget * 85.0 if currency.upper() in ["USD", "EUR"] else budget

    if budget_inr == 0:
        # Budget not specified
        budget_score = 10
        budget_display = "Budget not specified"
    elif budget_inr >= user_min_budget:
        budget_score = 15
        budget_display = f"{budget:,.2f} {currency}"
    elif budget_inr >= user_min_budget * 0.7:
        budget_score = 8
        budget_display = f"{budget:,.2f} {currency} (Below preferred minimum)"
    else:
        budget_score = 4
        budget_display = f"{budget:,.2f} {currency} (Significantly low)"

    # 3. Project Clarity (15 points)
    desc_clean = desc.strip()
    if len(desc_clean) >= 200:
        clarity_score = 15
        clarity_note = "Detailed scope with clear project deliverables"
    elif len(desc_clean) >= 70:
        clarity_score = 11
        clarity_note = "Moderate project description"
    else:
        clarity_score = 5
        clarity_note = "Brief or vague project description"

    # 4. Client Credibility (15 points)
    client_str = str(client_info).lower()
    if any(k in client_str for k in ["verified", "rating: 5", "rating: 4", "payment verified", "freelancer client", "upwork"]):
        credibility_score = 15
    elif len(client_str) > 5:
        credibility_score = 12
    else:
        credibility_score = 8

    # 5. Delivery Feasibility (15 points)
    difficulty, est_hours, completion_time = estimate_difficulty_and_hours(skills_required, len(desc_clean))
    if difficulty == "Low":
        delivery_score = 15
    elif difficulty == "Medium":
        delivery_score = 15 if user_exp in ["Intermediate", "Advanced"] else 12
    else: # High
        delivery_score = 15 if user_exp == "Advanced" else (10 if user_exp == "Intermediate" else 5)

    # 6. Deadline Feasibility (10 points)
    # Check if rush job
    if any(k in combined_text.lower() for k in ["urgent", "within 2 hours", "asap", "within 24 hours", "today only"]):
        deadline_score = 5 if user_exp == "Beginner" else 8
    else:
        deadline_score = 10

    total_score = skill_score + budget_score + clarity_score + credibility_score + delivery_score + deadline_score
    total_score = min(100, max(0, total_score))

    # Beginner Friendly Evaluation
    critical_advanced = {"VBA", "Power BI", "SQL", "Python"}
    has_critical_gap = any(s in critical_advanced for s in missing_skills)
    is_beginner_friendly = (difficulty == "Low" or (difficulty == "Medium" and not has_critical_gap))

    # Potential Risks (extracted from job notes or patterns)
    potential_risks = []
    if has_critical_gap:
        potential_risks.append(f"Requires advanced skills ({', '.join([s for s in missing_skills if s in critical_advanced])}) not yet confirmed in your profile.")
    if budget_inr > 0 and budget_inr < user_min_budget:
        potential_risks.append(f"Stated budget (₹{budget_inr:,.0f}) is below your minimum threshold of ₹{user_min_budget:,.0f}.")
    if len(desc_clean) < 70:
        potential_risks.append("Scope is poorly defined; requires client clarification before bidding.")
    if any(k in combined_text.lower() for k in ["telegram", "whatsapp", "security fee", "deposit"]):
        potential_risks.append("Contains high-risk fraud keywords (off-platform communication or deposit fees).")

    # Recommendation: Apply / Apply after learning something / Avoid
    if total_score >= 70 and not has_critical_gap and len(potential_risks) <= 1:
        recommendation = "Apply"
        rec_code = "A"
        reasoning = f"Excellent match ({total_score}/100). You possess the key skills ({', '.join(skills_possessed) or 'Core Excel'}) and the project scope aligns with your capabilities."
    elif total_score >= 50 and not any(s in ["VBA", "SQL", "Python"] for s in missing_skills):
        recommendation = "Apply after learning something"
        rec_code = "B"
        gap_str = ", ".join(missing_skills) if missing_skills else "clarifying scope"
        reasoning = f"Promising opportunity ({total_score}/100), but review or learn: {gap_str}. The project is attainable with minor preparation."
    else:
        recommendation = "Avoid"
        rec_code = "C"
        reasoning = f"Low suitability ({total_score}/100). " + (f"Requires missing advanced skills: {', '.join(missing_skills)}. " if missing_skills else "Budget or clarity is unfavorable for your current profile.")

    return {
        "suitability_score": total_score,
        "score_breakdown": {
            "skill_match": skill_score,
            "budget_suitability": budget_score,
            "project_clarity": clarity_score,
            "client_credibility": credibility_score,
            "delivery_feasibility": delivery_score,
            "deadline_feasibility": deadline_score
        },
        "skills_required": skills_required,
        "skills_possessed": skills_possessed,
        "missing_skills": missing_skills,
        "estimated_difficulty": difficulty,
        "estimated_hours": est_hours,
        "completion_time": completion_time,
        "budget_display": budget_display,
        "is_beginner_friendly": is_beginner_friendly,
        "potential_risks": potential_risks,
        "recommendation": recommendation,
        "recommendation_code": rec_code,
        "reasoning": reasoning
    }
