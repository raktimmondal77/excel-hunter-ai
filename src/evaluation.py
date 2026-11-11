import re
from typing import Dict, List, Tuple, Optional
from src.config import JOB_CATEGORIES

# Skill keyword mappings for the 10 prioritized Excel job categories
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "Excel dashboards": [
        "dashboard", "kpi", "slicer", "visual", "scorecard", "charts", "executive summary",
        "interactive dashboard", "summary sheet"
    ],
    "Excel automation": [
        "automation", "automate", "vba", "macro", "macros", "script", "power automate",
        "batch process", "routine"
    ],
    "Excel formulas and functions": [
        "formula", "formulas", "xlookup", "vlookup", "index match", "nested if",
        "dynamic array", "lambda", "calculate", "sumifs", "countifs", "indirect"
    ],
    "MIS reporting": [
        "mis", "management information system", "mis executive", "weekly mis",
        "monthly mis", "daily report", "consolidation"
    ],
    "Data cleaning": [
        "data clean", "data cleaning", "cleanup", "sanitize", "deduplicate", "duplicate",
        "remove duplicates", "split column", "text to columns"
    ],
    "Spreadsheet formatting": [
        "formatting", "conditional formatting", "template", "beautify", "layout",
        "font", "print setup", "align"
    ],
    "Excel trackers": [
        "tracker", "tracking", "log", "attendance tracker", "inventory tracker",
        "project tracker", "budget tracker", "expense tracker"
    ],
    "Business reporting": [
        "business report", "financial report", "sales report", "revenue report",
        "p&l", "profit and loss", "balance sheet", "variance analysis"
    ],
    "Operations reporting": [
        "operations report", "daily operations", "production report", "logistics",
        "supply chain", "shift report", "dispatch"
    ],
    "Custom Excel systems": [
        "custom excel", "excel tool", "quotation tool", "calculator", "invoice generator",
        "workbook system", "crm excel", "commission model"
    ]
}

# Suspicious / Risk signals
RISK_PATTERNS: List[Tuple[str, str]] = [
    (r"registration fee", "Requires registration fee before starting work"),
    (r"security deposit", "Demands security deposit from freelancer"),
    (r"pay.*(advance|deposit|fee).*(work|project|kit)", "Requires upfront fee/payment to receive project files"),
    (r"telegram", "Directs communication to off-platform Telegram account"),
    (r"whatsapp\s*[:\+]?\s*\d+", "Demands off-platform private WhatsApp contact"),
    (r"crypto|bitcoin|usdt|binance", "Proposes suspicious cryptocurrency payment"),
    (r"unpaid\s+(trial|test|sample|task)", "Demands unpaid preliminary trial/sample work"),
    (r"excessive\s+test", "Demands excessive unpaid preliminary assignments"),
    (r"(pay|contact|email)\s+outside\s+(upwork|fiverr|freelancer)", "Requests prohibited off-platform transaction")
]

# Disqualifying skill requirements (outside core Excel domain)
DISQUALIFYING_PATTERNS = [
    r"\bc\+\+", r"\bc#", r"\bjava\b(?!script)", r"\bdjango\b",
    r"\breact\b", r"\bflutter\b", r"\bandroid app\b", r"\bios app\b"
]

def detect_job_category(title: str, description: str) -> str:
    """Classifies a job into one of the 10 prioritized categories."""
    text = f"{title or ''} {description or ''}".lower()
    best_cat = "Excel formulas and functions"
    max_hits = 0

    for cat, keywords in CATEGORY_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in text)
        if hits > max_hits:
            max_hits = hits
            best_cat = cat

    return best_cat

def evaluate_job(
    title: str,
    description: str,
    budget: float = 0.0,
    client_info: str = "",
    deadline_text: str = ""
) -> Tuple[int, str, List[str], str]:
    """
    Evaluates an Excel freelance opportunity based on Stage 2 Job Intelligence.
    Returns:
        (score, priority, risk_flags, detected_category)
    Scoring breakdown (100 total):
        - Skill match: 30
        - Budget attractiveness: 20
        - Project clarity: 15
        - Client credibility: 15
        - Deliverability with current skills: 15
        - Deadline feasibility: 5
    """
    text = f"{title or ''} {description or ''}".lower()
    risk_flags: List[str] = []

    # 1. Detect Risks
    for pattern, reason in RISK_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            risk_flags.append(reason)

    # Unrealistic Budget check (e.g. ₹40,000+ for simple data entry)
    if budget >= 40000 and any(w in text for w in ["data entry", "copy paste", "typing"]):
        risk_flags.append("Unrealistically inflated budget for simple data entry task")

    # Vague description check
    if len((description or "").strip()) < 35:
        risk_flags.append("Vague project description with insufficient requirements")

    # 2. Skill Match (max 30 points)
    category = detect_job_category(title, description)
    matched_kws = [kw for cat_kws in CATEGORY_KEYWORDS.values() for kw in cat_kws if kw in text]
    skill_score = min(len(set(matched_kws)) * 5, 30)
    if skill_score < 10 and "excel" in text:
        skill_score = 15

    # 3. Budget Attractiveness (max 20 points)
    # Calibrated for ₹10,000–₹20,000 monthly income target
    if budget >= 10000:
        budget_score = 20
    elif budget >= 5000:
        budget_score = 16
    elif budget >= 2500:
        budget_score = 12
    elif budget >= 1000:
        budget_score = 8
    elif budget > 0:
        budget_score = 5
    else:
        # Negotiable / unstated budget
        budget_score = 4

    # 4. Project Clarity (max 15 points)
    desc_len = len(description or "")
    if desc_len >= 250:
        clarity_score = 15
    elif desc_len >= 100:
        clarity_score = 10
    elif desc_len >= 40:
        clarity_score = 6
    else:
        clarity_score = 2

    # 5. Client Credibility (max 15 points)
    c_info = (client_info or "").lower()
    if any(pos in c_info for pos in ["verified", "4.", "5.", "payment confirmed", "repeat", "established"]):
        credibility_score = 15
    elif c_info.strip():
        credibility_score = 10
    else:
        credibility_score = 6

    # 6. Deliverability with Current Skills (max 15 points)
    # Penalize if it demands complex outside tech
    outside_tech = [pat for pat in DISQUALIFYING_PATTERNS if re.search(pat, text, re.IGNORECASE)]
    if outside_tech:
        deliverability_score = 2
        risk_flags.append("Requires software development skills outside core Excel capability")
    else:
        # User is strong in Excel, VBA, Formulas, Dashboards, MIS
        deliverability_score = 15

    # 7. Deadline Feasibility (max 5 points)
    d_text = (deadline_text or "").lower()
    if any(rush in d_text or rush in text for rush in ["in 10 mins", "in 1 hour", "urgent immediately"]):
        deadline_score = 1
    else:
        deadline_score = 5

    # Aggregate Total
    raw_score = skill_score + budget_score + clarity_score + credibility_score + deliverability_score + deadline_score

    # Penalty for risk flags
    if risk_flags:
        raw_score = max(raw_score - (len(risk_flags) * 25), 0)

    score = min(max(raw_score, 0), 100)

    # Classify Priority
    if risk_flags or score < 40:
        priority = "Low"
    elif score >= 70:
        priority = "High"
    else:
        priority = "Medium"

    return score, priority, risk_flags, category
