from datetime import datetime, timedelta
import random
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

# Default settings applied to all tasks in this DAG
default_args = {
    'owner': 'data_engineering',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# 1. Define the DAG
dag = DAG(
    'daily_etl_pipeline',
    default_args=default_args,
    description='A simple daily ETL pipeline',
    schedule_interval=timedelta(days=1), # Run every day
    start_date=datetime(2023, 1, 1),     # Set in the past to see backfilling!
    catchup=False,                       # Change to True to run all historical days
    tags=['etl', 'data_engineering'],
)

# 2. Define the Python functions that will do the work
def extract_data(**kwargs):
    print("Extracting data from API...")
    # Simulate extraction
    record_count = random.randint(100, 1000)
    
    # We use XCom (Cross-Communication) to pass the record count to the next task
    # kwargs['ti'] gives us the TaskInstance object
    kwargs['ti'].xcom_push(key='extracted_records', value=record_count)
    print(f"Extracted {record_count} records.")

def transform_data(**kwargs):
    print("Transforming data...")
    # Retrieve the record count from the previous task using XCom
    ti = kwargs['ti']
    extracted_records = ti.xcom_pull(key='extracted_records', task_ids='extract_task')
    
    if not extracted_records:
        raise ValueError("No records extracted!")
        
    cleaned_records = extracted_records - random.randint(0, 50)
    print(f"Cleaned data. {cleaned_records} records remaining.")
    ti.xcom_push(key='cleaned_records', value=cleaned_records)

def load_data(**kwargs):
    print("Loading data into Data Warehouse...")
    ti = kwargs['ti']
    cleaned_records = ti.xcom_pull(key='cleaned_records', task_ids='transform_task')
    print(f"Successfully loaded {cleaned_records} records into Postgres.")

# 3. Instantiate the Operators (creating Tasks)
extract_task = PythonOperator(
    task_id='extract_task',
    python_callable=extract_data,
    provide_context=True,
    dag=dag,
)

transform_task = PythonOperator(
    task_id='transform_task',
    python_callable=transform_data,
    provide_context=True,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_task',
    python_callable=load_data,
    provide_context=True,
    dag=dag,
)

notify_task = BashOperator(
    task_id='notify_success',
    bash_command='echo "ETL Pipeline completed successfully for {{ ds }}"',
    dag=dag,
)

# 4. Define Task Dependencies (The Directed Acyclic Graph)
# Extract must run before Transform. Transform must run before Load.
extract_task >> transform_task >> load_task >> notify_task
