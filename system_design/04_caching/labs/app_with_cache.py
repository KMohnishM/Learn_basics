import time
import psycopg2
import redis
from fastapi import FastAPI
import uvicorn

app = FastAPI()

# Connect to Redis
cache = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def get_db_connection():
    return psycopg2.connect(
        dbname="caching_lab",
        user="db_admin",
        password="secretpassword",
        host="localhost"
    )

@app.get("/data/{item_id}")
def get_data(item_id: int):
    start_time = time.time()
    
    # 1. CACHE ASIDE PATTERN: Check the cache first!
    cache_key = f"heavy_data:{item_id}"
    cached_result = cache.get(cache_key)
    
    if cached_result:
        # Cache Hit! Return immediately.
        duration = time.time() - start_time
        return {"source": "redis_cache", "data": cached_result, "time_taken": f"{duration:.4f}s"}
    
    # 2. CACHE MISS: Hit the database (slow)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT pg_sleep(2), data FROM heavy_data WHERE id = {item_id};")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if result:
        db_data = result[1]
        # 3. Store the result in the cache for the next time, with a TTL (Time To Live) of 60 seconds
        cache.setex(cache_key, 60, db_data)
        
        duration = time.time() - start_time
        return {"source": "database", "data": db_data, "time_taken": f"{duration:.4f}s"}
        
    return {"error": "not found"}

if __name__ == "__main__":
    print("Starting app WITH cache on port 8002")
    uvicorn.run(app, host="0.0.0.0", port=8002)
