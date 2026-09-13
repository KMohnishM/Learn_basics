# 📦 Data Engineering Curriculum

A comprehensive, hands-on curriculum that takes you from the fundamentals of data engineering all the way to real-time streaming pipelines. Every module is built around **real tools, real code, and real concepts** — not just theory.

Each module follows a consistent structure:
- `README.md` — In-depth theory covering all concepts for that week
- `labs/` — Fully runnable code with Docker Compose environments
- `exercise/` — A challenge for you to solve independently
- `solution/` — The complete, annotated solution

---

## 🗺️ Curriculum Overview

| Week | Module | Key Tools | Topics |
|------|--------|-----------|--------|
| 1 | [Foundations](./01_foundations/) | Postgres, Python | OLTP vs OLAP, Data Stacks, File Formats, Parquet |
| 2 | [ETL & Batch Processing](./02_etl_batch/) | Python, Postgres | ETL vs ELT, Idempotency, Incremental Loads, Data Quality |
| 3 | [dbt](./03_dbt/) | dbt, Postgres | Transformations, Models, Tests, Incremental Materializations |
| 4 | [Airflow](./04_airflow/) | Apache Airflow | DAGs, Operators, XComs, Scheduling, Branching |
| 5 | [Spark](./05_spark/) | PySpark | Distributed Computing, DataFrames, Lazy Evaluation, Shuffles, Skew |
| 6 | [Kafka](./06_kafka/) | Apache Kafka | Event Streaming, Topics, Partitions, Offsets, Exactly-Once |
| 7 | [Data Warehouse](./07_data_warehouse/) | SQL, Postgres | Star Schema, Fact/Dimension Tables, SCD Type 2 |
| 8 | [Streaming](./08_streaming/) | PySpark Streaming | Event Time, Watermarks, Tumbling & Sliding Windows |

---

## 📅 Week-by-Week Breakdown

### Week 1 — [Foundations](./01_foundations/)
> *What is Data Engineering? How is data stored and moved at scale?*

You'll learn the foundational vocabulary and mental models that every Data Engineer must have. We cover the **Modern Data Stack** end-to-end (ingestion → storage → transformation → serving), and deep-dive into why OLAP columnar storage is 100x faster than OLTP row storage for analytics. You'll set up a local Postgres database and load it with e-commerce data to experience the difference yourself.

**Key Concepts:** OLTP vs OLAP, Row vs Columnar Storage, Data Lakes/Warehouses/Lakehouses, Batch vs Streaming, CSV/JSON/Parquet/Avro file formats.

---

### Week 2 — [ETL & Batch Processing](./02_etl_batch/)
> *How do you reliably move data from A to B without losing or corrupting it?*

The art of writing production-grade data pipelines. We go deep into what separates an amateur pipeline from a professional one: **idempotency** (safe to re-run), **incremental loading** (only process new data), and proper **error handling and logging**. You'll build a full Extract → Transform → Load pipeline against a real public REST API (Open Meteo weather data).

**Key Concepts:** ETL vs ELT, Idempotency, Full vs Incremental Loads, CDC, Watermarks, Schema Evolution, Data Quality.

---

### Week 3 — [dbt (Data Build Tool)](./03_dbt/)
> *How do data teams manage SQL transformations like software engineers manage code?*

dbt is the tool that brought software engineering best practices (version control, testing, documentation, CI/CD) into the world of data transformations. You'll build a complete dbt project from scratch: staging models that clean raw data, mart models that build business-ready tables, data tests that catch bad data automatically, and incremental models that only process new records.

**Key Concepts:** ELT Paradigm, dbt Project Structure, `ref()` and DAG Lineage, Materializations (table/view/incremental/ephemeral), Jinja Templating, Generic & Singular Tests.

---

### Week 4 — [Apache Airflow](./04_airflow/)
> *How do you reliably schedule and monitor complex multi-step data pipelines?*

When you have dozens of interdependent scripts that must run in order, cron jobs break catastrophically. Airflow solves this with **Directed Acyclic Graphs (DAGs)** — workflows defined as Python code. You'll deploy a full Airflow stack locally with Docker, build a DAG that orchestrates our ETL pipeline, and implement branching logic that makes runtime decisions based on data volume.

**Key Concepts:** Airflow Architecture (Scheduler, Webserver, Metadata DB), DAG Anatomy, Operators (Python, Bash, HTTP Sensor), XComs, Scheduling & Backfilling, Branching, Task Retries & SLAs.

---

### Week 5 — [Apache Spark](./05_spark/)
> *What happens when your data no longer fits in a single machine's RAM?*

