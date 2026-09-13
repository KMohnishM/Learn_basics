from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("SparkSQL") \
    .master("spark://localhost:7077") \
    .getOrCreate()

data = [
    (1, "Widget A", 100),
    (2, "Widget B", 200),
    (3, "Widget C", 150)
]
df = spark.createDataFrame(data, ["id", "product", "price"])

# Register the DataFrame as a temporary SQL view
df.createOrReplaceTempView("products")

print("--- Running Standard SQL via Spark ---")
# You can write literal SQL strings! 
# Spark parses this, optimizes it via the Catalyst Optimizer, and converts it to RDD code.
expensive_products = spark.sql("""
    SELECT product, price 
    FROM products 
    WHERE price >= 150
    ORDER BY price DESC
""")

expensive_products.show()

# To view the execution plan:
print("--- Execution Plan ---")
expensive_products.explain()

spark.stop()
