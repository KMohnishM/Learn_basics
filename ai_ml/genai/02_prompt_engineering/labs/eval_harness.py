"""
Lab: Prompt Evaluation Harness

Compares 4 prompting strategies (zero-shot, few-shot, CoT, structured output)
on a sentiment classification task and prints an accuracy comparison table.

Run: pip install openai tabulate
     export OPENAI_API_KEY=your_key
     python eval_harness.py
"""

import os
import json
import re
from openai import OpenAI
from pydantic import BaseModel

client = OpenAI()

# ─────────────────────────────────────────────
# Test Dataset
# ─────────────────────────────────────────────

DATASET = [
    {"input": "The delivery was late and the product was damaged.", "expected": "NEGATIVE"},
    {"input": "Fast shipping, great quality, highly recommend!", "expected": "POSITIVE"},
    {"input": "It arrived as described. Nothing special.", "expected": "NEUTRAL"},
    {"input": "Absolute garbage. Fell apart in an hour.", "expected": "NEGATIVE"},
    {"input": "Best purchase I've made all year!", "expected": "POSITIVE"},
    {"input": "Works fine. Does what it says on the box.", "expected": "NEUTRAL"},
    {"input": "Never buying from this seller again. Scam!", "expected": "NEGATIVE"},
    {"input": "Good value for money. Happy with it.", "expected": "POSITIVE"},
    {"input": "Average quality, average price. You get what you pay for.", "expected": "NEUTRAL"},
    {"input": "Unbelievably good! Blew my expectations out of the water!", "expected": "POSITIVE"},
]

# ─────────────────────────────────────────────
# Prompt Strategies
# ─────────────────────────────────────────────

def zero_shot(text: str) -> str:
    return f"Classify the sentiment as exactly one of: POSITIVE, NEGATIVE, or NEUTRAL.\n\nReview: \"{text}\"\nSentiment:"

def few_shot(text: str) -> str:
    return f"""Classify sentiment as POSITIVE, NEGATIVE, or NEUTRAL.

Review: "Amazing product, exceeded all my expectations!"
Sentiment: POSITIVE

Review: "Terrible quality. Broke after 2 days. Waste of money."
Sentiment: NEGATIVE

Review: "Does what it says. Nothing particularly great or bad."
Sentiment: NEUTRAL

Review: "Fast delivery but item was scratched."
Sentiment: NEGATIVE

Review: "{text}"
Sentiment:"""

def chain_of_thought(text: str) -> str:
    return f"""Classify the sentiment of this review as POSITIVE, NEGATIVE, or NEUTRAL.

Think through your reasoning, then on the final line write: "Sentiment: [LABEL]"

Review: "{text}"

Reasoning:"""

def structured_output_prompt(text: str) -> str:
    return f"Classify the sentiment of this review: \"{text}\""

# ─────────────────────────────────────────────
# Pydantic Schema for Structured Output
# ─────────────────────────────────────────────

class SentimentResult(BaseModel):
    reasoning: str
    sentiment: str  # Must be POSITIVE, NEGATIVE, or NEUTRAL

# ─────────────────────────────────────────────
# Evaluation Functions
# ─────────────────────────────────────────────

def call_model(prompt: str, temperature: float = 0.0) -> str:
    """Generic model call, returns raw text."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a sentiment classifier. Be precise."},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=200,
    )
    return response.choices[0].message.content.strip()

def extract_label(text: str) -> str:
    """Extract POSITIVE/NEGATIVE/NEUTRAL from a potentially verbose response."""
    text_upper = text.upper()
    for label in ["POSITIVE", "NEGATIVE", "NEUTRAL"]:
        if label in text_upper:
            return label
    return "UNKNOWN"

def evaluate_strategy(strategy_fn, use_structured: bool = False) -> dict:
    """Run a strategy against all examples and compute accuracy."""
    correct = 0
    results = []

    for example in DATASET:
        if use_structured:
            response = client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Classify the sentiment."},
                    {"role": "user", "content": strategy_fn(example["input"])},
                ],
                response_format=SentimentResult,
            )
            predicted = response.choices[0].message.parsed.sentiment.upper()
        else:
            raw = call_model(strategy_fn(example["input"]))
            predicted = extract_label(raw)

        is_correct = predicted == example["expected"]
        if is_correct:
            correct += 1

        results.append({
            "input": example["input"][:40] + "...",
            "expected": example["expected"],
            "predicted": predicted,
            "correct": "✅" if is_correct else "❌",
        })

    return {"accuracy": correct / len(DATASET), "results": results}

# ─────────────────────────────────────────────
# Main: Run All Strategies
# ─────────────────────────────────────────────

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Set OPENAI_API_KEY to run this lab.")
        exit()

    strategies = {
        "Zero-Shot": (zero_shot, False),
        "Few-Shot": (few_shot, False),
        "Chain-of-Thought": (chain_of_thought, False),
        "Structured Output": (structured_output_prompt, True),
    }

    print("Running evaluation across strategies...\n")
    print(f"{'Strategy':<22} {'Accuracy':>10}")
    print("-" * 35)

    for name, (fn, structured) in strategies.items():
        result = evaluate_strategy(fn, use_structured=structured)
        acc = result["accuracy"]
        print(f"{name:<22} {acc:>9.1%}")

    print("\nNote: Run multiple times to see variance (especially for CoT at temperature > 0)")
