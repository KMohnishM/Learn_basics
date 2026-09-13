"""
Lab: REST vs GraphQL API — Same Data, Two Interfaces

This single FastAPI app exposes:
  - REST endpoints: /api/v1/posts, /api/v1/users/{id}
  - GraphQL endpoint: /graphql (via Strawberry)

Run: pip install fastapi uvicorn strawberry-graphql
     uvicorn lab_api:app --reload
"""

import time
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import strawberry
from strawberry.fastapi import GraphQLRouter

app = FastAPI(title="API Design Lab", version="1.0")

# ─────────────────────────────────────────────
# Fake In-Memory Database
# ─────────────────────────────────────────────

USERS = {
    1: {"id": 1, "name": "Alice Chen", "email": "alice@example.com", "bio": "Engineer", "followers": 1200},
    2: {"id": 2, "name": "Bob Martin", "email": "bob@example.com", "bio": "Designer", "followers": 890},
    3: {"id": 3, "name": "Carol White", "email": "carol@example.com", "bio": "PM", "followers": 350},
}

POSTS = [
    {"id": 1, "title": "Building Scalable APIs", "body": "REST vs GraphQL...", "author_id": 1, "likes": 142, "views": 5000},
    {"id": 2, "title": "Design Systems in 2024", "body": "Component libraries...", "author_id": 2, "likes": 89, "views": 2200},
    {"id": 3, "title": "The PM's Dilemma", "body": "Roadmaps and reality...", "author_id": 3, "likes": 67, "views": 1800},
    {"id": 4, "title": "Async Python Patterns", "body": "asyncio deep dive...", "author_id": 1, "likes": 201, "views": 8900},
]

# ─────────────────────────────────────────────
# PART 1: REST API
# ─────────────────────────────────────────────

@app.get("/api/v1/posts", tags=["REST"])
def get_posts(
    limit: int = Query(default=10, le=100),
    after: Optional[int] = Query(default=None, description="Cursor: last seen post ID"),
):
    """
    REST endpoint with cursor-based pagination.

    Notice: The client ALWAYS gets all fields (id, title, body, author_id, likes, views).
    That's the over-fetching problem — even if you only need title and likes.
    """
    posts = POSTS
    if after:
        posts = [p for p in posts if p["id"] > after]

    page = posts[:limit]
    next_cursor = page[-1]["id"] if len(page) == limit else None

    return {
        "data": page,
        "pagination": {
            "has_next_page": next_cursor is not None,
            "next_cursor": next_cursor,
        }
    }

@app.get("/api/v1/users/{user_id}", tags=["REST"])
def get_user(user_id: int):
    """
    Fetch a single user.

    To get posts + authors in REST, you'd need:
      1. GET /api/v1/posts     (N+1 problem: need author for each post)
      2. GET /api/v1/users/1
      3. GET /api/v1/users/2
      4. ...
    """
    user = USERS.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return user

@app.post("/api/v1/users", status_code=201, tags=["REST"])
def create_user(name: str, email: str):
    """
    Create user. Returns 201 with Location header pointing to the new resource.
    """
    new_id = max(USERS.keys()) + 1
    USERS[new_id] = {"id": new_id, "name": name, "email": email, "bio": "", "followers": 0}
    return JSONResponse(
        status_code=201,
        content=USERS[new_id],
        headers={"Location": f"/api/v1/users/{new_id}"}
    )

# ─────────────────────────────────────────────
# PART 2: GraphQL API (via Strawberry)
# ─────────────────────────────────────────────

@strawberry.type
class User:
    id: int
    name: str
    email: str
    bio: str
    followers: int

@strawberry.type
class Post:
    id: int
    title: str
    body: str
    likes: int
    views: int
    author_id: int

    @strawberry.field
    def author(self) -> Optional[User]:
        """
        This resolver is called per post.
        Without DataLoader, this would be N+1 queries!
        In this demo we use the in-memory dict, but in a real DB you'd see the problem.
        """
        user_data = USERS.get(self.author_id)
        if user_data:
            return User(**user_data)
        return None

@strawberry.type
class Query:
    @strawberry.field
    def posts(self, limit: int = 10) -> list[Post]:
        """
        GraphQL resolver: client decides WHICH fields to return!

        Try querying with just { id title } vs { id title author { name } }
        and see the difference in response payload size.
        """
        return [Post(**p) for p in POSTS[:limit]]

    @strawberry.field
    def user(self, user_id: int) -> Optional[User]:
        user_data = USERS.get(user_id)
        return User(**user_data) if user_data else None

schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

# ─────────────────────────────────────────────
# Try these queries at http://localhost:8000/graphql
# ─────────────────────────────────────────────
"""
# Query 1: Over-fetching comparison
# REST always returns all fields. GraphQL returns only what you ask for.

query MobileFeed {
  posts(limit: 4) {
    id
    title
    likes
    author {
      name
    }
  }
}

# Query 2: Nested data in ONE request (vs N+1 in REST)
query PostsWithAuthors {
  posts {
    title
    author {
      name
      email
      followers
    }
  }
}
"""
