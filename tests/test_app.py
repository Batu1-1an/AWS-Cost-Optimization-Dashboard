import pytest
from unittest.mock import patch
import json
from app import app # Import the Flask app instance

@pytest.fixture
def client():
    """Create a Flask test client fixture."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# --- Test /api/cost-by-service ---

@patch('app.analyze_cost_data') # Patch the analyzer function used by the route
def test_get_cost_by_service_success(mock_analyze, client):
    """Tests successful response from /api/cost-by-service."""
    mock_data = {"EC2": 100.0, "S3": 50.0}
    mock_analyze.return_value = mock_data

    response = client.get('/api/cost-by-service')

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert json.loads(response.data) == mock_data
    mock_analyze.assert_called_once()

@patch('app.analyze_cost_data')
def test_get_cost_by_service_failure(mock_analyze, client):
    """Tests error response when analyzer fails for cost data."""
    mock_analyze.return_value = None # Simulate analyzer failure

    response = client.get('/api/cost-by-service')

    assert response.status_code == 500
    assert response.content_type == 'application/json'
    assert "error" in json.loads(response.data)
    mock_analyze.assert_called_once()

# --- Test /api/idle-instances ---

@patch('app.analyze_idle_instances')
def test_get_idle_instances_success(mock_analyze, client):
    """Tests successful response from /api/idle-instances."""
    mock_data = [{"InstanceId": "i-123", "AvgCPU": 1.0}]
    mock_analyze.return_value = mock_data

    response = client.get('/api/idle-instances')

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert json.loads(response.data) == mock_data
    mock_analyze.assert_called_once()

@patch('app.analyze_idle_instances')
def test_get_idle_instances_failure(mock_analyze, client):
    """Tests error response when analyzer fails for idle instances."""
    mock_analyze.return_value = None

    response = client.get('/api/idle-instances')

    assert response.status_code == 500
    assert response.content_type == 'application/json'
    assert "error" in json.loads(response.data)
    mock_analyze.assert_called_once()

# --- Test /api/untagged-resources ---

@patch('app.analyze_untagged_resources')
def test_get_untagged_resources_success(mock_analyze, client):
    """Tests successful response from /api/untagged-resources."""
    mock_data = {"Instances": [{"ResourceId": "i-456", "MissingTags": ["Owner"]}], "Volumes": []}
    mock_analyze.return_value = mock_data

    response = client.get('/api/untagged-resources')

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert json.loads(response.data) == mock_data
    mock_analyze.assert_called_once() # Add assertion for call

@patch('app.analyze_untagged_resources')
def test_get_untagged_resources_failure(mock_analyze, client):
    """Tests error response when analyzer fails for untagged resources."""
    mock_analyze.return_value = None

    response = client.get('/api/untagged-resources')

    assert response.status_code == 500
    assert response.content_type == 'application/json'
    assert "error" in json.loads(response.data)
    mock_analyze.assert_called_once() # Add assertion for call

# --- Test /api/ebs-optimization ---

@patch('app.analyze_ebs_optimization')
def test_get_ebs_optimization_success(mock_analyze, client):
    """Tests successful response from /api/ebs-optimization."""
    mock_data = {"UnattachedVolumes": [{"ResourceId": "vol-123"}], "Gp2Volumes": []}
    mock_analyze.return_value = mock_data

    response = client.get('/api/ebs-optimization')

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert json.loads(response.data) == mock_data
    mock_analyze.assert_called_once()

@patch('app.analyze_ebs_optimization')
def test_get_ebs_optimization_failure(mock_analyze, client):
    """Tests error response when analyzer fails for EBS optimization."""
    mock_analyze.return_value = None

    response = client.get('/api/ebs-optimization')

    assert response.status_code == 500
    assert response.content_type == 'application/json'
    assert "error" in json.loads(response.data)
    mock_analyze.assert_called_once()

# --- Test /api/cost-anomalies ---

@patch('app.analyze_cost_anomalies')
def test_get_cost_anomalies_success(mock_analyze, client):
    """Tests successful response from /api/cost-anomalies."""
    mock_data = {'latest_date': '2024-01-05', 'latest_cost': 150.0, 'average_cost': 100.0, 'std_dev': 20.0, 'threshold': 150.0, 'is_anomaly': True, 'history_days': 30, 'std_dev_threshold': 2.5}
    mock_analyze.return_value = mock_data

    response = client.get('/api/cost-anomalies')

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert json.loads(response.data) == mock_data
    mock_analyze.assert_called_once()

@patch('app.analyze_cost_anomalies')
def test_get_cost_anomalies_failure(mock_analyze, client):
    """Tests error response when analyzer fails for cost anomalies."""
    mock_analyze.return_value = None

    response = client.get('/api/cost-anomalies')

    assert response.status_code == 500
    assert response.content_type == 'application/json'
    assert "error" in json.loads(response.data)
    mock_analyze.assert_called_once()

# --- Test /api/cost-anomalies ---

@patch('app.analyze_cost_anomalies')
def test_get_cost_anomalies_success(mock_analyze, client):
    """Tests successful response from /api/cost-anomalies."""
    mock_data = {'latest_date': '2024-01-10', 'latest_cost': 150.5, 'is_anomaly': True}
    mock_analyze.return_value = mock_data

    response = client.get('/api/cost-anomalies')

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert json.loads(response.data) == mock_data
    mock_analyze.assert_called_once()

@patch('app.analyze_cost_anomalies')
def test_get_cost_anomalies_failure(mock_analyze, client):
    """Tests error response when analyzer fails for cost anomalies."""
    mock_analyze.return_value = None

    response = client.get('/api/cost-anomalies')

    assert response.status_code == 500
    assert response.content_type == 'application/json'
    assert "error" in json.loads(response.data)
    mock_analyze.assert_called_once()
# --- Test / route ---

@patch('app.render_template') # Mock render_template to avoid actual rendering
def test_index_route(mock_render, client):
    """Tests that the index route returns 200 OK."""
    mock_render.return_value = "OK" # Return simple string instead of rendered template
    response = client.get('/')
    assert response.status_code == 200
    mock_render.assert_called_once_with('index.html', title='AWS Cost Dashboard')