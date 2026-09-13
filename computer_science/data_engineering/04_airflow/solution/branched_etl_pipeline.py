from datetime import datetime, timedelta
import random
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'data_engineering',
    'depends_on_past': False,
    'retries': 1,
}

dag = DAG(
    'branched_etl_pipeline',
    default_args=default_args,
    schedule_interval=timedelta(days=1),
    start_date=datetime(2023, 1, 1),
    catchup=False,
)

def extract_data(**kwargs):
    record_count = random.randint(100, 1000)
    kwargs['ti'].xcom_push(key='extracted_records', value=record_count)

def transform_data(**kwargs):
    ti = kwargs['ti']
    extracted = ti.xcom_pull(key='extracted_records', task_ids='extract_task')
    cleaned = extracted - random.randint(0, 50)
    ti.xcom_push(key='cleaned_records', value=cleaned)

# The Branching Logic Function
def check_volume(**kwargs):
    ti = kwargs['ti']
    cleaned = ti.xcom_pull(key='cleaned_records', task_ids='transform_task')
    
    # Return the task_id of the next task to execute
    if cleaned > 500:
        return 'alert_ds_team_task'
    else:
        return 'load_task'

def load_data(**kwargs):
    print("Loading data...")

# Operators
extract_task = PythonOperator(task_id='extract_task', python_callable=extract_data, dag=dag)
transform_task = PythonOperator(task_id='transform_task', python_callable=transform_data, dag=dag)
load_task = PythonOperator(task_id='load_task', python_callable=load_data, dag=dag)

# The Branch Operator
branch_task = BranchPythonOperator(
    task_id='branch_check_volume',
    python_callable=check_volume,
    dag=dag,
)

alert_task = BashOperator(
    task_id='alert_ds_team_task',
    bash_command='echo "ALERT: High volume day!"',
    dag=dag,
)

# Note the trigger_rule! By default, tasks wait for ALL upstream to succeed.
# In a branch, some upstream tasks are skipped. We just want to ensure none failed.
notify_task = BashOperator(
    task_id='notify_success',
    bash_command='echo "Pipeline complete."',
    trigger_rule='none_failed_or_skipped',
    dag=dag,
)

# Dependencies
extract_task >> transform_task >> branch_task

# Branch path 1: High volume
branch_task >> alert_task >> load_task >> notify_task

# Branch path 2: Normal volume
branch_task >> load_task >> notify_task
