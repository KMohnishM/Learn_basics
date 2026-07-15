"""
Lab: Preparing a Fine-Tuning Dataset

This script shows how to:
  1. Generate a fine-tuning dataset using GPT-4o-mini (synthetic data generation)
  2. Format it correctly for Hugging Face SFT (Alpaca format)
  3. Validate dataset quality
  4. Split into train/val sets

This is the most underrated step — data quality determines fine-tuning quality.

Run: pip install openai datasets
     export OPENAI_API_KEY=your_key
     python prepare_dataset.py
"""

import os
import json
import random
from openai import OpenAI

client = OpenAI()

# ─────────────────────────────────────────────
# Step 1: Define what behavior we want to teach
# ─────────────────────────────────────────────

# We want a model that classifies Python code snippets by their purpose
CLASSIFICATION_LABELS = [
    "data_processing",
    "api_call",
    "file_io",
    "authentication",
    "database_query",
    "error_handling",
]

CODE_GENERATION_PROMPT = """Generate a realistic Python code snippet that demonstrates {label}.

Rules:
- 5-20 lines of code
- Include realistic variable names and comments
- Do NOT include any explanation, just the code

Code:"""

ANNOTATION_PROMPT = """You are a code classifier. Classify this Python code snippet into exactly one category.

Categories: {categories}

Code:
```python
{code}
```

Respond with only the category name, nothing else."""

# ─────────────────────────────────────────────
# Step 2: Generate synthetic training examples
# ─────────────────────────────────────────────

def generate_code_snippet(label: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": CODE_GENERATION_PROMPT.format(label=label)}],
        temperature=0.9,   # High diversity for varied examples
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()

def format_as_alpaca(code: str, label: str) -> dict:
    """Format a single example in Alpaca instruction format."""
    return {
        "instruction": f"Classify this Python code snippet into one of: {', '.join(CLASSIFICATION_LABELS)}",
        "input": code,
        "output": label,
    }

# ─────────────────────────────────────────────
# Step 3: Validate data quality
# ─────────────────────────────────────────────

def validate_example(example: dict) -> tuple[bool, str]:
    """Check if an example meets quality standards."""
    if not example.get("instruction"):
        return False, "Missing instruction"
    if not example.get("input") or len(example["input"]) < 20:
        return False, "Input too short"
    if example.get("output") not in CLASSIFICATION_LABELS:
        return False, f"Invalid label: {example.get('output')}"
    if len(example["input"].split()) > 500:
        return False, "Input too long"
    return True, "OK"

# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def create_dataset(examples_per_label: int = 5) -> list[dict]:
    """Generate a balanced dataset with examples_per_label examples per class."""
    dataset = []
    print(f"Generating {examples_per_label} examples per label × {len(CLASSIFICATION_LABELS)} labels...")

    for label in CLASSIFICATION_LABELS:
        for i in range(examples_per_label):
            code = generate_code_snippet(label)
            example = format_as_alpaca(code, label)

            valid, reason = validate_example(example)
            if valid:
                dataset.append(example)
                print(f"  ✅ [{label}] Example {i+1}/{examples_per_label}")
            else:
                print(f"  ❌ [{label}] Example {i+1} rejected: {reason}")

    return dataset

def save_dataset(dataset: list[dict], path: str = "dataset.jsonl"):
    """Save as JSONL (one JSON object per line — the standard format)."""
    with open(path, "w") as f:
        for example in dataset:
            f.write(json.dumps(example) + "\n")
    print(f"\n✅ Saved {len(dataset)} examples to {path}")

def train_val_split(dataset: list[dict], val_ratio: float = 0.1) -> tuple[list, list]:
    random.shuffle(dataset)
    split_idx = int(len(dataset) * (1 - val_ratio))
    return dataset[:split_idx], dataset[split_idx:]

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY to run this lab.")
        exit()

    dataset = create_dataset(examples_per_label=3)  # 3 examples per label for demo

    train, val = train_val_split(dataset)
    save_dataset(train, "train.jsonl")
    save_dataset(val, "val.jsonl")

    print(f"\nDataset Stats:")
    print(f"  Total:      {len(dataset)} examples")
    print(f"  Train:      {len(train)} examples")
    print(f"  Validation: {len(val)} examples")

    print("\nNext: Use train.jsonl with QLoRA on Google Colab!")
    print("Colab notebook: https://colab.research.google.com/drive/...")
