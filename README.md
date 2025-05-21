# Carbon Aware Provider for Apache Airflow

The Carbon Aware Provider for Apache Airflow allows you to optimize your workflows by scheduling tasks to run at times with lower carbon intensity. It introduces a `CarbonAwareOperator` that can shift the execution of downstream tasks to an optimal window based on forecasted carbon emissions data.

## Purpose

This package provides a time-shifting operator for Apache Airflow. Its main goal is to enable users to easily integrate carbon awareness into their data pipelines, reducing the environmental impact of their computations by running them when the energy grid is cleaner.

## Prerequisites

*   Apache Airflow >= 2.4
*   Python >= 3.8

## Installation

You can install the Carbon Aware Provider using pip:

```bash
pip install airflow-provider-carbonaware
```

This will also install the necessary dependencies, including `apache-airflow` (if not already present) and `carbonaware-scheduler-client`.

## Usage

To use the `CarbonAwareOperator`, you need to import it into your DAG file and then instantiate it as a task. Tasks downstream of the `CarbonAwareOperator` will be deferred. The `CarbonAwareOperator` itself will complete once it has identified the optimal time, and then it will defer. The Airflow scheduler will then resume the downstream tasks at that optimal time.

### Example DAG

Here's a basic example of how to incorporate the `CarbonAwareOperator` into your Airflow DAG:

```python
from pendulum import datetime as pendulum_datetime
from airflow.decorators import dag
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

from carbonaware_provider.operators.carbonaware import CarbonAwareOperator

@dag(
    start_date=pendulum_datetime(2023, 1, 1),
    schedule=None,
    default_args={"retries": 2},
    tags=["example", "carbon-aware"],
)
def my_carbon_aware_dag():
    """
    A DAG demonstrating the CarbonAwareOperator.
    """
    
    setup_task = BashOperator(
        task_id="setup_task",
        bash_command="echo 'Performing initial setup...'"
    )
    
    # This operator will find the best time within the next 2 hours
    # for a task that is expected to run for 30 minutes in the 'aws:us-east-1' zone.
    find_optimal_time = CarbonAwareOperator(
        task_id="find_optimal_carbon_time",
        execution_window_minutes=120,  # Look for optimal time in the next 120 minutes
        task_duration_minutes=30,      # The estimated duration of the carbon-sensitive workload
        zone={"provider": "aws", "region": "us-east-1"} # Specify your cloud provider and region
        # Alternatively, you can use:
        # location="eastus" # For Azure (example, consult client docs for exact supported values)
        # location="gcp-europe-west1" # For GCP (example, consult client docs for exact supported values)
    )
    
    def my_data_processing_task():
        print("Running data processing task at the optimal carbon intensity time.")
        # Your data processing logic here

    process_data = PythonOperator(
        task_id="process_data_at_optimal_time",
        python_callable=my_data_processing_task,
    )

    cleanup_task = BashOperator(
        task_id="cleanup_task_after_optimal_run",
        bash_command="echo 'Cleaning up after carbon-aware execution.'"
    )

    # Define dependencies
    # setup_task runs first.
    # find_optimal_time runs next, deferring until the best carbon intensity window.
    # process_data and cleanup_task run only after find_optimal_time completes at the optimal time.
    setup_task >> find_optimal_time >> process_data >> cleanup_task

my_carbon_aware_dag_instance = my_carbon_aware_dag()
```

### Operator Parameters

The `CarbonAwareOperator` accepts the following key parameters:

*   `task_id` (str): A unique, descriptive id for the task.
*   `execution_window_minutes` (int): The time window (in minutes) from the current time within which to find the optimal execution slot.
*   `task_duration_minutes` (int): The estimated duration (in minutes) of the tasks that will run at the optimal time.
*   `zone` (dict, optional): Specifies the cloud provider and region (e.g., `{"provider": "aws", "region": "us-east-1"}`) If not specified, the operator will attempt to introspect the cloud provider and region from instance metadata.
*   `deferrable` (bool, optional): Defaults to `True`. Set to `False` to make the operator blocking (not recommended for its intended use).

The operator leverages the `carbonaware-scheduler-client` to fetch carbon intensity data and determine the optimal time to run, according to carbon forecasting.

## Important Notes

### macOS Proxy Issues

If you are running Airflow on macOS, you might encounter segmentation faults related to system proxy lookups. This is a known issue with Python's `urllib` (and libraries that use it, such as `httpx` which is used by `carbonaware-scheduler-client`) on macOS, especially within complex execution environments like Airflow. To mitigate this, it is recommended to set the following environment variable in your Airflow environment:

```bash
export no_proxy='*'
```

This bypasses the system proxy lookup that can cause the crash.

## Project Links

*   Homepage: [https://carbonaware.dev](https://carbonaware.dev)
*   Source Code: [https://github.com/carbon-aware/airflow-provider-carbonaware/](https://github.com/carbon-aware/airflow-provider-carbonaware/)

---

This README provides a starting point. You can expand it with more details on configuration, advanced usage patterns, contribution guidelines, and more as the project evolves.
