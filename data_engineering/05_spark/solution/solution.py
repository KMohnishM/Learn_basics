from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, rand, sum

spark = SparkSession.builder.appName("DataSkewFix").getOrCreate()

# Assume 'df' is the skewed dataframe
# df = spark.read.parquet("...")

# 1. Add a "Salt" (a random number between 0 and 9) to every row
# This splits the massive "USA" group into 10 smaller groups: "USA_0", "USA_1", etc.
salted_df = df.withColumn("salt", (rand() * 10).cast("int"))
salted_df = salted_df.withColumn("salted_country", col("country") + lit("_") + col("salt").cast("string"))

# 2. First GroupBy (Distributed across many executors!)
# Instead of 1 executor handling all USA data, 10 executors handle 1/10th of it each.
partial_aggregates = salted_df.groupBy("salted_country", "country").agg(sum("amount").alias("partial_amount"))

# 3. Second GroupBy (The Final Answer)
# Now that the massive data has been pre-aggregated into small chunks, 
# we can safely group by the real country name to get the final sum.
final_revenue = partial_aggregates.groupBy("country").agg(sum("partial_amount").alias("total_revenue"))

# final_revenue.write.parquet("...")
