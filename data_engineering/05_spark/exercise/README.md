# Exercise: PySpark Performance Tuning

You are given a massive dataset of e-commerce transactions. 
Each row has: `transaction_id`, `country`, `product_id`, `amount`.

Your company is expanding to the USA, so the marketing team spent $10 million on ads there. As a result, 99% of all rows in the dataset have `country = "USA"`. The other 1% are spread across 199 other countries.

You run this Spark code to find the total revenue per country:

```python
revenue_by_country = df.groupBy("country").sum("amount")
revenue_by_country.write.parquet("s3://bucket/output/")
```

## The Problem
Your Spark cluster has 200 executors. 199 of them finish in 2 seconds and then sit idle. 1 executor runs for 4 hours, and then crashes with an `Out Of Memory (OOM)` error.

**This is classic Data Skew.** Because you grouped by `country`, all the "USA" records (99% of the data) were sent across the network to a SINGLE executor.

## Your Task
Write a PySpark script in `solution/solution.py` that fixes this data skew using the **Salting Technique**.

*Hint: Salting means adding a random number (e.g., 1 to 10) to the skewed key BEFORE grouping, so the data gets split across 10 executors instead of 1. After the first grouping, you group AGAIN without the salt to get the final answer.*
