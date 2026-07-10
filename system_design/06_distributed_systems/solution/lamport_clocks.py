class Process:
    def __init__(self, name):
        self.name = name
        self.clock = 0
        
    def internal_event(self, event_name):
        self.clock += 1
        print(f"[{self.name}] Event: {event_name} | Logical Clock: {self.clock}")
        
    def send_message(self, receiver, message_content):
        self.clock += 1
        print(f"[{self.name}] Sending msg to {receiver.name} | Logical Clock: {self.clock}")
        # The message carries the sender's current logical clock
        receiver.receive_message(self.name, message_content, self.clock)
        
    def receive_message(self, sender_name, message_content, sender_clock):
        # Lamport algorithm: max(local_clock, received_clock) + 1
        self.clock = max(self.clock, sender_clock) + 1
        print(f"[{self.name}] Received msg from {sender_name} | Logical Clock updated to: {self.clock}")

if __name__ == "__main__":
    pA = Process("Node A")
    pB = Process("Node B")
    pC = Process("Node C")
    
    pA.internal_event("Booted up")
    pB.internal_event("Booted up")
    
    # A sends a message to B
    pA.send_message(pB, "Hello B!")
    
    # C boots up late
    pC.internal_event("Booted up late")
    
    # B sends a message to C
    pB.send_message(pC, "Hello C, from B!")
    
    # Note how C's clock jumps to respect the causality chain!
    # Even if C's physical clock was behind, its logical clock 
    # guarantees it knows its event happened AFTER A's event.
