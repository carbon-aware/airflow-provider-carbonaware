from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Dict, Optional

from airflow.models import BaseOperator, BaseOperatorLink
from airflow.providers.standard.triggers.temporal import DateTimeTrigger
from airflow.utils.context import Context

from carbonaware_scheduler import CarbonawareScheduler
from carbonaware_scheduler.lib.introspection import detect_cloud_zone

if TYPE_CHECKING:
    from airflow.utils.context import Context


class CarbonAwareOperatorExtraLink(BaseOperatorLink):
    """Extra link for CarbonAware Operator that points to the CarbonAware website."""

    name = "CarbonAware"

    def get_link(self, operator: BaseOperator, *, ti_key=None):
        return "https://carbonaware.dev"


class CarbonAwareOperator(BaseOperator):
    """
    Defers execution of downstream tasks to an optimal time based on carbon intensity.
    
    This operator uses the CarbonAware Scheduler API to find the optimal time
    to run tasks within a specified time window, based on carbon intensity
    in the specified cloud region(s).
    
    When added to a DAG, this operator will defer execution of all downstream tasks
    until the optimal time for carbon intensity. This allows for carbon-aware scheduling
    of your workflows without modifying the tasks themselves.
    
    Args:
        execution_window_minutes (int, optional): The time window (in minutes) during which 
            the tasks can be executed. Defaults to 60.
        task_duration_minutes (int, optional): The expected duration of the downstream 
            tasks in minutes. Defaults to 30.
        zone (Optional[Dict[str, str]], optional): Cloud provider zone to find carbon intensity for. 
            Format: {"provider": "aws", "region": "us-east-1"}. If None, will attempt to 
            introspect from instance metadata. Defaults to None.
        **kwargs: Additional arguments passed to the BaseOperator constructor.
    
    Example:
        ```python
        with DAG(...) as dag:
            # This operator will determine the optimal time to run
            carbon_aware = CarbonAwareOperator(
                task_id="wait_for_optimal_carbon",
                execution_window_minutes=120,  # Look for optimal time in the next 2 hours
                task_duration_minutes=30,      # Expected duration of downstream tasks
                zone={"provider": "aws", "region": "us-east-1"},
            )
            
            # These tasks will run at the optimal time
            task1 = PythonOperator(...)
            task2 = BashOperator(...)
            
            # Define dependencies
            carbon_aware >> [task1, task2]
        ```
    """

    ui_color = "#5cb85c"
    operator_extra_links = (CarbonAwareOperatorExtraLink(),)

    template_fields = ["zone"]

    def __init__(
        self,
        *,
        execution_window_minutes: int = 60,
        task_duration_minutes: int = 30,
        zone: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.execution_window_minutes = execution_window_minutes
        self.task_duration_minutes = task_duration_minutes
        self.zone = zone

    def execute(self, context: Context) -> Any:
        """
        Determines the optimal time to execute based on carbon intensity and defers execution to that time.
        
        Args:
            context (Context): The execution context.
            
        Returns:
            Any: None if executing immediately, otherwise defers execution.
        """
        # Find the optimal time and defer
        self.log.info("Finding optimal execution time based on carbon intensity")
        optimal_time = self._find_optimal_time()

        # If optimal time is now or in the past, execute immediately
        now = datetime.now(timezone.utc)
        if optimal_time <= now:
            self.log.info(
                "Optimal time is now or in the past, proceeding with execution"
            )
            return None

        # Otherwise, defer to the optimal time
        self.log.info(f"Deferring execution to optimal time: {optimal_time}")
        self.defer(
            trigger=DateTimeTrigger(moment=optimal_time, end_from_trigger=True),
            method_name="execute_complete",
        )

    def execute_complete(
        self, context: Context, event: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Callback for deferred execution. This is called when the trigger fires.
        
        Args:
            context (Context): The execution context.
            event (Optional[Dict[str, Any]], optional): The event data from the trigger.
                Defaults to None.
                
        Returns:
            Any: None, allowing downstream tasks to proceed.
        """
        moment = event.get("moment") if event else None
        self.log.info(f"Reached optimal carbon intensity time: {moment}")
        return None

    def _find_optimal_time(self) -> datetime:
        """
        Find the optimal time to execute the task based on carbon intensity.
        
        Uses the CarbonAware Scheduler API to determine the optimal time within
        the specified execution window based on forecasted carbon intensity.
        
        Returns:
            datetime: The optimal time to execute the task. Returns current time
                if an error occurs during the API call.
        """
        client = CarbonawareScheduler()

        # Calculate time window
        now = datetime.now(timezone.utc)
        end_time = now + timedelta(minutes=self.execution_window_minutes)

        window = {"start": now, "end": end_time}

        # Convert task duration to ISO 8601 duration format
        duration = f"PT{self.task_duration_minutes}M"

        # If zone is not specified, attempt to introspect from instance metadata
        if self.zone is None:
            zones = detect_cloud_zone()
        else:
            zones = [self.zone]

        # Get optimal schedule
        try:
            schedule_response = client.schedule.create(
                duration=duration,
                windows=[window],
                zones=zones,
                num_options=0,
            )
        except Exception as e:
            self.log.error(f"Failed to find optimal time -- defaulting to now: {e}")
            return now

        # Return the optimal time
        return schedule_response.ideal.time
