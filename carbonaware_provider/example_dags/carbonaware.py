"""
Example DAG demonstrating the CarbonAwareOperator with explicit zone configuration.

This example shows how to use the CarbonAwareOperator with an explicitly specified
cloud provider zone for carbon intensity optimization.
"""

from pendulum import datetime as pendulum_datetime
from datetime import datetime

from airflow.decorators import dag

# Compatible with both Airflow 1.x and 2.x
try:
    # Airflow 2.x
    from airflow.operators.python import PythonOperator  # noqa: F401
    from airflow.operators.bash import BashOperator
except ImportError:
    # Airflow 1.x
    from airflow.operators.python_operator import PythonOperator  # noqa: F401
    from airflow.operators.bash_operator import BashOperator

from carbonaware_provider.operators.carbonaware import CarbonAwareOperator


@dag(
    start_date=pendulum_datetime(2023, 1, 1),
    schedule=None,
    default_args={"retries": 2},
    tags=["example", "carbon-aware"],
)
def carbon_aware_workflow():
    """
    ### Carbon Aware DAG Example

    This DAG demonstrates the use of the CarbonAwareOperator to schedule tasks
    at optimal times based on carbon intensity.

    The operator will find the optimal time to run downstream tasks within the specified
    execution window and defer execution to that time.
    """

    # This task runs immediately and is not affected by carbon-aware scheduling
    setup_task = BashOperator(
        task_id="setup_task",
        bash_command="echo 'Setting up resources for carbon-aware execution...'",
    )

    # This operator determines the optimal time to run based on carbon intensity
    # All tasks downstream from this operator will run at the optimal time
    carbon_aware = CarbonAwareOperator(
        task_id="wait_for_optimal_carbon",
        execution_window_minutes=120,
        task_duration_minutes=30,
        zone={"provider": "aws", "region": "us-east-1"},
    )

    # These tasks will run at the optimal time for carbon intensity

    # Python task that runs at optimal carbon intensity time
    def process_data(ts=None, **kwargs):
        current_time = datetime.now()
        print(f"Processing data at optimal carbon intensity time: {current_time}")
        return "Processed data"

    process_task = PythonOperator(
        task_id="process_data",
        python_callable=process_data,
    )

    # Bash task that also runs at optimal carbon intensity time
    compute_task = BashOperator(
        task_id="compute_task",
        bash_command="echo 'Running compute-intensive task at optimal carbon intensity time: $(date)'",
    )

    # Define the task dependencies
    # setup_task runs immediately
    # carbon_aware determines the optimal time to run
    # process_task and compute_task run at the optimal time
    setup_task >> carbon_aware >> [process_task, compute_task]


carbon_aware_workflow()
