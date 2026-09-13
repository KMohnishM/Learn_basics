from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import httpx
import time
import asyncio

app = FastAPI(title="API Gateway")

# Simulated Downstream Service URLs (In reality, these would be separate servers)
# For this lab, we mock the endpoints within this same file just to demonstrate routing.
USER_SERVICE_URL = "http://localhost:8000/internal/users"
ORDER_SERVICE_URL = "http://localhost:8000/internal/orders"

# --- RATE LIMITER (Token Bucket Algorithm) ---
class TokenBucket:
    def __init__(self, capacity, refill_rate_per_sec):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate_per_sec
        self.last_refill = time.time()

    def consume(self, tokens=1):
        now = time.time()
        time_passed = now - self.last_refill
        
        # Refill tokens
        self.tokens = min(self.capacity, self.tokens + time_passed * self.refill_rate)
        self.last_refill = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

# Allow 5 requests max, refilling at 1 request per second
rate_limiter = TokenBucket(capacity=5, refill_rate_per_sec=1)


# --- GATEWAY MIDDLEWARE ---
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if not rate_limiter.consume():
        return JSONResponse(status_code=429, content={"error": "Too Many Requests"})
    
    # In a real Gateway, you would validate JWT auth tokens here before routing!
    
    response = await call_next(request)
    return response


# --- GATEWAY ROUTES ---
@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    """Routes traffic to the User Service"""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{USER_SERVICE_URL}/{user_id}")
            return resp.json()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="User Service Unavailable")

@app.get("/api/dashboard/{user_id}")
async def get_dashboard(user_id: int):
    """
    REQUEST AGGREGATION: 
    The Gateway calls two microservices concurrently and combines their data!
    This saves the mobile app from making 2 separate round trips over slow cellular networks.
    """
    async with httpx.AsyncClient() as client:
        # Call both services in parallel
        user_task = client.get(f"{USER_SERVICE_URL}/{user_id}")
        orders_task = client.get(f"{ORDER_SERVICE_URL}?user_id={user_id}")
        
        user_resp, orders_resp = await asyncio.gather(user_task, orders_task)
        
        return {
            "user_profile": user_resp.json(),
            "recent_orders": orders_resp.json()
        }


# --- MOCKED DOWNSTREAM SERVICES (For lab purposes) ---
@app.get("/internal/users/{user_id}")
def mock_user_service(user_id: int):
    return {"id": user_id, "name": "Alice", "status": "active"}

@app.get("/internal/orders")
def mock_order_service(user_id: int):
    return [{"order_id": 101, "total": 45.00}, {"order_id": 102, "total": 12.50}]

# Run with: pip install fastapi httpx uvicorn && uvicorn api_gateway:app --reload
