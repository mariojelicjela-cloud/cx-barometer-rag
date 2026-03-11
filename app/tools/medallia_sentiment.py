from pathlib import Path


NEGATIVE_KEYWORDS = [
    "unstable",
    "slow",
    "outage",
    "interruptions",
    "complaint",
    "not resolved",
    "unclear",
    "confusing",
    "frustration",
    "problem",
    "billing issue",
    "too long",
    "degraded",
]

POSITIVE_KEYWORDS = [
    "satisfied",
    "stable",
    "fast",
    "clear",
    "helpful",
    "professional",
    "improved",
    "working well",
    "no complaints",
    "good",
]


def load_medallia_text() -> str:
    path = Path("data/seed/medallia_feedback.md")
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def extract_customer_comments(customer_id: str) -> list[str]:
    text = load_medallia_text()
    if not text:
        return []

    sections = text.split("---")
    customer_comments = []

    for section in sections:
        if f"customer_id: {customer_id}" in section.lower():
            lines = [line.strip() for line in section.splitlines() if line.strip()]
            current_comment = []
            collecting = False

            for line in lines:
                if line.lower().startswith("survey comment:"):
                    if current_comment:
                        customer_comments.append(" ".join(current_comment).strip())
                        current_comment = []
                    collecting = True
                    remainder = line[len("survey comment:"):].strip()
                    if remainder:
                        current_comment.append(remainder)
                elif collecting:
                    current_comment.append(line)

            if current_comment:
                customer_comments.append(" ".join(current_comment).strip())

    return customer_comments


def score_medallia_sentiment(customer_id: str):
    comments = extract_customer_comments(customer_id)

    if not comments:
        return {
            "customer_id": customer_id,
            "sentiment_score": 0,
            "sentiment_label": "unknown",
            "negative_hits": 0,
            "positive_hits": 0,
            "comment_count": 0,
            "summary": "No Medallia comments found.",
        }

    full_text = " ".join(comments).lower()

    negative_hits = sum(1 for kw in NEGATIVE_KEYWORDS if kw in full_text)
    positive_hits = sum(1 for kw in POSITIVE_KEYWORDS if kw in full_text)

    score = positive_hits - negative_hits

    if score <= -3:
        label = "red"
    elif score <= -1:
        label = "yellow"
    else:
        label = "green"

    return {
        "customer_id": customer_id,
        "sentiment_score": score,
        "sentiment_label": label,
        "negative_hits": negative_hits,
        "positive_hits": positive_hits,
        "comment_count": len(comments),
        "summary": f"Detected {negative_hits} negative and {positive_hits} positive keyword signals across {len(comments)} Medallia comments.",
    }