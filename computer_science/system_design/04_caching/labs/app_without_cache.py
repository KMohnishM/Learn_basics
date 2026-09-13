import time
import psycopg2
from fastapi import FastAPI
import uvicorn

app = FastAPI()

def get_db_connection():
    return psycopg2.connect(
        dbname="caching_lab",
        user="db_admin",
        password="secretpassword",
        host="localhost"
    )

@app.get("/data/{item_id}")
def get_data(item_id: int):
    # This simulates a very slow, complex database query (e.g. huge table join)
    start_time = time.time()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # We use pg_sleep(2) to simulate a query that takes 2 seconds to execute
    cursor.execute(f"SELECT pg_sleep(2), data FROM heavy_data WHERE id = {item_id};")
    result = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    duration = time.time() - start_time
    
    if result:
        return {"source": "database", "data": result[1], "time_taken": f"{duration:.4f}s"}
    return {"error": "not found"}

if __name__ == "__main__":
    print("Starting app WITHOUT cache on port 8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
