import urllib.request
import json
import collections

def run_load_test(url="http://localhost:8000", num_requests=100):
    print(f"Sending {num_requests} requests to the load balancer at {url}...\n")
    
    responses = collections.Counter()
    
    for i in range(num_requests):
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                instance = data.get("instance", "Unknown")
                responses[instance] += 1
        except Exception as e:
            print(f"Request {i} failed: {e}")
            
    print("--- Results ---")
    for instance, count in responses.items():
        percentage = (count / num_requests) * 100
        print(f"{instance}: {count} requests ({percentage:.1f}%)")

if __name__ == "__main__":
    # Make sure docker-compose is running before executing this!
    run_load_test()
