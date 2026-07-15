"""
Solution: Fixing the N+1 Query Problem

Demonstrates three approaches:
  1. Original N+1 (baseline — slow)
  2. Fix A: Single JOIN query
  3. Fix B: Two-query approach with WHERE id IN (...)
"""

import time
import psycopg2
import psycopg2.extras

conn = psycopg2.connect(
    dbname="authdb", user="authuser", password="authpass", host="localhost"
)

def setup_test_data():
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY, name TEXT, email TEXT
            );
            CREATE TABLE IF NOT EXISTS posts (
                id SERIAL PRIMARY KEY, title TEXT,
                author_id INT REFERENCES users(id),
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        # Clear and repopulate
        cur.execute("TRUNCATE TABLE posts, users RESTART IDENTITY CASCADE;")
        cur.execute("INSERT INTO users (name, email) SELECT 'User ' || i, 'user' || i || '@test.com' FROM generate_series(1, 20) AS i;")
        cur.execute("INSERT INTO posts (title, author_id) SELECT 'Post ' || i, (RANDOM() * 19 + 1)::INT FROM generate_series(1, 50) AS i;")
        conn.commit()

def approach_n_plus_1() -> tuple[list, int]:
    """Original broken approach: 1 + N queries"""
    query_count = 0
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT id, title, author_id, created_at FROM posts LIMIT 50")
        query_count += 1
        posts = cur.fetchall()

        result = []
        for post in posts:
            cur.execute("SELECT name, email FROM users WHERE id = %s", (post["author_id"],))
            query_count += 1
            author = cur.fetchone()
            result.append({"title": post["title"], "author": author["name"]})

    return result, query_count

def approach_join() -> tuple[list, int]:
    """Fix A: Single JOIN — always prefer this for SQL."""
    query_count = 0
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT posts.id, posts.title, posts.created_at, users.name, users.email
            FROM posts
            JOIN users ON posts.author_id = users.id
            ORDER BY posts.id
            LIMIT 50;
        """)
        query_count += 1
        rows = cur.fetchall()
        result = [{"title": r["title"], "author": r["name"]} for r in rows]

    return result, query_count

def approach_in_clause() -> tuple[list, int]:
    """Fix B: Two queries — fetch posts, then all authors with WHERE IN."""
    query_count = 0
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT id, title, author_id FROM posts LIMIT 50")
        query_count += 1
        posts = cur.fetchall()

        author_ids = list({p["author_id"] for p in posts})
        cur.execute("SELECT id, name, email FROM users WHERE id = ANY(%s)", (author_ids,))
        query_count += 1
        authors = {u["id"]: u for u in cur.fetchall()}

        result = [
            {"title": p["title"], "author": authors[p["author_id"]]["name"]}
            for p in posts
        ]

    return result, query_count


if __name__ == "__main__":
    setup_test_data()
    print("Benchmarking three approaches for fetching 50 posts with authors:\n")

    for name, fn in [
        ("N+1 (broken)", approach_n_plus_1),
        ("JOIN (fix A)", approach_join),
        ("WHERE IN (fix B)", approach_in_clause),
    ]:
        start = time.time()
        results, query_count = fn()
        elapsed = time.time() - start
        print(f"  {name:<22} {query_count:>3} queries  {elapsed*1000:>8.1f}ms")

    print("\n📝 Key Insight: JOIN and WHERE IN both reduce 51 queries to 1-2 queries.")
    print("   In production on a remote DB (5ms RTT), N+1 adds 50 × 5ms = 250ms of pure latency overhead.")
