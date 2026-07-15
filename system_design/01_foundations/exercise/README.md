# Exercise: URL Shortener Back-of-Envelope Estimation

## Objective

Perform a complete back-of-envelope estimation for a URL shortener service (similar to bit.ly or TinyURL).

This exercise tests your ability to:
1. Make reasonable assumptions when requirements are vague
2. Convert user behavior assumptions into infrastructure numbers
3. Calculate QPS, storage, and bandwidth requirements
4. Identify the most challenging components from the numbers

---

## Service Requirements

You are designing a URL shortening service with the following characteristics:

**Functional Requirements** (what it does):
- Users can submit a long URL and receive a short URL (e.g., `bit.ly/abc123`)
- Visiting the short URL redirects the user to the original long URL
- Users can see click analytics for their URLs (total clicks, clicks over time)
- URLs can optionally expire after a set number of days
- Support both anonymous users and registered users (registered users get analytics)

**Non-Functional Requirements** (scale):
- The service has **100 million Daily Active Users** (DAU)
- Read-heavy: URL redirections far outnumber URL creations
- High availability: 99.99% uptime required
- Low latency: Redirects should complete within **50ms at p99**
- Data retention: URLs never expire unless user sets an expiry date

---

## Your Task

Answer ALL of the following questions. Show your work and state your assumptions explicitly.

### Part 1: QPS Calculations

**Question 1a - Write QPS (URL Creation)**:
- What percentage of DAU do you think creates new short URLs each day?
- How many URL creations per user per day?
- Calculate the average and peak write QPS
- (Use 2x peak multiplier for average traffic)

**Question 1b - Read QPS (URL Redirect)**:
- For each short URL created, estimate how many times it gets clicked per day (on average)
- Calculate the average and peak read QPS for redirects
- What is the read:write ratio?

**Question 1c - Analytics Read QPS**:
- What % of registered users check their analytics daily?
- Calculate analytics dashboard read QPS

---

### Part 2: Storage Calculations

For each table/entity, calculate the total storage needed after **5 years**:

**Question 2a - URLs Table**:
Design a schema for the `urls` table. Include at minimum:
- `short_code` (the generated 6-character code)
- `original_url` (the long URL)
- `user_id` (nullable for anonymous)
- `created_at`, `expires_at`, `click_count`
- Estimate the size of one row in bytes
- Calculate total storage (5 years, 3x replication, 30% index overhead)

**Question 2b - Analytics Table**:
Every click generates an analytics event. Design the schema and estimate storage:
- Include: `short_code`, `clicked_at`, `ip_address`, `country`, `referrer`, `user_agent`
- Estimate row size in bytes
- Calculate total storage (5 years, 3x replication, 20% index overhead)

**Question 2c - Which table uses more storage? Why?**

---

### Part 3: Bandwidth Calculations

**Question 3a - Incoming bandwidth (URL creation)**:
- Average size of a URL creation request payload (include the original URL and headers)
- Calculate total incoming bandwidth for URL creation traffic

**Question 3b - Outgoing bandwidth (redirects)**:
- A redirect response is just HTTP headers (no body), about 500 bytes
- Calculate the total outgoing bandwidth for redirect traffic

**Question 3c - Which is larger? What does this tell you about the system design?**

---

### Part 4: Short Code Generation

**Question 4a**: If you use 6-character Base62 codes (a-z, A-Z, 0-9):
- How many unique codes are possible?
- Given your URL creation rate, how many years until you run out of codes?
- Is 6 characters enough?

**Question 4b**: What are the trade-offs between these three short code generation strategies?
1. Random Base62 (pick random 6 characters and check for collisions)
2. MD5 hash of original URL, take first 6 characters
3. Auto-increment integer converted to Base62

---

### Part 5: Architecture Implications

Based on your calculations:

**Question 5a**: The p99 redirect latency requirement is 50ms. What does this imply about:
- Can you query the database (Postgres) for every redirect? Why or why not?
- What caching strategy would you use?
- Where should the cache live?

**Question 5b**: Your analytics table will grow to be very large. What database type would you use for:
- Storing and querying individual click events
- Generating aggregate reports (clicks per day, per country)?

**Question 5c**: For the 99.99% availability requirement:
- How many minutes of downtime per year are allowed?
- What is the minimum architecture you need to achieve this?

---

## Deliverable

Write your answers in a markdown file called `my_estimation.md` in this directory.

Your answer should follow this structure:
```
# URL Shortener Estimation

## Assumptions
[List all assumptions you're making]

## Part 1: QPS
[Show calculations with formulas]

## Part 2: Storage
[Show calculations with schemas and formulas]

## Part 3: Bandwidth
[Show calculations]

## Part 4: Short Code Generation
[Analysis of options]

## Part 5: Architecture Implications
[Reasoning based on your numbers]

## Summary Table
| Metric | Value |
|--------|-------|
| Write QPS (avg) | ? |
| Write QPS (peak) | ? |
| Read QPS (avg) | ? |
| Read QPS (peak) | ? |
| Storage (5 years) | ? |
| Incoming bandwidth | ? Mbps |
| Outgoing bandwidth | ? Mbps |
```

---

## Hints

- The read:write ratio for URL shorteners is typically **100:1 to 1000:1**
- The 50ms p99 latency requirement almost certainly means you NEED caching
- 100M DAU with even 1% creating URLs = 1M URL creations per day = ~11.5/sec average
- Don't forget that the HTTP redirect response (301 or 302) also carries data
- Redis can serve 100,000+ operations per second -- much faster than Postgres

---

## Grading Criteria

You will be evaluated on:
1. **Reasonableness of assumptions**: Are your assumptions defensible with real-world reasoning?
2. **Calculation accuracy**: Are the math and unit conversions correct?
3. **Read:write ratio insight**: Did you identify that this is heavily read-dominated?
4. **Caching necessity**: Did you connect the latency requirement to the need for caching?
5. **Short code analysis**: Did you correctly calculate Base62 capacity?
