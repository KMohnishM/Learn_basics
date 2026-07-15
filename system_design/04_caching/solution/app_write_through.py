import time
import psycopg2
import redis
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI()
cache = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def get_db_connection():
    return psycopg2.connect(
        dbname="caching_lab",
        user="db_admin",
        password="secretpassword",
        host="localhost"
    )

class UpdatePayload(BaseModel):
    new_data: str

@app.post("/data/{item_id}")
def update_data(item_id: int, payload: UpdatePayload):
    # WRITE-THROUGH PATTERN
    
    # 1. Write to Database
    conn = get_db_connection()
    cursor = conn.cursor()
    # Note: Using pg_sleep to simulate a slow DB write
    cursor.execute(
        "UPDATE heavy_data SET data = %s WHERE id = %s RETURNING id;", 
        (payload.new_data, item_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    # 2. Write to Cache (Immediately update it, don't just invalidate it!)
    cache_key = f"heavy_data:{item_id}"
    cache.setex(cache_key, 60, payload.new_data)
    
    return {"status": "success", "message": "Data updated in DB and Cache!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
