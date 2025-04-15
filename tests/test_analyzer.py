import pytest
from unittest.mock import patch
from analyzer import (
    analyze_cost_data, analyze_idle_instances, analyze_untagged_resources,
    analyze_ebs_optimization, analyze_cost_anomalies # Import new functions
)

# Basic test structure - more tests to be added

@patch('analyzer.get_cost_by_service') # Mock the data fetcher function
def test_analyze_cost_data_success(mock_get_cost):
    """Tests that analyze_cost_data returns data from the fetcher."""
    mock_cost_data = {"EC2": 100.0, "S3": 50.0}
    mock_get_cost.return_value = mock_cost_data

    result = analyze_cost_data(days=30)

    assert result == mock_cost_data
    mock_get_cost.assert_called_once_with(days=30)

@patch('analyzer.get_cost_by_service')
def test_analyze_cost_data_failure(mock_get_cost):
    """Tests that analyze_cost_data returns None when fetcher fails."""
    mock_get_cost.return_value = None

    result = analyze_cost_data(days=30)

    assert result is None
    mock_get_cost.assert_called_once_with(days=30)

@patch('analyzer.get_idle_ec2_instances') # Mock the data fetcher function
def test_analyze_idle_instances_success(mock_get_idle):
    """Tests that analyze_idle_instances returns data from the fetcher."""
    mock_idle_data = [{"InstanceId": "i-123", "Region": "us-east-1", "AvgCPU": 1.0, "Reason": "Test"}]
    mock_get_idle.return_value = mock_idle_data

    result = analyze_idle_instances(region="us-east-1")

    assert result == mock_idle_data
    mock_get_idle.assert_called_once_with(region="us-east-1")

@patch('analyzer.get_idle_ec2_instances')
def test_analyze_idle_instances_failure(mock_get_idle):
    """Tests that analyze_idle_instances returns None when fetcher fails."""
    mock_get_idle.return_value = None

    result = analyze_idle_instances(region="us-east-1")

    assert result is None
    mock_get_idle.assert_called_once_with(region="us-east-1")

@patch('analyzer.get_untagged_resources')  # Mock the data fetcher function
def test_analyze_untagged_resources_success(mock_get_untagged):
    """Tests that analyze_untagged_resources returns data from the fetcher."""
    mock_untagged_data = {"Instances": [{"ResourceId": "i-123", "MissingTags": ["Owner"]}], "Volumes": []}
    mock_get_untagged.return_value = mock_untagged_data

    result = analyze_untagged_resources(region="us-east-1")

    assert result == mock_untagged_data
    mock_get_untagged.assert_called_once_with(required_tags=None, region="us-east-1")  # Check default tags

@patch('analyzer.get_untagged_resources')
def test_analyze_untagged_resources_failure(mock_get_untagged):
    """Tests that analyze_untagged_resources returns None when fetcher fails."""
    mock_get_untagged.return_value = None

    result = analyze_untagged_resources(region="us-east-1")

    assert result is None
    mock_get_untagged.assert_called_once_with(required_tags=None, region="us-east-1")

@patch('analyzer.get_ebs_optimization_candidates') # Mock the data fetcher function
def test_analyze_ebs_optimization_success(mock_get_ebs):
    """Tests that analyze_ebs_optimization returns data from the fetcher."""
    mock_ebs_data = {"UnattachedVolumes": [{"ResourceId": "vol-123"}], "Gp2Volumes": []}
    mock_get_ebs.return_value = mock_ebs_data

    result = analyze_ebs_optimization(region="us-east-1")

    assert result == mock_ebs_data
    mock_get_ebs.assert_called_once_with(region="us-east-1")

@patch('analyzer.get_ebs_optimization_candidates')
def test_analyze_ebs_optimization_failure(mock_get_ebs):
    """Tests that analyze_ebs_optimization returns None when fetcher fails."""
    mock_get_ebs.return_value = None

    result = analyze_ebs_optimization(region="us-east-1")

    assert result is None
    mock_get_ebs.assert_called_once_with(region="us-east-1")

# --- Test analyze_cost_anomalies ---

@patch('analyzer.get_daily_cost_history')
def test_analyze_cost_anomalies_detected(mock_get_history):
    """Tests when a cost anomaly is detected."""
    # Mock data: last day's cost is > avg + 2.5 * std_dev
    mock_history = {
        '2024-01-01': 10.0, '2024-01-02': 11.0, '2024-01-03': 9.0,
        '2024-01-04': 10.5, '2024-01-05': 50.0  # Anomaly
    }
    mock_get_history.return_value = mock_history
    result = analyze_cost_anomalies(history_days=5, std_dev_threshold=2.5)

    assert result is not None
    assert result['is_anomaly'] == True
    assert result['latest_date'] == '2024-01-05'
    assert result['latest_cost'] == 50.0
    # Avg/StdDev based on first 4 days: (10 + 11 + 9 + 10.5) / 4 = 10.125, rounded to 10.12
    assert result['average_cost'] == 10.12
    # StdDev: sqrt(((10-10.125)^2 + (11-10.125)^2 + (9-10.125)^2 + (10.5-10.125)^2) / 4) = 0.7395, rounded to 0.74
    assert result['std_dev'] == pytest.approx(0.74)
    # Threshold: 10.12 + 2.5 * 0.74 = 10.12 + 1.85 = 11.97
    assert result['threshold'] == 11.97
    mock_get_history.assert_called_once_with(days=5)

@patch('analyzer.get_daily_cost_history')
def test_analyze_cost_anomalies_not_detected(mock_get_history):
    """Tests when no cost anomaly is detected."""
    # Mock data: last day's cost is NOT > avg + 2.5 * std_dev
    mock_history = {
        '2024-01-01': 10.0, '2024-01-02': 11.0, '2024-01-03': 9.0,
        '2024-01-04': 10.5, '2024-01-05': 11.5  # Not an anomaly
    }
    mock_get_history.return_value = mock_history
    result = analyze_cost_anomalies(history_days=5, std_dev_threshold=2.5)

    assert result is not None
    assert result['is_anomaly'] == False
    assert result['latest_date'] == '2024-01-05'
    assert result['latest_cost'] == 11.5
    # Avg/StdDev based on first 4 days: (10 + 11 + 9 + 10.5) / 4 = 10.125, rounded to 10.12
    assert result['average_cost'] == 10.12
    # StdDev: sqrt(((10-10.125)^2 + (11-10.125)^2 + (9-10.125)^2 + (10.5-10.125)^2) / 4) = 0.7395, rounded to 0.74
    assert result['std_dev'] == pytest.approx(0.74)
    # Threshold: 10.12 + 2.5 * 0.74 = 10.12 + 1.85 = 11.97
    assert result['threshold'] == 11.97
    mock_get_history.assert_called_once_with(days=5)

@patch('analyzer.get_daily_cost_history')
def test_analyze_cost_anomalies_insufficient_data(mock_get_history):
    """Tests behavior with insufficient historical data."""
    mock_get_history.return_value = {'2024-01-01': 10.0} # Only one day
    result = analyze_cost_anomalies(history_days=1)
    assert result is None
    mock_get_history.assert_called_once_with(days=1)

@patch('analyzer.get_daily_cost_history')
def test_analyze_cost_anomalies_fetch_failure(mock_get_history):
    """Tests behavior when history fetching fails."""
    mock_get_history.return_value = None
    result = analyze_cost_anomalies(history_days=30)
    assert result is None
    mock_get_history.assert_called_once_with(days=30)

# Add more tests for different scenarios and edge cases