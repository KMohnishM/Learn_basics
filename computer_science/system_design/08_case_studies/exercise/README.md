# Final Exercise: Design a URL Shortener (Bitly)

You are tasked with designing a URL shortener like bit.ly or tinyurl.com.

## 1. Requirements
- **Functional**:
  - Given a long URL, return a much shorter URL (e.g., `bit.ly/3xY8a`).
  - When a user clicks the short URL, redirect them to the original long URL.
  - Links expire after 5 years.
- **Non-Functional**:
  - 100 million new URLs generated per month.
  - Read-heavy: 10 times more redirects than generations (1 Billion reads/month).
  - The system must be highly available and have minimal latency.

## Your Task

Write a design document in `solution/pastebin_design.md` following the **RADIO** framework.

Make sure you explicitly answer these difficult questions in your design:
1. **The Hash**: How exactly do you generate the 7-character string? (MD5? Base62 encoding? A distributed ID generator?)
2. **Collisions**: What happens if two users submit the exact same long URL?
3. **Database**: What database will you use and why? (Hint: The data is flat, doesn't need joins, and scale is massive).
4. **Caching**: Since reads outnumber writes 10:1, how will you cache the data? What eviction policy will you use?

Good luck!
