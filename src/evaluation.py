import re
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional
from src.config import JOB_CATEGORIES
from src.currency import to_inr

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

# ---------------------------------------------------------------------------
# EXCEL RELEVANCE GATE (Stage 3)
# Distinguishes genuine Microsoft Excel / spreadsheet work from posts that
# merely use "excel" as an English verb ("candidates who excel at ...") or
# fuzzy API matches that have nothing to do with spreadsheets.
# ---------------------------------------------------------------------------
EXCEL_TOOL_PATTERN = re.compile(
    r"(\bmicrosoft\s+excel\b|\bms\s+excel\b|\bexcel\b|\bxlsx\b|\bxls\b|"
    r"\bspreadsheets?\b|\bgoogle\s+sheets?\b|\bgsheets?\b|"
    r"\bvba\b|\bmacros?\b|\bpivot\s+(?:table|chart)s?\b|"
    r"\bxlookup\b|\bvlookup\b|\bhlookup\b|\bindex\s*/?\s*match\b|"
    r"\bpower\s+query\b|\bpower\s+pivot\b|"
    r"\bmis\s+report\w*\b|\bopenpyxl\b)",
    re.IGNORECASE
)

# "excel" used as a verb — exclude these ("excel at communication", "excel in their field")
EXCEL_VERB_EXCEPTION = re.compile(r"\bexcel\s+(?:at|in|to)\b", re.IGNORECASE)


def is_excel_job(title: str, description: str = "") -> bool:
    """True only when the text clearly refers to spreadsheet/Excel TOOL work."""
    text = f"{title or ''} {description or ''}"
    if not text.strip():
        return False
    # Strip verb usages first ("excel at ..."), then look for tool mentions.
    cleaned = EXCEL_VERB_EXCEPTION.sub(" ", text)
    return bool(EXCEL_TOOL_PATTERN.search(cleaned))


# Soft warnings are quality notices (rush deadline, staleness, tiny budget).
# They are NOT fraud signals: a job with only soft warnings can still be a
# legitimate opportunity worth applying to.
SOFT_WARNING_PREFIXES = (
    "Rush deadline",
    "Stale posting",
    "Posting is",
    "Very small budget",
)


def is_soft_warning(flag_text: str) -> bool:
    """True when a risk-flag entry is a soft quality warning, not fraud."""
    return any(str(flag_text or "").startswith(p) for p in SOFT_WARNING_PREFIXES)


# Suspicious / Risk signals (severe — each costs 25 points)
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

