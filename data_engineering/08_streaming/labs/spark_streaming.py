from pyspark.sql import SparkSession
from pyspark.sql.functions import window, col
import time

spark = SparkSession.builder \
    .appName("StructuredStreamingDemo") \
    .master("local[*]") \
    .getOrCreate()

# To keep the lab simple without requiring a full Kafka setup, 
# we simulate a stream by reading from a directory. Spark will treat
# any new CSV files dropped into this directory as new streaming data!
schema = "timestamp TIMESTAMP, user_id STRING, amount DOUBLE"

print("Listening for new files in '/tmp/stream_data' ...")
# 1. readStream (Instead of read)
streaming_df = spark.readStream \
    .schema(schema) \
    .csv("/tmp/stream_data")

# 2. Windowing Aggregation
# We want the total revenue every 5 minutes (Tumbling Window)
# based on the EVENT TIME (the timestamp in the CSV file).
# We also add a Watermark of 10 minutes to handle late data!
windowed_revenue = streaming_df \
    .withWatermark("timestamp", "10 minutes") \
    .groupBy(
        window(col("timestamp"), "5 minutes")
    ) \
    .sum("amount")

# 3. writeStream (Instead of write)
# Output modes: 
# - 'append' (only output new rows once the watermark passes)
# - 'update' (output rows that have changed)
# - 'complete' (output the entire aggregated table every time)
query = windowed_revenue.writeStream \
    .outputMode("update") \
    .format("console") \
    .option("truncate", "false") \
    .start()

# query.awaitTermination() # In reality, this runs forever. 
time.sleep(2) # Mock exit for lab purposes
spark.stop()
