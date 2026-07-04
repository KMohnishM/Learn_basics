# Exercise: Sliding Windows and Anomaly Detection

In the lab, we created a **Tumbling Window** (fixed 5-minute blocks). 
This is fine for simple reporting, but bad for anomaly detection. 
If a user commits credit card fraud by spending $1000 at 12:04:59 and another $1000 at 12:05:01, a tumbling window will split this into two separate windows of $1000 each. It might not trigger your "$1500 threshold" alert!

## Your Task

Rewrite the aggregation query in `solution/anomaly_detection.py` to use a **Sliding Window**.

Requirements:
1. Create a 10-minute window that slides every 2 minutes. (This means windows overlap, and the fraudster's two purchases will definitely be caught inside the same window!).
2. Group the data by `user_id` AND the sliding window.
3. Sum the `amount`.
4. Add a `.filter()` to only output rows where the sum is greater than 1500.

*Hint: The `window()` function in PySpark takes a third parameter for the slide duration! `window("col", "windowDuration", "slideDuration")`.*