When Pandas crashes with an Out of Memory error on your terabyte dataset, you need distributed computing. Spark is the industry standard for processing massive datasets across a cluster of machines. We cover the critical concepts most tutorials skip: **why shuffles are expensive**, **how lazy evaluation enables optimization**, and **how to fix Data Skew** — the #1 cause of Spark jobs running for hours before crashing.

**Key Concepts:** Spark Architecture (Driver/Executors), RDDs vs DataFrames, Lazy Evaluation, Transformations vs Actions, Narrow vs Wide Transformations, Shuffles, Catalyst Optimizer, Data Skew & Salting.

---

### Week 6 — [Apache Kafka](./06_kafka/)
> *How do you build systems that react to events in real time?*

Kafka is not a message queue — it's a **distributed commit log**. This distinction is critical. Unlike RabbitMQ, messages in Kafka are not deleted when consumed. They are retained on disk, allowing multiple completely independent applications to read the same data at their own pace. We cover the internals deeply: partitions, consumer groups, offset management, and how Kafka achieves exactly-once delivery via the Transactional API.

**Key Concepts:** Event-Driven Architecture, Kafka vs Message Queues, Brokers/Topics/Partitions/Replicas, Producer Internals (acks, retries), Consumer Groups & Offset Management, Exactly-Once Semantics.

---

### Week 7 — [Data Warehousing & Dimensional Modeling](./07_data_warehouse/)
> *How do you design a database that makes analytics blazing fast?*

An OLAP database schema is designed completely differently from an OLTP schema. Ralph Kimball's **Star Schema** — with Fact tables at the center and Dimension tables around them — is the gold standard for making complex analytical queries both fast and readable. We go deep on a subtle but critical concept: **Slowly Changing Dimensions (SCD Type 2)**, which is how you preserve historical accuracy when real-world data changes (e.g., a customer moves from New York to California).

**Key Concepts:** Star Schema vs Snowflake Schema, Fact Table Types (Transaction/Snapshot/Accumulating), Dimension Tables, Surrogate Keys, SCD Types 0/1/2/3, Modern Cloud Data Warehouses (BigQuery/Snowflake/Redshift).

---

### Week 8 — [Real-Time Streaming](./08_streaming/)
> *What if you need to react to data in milliseconds, not hours?*

Batch processing runs at midnight. But credit card fraud happens right now. This module covers the conceptual and practical challenges of real-time stream processing. The hardest concept — **Event Time vs Processing Time** — is what separates engineers who build correct streaming systems from those who build systems that are fast but subtly wrong. We implement windowed aggregations in PySpark Structured Streaming and build an anomaly detection pipeline using sliding windows.

**Key Concepts:** Batch vs Streaming Trade-offs, Event Time vs Processing Time, Watermarks, Tumbling/Sliding/Session Windows, Stateful Processing, Lambda vs Kappa Architecture, PySpark Structured Streaming.

---

## 🚀 Getting Started

### Prerequisites
- **Docker Desktop** — All lab environments run via Docker Compose
- **Python 3.9+** — For running lab scripts
- **pip** — For installing Python dependencies per module

### Running a Lab
```bash
# Navigate to any module's labs directory
cd data_engineering/02_etl_batch/labs

# Start the Docker environment
docker-compose up -d

# Install Python dependencies for that module
pip install -r requirements.txt   # if present, otherwise check the README

# Run the lab script
python pipeline.py
```

### Recommended Learning Path
Work through the modules **in order** — each one builds on concepts from the previous. The weekly cadence (1 module per week) gives you enough time to:
1. Read the theory thoroughly
2. Run the labs and observe what's happening
3. Attempt the exercise independently before peeking at the solution

---

## 🛠️ Tech Stack

| Category | Tools |
|----------|-------|
| Databases | PostgreSQL, (BigQuery/Snowflake concepts) |
| Transformation | dbt, PySpark SQL |
| Orchestration | Apache Airflow |
| Distributed Processing | Apache Spark (PySpark) |
| Streaming | Apache Kafka, PySpark Structured Streaming |
| Infrastructure | Docker, Docker Compose |
| Languages | Python 3, SQL |

---

## 📁 Repository Structure

```
data_engineering/
├── 01_foundations/
│   ├── README.md          ← Deep-dive theory
│   ├── labs/              ← Runnable code + docker-compose.yml
│   ├── exercise/          ← Your challenge
│   └── solution/          ← Complete solution
├── 02_etl_batch/
│   └── ...
├── 03_dbt/
│   └── ...
├── 04_airflow/
│   └── ...
├── 05_spark/
│   └── ...
├── 06_kafka/
│   └── ...
├── 07_data_warehouse/
│   └── ...
└── 08_streaming/
    └── ...
```

---

*Happy learning! 🎉 Work through the labs, break things, and fix them — that's how Data Engineers are made.*
