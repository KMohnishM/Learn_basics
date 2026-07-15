import urllib.request
import json
import time

def run_benchmark():
    print("=== BENCHMARKING APP WITHOUT CACHE (Port 8001) ===")
    
    # First request
    print("Request 1 (Fetching ID 1):")
    req = urllib.request.Request("http://localhost:8001/data/1")
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode())
    print(f"  Source: {data['source']}")
    print(f"  Time taken: {data['time_taken']}")
    
    # Second request
    print("Request 2 (Fetching ID 1 again):")
    req = urllib.request.Request("http://localhost:8001/data/1")
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode())
    print(f"  Source: {data['source']}")
    print(f"  Time taken: {data['time_taken']}")
    
    
    print("\n=== BENCHMARKING APP WITH CACHE (Port 8002) ===")
    
    # First request (Cache Miss)
    print("Request 1 (Fetching ID 1 - Cache Miss):")
    req = urllib.request.Request("http://localhost:8002/data/1")
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode())
    print(f"  Source: {data['source']}")
    print(f"  Time taken: {data['time_taken']}")
    
    # Second request (Cache Hit)
    print("Request 2 (Fetching ID 1 again - Cache Hit):")
    req = urllib.request.Request("http://localhost:8002/data/1")
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode())
    print(f"  Source: {data['source']}")
    print(f"  Time taken: {data['time_taken']}")

if __name__ == "__main__":
    print("Make sure you are running BOTH app_without_cache.py (8001) and app_with_cache.py (8002)!")
    try:
        run_benchmark()
    except Exception as e:
        print(f"Error: {e}")
