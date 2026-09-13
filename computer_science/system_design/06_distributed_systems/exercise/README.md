# Exercise: Lamport Clocks

You cannot trust physical time (`time.time()`) across multiple servers. 
If Server A sends a message to Server B, the physical timestamp on the message might actually be *later* than the time Server B receives it, because Server A's clock is 50ms fast.

Leslie Lamport solved this with **Logical Clocks**.

The algorithm is simple:
1. Every node keeps an internal integer counter `C` (initialized to 0).
2. Whenever a node does an internal event, it increments `C = C + 1`.
3. When a node sends a message to another node, it attaches its current `C` to the message.
4. When a node *receives* a message with timestamp `T_msg`, it updates its own clock: `C = max(C, T_msg) + 1`.

This guarantees that if Event A *caused* Event B, then `C(A) < C(B)`. 

## Your Task
Write a Python script in `solution/lamport_clocks.py` that simulates 3 processes (A, B, C) exchanging messages and updating their logical clocks using the Lamport algorithm.
