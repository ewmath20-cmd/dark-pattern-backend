import requests
from bs4 import BeautifulSoup

# ── Dark Pattern Rules ──────────────────────────────────

URGENCY_KEYWORDS = [
    "limited time", "hurry", "only left", "act now",
    "expires soon", "last chance", "today only",
    "while stocks last", "selling fast", "almost gone"
]

TRICK_QUESTION_KEYWORDS = [
    "uncheck to not", "untick to opt out",
    "do not uncheck", "unsubscribe by unchecking"
]

PRIVACY_KEYWORDS = [
    "share with partners", "share with third parties",
    "share your data", "share information with",
    "we may share", "trusted partners"
]


def fetch_html(url):
    """Fetch the HTML content of a URL."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=8)
        return response.text
    except Exception as e:
        return None


def check_forced_consent(soup):
    """Detect pre-checked checkboxes."""
    issues = []
    checkboxes = soup.find_all("input", {"type": "checkbox"})
    for box in checkboxes:
        if box.get("checked") is not None:
            label = box.find_next("label")
            label_text = label.get_text(strip=True) if label else "Unknown checkbox"
            issues.append({
                "pattern": "Forced Consent",
                "detail": f'Pre-checked checkbox found: "{label_text[:60]}"',
                "suggestion": "Checkboxes should be unchecked by default. Let users actively opt in."
            })
    return issues


def check_urgency(soup):
    """Detect urgency/scarcity language."""
    issues = []
    page_text = soup.get_text().lower()
    found = [kw for kw in URGENCY_KEYWORDS if kw in page_text]
    if found:
        issues.append({
            "pattern": "Urgency / Scarcity Trick",
            "detail": f'Urgency language detected: {", ".join(found[:3])}',
            "suggestion": "Avoid artificial urgency. Give users time to make informed decisions."
        })
    return issues


def check_hidden_unsubscribe(soup):
    """Detect missing unsubscribe or cancel options."""
    issues = []
    page_text = soup.get_text().lower()
    links = [a.get_text().lower() for a in soup.find_all("a")]
    all_text = page_text + " ".join(links)

    has_unsubscribe = any(
        word in all_text for word in ["unsubscribe", "cancel", "opt out", "opt-out"]
    )

    # Only flag subscription/account pages
    is_relevant = any(
        word in page_text for word in ["subscribe", "newsletter", "account", "membership"]
    )

    if is_relevant and not has_unsubscribe:
        issues.append({
            "pattern": "Hidden Unsubscribe",
            "detail": "Subscription-related page has no visible unsubscribe or cancel option.",
            "suggestion": "Always provide a clear, easy-to-find unsubscribe or cancel link."
        })
    return issues


def check_trick_questions(soup):
    """Detect confusing double-negative opt-out language."""
    issues = []
    page_text = soup.get_text().lower()
    found = [kw for kw in TRICK_QUESTION_KEYWORDS if kw in page_text]
    if found:
        issues.append({
            "pattern": "Trick Question",
            "detail": f'Confusing opt-out language found: "{found[0]}"',
            "suggestion": "Use clear, plain language. Avoid double negatives in consent options."
        })
    return issues


def check_privacy_zuckering(soup):
    """Detect vague data sharing language."""
    issues = []
    page_text = soup.get_text().lower()
    found = [kw for kw in PRIVACY_KEYWORDS if kw in page_text]
    if found:
        issues.append({
            "pattern": "Privacy Zuckering",
            "detail": f'Vague data sharing language: "{found[0]}"',
            "suggestion": "Be specific about what data is shared, with whom, and why."
        })
    return issues


def calculate_score(issues):
    """
    Score from 0 (clean) to 100 (very manipulative).
    Each issue adds points based on severity.
    """
    severity = {
        "Forced Consent": 20,
        "Urgency / Scarcity Trick": 15,
        "Hidden Unsubscribe": 20,
        "Trick Question": 25,
        "Privacy Zuckering": 20,
    }
    total = 0
    for issue in issues:
        total += severity.get(issue["pattern"], 10)
    return min(total, 100)  # Cap at 100


def get_risk_label(score):
    if score == 0:
        return "✅ Clean"
    elif score <= 30:
        return "🟡 Low Risk"
    elif score <= 60:
        return "🟠 Medium Risk"
    else:
        return "🔴 High Risk"


# ── Main Analyze Function ───────────────────────────────

def analyze_url(url):
    html = fetch_html(url)

    if not html:
        return {
            "error": "Could not fetch the URL. Check if it is valid and accessible."
        }

    soup = BeautifulSoup(html, "html.parser")

    # Run all checks
    issues = []
    issues += check_forced_consent(soup)
    issues += check_urgency(soup)
    issues += check_hidden_unsubscribe(soup)
    issues += check_trick_questions(soup)
    issues += check_privacy_zuckering(soup)

    score = calculate_score(issues)
    risk = get_risk_label(score)

    return {
        "url": url,
        "score": score,
        "risk": risk,
        "total_issues": len(issues),
        "patterns": issues
    }
