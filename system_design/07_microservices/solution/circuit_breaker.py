import time

class CircuitBreakerOpenException(Exception):
    pass

class CircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_timeout_sec=5):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        
        self.state = "CLOSED"
        self.failures = 0
        self.last_failure_time = None

    def call(self, func, *args, **kwargs):
        # 1. State check
        if self.state == "OPEN":
            # Check if enough time has passed to try again
            if time.time() - self.last_failure_time >= self.recovery_timeout_sec:
                print("[CircuitBreaker] Timeout expired. Entering HALF-OPEN state.")
                self.state = "HALF_OPEN"
            else:
                # Fast Fail!
                raise CircuitBreakerOpenException("Circuit is OPEN. Fast failing.")

        # 2. Execution attempt
        try:
            print(f"[CircuitBreaker] Calling function in {self.state} state...")
            result = func(*args, **kwargs)
            
            # If we succeed and were half-open, we are healed!
            if self.state == "HALF_OPEN":
                print("[CircuitBreaker] Call succeeded. Circuit is now CLOSED.")
                self.state = "CLOSED"
                self.failures = 0
                
            return result
            
        except Exception as e:
            # 3. Failure handling
            self.failures += 1
            self.last_failure_time = time.time()
            print(f"[CircuitBreaker] Call failed. Failure count: {self.failures}")
            
            if self.state == "HALF_OPEN" or self.failures >= self.failure_threshold:
                print("[CircuitBreaker] Threshold reached. Circuit is now OPEN!")
                self.state = "OPEN"
                
            raise e


# --- DEMO ---
if __name__ == "__main__":
    def unreliable_network_call(should_fail):
        if should_fail:
            raise ConnectionError("Network timeout!")
        return "200 OK"

    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout_sec=3)

    print("\n--- 1. Normal Operation ---")
    print(breaker.call(unreliable_network_call, False))

    print("\n--- 2. Inducing Failures ---")
    try: breaker.call(unreliable_network_call, True) # Fail 1
    except: pass
    try: breaker.call(unreliable_network_call, True) # Fail 2 -> Breaker OPENS
    except: pass

    print("\n--- 3. Fast Failing ---")
    try: 
        breaker.call(unreliable_network_call, False) # Should fast fail even though func is 'good'
    except Exception as e: 
        print(f"Caught: {e}")

    print("\n--- 4. Waiting for Recovery ---")
    time.sleep(3.1)
    
    print("\n--- 5. Half-Open Test ---")
    # This successful call will transition the breaker back to CLOSED
    print(breaker.call(unreliable_network_call, False))
