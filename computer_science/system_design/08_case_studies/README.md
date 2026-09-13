# Module 8: System Design Case Studies

> **Goal**: Apply foundational knowledge to real-world architectures.
> We will dissect five canonical system design problems, using a structured
> framework to go from ambiguous requirements to production-ready architectures.
> 
> System design is not about memorizing architectures; it is about understanding 
> trade-offs. In this module, we will explore deeply how companies like Twitter, 
> WhatsApp, YouTube, Uber, and Bit.ly scaled to billions of users. We will look 
> at their capacity estimations, API designs, data models, and the core 
> architectural choices that allowed them to survive extreme scale.

---

## Table of Contents

1. [The System Design Interview Framework (RADIO)](#1-the-system-design-interview-framework-radio)
    - [Requirements](#11-requirements-gathering)
    - [API Design](#12-api-design)
    - [Data Model](#13-data-model)
    - [Infrastructure](#14-infrastructure-and-core-design)
    - [Optimizations](#15-optimizations-and-deep-dives)
    - [Time Management](#16-how-to-structure-a-45-minute-interview)
    - [Back-of-Envelope Math](#17-back-of-envelope-calculation-template)
2. [Case Study 1: Design Twitter / X](#2-case-study-1-design-twitter--x)
3. [Case Study 2: Design WhatsApp](#3-case-study-2-design-whatsapp)
4. [Case Study 3: Design YouTube](#4-case-study-3-design-youtube)
5. [Case Study 4: Design Uber / Lyft](#5-case-study-4-design-uber--lyft)
6. [Case Study 5: Design a URL Shortener](#6-case-study-5-design-a-url-shortener)

---

## 1. The System Design Interview Framework (RADIO)

To succeed in a system design scenario (whether an interview or an architectural review), you need a structured approach. Jumping straight into architecture diagrams is a guaranteed path to failure. 

Use the **RADIO** framework to systematically break down the problem. This ensures you cover all bases before committing to a specific infrastructure.

### 1.1 Requirements Gathering (R)

Never assume you know exactly what the system should do. Ambiguity is intentionally introduced in design discussions. You must clarify both the Functional and Non-Functional requirements.

**Functional Requirements**: 
What are the core features the system must perform? Define the absolute minimum viable product (MVP) scope.
- *Bad*: "The system should be like Twitter."
- *Good*: "Users can post tweets (text only), follow other users, and view a chronological home timeline of tweets from people they follow."

**Non-Functional Requirements**: 
These dictate the architecture more than the functional requirements.
- **Scale**: How many Daily Active Users (DAU)? 
- **Traffic Profile**: Is it read-heavy (100:1) or write-heavy? 
- **Latency**: What is the acceptable p99 latency? (e.g., < 200ms for web loads).
- **Availability**: How many nines of availability? (e.g., 99.99%).
- **Consistency**: Does it require Strong Consistency (financial transactions) or Eventual Consistency (social media feeds)?

### 1.2 API Design (A)

Define the contract between the client and the server early. This grounds the discussion in reality.

- **Protocol Selection**: 
  - Will you use REST over HTTP/1.1 for simple CRUD? 
  - gRPC for high-performance internal microservices? 
  - WebSockets or Server-Sent Events (SSE) for real-time bidirectional communication?
- **Endpoint Definition**: Write out the exact endpoints.
  - `POST /v1/resource`
  - `GET /v1/resource/{id}`
- **Payloads**: Define the JSON body for requests and responses. Emphasize pagination (e.g., `cursor`, `limit`) for any endpoints returning lists.

### 1.3 Data Model (D)

Define the core entities and their relationships. Then, make the most critical decision: Database Selection.

- **Entities**: Users, Posts, Relationships, Messages.
- **Database Types**:
  - **Relational (PostgreSQL, MySQL)**: Use for ACID transactions, complex joins, and structured data.
  - **Key-Value (Redis, DynamoDB)**: Use for caching, session management, or simple lookups.
  - **Wide-Column (Cassandra, HBase)**: Use for massive write-heavy workloads, time-series data, and high availability.
  - **Document (MongoDB, Couchbase)**: Use for unstructured or rapidly changing schemas.
  
> [!WARNING] Accuracy Rule: DynamoDB Consistency
> Do not assume modern databases are strictly locked into legacy CAP theorem categories. For example, DynamoDB in 2024 supports strongly consistent reads. It is NOT inherently an AP-only system. You can tune its consistency model on a per-query basis by setting `ConsistentRead=true`.

### 1.4 Infrastructure and Core Design (I)

This is the meat of the design. How do the components fit together?

- **Data Flow**: Draw the path a request takes from the client -> DNS -> CDN -> Load Balancer -> API Gateway -> Application Servers -> Caches -> Databases.
- **Core Algorithms**: If the system requires a specific algorithm (e.g., Geohashing for Uber, Fan-out for Twitter), define it here.
- **Asynchronous Processing**: Introduce Message Queues (Kafka, RabbitMQ) to decouple heavy background processing from the synchronous request/response cycle.

### 1.5 Optimizations and Deep Dives (O)

No architecture is perfect on the first pass. You must identify bottlenecks and single points of failure (SPOF).

- **Scale the Database**: Discuss sharding (horizontal partitioning), read replicas, and consistent hashing.
- **Caching Strategies**: Introduce Cache-Aside, Write-Through, or Write-Behind caches. Discuss eviction policies (LRU, LFU).
- **Hot Keys**: How do you handle a massive spike in traffic to a single resource? (e.g., a celebrity tweet, or a highly popular URL).

### 1.6 How to Structure a 45-Minute Interview

If you are applying this in an interview setting, time management is critical. Stick to this timeline:

```text
00:00 - 05:00 : Requirements Gathering (Clarify scope, define MVP)
05:00 - 10:00 : Capacity Estimation (Math and scaling limits)
10:00 - 15:00 : API & Data Model (Contracts and schemas)
15:00 - 30:00 : High-Level Design (Core architecture and data flow)
30:00 - 45:00 : Deep Dives & Bottlenecks (Scaling, fault tolerance)
```

### 1.7 Back-of-Envelope Calculation Template

Always follow this sequence when estimating scale. You do not need exact numbers; order-of-magnitude estimates are sufficient to prove whether a design is viable.

1. **Traffic**: 
   - Daily Active Users (DAU) * Actions per user per day = Total Actions/day.
   - Total Actions/day / 86,400 seconds = Queries Per Second (QPS).
   - Peak QPS = Average QPS * 2 (or 5 for bursty traffic).
2. **Bandwidth**: 
   - Write Bandwidth = Write QPS * Average Payload Size.
   - Read Bandwidth = Read QPS * Average Payload Size.
3. **Storage**: 
   - Daily Actions * Size per record = Daily Storage.
   - Daily Storage * 365 days * Retention Period (e.g., 5 years) = Total Raw Storage.
   - Total Raw Storage * Replication Factor (usually 3) = Total Physical Storage.
4. **Memory/Cache**: 
   - Apply the 80/20 rule: 20% of the data generates 80% of the traffic. 
   - Cache Size = Daily Read Volume * 0.20 * Size per record.

---

## 2. Case Study 1: Design Twitter / X

Twitter is the canonical example of a massive, read-heavy social network. The primary challenge is the fan-out problem: how to efficiently deliver a single piece of content to millions of interested consumers.

### 2.1 Requirements

**Functional:**
- Users can post tweets (text and media).
- Users can follow and unfollow other users.
- Users can view a personalized, chronological home timeline of tweets from people they follow.
- Users can search for tweets using keywords.

**Non-Functional:**
- Read-heavy system (roughly 10:1 to 100:1 read-to-write ratio).
- Fast timeline rendering is critical (p99 latency < 200ms).
- Eventual consistency is acceptable for timelines (it's okay if a user sees a tweet a few seconds after it is posted).
- High availability is prioritized over strict consistency (AP system).

### 2.2 Capacity Estimation

Let's do the math for a globally scaled system like Twitter.

- **Users**: 300 Million Daily Active Users (DAU).
- **Tweets**: 500 Million tweets posted per day.
- **Write QPS**: 
  - 500M / 86,400 = ~5,800 tweets/sec on average.
  - Peak Write QPS = ~12,000 tweets/sec.
- **Read QPS**: 
  - Assuming a 10:1 ratio. 5,800 * 10 = ~58,000 reads/sec average.
  - Peak Read QPS = ~120,000 reads/sec.
- **Storage**:
  - Text storage: 500M tweets * 300 bytes average = 150 GB/day.
  - Yearly text storage: 150 GB/day * 365 = ~55 TB/year.
  - Media storage is handled entirely separately (assumed to be object storage + CDN). Let's assume 20% of tweets have media averaging 1MB. 100M * 1MB = 100 TB/day = 36.5 PB/year.

### 2.3 API Design

The API should be RESTful, focusing on standard HTTP verbs and proper pagination using cursors, not offsets. Offset-based pagination is dangerous in real-time feeds because offsets shift as new items are inserted.

```http
POST /v1/tweets
Authorization: Bearer <token>
Content-Type: application/json
{
  "content": "Exploring the depths of distributed systems today!",
  "media_ids": ["media-12345"]
}
Response: 201 Created
{
  "tweet_id": "14567890123",
  "created_at": "2024-03-10T12:00:00Z"
}

GET /v1/timeline/home?cursor=14567890123&limit=20
Authorization: Bearer <token>
Response: 200 OK
{
  "tweets": [
    { "tweet_id": "...", "content": "...", "user": {...} },
    ...
  ],
  "next_cursor": "14567800000"
}
```

### 2.4 Data Model

- **Users Table**: `user_id` (PK), `username`, `email`, `created_at`, `profile_url`. (Usually PostgreSQL/MySQL).
- **Tweets Table**: `tweet_id` (PK), `user_id` (FK), `content`, `created_at`.
- **Followers Table**: `follower_id` (PK/FK), `followee_id` (PK/FK), `created_at`. 
  - This table must be heavily indexed on both columns to allow ultra-fast reverse lookups ("Who follows user X?" and "Who does user Y follow?").

### 2.5 Core Design: The Fan-Out Problem

The most complex component of Twitter is generating the **Home Timeline**. When a user requests their timeline, they need the most recent tweets from everyone they follow, perfectly sorted by time. 

Executing a massive SQL `JOIN` at read-time across millions of rows is impossible at this scale. There are three primary architectures to solve this "Fan-Out" problem:

#### Approach 1: Fan-out on Write (The Push Model)
- **How it works**: When User A tweets, the system looks up all of User A's followers. It then takes the `tweet_id` and pushes it into an in-memory cache (a Redis list or sorted set) for each individual follower.
- **Pros**: Reading the timeline is O(1). The system simply fetches the user's pre-computed timeline from Redis. Blazing fast.
- **Cons**: Writing is O(N) where N is the number of followers. 
  - **The Celebrity Problem**: If Justin Bieber (100M+ followers) tweets, the system must execute 100 million Redis `LPUSH` commands. This will completely clog the asynchronous worker queues and delay timeline updates for the entire platform for minutes.

#### Approach 2: Fan-out on Read (The Pull Model)
- **How it works**: When User A tweets, it is simply saved to the database. No cache pushing occurs. When User B loads their timeline, the system fetches all users User B follows, queries the database for their recent tweets, merges them, sorts them in memory, and returns the result.
- **Pros**: Writes are O(1) and instantaneous. Celebrities are no longer a problem.
- **Cons**: Reads are O(N). This is horribly slow for users who follow thousands of people.

#### Approach 3: Hybrid Model (The Production Solution)
- **How it works**: We categorize users based on their follower count.
  - **Regular Users** (e.g., < 1M followers): We use Fan-out on Write (Push). Their tweets are actively pushed to their followers' Redis timelines.
  - **Celebrities** (e.g., > 1M followers): We use Fan-out on Read (Pull). Their tweets are NOT pushed. 
- **Read Time Merge**: When a user loads their timeline, the system fetches their pre-computed Redis cache (which contains tweets from regular users they follow) AND concurrently queries the recent tweets of the specific celebrities they follow. The results are merged, sorted by timestamp, and served.

#### Additional Components
- **Timeline Cache**: Handled by massive Redis clusters using Sorted Sets (ZSET). The score is the Unix timestamp, and the value is the `tweet_id`.
- **Media Delivery**: Media is uploaded directly to Object Storage (like Amazon S3) and served exclusively through globally distributed CDNs (Cloudflare, Akamai) to minimize bandwidth costs and latency.
- **Search**: A Kafka stream ingests every new tweet. Search indexer workers consume this stream and update an Elasticsearch cluster. Elasticsearch provides inverted indexing for rapid full-text keyword searches.

### 2.6 Architecture Diagram

```text
                                [ Mobile / Web Clients ]
                                          |
                                    (DNS / CDN)
                                          |
                                 [ API Gateway / LB ]
                                          |
                 +------------------------+------------------------+
                 |                                                 |
         [ Write API Service ]                             [ Read API Service ]
                 |                                                 |
      +----------+----------+                           +----------+----------+
      |                     |                           |                     |
[ DB Write ]        [ Fan-out Workers ]           [ Timeline Merge ]    [ Search Service ]
(Postgres)                  |                           |                     |
      |                     v                           v                     v
      |              [ Redis Cache ] <--------- [ User Cache ]         [ Elasticsearch ]
      v              (Push Timelines)           (Redis ZSET)                  ^
[ Kafka Stream ]            |                           |                     |
      |                     v                           v                     |
      +------------> [ Pull Service ] ----------+ (Merge celebrity tweets)    |
                            |                                                 |
                            +-------------------------------------------------+
```

---

## 3. Case Study 2: Design WhatsApp

WhatsApp is an incredibly high-throughput, low-latency system that relies on persistent, bidirectional connections rather than the traditional request/response cycle.

### 3.1 Requirements

**Functional:**
- Users can send and receive 1-on-1 text messages in real-time.
- Users can participate in group chats.
- The system must support delivery receipts (Sent, Delivered, Read).
- Users must see online/offline presence and typing indicators.

**Non-Functional:**
- Massive scale: 2 Billion Monthly Active Users (MAU).
- Extremely low latency messaging (messages should arrive in milliseconds).
- Privacy is paramount: End-to-End Encryption (E2EE) is mandatory.
- High availability for message routing.

### 3.2 Capacity Estimation

- **Traffic**: 100 Billion messages sent per day.
- **QPS**: 
  - 100B / 86,400 = ~1.16 Million messages/sec average.
  - Peak QPS = ~2.5 Million messages/sec.
- **Storage**: 
  - 100B messages * 500 bytes average = 50 TB/day for text.
  - Yearly text storage: ~18 PB/year.
  - Keep in mind, WhatsApp deletes messages from servers once delivered, so long-term server storage is actually much lower than this theoretical maximum. Media (images/video) is stored longer but also eventually purged.

### 3.3 API Design

The API is split into two distinct protocols:
- **REST over HTTPS**: Used for heavy, infrequent, static operations like profile picture updates, initial account registration, and media upload/download URLs.
- **WebSockets / TCP**: Used for the persistent, real-time chat connection. The client maintains an open socket with a Chat Server to instantly push and pull binary payloads.

### 3.4 Data Model

Because messages are transient (deleted once delivered), the database acts primarily as an **Offline Message Queue** rather than an archive.

- **Messages Table**: `message_id` (PK), `sender_id`, `receiver_id`, `chat_id`, `status` (sent, delivered, read), `timestamp`, `encrypted_payload`.
- **Database Choice**: A NoSQL wide-column store like **Cassandra** or **HBase**. These systems provide incredibly high write throughput, which is essential when ingesting 2.5 million inserts per second during peak hours.

### 3.5 Core Design

#### 1. Connection Management (The WebSocket Fleet)
With 2 Billion users and an assumption that 50% are online at peak, the system must hold **1 Billion concurrent WebSocket connections**.
A well-tuned Linux server can hold about 1 million concurrent connections (using `epoll` or `kqueue`). Therefore, we need a fleet of at least a few thousand **Chat Servers** just to hold TCP connections.

#### 2. User-to-Server Mapping (Crucial Architecture Choice)
When User A sends a message to User B, User A pushes the message to their connected Chat Server (e.g., Server #142). Server #142 must figure out *exactly which* server User B is connected to so it can route the payload.

> [!CAUTION] Accuracy Rule: Session Tracking
> **Use Redis for session tracking. DO NOT use Zookeeper.**
> You must track session mappings (`user_id` -> `server_id`) using an incredibly fast, highly partitioned in-memory datastore like a Redis cluster. Some candidates mistakenly propose Zookeeper for this. Zookeeper is a consensus system (CP) designed for coarse-grained configuration management and leader election. It will catastrophically fail if subjected to millions of high-frequency session lookups and updates per second. Redis is the correct tool.

#### 3. The Message Delivery Flow
1. **Send**: User A sends an encrypted message payload over their WebSocket to Chat Server 1.
2. **Lookup**: Chat Server 1 queries the Redis Session Cache: "Which server is User B on?"
3. **Route**: Redis replies: "User B is on Chat Server 5."
4. **Forward**: Chat Server 1 forwards the payload via internal RPC to Chat Server 5.
5. **Deliver**: Chat Server 5 pushes the message down the open WebSocket to User B.
6. **Acknowledge**: User B's device returns a "Delivered" ACK back up the chain.
7. **Offline Handling**: If User B is offline (Redis returns null), Chat Server 1 pushes the message into Cassandra. When User B comes online later, they connect to a Chat Server, which pulls pending messages from Cassandra and delivers them. Once ACKed, the messages are deleted from Cassandra.

#### 4. End-to-End Encryption (E2EE)
WhatsApp uses the **Signal Protocol**. 
- The server NEVER sees plaintext. It only routes binary encrypted blobs.
- Keys are exchanged directly between devices using Public Key Infrastructure (PKI).
- This severely limits what the server can do (no server-side searching of message history), but provides mathematically guaranteed privacy.
- Local chat history is stored entirely on the client's device, typically using a local SQLite database on iOS/Android.

#### 5. Group Chats
- **Small Groups**: Fan-out on write. If User A messages a group of 5, User A's client (or the server) copies the encrypted message 4 times and routes it individually to the 4 other members.
- **Large Groups**: Routing individual messages across servers becomes inefficient. Messages are pushed into a distributed message queue (Kafka). Chat Servers subscribe to group topics and pull messages for the specific users connected to them.

### 3.6 Architecture Diagram

```text
       [ User A Device ]                                 [ User B Device ]
         (Local SQLite)                                    (Local SQLite)
               |                                                 |
         (WebSocket)                                       (WebSocket)
               |                                                 |
               v                                                 v
       [ Load Balancer ]                                 [ Load Balancer ]
               |                                                 |
       [ Chat Server 1 ] -------- (Internal RPC) ------> [ Chat Server 5 ]
               |       ^                                         ^
               |       |             [ Redis Cluster ]           |
               |       +------- (Lookup user_id=B's Server)      |
               |                             |                   |
               v                             v                   |
      [ Offline Queue ] <--- (Persist if offline until ACK) -----+
         (Cassandra)
```

---

## 4. Case Study 3: Design YouTube

YouTube is the ultimate test of bandwidth, storage, and distributed media processing. The system requires orchestrating massive upload pipelines and globally distributed streaming networks.

### 4.1 Requirements

**Functional:**
- Creators can upload videos.
- Viewers can stream videos across varying network conditions (mobile, desktop, TV).
- Users can leave comments, likes, and view counts must be tracked accurately.
- System must generate thumbnails automatically.

**Non-Functional:**
- Highly available streaming with zero buffering.
- Global scale and low latency for video delivery.
- High durability for uploaded raw video files (no data loss).

### 4.2 Capacity Estimation

Let's calculate the astronomical storage required for YouTube.

- **Audience**: 2 Billion MAU. 1 Billion hours of video watched per day.
- **Upload Scale**: 500 hours of video uploaded per minute.
- **Upload Storage**:
  - 500 hours/min. Assume raw 1080p video is roughly 2 GB per hour (highly variable, but a safe estimate).
  - 500 hours/min = ~1 TB/min of raw video data.
  - Video must be encoded into multiple resolutions (144p, 360p, 720p, 1080p, 4k). This expands the storage footprint. Let's say encoding multiplies storage by 2x. 1 TB -> 2 TB/min.
  - To prevent data loss, the data is replicated 3x geographically. 2 TB -> 6 TB/min.
- **Annual Storage Math**:
  - 6 TB/min × 60 mins × 24 hrs × 365 days = 3,153,600 TB / year.
  - > [!IMPORTANT] Accuracy Rule: Exabyte Math
    > 1 PB = 1000 TB. 1 EB = 1000 PB.
    > 3,153,600 TB = 3,153.6 PB = **~3.15 Exabytes (EB) of new storage per year.**
- **Egress (Bandwidth)**: 
  - 1 Billion hours watched/day * 3.6 GB/hour (avg 1080p bitrate) = ~3.6 Exabytes of outbound data daily. This cannot be served from a central datacenter; it mandates an enormous CDN.

### 4.3 API Design

```http
POST /v1/videos/upload
Content-Type: multipart/form-data
(Client uploads raw file in chunks using resumable uploads to handle network drops)

GET /v1/videos/{video_id}/stream
(Returns the master playlist manifest file for HLS or DASH)
```

### 4.4 Data Model & Database Choices

> [!CAUTION] Accuracy Rule: YouTube Core Metadata Database
> **YouTube uses Vitess for core video metadata — NOT Cassandra.** 
> Vitess is a database clustering system built at YouTube for horizontal scaling of MySQL. It provides distributed MySQL sharding while maintaining relational schemas, foreign keys, and transactional integrity. Transactional integrity is strictly required for critical video metadata, monetization ledgers, user profiles, and channel configurations. 
> 
> Cassandra, however, IS used heavily by YouTube for high-throughput, eventual-consistency data like comments, likes, and real-time watch history.

### 4.5 Core Design

#### 1. The Upload & Transcoding Pipeline
When a creator uploads a massive 50GB 4k video, processing it on a single machine is too slow. It must be parallelized.
1. **Chunking**: The client uploads the video in chunks using resumable HTTP protocols directly to an Object Store (Google Cloud Storage / Amazon S3).
2. **Event Generation**: Once the final chunk arrives, the Object Store fires a "Upload Complete" event into a high-throughput message queue (**Kafka**).
3. **DAG Workflow**: A Directed Acyclic Graph (DAG) scheduler picks up the job. It breaks the raw video into 10-second segments.
4. **Elastic Transcoding Workers**: Thousands of independent worker nodes (running FFmpeg on CPU-optimized cloud instances) pick up individual 10-second segments. Worker A transcodes segment 1 to 720p. Worker B transcodes segment 1 to 1080p.
5. **Assembly**: The transcoded segments are pushed to origin storage, and a master manifest file is generated.

#### 2. Video Streaming (Adaptive Bitrate)
Modern video is never served as a single giant `.mp4` file over HTTP. It uses **HLS (HTTP Live Streaming)** or **MPEG-DASH**.
- The client receives a Manifest file listing URLs for 10-second segments of the video at various qualities.
- The video player monitors the client's current bandwidth.
- If the user drives into a tunnel and their 5G drops to 3G, the player seamlessly switches to requesting the 360p segment URLs for the next block, preventing buffering.

#### 3. Content Delivery Network (CDN) Architecture
Serving 3.6 Exabytes a day requires placing data physically close to the user.
- YouTube uses a tiered CDN architecture.
- **Edge PoPs (Points of Presence)**: Google Global Cache servers are physically installed inside ISP datacenters (Comcast, AT&T). If a video is viral, it is served directly from the ISP, bypassing the broader internet.
- **Regional Caches**: If the edge misses, it queries a larger regional datacenter.
- **Origin Servers**: The absolute source of truth, used only when all caches miss.

### 4.6 Architecture Diagram

```text
    [ Creator / Uploader ]                            [ Viewer / Player ]
             |                                                 |
      (Upload Chunks)                               (Stream Segments via ABR)
             |                                                 |
             v                                                 v
      [ API Gateway ]                              [ ISP Edge CDN Node (GGC) ]
             |                                                 | (Cache Miss)
    [ Raw Object Store ] <------ (Save) -------- [ Tier 2 Regional Cache ]
             |                                                 | (Cache Miss)
             | (Event Trigger)                                 v
             v                                         [ Origin Storage ]
      [ Kafka Queue ]                                          ^
             |                                                 |
             +--------------> [ DAG Scheduler ]                |
                                     |                         |
                           +---------+---------+ (Push transcoded segments)
                           |         |         |               |
                       [ FFmpeg Transcoder Workers ] ----------+
                       (Massively Parallel Cluster)
```

---

## 5. Case Study 4: Design Uber / Lyft

Uber introduces a unique challenge in system design: real-time geospatial processing. The system must ingest millions of GPS coordinates per second and instantly execute complex spatial queries to match supply and demand.

### 5.1 Requirements

**Functional:**
- Real-time location tracking of active drivers.
- Rider requests a ride; system matches them with the nearest suitable driver.
- Fare calculation and dynamic surge pricing.
- Trip state tracking (Requested -> Accepted -> Arrived -> In Progress -> Completed).

**Non-Functional:**
- High throughput of location updates (write-heavy for driver GPS).
- Low latency matching algorithm.
- Strong consistency for trip states and financial ledgers.

### 5.2 Capacity Estimation

- **Rides**: 20 Million rides / day.
- **Ride QPS**: 20M / 86,400 = ~230 rides/sec (average). Very low compared to social media.
- **Location Updates**: This is the real bottleneck.
  - 5 Million active drivers simultaneously on the road.
  - Each driver app pings the server with GPS coordinates every 4 seconds.
  - **Update QPS**: 5,000,000 / 4 = **1.25 Million location updates/sec.**
- **Storage for tracking**: 1.25M updates/sec * 50 bytes (ID, lat, long, timestamp) = 62.5 MB/sec. Over a day, this is ~5.4 TB of telemetry data. Only the latest position is kept in hot cache; the historical data is asynchronously piped via Kafka into a Data Lake (Hadoop/S3) for machine learning and analytics.

### 5.3 Data Model

- **Users/Drivers/Vehicles**: Relational DB (PostgreSQL) for structured profile data.
- **Trips Table**: `trip_id` (PK), `rider_id`, `driver_id`, `status`, `start_time`, `end_time`, `fare`.
- **Driver Location**: Needs specialized spatial indexing. Standard relational DBs cannot handle the write throughput and spatial read requirements simultaneously.

### 5.4 Core Design

#### 1. Geospatial Indexing (The Secret Sauce)
You cannot query a standard SQL database with `WHERE lat BETWEEN x AND y AND long BETWEEN a AND b` at a rate of 1.25M writes and thousands of reads per second. Table locks and B-tree updates would bring the system to a halt.

**Solution**: Discretize the continuous map into a manageable grid system.
- **Geohash**: Encodes a 2D geographic area into a short 1D string (e.g., `9q8yy`). Drivers in the same physical grid square share the same Geohash prefix. 
- **Google S2 Geometry**: A more advanced approach heavily utilized by Uber. It divides the Earth into a spherical grid system, mapping coordinates to 64-bit integers. It is highly optimized for the Earth's curvature and allows for varying levels of precision (cell sizes).

#### 2. Driver Location Storage
Active driver locations must be stored in memory for instant access.
- Use a distributed **Redis Cluster**.
- Redis provides built-in **Geo commands** (`GEOADD`, `GEORADIUS`, `GEOSEARCH`). Under the hood, Redis implements Geohashing using its extremely fast Sorted Sets (ZSET), where the score is the 52-bit integer Geohash.

#### 3. The Matching & Dispatch Algorithm
When a rider requests a ride, the system must find the optimal driver. It is not just about Euclidean distance; it's about ETA.
1. **Request**: Rider requests a ride at coordinates (Lat A, Long B).
2. **Grid Resolution**: The system calculates the Rider's S2 Cell ID or Geohash at a specific precision level (e.g., a 1km x 1km box).
3. **Candidate Fetch**: The Matchmaking Service queries Redis for all drivers currently inside that specific Geohash AND the 8 immediately surrounding neighbor Geohashes.
4. **Filtering**: Filter out drivers who are already on a trip, offline, or don't match the vehicle type (UberX vs UberBlack).
5. **Routing & ETA**: Send the remaining candidate drivers to a dedicated Routing Service. This service runs advanced graph algorithms (A* or Dijkstra) on real-time traffic maps to calculate the actual driving ETA for each driver.
6. **Dispatch**: Rank the drivers by lowest ETA and ping the top driver's app. If they decline, ping the next.

#### 4. Real-time Communication
- Both the Rider app and Driver app maintain persistent **WebSocket** connections to a fleet of API Gateways.
- The core Trip State Machine lives in a strongly consistent backend (e.g., CockroachDB or Postgres). As the state changes, events are fired and pushed down the WebSockets to instantly update the UI for both parties.

### 5.5 Architecture Diagram

```text
      [ Driver App ] (1.25M GPS/sec)            [ Rider App ] (Request Ride)
            |                                         |
      (WebSockets)                              (WebSockets)
            |                                         |
            v                                         v
   [ Driver Gateway ]                         [ Rider Gateway ]
            |                                         |
            v                                         v
 [ Location Ingestion Svc ]               [ Matchmaking / Dispatch Svc ]
            |                                         |
            +-----------> [ Redis Cluster ] <---------+
            |             (S2 Geo Index)              |
            v                                         v
   [ Kafka Stream ]                           [ Trip State Machine ]
            |                                 (Postgres/CockroachDB)
            v                                         |
 [ Analytics Data Lake ] <--- (Trip Data & Fares) ----+
```

---

## 6. Case Study 5: Design a URL Shortener

Designing a URL shortener (like Bit.ly) is a classic exercise in data modeling, hashing collisions, caching, and handling extremely read-heavy, redirected traffic.

### 6.1 Requirements

**Functional:**
- Given a long URL, generate a unique, short alias (e.g., `bit.ly/3xY7z`).
- Given a short alias, redirect the user's browser to the original long URL.
- Track analytics (click counts, geographic location of clicks).

**Non-Functional:**
- Extremely read-heavy architecture.
- Minimal latency for redirects (must be imperceptible to the user).
- Short links must not be guessable (optional but common requirement).
- Links must be retained for at least 5 years.

### 6.2 Capacity Estimation

- **Traffic**: 100 Million URLs shortened per day. 10 Billion redirects requested per day. This is a 100:1 read-to-write ratio.
- **Write QPS**: 100M / 86,400 = ~1,160 writes/sec average.
- **Read QPS**: 10B / 86,400 = ~115,700 reads/sec average. (Peak could be 300k+).
- **Storage**:
  - 100M URLs/day * 365 days * 5 years = 182.5 Billion URLs stored.
  - Assume an average of 500 bytes per database row (short_code, long_url, user_id, timestamps).
  - 182.5B * 500 bytes = **~91 TB of storage over 5 years**.

### 6.3 Core Design: Short Code Generation

How do we generate the 7-character string after the domain?
- **Base62 Encoding**: We use characters [a-z, A-Z, 0-9]. This gives us 62 possible characters per slot.
- A 7-character Base62 string yields `62^7 = ~3.5 Trillion` combinations. This is vastly more than the 182.5 Billion URLs we need to store.

**Approach 1: Hashing + Truncation**
- Run the long URL through a cryptographic hash like MD5. MD5 outputs 128 bits.
- Convert to Base62 and take the first 7 characters.
- **The Problem**: Hash collisions. Two different URLs might yield the same first 7 characters. You must query the database to check if the code exists. If it does, you have to append a string, re-hash, and check again. This is computationally expensive and slow.

**Approach 2: Distributed ID Generator + Base62 (The Production Winner)**
- Use a highly available, distributed sequence generator (like Twitter's Snowflake or an auto-incrementing counter in a dedicated database cluster) to generate a globally unique 64-bit integer.
- Convert that unique base-10 integer directly into Base62.
- **Pros**: Zero collisions mathematically guaranteed. Highly scalable. O(1) generation time.

### 6.4 The Read Path & Redirection Mechanics

When a user's browser hits the short URL, the server responds with an HTTP Redirect status code.

**HTTP 301 vs 302**
- **301 (Moved Permanently)**: The browser caches the redirect forever. Future clicks go directly to the long URL without hitting our server. 
  - *Pros*: Massive reduction in server load.
  - *Cons*: We lose all click analytics after the first click.
- **302 (Found / Temporary)**: The browser MUST hit our server every single time it processes the link.
  - *Pros*: We capture 100% of click analytics, geographic data, and referrers.
  - *Cons*: High load on our servers. (Bit.ly heavily uses 302s because analytics is their core business model).

**Caching (The 80/20 Rule)**
- 20% of URLs (viral tweets, breaking news, popular videos) will drive 80% of the redirect traffic.
- We put a massive **Redis cache** in front of the primary database.
- Memory calculation: Cache 20% of daily read requests = 2 Billion cache entries. 2B * 500 bytes = 1 TB of RAM. This easily fits across a small cluster of Redis nodes.
- Eviction policy: LRU (Least Recently Used) to cycle out old viral links as new ones take their place.

### 6.5 Architecture Diagram

```text
      [ User Browser ] --- (GET /3xY7z) ---> [ Load Balancer ]
                                                     |
                                               [ Read API Server ]
                                                     |
                                           +---------+---------+
                                           |                   |
                                     [ Redis Cache ]     [ MySQL Replicas ]
                                           |                   |
                                        (Hit)               (Miss, Fetch DB, Update Cache)
                                           |                   |
                                           +------< Return Long URL
                                                     |
                                                     v
                                              [ Kafka Stream ]
                                                     |
                                             [ Click Analytics Engine ]
```

---
*End of Module 8. Ensure you can replicate the mathematical formulas, capacity estimations, database selections, and bottleneck mitigations for any arbitrary system using the RADIO framework.*
