# Exercise: Write-Through Cache

In the lab, we implemented a **Cache-Aside** pattern. 
When data is requested, we check the cache. If it's not there, we fetch from the DB and populate the cache.

But what happens when data is UPDATED?
In Cache-Aside, an update usually means we write to the DB, and then `DELETE` the cache key (Invalidation). The next person who reads the data will experience a slow Cache Miss.

## Your Task

Implement a **Write-Through** Cache for a `POST` endpoint that updates the data.

Requirements:
1. Create a FastAPI `POST /data/{item_id}` endpoint.
2. The endpoint should accept a JSON body like `{"new_data": "Updated info"}`.
3. First, update the database (we have provided the raw SQL).
4. Second, INSTEAD of deleting the cache key, immediately overwrite the cache key with the `new_data`.
5. Set the cache TTL to 60 seconds.

This ensures that the database and cache are perfectly in sync, and the next reader gets a lightning-fast Cache Hit!

Write your answer in `solution/app_write_through.py`.
