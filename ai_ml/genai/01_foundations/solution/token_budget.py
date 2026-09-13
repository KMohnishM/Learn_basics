"""
Solution: Token Budget Enforcer

Prevents runaway LLM costs by checking token counts BEFORE making API calls.
"""

import tiktoken
from openai import OpenAI


class TokenBudgetExceededError(Exception):
    """Raised when a prompt would exceed the configured token budget."""
    pass


class TokenBudget:
    def __init__(self, max_tokens: int):
        """
        Args:
            max_tokens: The maximum combined budget for input + output tokens.
        """
        self.max_tokens = max_tokens

    def _count_tokens(self, text: str, model: str) -> int:
        """Count tokens in text using tiktoken."""
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fall back to cl100k_base for unknown models
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

    def check(self, prompt: str, model: str, reserved_for_output: int = 500) -> int:
        """
        Check if a prompt fits within the token budget.

        Returns:
            Number of prompt tokens if within budget.

        Raises:
            TokenBudgetExceededError: If the budget would be exceeded.
        """
        prompt_tokens = self._count_tokens(prompt, model)
        total = prompt_tokens + reserved_for_output

        if total > self.max_tokens:
            raise TokenBudgetExceededError(
                f"Prompt ({prompt_tokens} tokens) + reserved output ({reserved_for_output}) "
                f"= {total} > budget ({self.max_tokens})"
            )

        return prompt_tokens

    def safe_call(
        self,
        prompt: str,
        model: str = "gpt-4o-mini",
        reserved_for_output: int = 500,
        system: str = "You are a helpful assistant.",
    ) -> str:
        """
        Make an LLM API call only if within token budget.

        Args:
            prompt: The user's prompt.
            model: The OpenAI model to use.
            reserved_for_output: How many tokens to reserve for the response.
            system: The system message.

        Returns:
            The LLM's response text.
        """
        # This check raises BEFORE any API call if over budget
        prompt_tokens = self.check(prompt, model, reserved_for_output)
        print(f"✅ Budget check passed: {prompt_tokens} input tokens, "
              f"{reserved_for_output} reserved = {prompt_tokens + reserved_for_output} "
              f"/ {self.max_tokens} total budget")

        client = OpenAI()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            max_tokens=reserved_for_output,
        )
        return response.choices[0].message.content


# ─────────────────────────────────────────────
# Demo
# ─────────────────────────────────────────────
if __name__ == "__main__":
    budget = TokenBudget(max_tokens=1000)

    print("Test 1: Short prompt (should succeed)")
    try:
        result = budget.safe_call("What is 2 + 2?", model="gpt-4o-mini")
        print(f"Response: {result}\n")
    except TokenBudgetExceededError as e:
        print(f"Budget exceeded: {e}\n")

    print("Test 2: Long prompt (should fail BEFORE API call)")
    long_prompt = "Explain quantum computing in extreme detail. " * 50
    try:
        result = budget.safe_call(long_prompt, model="gpt-4o-mini")
        print(f"Response: {result}\n")
    except TokenBudgetExceededError as e:
        print(f"❌ Budget exceeded (no API call made): {e}\n")
