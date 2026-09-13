# Module 5: Large-Scale Processing with Apache Spark

When your data no longer fits into the RAM of a single machine (e.g., hundreds of gigabytes or terabytes), Python and Pandas will crash with an Out of Memory (OOM) error. You need distributed computing. 

**Apache Spark** is the undisputed king of distributed data processing.

## 1. Why Spark? (The End of Hadoop MapReduce)
Before Spark, we used Hadoop MapReduce. MapReduce was incredibly slow because it wrote intermediate results to the hard disk after every single step.
Spark solved this by processing data **in memory**. It is up to 100x faster than Hadoop.

## 2. Spark Architecture
- **Driver**: The master node. It runs your `main()` function, analyzes your code, and creates the execution plan.
- **Cluster Manager**: Allocates resources (CPU, RAM). Can be YARN, Mesos, or Kubernetes.
- **Executors**: The worker nodes. They receive tasks from the Driver, execute them on their chunk of the data, and store data in memory.

## 3. Core Concepts

### RDDs vs DataFrames
- **RDD (Resilient Distributed Dataset)**: The low-level, original Spark data structure. It's just a distributed collection of objects. Hard to optimize.
- **DataFrame**: High-level, organized into named columns (like a SQL table or Pandas dataframe). Spark's **Catalyst Optimizer** automatically optimizes DataFrame queries under the hood. *Always use DataFrames.*

### Lazy Evaluation
When you tell Spark to filter a dataset, it does... absolutely nothing. 
Spark builds a logical graph (DAG) of your instructions. It only actually executes the code when you call an **Action** (e.g., `.show()`, `.count()`, or `.write()`). 
*Why?* If you filter a 1TB dataset, and then ask for `.limit(10)`, Spark's lazy evaluation is smart enough to just process the first 10 rows and stop, rather than processing 1TB and throwing away the rest!

### Transformations vs Actions
- **Transformations**: `filter()`, `groupBy()`, `select()`, `join()`. (Lazy).
- **Actions**: `count()`, `show()`, `write()`, `collect()`. (Trigger execution).

## 4. The Spark Bottleneck: The Shuffle
When analyzing performance, you must understand Narrow vs Wide transformations.

- **Narrow Transformation**: E.g., `filter()`. Each partition of data can be processed independently on its own executor. Fast.
- **Wide Transformation**: E.g., `groupBy()`, `join()`. To group data by user_id, Spark must move all data for User A to the same executor. This requires sending massive amounts of data across the network. This is called a **Shuffle**. Shuffles are the #1 cause of slow Spark jobs.

## 5. Performance Tuning
- **Data Skew**: If you group by "Country", and 99% of your users are in the "US", one executor will get 99% of the data and crash, while the others sit idle. (Fix: Salting).
- **Small Files Problem**: Reading 10,000 1MB files is much slower than reading ten 1GB files due to metadata overhead.
- **Caching**: If you use the same transformed DataFrame twice, call `.cache()` so Spark doesn't recompute it from scratch the second time.

---
## Next Steps
Go to `labs/` to spin up a local Spark cluster and write PySpark code!
