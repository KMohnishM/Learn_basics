# Module 4: Workflow Orchestration with Apache Airflow

As your data ecosystem grows, you will have dozens (or hundreds) of scripts running. 
- "Script A extracts data at 2 AM."
- "Script B transforms it at 3 AM."
- "Script C loads it into the warehouse at 4 AM."

What happens if Script A fails? If you just use Linux `cron`, Script B will still run at 3 AM, process incomplete data, and corrupt your warehouse. 
You need **Workflow Orchestration**.

## What is Apache Airflow?
Airflow is the industry standard open-source platform to programmatically author, schedule, and monitor workflows. Workflows in Airflow are defined as code (Python), which means they can be version controlled, tested, and code-reviewed.

### The Core Concept: DAGs
A workflow in Airflow is represented as a **DAG (Directed Acyclic Graph)**.
- **Directed**: The workflow has a specific direction (Task A must run before Task B).
- **Acyclic**: The workflow cannot have loops (Task B cannot loop back to Task A).

### Airflow Architecture
1. **Scheduler**: The heart of Airflow. It reads the DAGs, determines when tasks should run, and sends them to the executor.
2. **Webserver**: The UI. Allows you to view DAGs, see logs, trigger runs, and debug failures.
3. **Database (Metadata Store)**: Usually Postgres. Stores state (which tasks passed, failed, are currently running).
4. **Executor/Workers**: The processes that actually run the task code. (Local, Celery, or Kubernetes).

### Operators & Tasks
An Operator is a template for a specific type of work. When you instantiate an Operator in a DAG, it becomes a **Task**.
- `PythonOperator`: Runs a Python function.
- `BashOperator`: Runs a bash script.
- `PostgresOperator`: Runs a SQL query.
- `HttpSensor`: Waits for a REST API to return a specific response before continuing.

### XComs (Cross-Communication)
Tasks in Airflow are designed to be isolated. But what if Task A downloads a file and needs to pass the filename to Task B? 
Airflow uses **XComs** (a small key-value store in the metadata database). 
*Anti-pattern*: Do NOT use XComs to pass massive datasets (like a 1GB Pandas dataframe) between tasks. Pass the *metadata* (like an S3 URI), and let the tasks fetch the data themselves.

### Catchup and Backfilling
If you define a daily DAG that started on January 1st, and today is January 5th, Airflow's `catchup=True` feature will automatically run the DAG 5 times to process the historical data. 

## Best Practices
1. **Idempotency**: Tasks must produce the exact same result no matter how many times they run. If a task fails halfway, re-running it should not duplicate data.
2. **Atomic Tasks**: Each task should do exactly one thing. Don't write one massive PythonOperator that does Extract, Transform, and Load. Split them up so if Transform fails, you don't have to re-Extract.

---

## Next Steps
Go to the `labs/` folder. We have a full Airflow stack configured via Docker Compose. We will orchestrate a Python ETL pipeline using DAGs!
