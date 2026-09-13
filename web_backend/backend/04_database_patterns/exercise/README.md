# Exercise: Find and Fix the N+1 Problem

## The Scenario

You're given a slow API endpoint. Users are complaining it takes 3-4 seconds to load. Your job is to find the N+1 query problem and fix it.

## The Code

```python
# The "slow" endpoint
@app.get("/posts")
def get_posts_with_authors():
    posts = db.execute("SELECT id, title, author_id, created_at FROM posts LIMIT 50").fetchall()
    
    result = []
    for post in posts:
        # N+1: One query per post to get the author
        author = db.execute(
            "SELECT name, email FROM users WHERE id = %s", 
            (post["author_id"],)
        ).fetchone()
        
        result.append({
            "id": post["id"],
            "title": post["title"],
            "author_name": author["name"],
            "created_at": post["created_at"],
        })
    
    return result
```

## Your Task

1. **Identify**: How many SQL queries does this generate for 50 posts?
2. **Fix Option A**: Rewrite using a single SQL JOIN.
3. **Fix Option B**: Use a two-query approach (fetch all posts, then fetch all relevant authors in one `WHERE id IN (...)` query).
4. **Benchmark**: Using Python's `time` module, measure the before and after.

Write your solution in `solution/fix_n_plus_1.py` as a standalone script using psycopg2.

**Setup the test data first:**

```sql
CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT, email TEXT);
CREATE TABLE posts (id SERIAL PRIMARY KEY, title TEXT, author_id INT REFERENCES users(id), created_at TIMESTAMPTZ DEFAULT NOW());

INSERT INTO users (name, email) SELECT 'User ' || i, 'user' || i || '@test.com' FROM generate_series(1, 20) AS i;
INSERT INTO posts (title, author_id) SELECT 'Post ' || i, (RANDOM() * 19 + 1)::INT FROM generate_series(1, 50) AS i;
```
