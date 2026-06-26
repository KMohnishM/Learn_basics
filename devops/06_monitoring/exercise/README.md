# Module 6 Exercise: Writing PromQL

In Prometheus, data is queried using PromQL. 

Imagine you have an application exposing a metric called `http_requests_total`. This metric has "labels" that allow you to filter it. For example, it might look like this in the database:
`http_requests_total{method="GET", status="200"}`
`http_requests_total{method="POST", status="500"}`

## The Challenge

Your task is to write a PromQL query that calculates the **per-second rate of HTTP 500 errors** over the last **5 minutes**.

1. You will need to use the `http_requests_total` metric.
2. You will need to filter it using the `status` label to only look at `"500"` errors.
3. You will need to use the `rate()` function, passing in a 5-minute time window (`[5m]`).

Write your query in a file called `query.txt`.

Good luck! Check the `solution/` folder when you are done.
