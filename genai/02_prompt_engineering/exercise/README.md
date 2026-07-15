# Exercise: Self-Consistency Voting

## The Problem

Your team is using an LLM to classify support tickets into one of 5 categories:
- `BILLING` — payment, refunds, invoices
- `TECHNICAL` — bugs, errors, setup issues
- `SHIPPING` — delivery, tracking, lost packages
- `RETURNS` — return requests, exchange
- `GENERAL` — everything else

The model gets it right ~85% of the time with a single call. But for tickets that get misclassified, it costs the team an average of 30 minutes to reroute them. With 1000 tickets/day, that's significant.

You want to push accuracy above 95% using **Self-Consistency**.

## Your Task

Write `solution/self_consistent_classifier.py` that:

1. Classifies a support ticket using `n=5` independent LLM calls with `temperature=0.7`.
2. Extracts just the category label from each response.
3. Returns the majority vote as the final classification.
4. Returns a **confidence score** (`majority_count / n`) alongside the label.
5. If confidence < 0.6 (no clear majority), flags the ticket for human review instead of guessing.

## Starter Tickets to Test With

```python
tickets = [
    "I was charged twice for my last order. Please refund the duplicate.",       # BILLING
    "The app crashes every time I try to log in on iOS 17.",                     # TECHNICAL
    "My package was supposed to arrive 3 days ago and tracking shows 'delayed'", # SHIPPING
    "I want to return a jacket I bought last week. It doesn't fit.",              # RETURNS
    "Do you have a physical store in Mumbai?",                                   # GENERAL
]
```
