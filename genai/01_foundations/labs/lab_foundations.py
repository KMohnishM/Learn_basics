"""
Lab: LLM Foundations — Connecting to providers, measuring tokens, and understanding sampling.

Prerequisites:
  pip install openai anthropic tiktoken

Optional (for local models):
  Install Ollama from https://ollama.ai and run: ollama pull llama3.2
"""

import os
import time
import tiktoken
from openai import OpenAI

# ─────────────────────────────────────────────
# PART 1: Counting Tokens Before Sending
# ─────────────────────────────────────────────

def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Count tokens in a string without making an API call."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def estimate_cost(prompt: str, model: str = "gpt-4o-mini") -> dict:
    """Estimate API cost before sending a request."""
    prices = {
        "gpt-4o":        {"input": 2.50,  "output": 10.00},  # per 1M tokens
        "gpt-4o-mini":   {"input": 0.15,  "output": 0.60},
        "gpt-3.5-turbo": {"input": 0.50,  "output": 1.50},
    }
    token_count = count_tokens(prompt, model)
    price = prices.get(model, prices["gpt-4o-mini"])
    cost = (token_count / 1_000_000) * price["input"]
    return {"tokens": token_count, "estimated_cost_usd": round(cost, 6)}

print("=" * 60)
print("PART 1: Token Counting")
print("=" * 60)

sample_texts = [
    "Hello, world!",
    "The attention mechanism in Transformers allows each token to attend to every other token in the sequence.",
    "Explain the difference between supervised and unsupervised learning in detail.",
]

for text in sample_texts:
    result = estimate_cost(text)
    print(f"\nText: '{text[:50]}...' " if len(text) > 50 else f"\nText: '{text}'")
    print(f"  Tokens: {result['tokens']}")
    print(f"  Estimated input cost (gpt-4o-mini): ${result['estimated_cost_usd']}")

# ─────────────────────────────────────────────
# PART 2: Temperature Effect
# ─────────────────────────────────────────────

print("\n" + "=" * 60)
print("PART 2: Temperature — How It Affects Output Diversity")
print("=" * 60)

def query_with_temperature(prompt: str, temperature: float, n: int = 3) -> list[str]:
    """
    Query the same prompt multiple times at a given temperature.
    At temperature=0, all responses should be identical.
    At temperature=1.5, they should be quite different.
    """
    client = OpenAI()
    responses = []
    for i in range(n):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=50,
        )
        responses.append(response.choices[0].message.content.strip())
    return responses

# Only run this if OPENAI_API_KEY is set
if os.getenv("OPENAI_API_KEY"):
    prompt = "Complete this sentence creatively: 'The robot walked into the bar and'"

    for temp in [0.0, 0.7, 1.5]:
        print(f"\nTemperature = {temp}:")
        responses = query_with_temperature(prompt, temp)
        for i, r in enumerate(responses, 1):
            print(f"  Run {i}: {r}")
else:
    print("\n⚠️  Set OPENAI_API_KEY to run the API sections.")
    print("   You can still run Part 1 (token counting) without an API key.")

# ─────────────────────────────────────────────
# PART 3: Model Comparison (Quality vs Cost)
# ─────────────────────────────────────────────

print("\n" + "=" * 60)
print("PART 3: Model Comparison — Quality vs Latency vs Cost")
print("=" * 60)

def benchmark_model(model: str, prompt: str) -> dict:
    client = OpenAI()
    start = time.time()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Be concise."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200,
    )
    latency = time.time() - start
    return {
        "model": model,
        "latency_sec": round(latency, 2),
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
        "response": response.choices[0].message.content.strip(),
    }

if os.getenv("OPENAI_API_KEY"):
    test_prompt = "What is a binary search tree and what is its time complexity for search?"
    models = ["gpt-4o-mini", "gpt-4o"]

    print(f"\nPrompt: '{test_prompt}'\n")
    for model in models:
        result = benchmark_model(model, test_prompt)
        print(f"Model: {result['model']}")
        print(f"  Latency: {result['latency_sec']}s")
        print(f"  Tokens: {result['input_tokens']} in / {result['output_tokens']} out")
        print(f"  Response: {result['response'][:100]}...")
        print()

# ─────────────────────────────────────────────
# PART 4: Using Ollama (100% Free, Local)
# ─────────────────────────────────────────────

print("=" * 60)
print("PART 4: Ollama — Running LLMs Locally for Free")
print("=" * 60)
print("""
To use Ollama:
  1. Install from https://ollama.ai
  2. Run: ollama pull llama3.2
  3. Uncomment and run the code below

from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
response = client.chat.completions.create(
    model="llama3.2",
    messages=[{"role": "user", "content": "What is an LLM?"}],
    temperature=0.7,
)
print(response.choices[0].message.content)
""")
