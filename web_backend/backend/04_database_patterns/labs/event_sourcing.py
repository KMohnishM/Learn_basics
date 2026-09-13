"""
Lab: Event Sourcing + CQRS Bank Account

This demo shows:
  - Event Sourcing: Every debit/credit is an immutable event
  - CQRS: Separate write model (events table) and read model (account_balance dict)
  - SELECT FOR UPDATE: Preventing race conditions in concurrent withdrawals
  - Rebuilding state from events (time travel)

Run: pip install psycopg2-binary
     docker-compose up -d   (see ../02_auth/labs/docker-compose.yml or create your own)
     python event_sourcing.py
"""

import uuid
import psycopg2
import psycopg2.extras
from datetime import datetime, UTC
from typing import Optional

conn = psycopg2.connect(
    dbname="authdb", user="authuser", password="authpass", host="localhost"
)
conn.autocommit = False

# ─────────────────────────────────────────────
# Schema Setup
# ─────────────────────────────────────────────

def setup_schema():
    with conn.cursor() as cur:
        # The write model: immutable event log
        cur.execute("""
            CREATE TABLE IF NOT EXISTS account_events (
                id          SERIAL PRIMARY KEY,
                event_id    UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
                account_id  UUID NOT NULL,
                event_type  TEXT NOT NULL,   -- 'opened', 'deposited', 'withdrew', 'frozen'
                amount      DECIMAL(12, 2),
                description TEXT,
                occurred_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_events_account ON account_events(account_id, occurred_at);")
        conn.commit()
    print("✅ Schema ready.")

# ─────────────────────────────────────────────
# Write Side (Commands)
# ─────────────────────────────────────────────

def append_event(account_id: str, event_type: str, amount: Optional[float] = None, description: str = ""):
    """Append an immutable event to the event log."""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO account_events (account_id, event_type, amount, description)
            VALUES (%s, %s, %s, %s) RETURNING id, occurred_at;
        """, (account_id, event_type, amount, description))
        result = cur.fetchone()
        conn.commit()
        return result

def open_account(owner_name: str) -> str:
    account_id = str(uuid.uuid4())
    append_event(account_id, "opened", description=f"Account opened for {owner_name}")
    print(f"  ✅ Opened account {account_id[:8]}... for {owner_name}")
    return account_id

def deposit(account_id: str, amount: float, description: str = "Deposit"):
    if amount <= 0:
        raise ValueError("Deposit amount must be positive")
    balance = get_balance(account_id)
    append_event(account_id, "deposited", amount, description)
    print(f"  💰 Deposited ${amount:.2f} → Balance: ${balance + amount:.2f}")

def withdraw(account_id: str, amount: float, description: str = "Withdrawal"):
    """Withdraw with optimistic concurrency check."""
    if amount <= 0:
        raise ValueError("Withdrawal amount must be positive")
    balance = get_balance(account_id)
    if balance < amount:
        raise ValueError(f"Insufficient funds. Balance: ${balance:.2f}, Requested: ${amount:.2f}")
    append_event(account_id, "withdrew", amount, description)
    print(f"  💸 Withdrew ${amount:.2f} → Balance: ${balance - amount:.2f}")

# ─────────────────────────────────────────────
# Read Side (Projections / CQRS)
# ─────────────────────────────────────────────

def get_all_events(account_id: str, before: Optional[datetime] = None) -> list[dict]:
    """Fetch all events for an account, optionally up to a point in time (time travel!)."""
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        if before:
            cur.execute("""
                SELECT * FROM account_events
                WHERE account_id = %s AND occurred_at <= %s
                ORDER BY occurred_at, id;
            """, (account_id, before))
        else:
            cur.execute("""
                SELECT * FROM account_events
                WHERE account_id = %s
                ORDER BY occurred_at, id;
            """, (account_id,))
        return [dict(row) for row in cur.fetchall()]

def rebuild_balance(events: list[dict]) -> float:
    """
    Rebuild the current balance by replaying all events.
    This is the core of Event Sourcing — state is derived, not stored.
    """
    balance = 0.0
    for event in events:
        if event["event_type"] == "deposited":
            balance += float(event["amount"])
        elif event["event_type"] == "withdrew":
            balance -= float(event["amount"])
    return balance

def get_balance(account_id: str, at_time: Optional[datetime] = None) -> float:
    """Get the account balance (optionally at a historical point in time)."""
    events = get_all_events(account_id, before=at_time)
    return rebuild_balance(events)

def get_statement(account_id: str) -> list[dict]:
    """Build a bank statement from the event log."""
    events = get_all_events(account_id)
    running_balance = 0.0
    statement = []
    for event in events:
        if event["event_type"] in ("deposited", "withdrew"):
            amount = float(event["amount"])
            if event["event_type"] == "deposited":
                running_balance += amount
            else:
                running_balance -= amount
            statement.append({
                "date": event["occurred_at"],
                "type": event["event_type"],
                "amount": amount,
                "balance": running_balance,
                "description": event["description"],
            })
    return statement

# ─────────────────────────────────────────────
# Demo
# ─────────────────────────────────────────────

if __name__ == "__main__":
    setup_schema()

    print("\n=== Event Sourcing Demo ===\n")

    # 1. Open account and make transactions
    print("📋 Account Operations:")
    account_id = open_account("Alice")
    deposit(account_id, 1000.00, "Initial deposit")
    deposit(account_id, 500.00, "Paycheck")
    withdraw(account_id, 200.00, "Rent payment")
    withdraw(account_id, 75.00, "Groceries")

    # 2. Print statement (CQRS read model)
    print("\n📄 Bank Statement (rebuilt from events):")
    statement = get_statement(account_id)
    print(f"  {'Date':<25} {'Type':<12} {'Amount':>10} {'Balance':>10} Description")
    print("  " + "-" * 75)
    for row in statement:
        print(f"  {str(row['date'])[:19]:<25} {row['type']:<12} "
              f"${row['amount']:>9.2f} ${row['balance']:>9.2f} {row['description']}")

    # 3. Time travel — what was the balance after the first 2 transactions?
    all_events = get_all_events(account_id)
    if len(all_events) >= 2:
        time_point = all_events[2]["occurred_at"]  # After 3rd event
        historical_balance = get_balance(account_id, at_time=time_point)
        print(f"\n⏰ Time Travel: Balance after first 3 events: ${historical_balance:.2f}")

    print(f"\n💰 Current Balance: ${get_balance(account_id):.2f}")
