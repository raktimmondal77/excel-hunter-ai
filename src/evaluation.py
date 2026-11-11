import re
from typing import Dict, List, Tuple

# Positive skill keywords relevant to Excel freelance jobs
EXCEL_SKILLS = [
    "dashboard", "excel", "formula", "formulas", "vba", "macro", "macros",
    "pivot", "vlookup", "xlookup", "index match", "data cleaning", "mis",
    "automation", "spreadsheet", "google sheets", "financial model", "tracker",
    "report", "reconciliation"
]

# Suspicious / Risk signals
RISK_PATTERNS = [
    (r"registration fee", "Requires registration fee before starting"),
    (r"security deposit", "Requires security deposit"),
    (r"pay.*(advance|deposit|fee).*(work|project|kit)", "Demands payment from freelancer to get work"),
    (r"telegram", "Directs communication to off-platform Telegram"),
    (r"whatsapp\s*[:\+]?\s*\d+", "Directs communication to private WhatsApp number"),
    (r"crypto|bitcoin|usdt", "Offers suspicious cryptocurrency payment"),
    (r"unpaid\s+(trial|test|sample)", "Demands unpaid test project or sample"),
    (r"excessive\s+test", "Demands extensive unpaid preliminary work")
]

def evaluate_job(title: str, description: str, budget: float = 0.0) -> Tuple[int, str, List[str]]:
    """
    Evaluates an Excel job.
    Returns:
        (score, priority, risk_flags)
        - score: 0 to 100
        - priority: 'High', 'Medium', 'Low'
        - risk_flags: List of risk descriptions
    """
    text = f"{title or ''} {description or ''}".lower()
    risk_flags: List[str] = []

    # 1. Detect Risks
    for pattern, reason in RISK_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            risk_flags.append(reason)

    # 2. Skill Match (max 60 points)
    matched_skills = [skill for skill in EXCEL_SKILLS if skill in text]
    skill_score = min(len(matched_skills) * 12, 60)

    # 3. Budget Score (max 25 points)
    budget_score = 0
    if budget >= 10000:
        budget_score = 25
    elif budget >= 5000:
        budget_score = 20
    elif budget >= 2000:
        budget_score = 15
    elif budget > 0:
        budget_score = 10
    else:
        # Undefined budget
        budget_score = 5

    # 4. Description Clarity / Completeness (max 15 points)
    desc_length = len(description or "")
    if desc_length > 250:
        clarity_score = 15
    elif desc_length > 80:
        clarity_score = 10
    else:
        clarity_score = 5

    raw_score = skill_score + budget_score + clarity_score

    # Penalty for risk flags
    if risk_flags:
        raw_score = max(raw_score - (len(risk_flags) * 30), 0)

    score = min(max(raw_score, 0), 100)

    # Determine Priority
    if risk_flags or score < 40:
        priority = "Low"
    elif score >= 70:
        priority = "High"
    else:
        priority = "Medium"

    return score, priority, risk_flags
