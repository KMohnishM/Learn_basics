from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# 1. Initialize SparkSession (The entry point to programming Spark)
spark = SparkSession.builder \
    .appName("SparkBasics") \
    .master("spark://localhost:7077") \
    .getOrCreate()

# Normally you'd read a CSV or Parquet file from S3:
# df = spark.read.csv("s3://my-bucket/data.csv", header=True)

# For this lab, we'll create a DataFrame in memory
data = [
    ("Alice", "Sales", 5000),
    ("Bob", "Engineering", 7000),
    ("Charlie", "Sales", 4500),
    ("Diana", "Engineering", 8000),
    ("Evan", "HR", 4000)
]
columns = ["Name", "Department", "Salary"]

print("--- Creating DataFrame ---")
df = spark.createDataFrame(data, columns)
# Action: show() triggers execution
df.show()

# 2. Transformations (Lazy)
print("--- Applying Transformations (Lazy Evaluation) ---")
# This runs instantly because nothing is actually computed yet
high_earners = df.filter(col("Salary") > 5000)
engineering_high_earners = high_earners.filter(col("Department") == "Engineering")

print("--- Triggering Action ---")
# Now Spark looks at the DAG, optimizes it (combining the two filters into one), and executes.
engineering_high_earners.show()

# 3. GroupBy (A Wide Transformation causing a Shuffle)
print("--- GroupBy (Shuffle) ---")
dept_salaries = df.groupBy("Department").sum("Salary")
dept_salaries.show()

spark.stop()
