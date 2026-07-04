# Exercise: Branching in Airflow

In the lab, our pipeline is strictly linear: Extract -> Transform -> Load -> Notify.

However, in real-world pipelines, you often need to make decisions dynamically based on the data. For example:
- If we extracted fewer than 500 records, it's a slow day, just load them normally.
- If we extracted MORE than 500 records, it's a high-volume day, and we need to alert the Data Science team.

Airflow handles this using the `BranchPythonOperator`.

## Your Task

Modify the ETL DAG to include branching logic after the `transform_task`:

1. Import the `BranchPythonOperator` from `airflow.operators.python`.
2. Create a new python function `check_volume(**kwargs)` that pulls the `cleaned_records` count from XCom.
3. If `cleaned_records > 500`, the function should return the string `'alert_ds_team_task'`.
4. If `cleaned_records <= 500`, the function should return the string `'load_task'`.
5. Create a new `BranchPythonOperator` task that calls this function.
6. Create a new dummy `BashOperator` named `alert_ds_team_task` that simply echos "Alerting DS Team: High Volume!".
7. Update your task dependencies (`>>`) so that the DAG splits after the branch task. 

*Hint: If a task follows a branch but you want it to run regardless of which path was taken (like the final `notify_success` task), you may need to set `trigger_rule='none_failed_or_skipped'` on that final task.*

Check the `solution/` folder for the complete DAG implementation!