# Rush / deadline pressure phrases (soft warnings — 5 points each)
RUSH_PATTERNS = [
    "in 10 mins", "in 1 hour", "within an hour", "urgent immediately",
    "within 2 hours", "within 24 hours", "asap", "today only", "right now",
    "immediately today"
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


def _parse_date_str(date_text: str) -> Optional[date]:
    """Safely parses YYYY-MM-DD (or ISO datetime) strings."""
    if not date_text:
        return None
    raw = str(date_text).strip()[:10]
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return None


def evaluate_job(
    title: str,
    description: str,
    budget: float = 0.0,
    client_info: str = "",
    deadline_text: str = "",
    currency: str = "INR",
    date_posted: str = ""
) -> Tuple[int, str, List[str], str]:
    """
    Evaluates an Excel freelance opportunity — Stage 3 Job Intelligence v3.

    Returns:
        (score, priority, risk_flags, detected_category)

    Scoring breakdown (100 total) — everything budget-related is normalized
    to INR first, so USD/EUR budgets are scored fairly against the
    ₹10,000–₹20,000 monthly target:
        - Excel relevance & skill match: 30
        - Budget attractiveness (INR):   20
        - Project clarity:              10
        - Client credibility:           15
        - Deliverability:               15
        - Freshness:                    10

    Penalties:
        - Severe fraud/risk flags: -25 each (hard floor at 0)
        - Rush deadline warnings:  -5 each
        - Non-Excel jobs: score capped at 35 + flagged
    """
    text = f"{title or ''} {description or ''}".lower()
    risk_flags: List[str] = []
    warnings: List[str] = []

    # 1. Detect severe risks
    for pattern, reason in RISK_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            risk_flags.append(reason)

    # Unrealistic Budget check (e.g. ₹40,000+ for simple data entry)
    budget_inr = to_inr(budget, currency)
    if budget_inr >= 40000 and any(w in text for w in ["data entry", "copy paste", "typing"]):
        risk_flags.append("Unrealistically inflated budget for simple data entry task")

    # Vague description check
    if len((description or "").strip()) < 35:
        risk_flags.append("Vague project description with insufficient requirements")

    # Rush deadline (soft warning, not a scam flag)
    d_text = (deadline_text or "").lower()
    if any(rush in d_text or rush in text for rush in RUSH_PATTERNS):
        warnings.append("Rush deadline — confirm feasibility before bidding")

    # Very small budget (soft warning): below typical Excel gig minimums
    if 0 < budget_inr < 1500:
        warnings.append(f"Very small budget (₹{budget_inr:,.0f}) — barely worth the effort")

    # ------------------------------------------------------------------
    # 2. Excel Relevance & Skill Match (max 30 points)
    # ------------------------------------------------------------------
    category = detect_job_category(title, description)
    relevant = is_excel_job(title, description)

    matched_kws = [kw for cat_kws in CATEGORY_KEYWORDS.values() for kw in cat_kws if kw in text]
    skill_depth = min(len(set(matched_kws)) * 4, 16)  # up to 16 from keyword depth

    if relevant:
        # Base 14 for being genuinely spreadsheet-related,
        # +14 if "excel"/spreadsheet appears in the TITLE (strongest signal)
        title_hit = bool(EXCEL_TOOL_PATTERN.search(EXCEL_VERB_EXCEPTION.sub(" ", title or "")))
        relevance_score = 14 + (14 if title_hit else 4) + skill_depth
        relevance_score = min(relevance_score, 30)
    else:
        relevance_score = 4
        risk_flags.append("Not an Excel/spreadsheet project — outside your service catalogue")

    # ------------------------------------------------------------------
    # 3. Budget Attractiveness (max 20 points, INR-normalized)
    # Calibrated for the ₹10,000–₹20,000 monthly income target.
    # ------------------------------------------------------------------
    if budget_inr >= 40000:
        budget_score = 20
    elif budget_inr >= 10000:
        budget_score = 18
    elif budget_inr >= 5000:
        budget_score = 15
    elif budget_inr >= 2500:
        budget_score = 12
    elif budget_inr >= 1000:
        budget_score = 8
    elif budget_inr > 0:
        budget_score = 5
    else:
        # Negotiable / unstated budget
        budget_score = 4

    # ------------------------------------------------------------------
    # 4. Project Clarity (max 10 points)
    # ------------------------------------------------------------------
    desc_len = len(description or "")
    if desc_len >= 250:
        clarity_score = 10
    elif desc_len >= 100:
        clarity_score = 7
    elif desc_len >= 40:
        clarity_score = 4
    else:
        clarity_score = 1

    # ------------------------------------------------------------------
    # 5. Client Credibility (max 15 points)
    # Real signals only: verified payments, escrow, repeat clients,
    # ratings, paid listing upgrades (featured/urgent), hiring history.
    # ------------------------------------------------------------------
    c_info = (client_info or "").lower()
    if any(pos in c_info for pos in [
        "verified", "payment confirmed", "payment verified", "repeat",
        "escrow", "featured", "established", "4.9", "4.8", "4.7", "4.6",
        "rating: 4", "rating: 5", "hires", "hired"
    ]):
        credibility_score = 15
    elif any(pos in c_info for pos in ["rating", "reviews", "company:", "buyer", "client"]):
        credibility_score = 11
    elif c_info.strip():
        credibility_score = 10
    else:
        credibility_score = 6

    # ------------------------------------------------------------------
    # 6. Deliverability with Current Skills (max 15 points)
    # ------------------------------------------------------------------
    outside_tech = [pat for pat in DISQUALIFYING_PATTERNS if re.search(pat, text, re.IGNORECASE)]
    if outside_tech:
        deliverability_score = 2
        risk_flags.append("Requires software development skills outside core Excel capability")
    else:
        deliverability_score = 15

    # ------------------------------------------------------------------
    # 7. Freshness (max 10 points) — NEW in v3
    # A 4-week-old posting is usually already awarded; fresh posts get
    # the full points so the best opportunities surface first.
    # ------------------------------------------------------------------
    posted = _parse_date_str(date_posted)
    if posted is None:
        freshness_score = 5  # unknown date — neutral
        age_days = None
    else:
        try:
            age_days = (date.today() - posted).days
        except Exception:
            age_days = None
        if age_days is None or age_days < 0:
            freshness_score = 5
        elif age_days <= 2:
            freshness_score = 10
        elif age_days <= 5:
            freshness_score = 8
        elif age_days <= 10:
            freshness_score = 6
        elif age_days <= 20:
            freshness_score = 3
            warnings.append(f"Posting is {age_days} days old — may already be awarded")
        else:
            freshness_score = 1
            warnings.append(f"Stale posting ({age_days} days old) — likely already awarded")

    # ------------------------------------------------------------------
    # Aggregate
    # ------------------------------------------------------------------
    raw_score = (
        relevance_score + budget_score + clarity_score
        + credibility_score + deliverability_score + freshness_score
    )

    # Penalties: severe flags -25 each, soft warnings -5 each
    raw_score -= len(risk_flags) * 25
    raw_score -= len(warnings) * 5
    score = min(max(raw_score, 0), 100)

    # Non-Excel jobs can never look attractive
    if not relevant:
        score = min(score, 35)

    # Classify Priority
    if risk_flags or score < 40:
        priority = "Low"
    elif score >= 70:
        priority = "High"
    else:
        priority = "Medium"

    all_flags = risk_flags + warnings
    return score, priority, all_flags, category
