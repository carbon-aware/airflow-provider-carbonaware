"""
Example DAG demonstrating the CarbonAwareOperator with cloud zone auto-detection.

This example shows how to use the CarbonAwareOperator with automatic zone detection
from cloud instance metadata. This will only work when running on a cloud instance on a supported provider (AWS, GCP, Azure).
"""

from pendulum import datetime as pendulum_datetime

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

from airflow_provider_carbonaware.operators.carbonaware import CarbonAwareOperator


@dag(
    start_date=pendulum_datetime(2023, 1, 1),
    schedule=None,
    default_args={"retries": 2},
    tags=["example", "carbon-aware", "cloud-introspection"],
)
def carbon_aware_workflow_introspection():
    """
    ### Carbon Aware DAG Example with Cloud Zone Auto-Detection

    This DAG demonstrates the use of the CarbonAwareOperator with automatic
    cloud zone detection from instance metadata.

    NOTE: This example will only work when running on a cloud instance.
    When running locally, the zone detection may fail or return incorrect results.

    The operator will:
    1. Automatically detect the cloud provider and region from instance metadata
    2. Find the optimal time to run downstream tasks within the specified execution window
    3. Defer execution to that optimal time
    """

    # This task runs immediately and is not affected by carbon-aware scheduling
    setup_task = BashOperator(
        task_id="setup_task",
        bash_command="echo 'Setting up resources for carbon-aware execution...'",
    )

    # This operator uses auto-detection to determine the cloud zone
    # All tasks downstream from this operator will run at the optimal time
    carbon_aware = CarbonAwareOperator(
        task_id="wait_for_optimal_carbon",
        execution_window_minutes=120,
        task_duration_minutes=30,
        zone=None,  # Auto-detect zone from instance metadata
    )

    # This task will run at the optimal time for carbon intensity
    compute_task = BashOperator(
        task_id="compute_task",
        bash_command="echo 'Running compute-intensive task at optimal carbon intensity time: $(date)'",
    )

    # Define the task dependencies
    setup_task >> carbon_aware >> compute_task


# Instantiate the DAG
carbon_aware_workflow_introspection()
