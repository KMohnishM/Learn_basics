from pyspark.sql import SparkSession
from pyspark.sql.functions import window, col, sum

spark = SparkSession.builder.appName("AnomalyDetection").getOrCreate()

# Assume streaming_df is already defined
# streaming_df = spark.readStream...

# The Solution:
anomalies = streaming_df \
    .withWatermark("timestamp", "10 minutes") \
    .groupBy(
        "user_id", 
        # A 10-minute window that slides every 2 minutes!
        window(col("timestamp"), "10 minutes", "2 minutes")
    ) \
    .agg(sum("amount").alias("total_spent")) \
    .filter(col("total_spent") > 1500)  # The anomaly threshold

# In a real system, you would write this stream to a Kafka topic or database
# that triggers a real-time alert to the fraud department.
"""
query = anomalies.writeStream \
    .outputMode("append") \
    .format("kafka") \
    ...
"""
