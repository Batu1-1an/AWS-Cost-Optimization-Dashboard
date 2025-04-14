import pytest
from unittest.mock import patch
from analyzer import analyze_cost_data, analyze_idle_instances

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

# Add more tests for different scenarios and edge cases