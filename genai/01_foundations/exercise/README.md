# Exercise: Token Budget Enforcer

## Background

Every LLM API call costs money. In production, an engineer's worst nightmare is a runaway process that generates millions of tokens and runs up a $3,000 AWS bill overnight.

The solution is a **Token Budget Enforcer** — a wrapper around any LLM call that enforces a maximum token budget and raises an error before making the API call if the prompt alone would exceed the budget.

## Your Task

Write a Python class `TokenBudget` in `solution/token_budget.py` that:

1. Accepts a `max_tokens` parameter on init (the total budget for input + output combined).
2. Has a method `check(prompt: str, model: str, reserved_for_output: int)` that:
   - Counts the tokens in the prompt
   - Checks if `prompt_tokens + reserved_for_output > max_tokens`
   - Raises a `TokenBudgetExceededError` if the budget is exceeded
   - Returns the number of prompt tokens if within budget
3. Has a method `safe_call(prompt: str, model: str, reserved_for_output: int = 500)` that:
   - Calls `check()` first
   - Only proceeds to make the OpenAI API call if the budget is fine
   - Returns the response

## Example Usage

```python
budget = TokenBudget(max_tokens=1000)

# This should succeed (~10 tokens in prompt, 500 reserved for output = 510 total < 1000)
result = budget.safe_call("What is 2 + 2?", model="gpt-4o-mini")
print(result)

# This should FAIL before making any API call
long_prompt = "Explain quantum computing. " * 200  # ~1400 tokens
result = budget.safe_call(long_prompt, model="gpt-4o-mini")
# Should raise: TokenBudgetExceededError: Prompt (1400 tokens) + reserved output (500) = 1900 > budget (1000)
```

Check `solution/token_budget.py` when done!
