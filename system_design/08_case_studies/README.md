# Module 8: System Design Case Studies

The final step in mastering System Design is pulling everything you've learned (load balancing, caching, databases, sharding, queues, microservices) into a single cohesive architecture to solve a real-world problem.

When doing a case study (or an interview), always follow the **RADIO framework**:
1. **R**equirements (Functional & Non-Functional)
2. **A**PI Design
3. **D**ata Model
4. **I**nfrastructure / High-Level Design
5. **O**ptimizations / Deep Dives

## Case Study 1: Design Twitter (X)
**Core Challenge**: Massive read-heavy fan-out.
- When Elon Musk (100M followers) tweets, you cannot insert 100M rows into a database instantly.
- **Solution**: Pre-computed Home Timelines in Redis.
- When an average user tweets, we push the tweet into the Redis cache of all their followers (Push Model).
- When a celebrity tweets, we don't push. Instead, when a follower loads their app, the app pulls the celebrity's tweets and merges them with their Redis timeline on the fly (Pull Model / Hybrid approach).

## Case Study 2: Design WhatsApp
**Core Challenge**: Real-time bi-directional communication and extreme state management.
- **Solution**: WebSockets.
- You cannot use HTTP requests for chatting (too slow, requires polling).
- Users establish a persistent WebSocket connection to a "Chat Server".
- The system must use a distributed cache (Redis) or Zookeeper to track *which* Chat Server User B is connected to, so User A's message can be routed there.
- Messages are stored on device (end-to-end encrypted). The server only queues messages temporarily until they are delivered.

## Case Study 3: Design YouTube
**Core Challenge**: Handling massive files and global content delivery.
- **Solution**: Chunking and CDNs.
- When a video is uploaded, it is split into chunks, put into a Message Queue, and parallel processed by workers to convert it into 1080p, 720p, 360p.
- The actual video files are stored in object storage (AWS S3) and served via a Content Delivery Network (CDN) so users in Tokyo download the video from a server in Tokyo, not Virginia.
- The metadata (likes, comments) is stored in a scalable NoSQL database like Cassandra.

## Case Study 4: Design Uber / Lyft
**Core Challenge**: Geospatial indexing and high-frequency location updates.
- **Solution**: Geohashing.
- You cannot query a traditional SQL database for "drivers within 2 miles" millions of times a second.
- The world is divided into a grid (Geohashes or Google S2 geometry). Each grid square has a unique string ID.
- Drivers constantly stream their location to Kafka. A stream processor updates their current Geohash in Redis.
- When a rider opens the app, we calculate their Geohash, and instantly query Redis for all drivers in that specific hash (and the 8 surrounding hashes).

---
## Next Steps
It's your turn. Go to the `exercise/` folder and design your own system from scratch!
