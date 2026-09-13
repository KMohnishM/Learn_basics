"""
Solution: Self-Consistency Voting for Support Ticket Classification

Runs n independent LLM calls and votes on the majority label.
Flags low-confidence results for human review.
"""

from collections import Counter
from openai import OpenAI

client = OpenAI()

CATEGORIES = ["BILLING", "TECHNICAL", "SHIPPING", "RETURNS", "GENERAL"]

SYSTEM_PROMPT = """You are a support ticket classifier. 
Classify the given ticket into exactly one of these categories:
BILLING, TECHNICAL, SHIPPING, RETURNS, GENERAL

Respond with only the category name. No explanation, no punctuation."""

def classify_once(ticket: str) -> str:
    """Single LLM classification call."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": ticket},
        ],
        temperature=0.7,   # Diversity is intentional here!
        max_tokens=10,
    )
    label = response.choices[0].message.content.strip().upper()
    # Validate the label
    return label if label in CATEGORIES else "GENERAL"

def classify_with_voting(ticket: str, n: int = 5, confidence_threshold: float = 0.6) -> dict:
    """
    Classify a ticket using self-consistency voting.
    
    Returns:
        {
            "label": str | "HUMAN_REVIEW",
            "confidence": float,
            "votes": dict,
            "needs_human_review": bool
        }
    """
    votes = [classify_once(ticket) for _ in range(n)]
    vote_counts = Counter(votes)
    top_label, top_count = vote_counts.most_common(1)[0]
    confidence = top_count / n

    if confidence < confidence_threshold:
        return {
            "label": "HUMAN_REVIEW",
            "confidence": confidence,
            "votes": dict(vote_counts),
            "needs_human_review": True,
        }

    return {
        "label": top_label,
        "confidence": confidence,
        "votes": dict(vote_counts),
        "needs_human_review": False,
    }


# ─────────────────────────────────────────────
# Demo
# ─────────────────────────────────────────────
if __name__ == "__main__":
    tickets = [
        "I was charged twice for my last order. Please refund the duplicate.",
        "The app crashes every time I try to log in on iOS 17.",
        "My package was supposed to arrive 3 days ago and tracking shows 'delayed'",
        "I want to return a jacket I bought last week. It doesn't fit.",
        "Do you have a physical store in Mumbai?",
    ]

    expected = ["BILLING", "TECHNICAL", "SHIPPING", "RETURNS", "GENERAL"]

    print(f"{'Ticket':<55} {'Label':<15} {'Conf':>6}  {'Review'}")
    print("-" * 95)

    for ticket, exp in zip(tickets, expected):
        result = classify_with_voting(ticket, n=5)
        icon = "✅" if result["label"] == exp and not result["needs_human_review"] else "⚠️ "
        review = "🚨 HUMAN" if result["needs_human_review"] else ""
        print(f"{icon} {ticket[:52]:<52} {result['label']:<15} {result['confidence']:>5.0%}  {review}")
