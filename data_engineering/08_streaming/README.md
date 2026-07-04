# Module 8: Real-Time Streaming Data

Batch processing (e.g., Airflow running a script at midnight) is great for historical reports. But what if a credit card is stolen, and you need to detect fraud *before* the transaction completes? You need **Stream Processing**.

## 1. Event Time vs Processing Time
The hardest concept in streaming data is the concept of time.
- **Event Time**: The time the event actually occurred on the user's mobile phone (e.g., 2:00 PM).
- **Processing Time**: The time your server received the event (e.g., 2:05 PM, because the user went through a tunnel and their phone lost internet).

If you aggregate revenue by *Processing Time*, your hourly reports will be completely wrong if there is network lag. You must always aggregate by *Event Time*.

## 2. Watermarks & Late Data
If you are aggregating data for the 2:00-3:00 PM window by Event Time, how long do you wait for late data to arrive before you declare the window "closed" and save the results to the database?
- A **Watermark** is a threshold you set. "I will wait 10 minutes for late data." 
- If an event from 2:59 PM arrives at 3:05 PM, it is processed.
- If an event from 2:59 PM arrives at 3:15 PM, it is dropped because it fell behind the watermark.

## 3. Windowing Functions
Stream processors (like Flink or Spark Streaming) group infinite streams of data into finite "windows" for aggregation.
- **Tumbling Window**: Fixed, non-overlapping intervals (e.g., 0-5 mins, 5-10 mins). An event belongs to exactly one window.
- **Sliding Window**: Overlapping intervals. e.g., "A 10-minute window, sliding every 2 minutes" (0-10, 2-12, 4-14). An event belongs to multiple windows. Great for moving averages.
- **Session Window**: Dynamic windows based on activity. e.g., "Keep the window open as long as the user clicks. Close it if 30 minutes of inactivity pass."

## 4. Architecture Patterns
- **Lambda Architecture**: You have two completely separate pipelines. A fast streaming pipeline for real-time dashboards (approximate data), and a slow batch pipeline that runs at night to correct the streaming pipeline (accurate data). Very complex to maintain two codebases.
- **Kappa Architecture**: Everything is a stream. Even batch processing is just a stream processor reading from a Kafka topic from the very beginning.

## 5. Spark Structured Streaming vs Apache Flink
- **Spark Structured Streaming**: Uses "Micro-batching". It gathers data for e.g., 1 second, processes it as a tiny batch, and repeats. High throughput, but has a base latency of ~1 second.
- **Apache Flink**: True continuous streaming. Processes events one-by-one as they arrive. Sub-millisecond latency. Flink is widely considered the superior pure-streaming engine, though Spark is easier if you already know PySpark.

---
## Next Steps
Go to `labs/` to see how PySpark Structured Streaming handles windowing!
