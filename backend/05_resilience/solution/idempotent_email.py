"""
Solution: Idempotent Email Sender with Retry

Combines tenacity's retry logic with idempotency keys to ensure:
  - Emails are retried on transient failures
  - Emails are never sent twice for the same idempotency key
"""

import random
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_log, after_log
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

# Simulated cache (Redis in production)
sent_emails: dict[str, dict] = {}

attempt_counter = 0  # Global for demo purposes


# ─────────────────────────────────────────────
# Simulate a flaky email API
# ─────────────────────────────────────────────

def flaky_send_email_api(to: str, subject: str, body: str) -> dict:
    """
    Simulates a third-party email API.
    - Raises ValueError for invalid email addresses (not retryable)
    - Raises ConnectionError 60% of the time (retryable)
    - Returns success dict on successful call
    """
    global attempt_counter
    attempt_counter += 1

    if "@" not in to:
        raise ValueError(f"Invalid email address: {to}")

    if random.random() < 0.6:
        logger.warning(f"  [API] Attempt #{attempt_counter} — ConnectionError! (transient)")
        raise ConnectionError("Email API is temporarily unavailable")

    logger.info(f"  [API] Attempt #{attempt_counter} — Success!")
    return {"message_id": f"msg_{random.randint(1000, 9999)}", "to": to, "status": "delivered"}


# ─────────────────────────────────────────────
# Retry-decorated sender
# ─────────────────────────────────────────────

@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    retry=retry_if_exception_type(ConnectionError),   # Only retry transient errors!
    reraise=True,                                     # Re-raise after all attempts exhausted
)
def _send_with_retry(to: str, subject: str, body: str) -> dict:
    """Internal sender with retry logic."""
    return flaky_send_email_api(to, subject, body)


# ─────────────────────────────────────────────
# Public API with Idempotency
# ─────────────────────────────────────────────

def send_email(idempotency_key: str, to: str, subject: str, body: str) -> dict:
    """
    Idempotent email sender.
    Calling with the same idempotency_key twice sends only ONE email.
    """
    # Check for existing send
    if idempotency_key in sent_emails:
        logger.info(f"  [CACHE HIT] Key '{idempotency_key}' already sent — skipping API call.")
        return {**sent_emails[idempotency_key], "idempotent": True}

    # Validate before retrying (ValueError is not retryable)
    if "@" not in to:
        raise ValueError(f"Invalid email address: {to}")

    logger.info(f"  [SEND] New email to {to} — attempting with retry...")
    result = _send_with_retry(to, subject, body)

    # Cache the result
    sent_emails[idempotency_key] = result
    return {**result, "idempotent": False}


# ─────────────────────────────────────────────
# Demo
# ─────────────────────────────────────────────

if __name__ == "__main__":
    random.seed(99)  # Fixed seed for reproducible demo

    print("=== Test 1: Normal send (may require retries) ===")
    attempt_counter = 0
    result = send_email("email-welcome-user-42", "alice@example.com", "Welcome!", "Hello!")
    print(f"Result: {result}\n")

    print("=== Test 2: Same idempotency key — should not call API ===")
    attempt_counter = 0
    result = send_email("email-welcome-user-42", "alice@example.com", "Welcome!", "Hello!")
    print(f"Result: {result}")
    print(f"API calls made: {attempt_counter} (should be 0)\n")

    print("=== Test 3: Invalid email — should fail immediately, no retry ===")
    attempt_counter = 0
    try:
        result = send_email("email-invalid", "not-an-email", "Hello", "Body")
    except ValueError as e:
        print(f"ValueError raised correctly: {e}")
        print(f"API calls made: {attempt_counter} (should be 0)")
