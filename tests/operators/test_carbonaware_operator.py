"""
Pytest module to test CarbonAwareOperator.

Requires pytest and pytest-mock libraries.

Run test:

    pytest tests/operators/test_carbonaware_operator.py -v

"""

import time
from airflow.exceptions import TaskDeferred
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from airflow.models.taskinstance import TaskInstance
from airflow.utils.context import Context

from carbonaware_provider.operators.carbonaware import CarbonAwareOperator
from carbonaware_scheduler.types.schedule_create_response import ScheduleCreateResponse, ScheduleOption

"""
Test CarbonAware Operator.
"""

@pytest.mark.parametrize(
    ["execution_window_minutes", "task_duration_minutes", "zone"],
    [
        (120, 45, {"provider": "aws", "region": "us-east-1"}),
        (60, 30, {"provider": "gcp", "region": "us-central1"}),
        (60, 30, None)
    ]
)
def test_init(execution_window_minutes: int, task_duration_minutes: int, zone: dict | None):
    """Test operator initialization."""
    operator = CarbonAwareOperator(
        task_id="test_carbon_aware",
        execution_window_minutes=execution_window_minutes,
        task_duration_minutes=task_duration_minutes,
        zone=zone,
    )

    assert operator.execution_window_minutes == execution_window_minutes
    assert operator.task_duration_minutes == task_duration_minutes
    assert operator.zone == zone


@pytest.mark.parametrize(
    "zone",
    [
        # Test with explicit zone
        ({"provider": "aws", "region": "us-east-1"}),
    ]
)
def test_find_optimal_time_with_zone(zone: dict | None):
    """Test finding optimal execution time with explicit zone."""
    # Mock the scheduler client and response
    mock_client = MagicMock()
    mock_response = MagicMock(ScheduleCreateResponse)
    mock_ideal = MagicMock(ScheduleOption)
    optimal_time = datetime.now(timezone.utc) + timedelta(minutes=30)
    mock_ideal.time = optimal_time
    mock_response.ideal = mock_ideal
    mock_client.schedule.create.return_value = mock_response
    
    # Use patch as a context manager
    with patch('carbonaware_provider.operators.carbonaware.CarbonawareScheduler', return_value=mock_client):
        operator = CarbonAwareOperator(
            task_id="test_carbon_aware",
            execution_window_minutes=60,
            task_duration_minutes=30,
            zone=zone
        )
        
        result = operator._find_optimal_time()
        
    # Assert scheduler was called with correct parameters
    mock_client.schedule.create.assert_called_once()
    call_args = mock_client.schedule.create.call_args[1]
    assert call_args["duration"] == "PT30M"
    assert len(call_args["windows"]) == 1
    assert call_args["zones"] == [zone] if zone else []
    
    # Assert result is the optimal time
    assert result == optimal_time


def test_find_optimal_time_with_auto_detection():
    """Test finding optimal execution time with auto-detected zone."""
    # Mock the scheduler client and response
    mock_client = MagicMock()
    
    # Mock the detect_cloud_zone function
    detected_zone = [{"provider": "gcp", "region": "us-central1"}]
    
    # Mock the schedule response
    mock_response = MagicMock(ScheduleCreateResponse)
    mock_ideal = MagicMock(ScheduleOption)
    optimal_time = datetime.now(timezone.utc) + timedelta(minutes=30)
    mock_ideal.time = optimal_time
    mock_response.ideal = mock_ideal
    
    mock_client.schedule.create.return_value = mock_response
    
    with (
        patch('carbonaware_provider.operators.carbonaware.CarbonawareScheduler', return_value=mock_client),
        patch('carbonaware_provider.operators.carbonaware.detect_cloud_zone', return_value=detected_zone)
    ):
        operator = CarbonAwareOperator(
            task_id="test_carbon_aware",
            execution_window_minutes=60,
            task_duration_minutes=30,
            zone=None  # Auto-detect zone
        )
        
        result = operator._find_optimal_time()
    
    # Assert scheduler was called with correct parameters
    mock_client.schedule.create.assert_called_once()
    call_args = mock_client.schedule.create.call_args[1]
    assert call_args["duration"] == "PT30M"
    assert len(call_args["windows"]) == 1
    assert call_args["zones"] == detected_zone
    
    # Assert result is the optimal time
    assert result == optimal_time


def test_execute_immediate():
    """Test execution when optimal time is now."""
    # Mock the scheduler client and response, with optimal time being now
    mock_client = MagicMock()
    mock_response = MagicMock(ScheduleCreateResponse)
    mock_ideal = MagicMock(ScheduleOption)
    optimal_time = datetime.now(timezone.utc)
    mock_ideal.time = optimal_time
    mock_response.ideal = mock_ideal
    mock_client.schedule.create.return_value = mock_response
    
    # Use patch as a context manager
    with patch('carbonaware_provider.operators.carbonaware.CarbonawareScheduler', return_value=mock_client):
        operator = CarbonAwareOperator(
            task_id="test_carbon_aware",
            execution_window_minutes=60,
            task_duration_minutes=30,
            zone={"provider": "aws", "region": "us-east-1"}
        )
    
        # Create a mock context that conforms to Context type
        mock_ti = MagicMock()
        mock_context = Context({
            "task_instance": mock_ti,
            "execution_date": datetime.now(timezone.utc)
        })
        
        # Execute the operator
        start = time.time()
        result = operator.execute(mock_context)
        end = time.time()
        
        # Assert that the operator returns None immediately (allowing downstream tasks to run)
        assert result is None, "Operator should return None immediately"
        assert (end - start) < 1, "Operator should execute in less than 1 second"


def test_execute_defer():
    """Test deferral when optimal time is in the future."""
    # Mock that the optimal time is in the future
    future_time = datetime.now(timezone.utc) + timedelta(minutes=30)

    # Mock the scheduler client and response
    mock_client = MagicMock()
    mock_response = MagicMock(ScheduleCreateResponse)
    mock_ideal = MagicMock(ScheduleOption)
    mock_ideal.time = future_time
    mock_response.ideal = mock_ideal
    mock_client.schedule.create.return_value = mock_response
        
    operator = CarbonAwareOperator(
        task_id="test_carbon_aware",
        execution_window_minutes=60,
        task_duration_minutes=30,
        zone={"provider": "aws", "region": "us-east-1"}
    )

    # Create a mock context that conforms to Context type
    mock_ti = MagicMock()
    mock_context = Context({
        "task_instance": mock_ti,
        "execution_date": datetime.now()
    })
    
    with (
        patch('carbonaware_provider.operators.carbonaware.CarbonawareScheduler', return_value=mock_client),
    ):
        with pytest.raises(TaskDeferred) as exc_info:
            # Execute the operator
            operator.execute(mock_context)

    # Assert that the task was deferred
    assert exc_info.value.trigger == "DateTimeTrigger"
    assert exc_info.value.method_name == "execute_complete"
    assert exc_info.value.kwargs["optimal_time"] == future_time.isoformat()
