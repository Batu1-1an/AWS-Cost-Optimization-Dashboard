# AWS Cost Optimization Dashboard - API Documentation

## Table of Contents
- [Overview](#overview)
- [Setup and Installation](#setup-and-installation)
- [Flask API Endpoints](#flask-api-endpoints)
- [Core Modules](#core-modules)
- [Frontend Components](#frontend-components)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Error Handling](#error-handling)

## Overview

The AWS Cost Optimization Dashboard is a Flask-based web application that provides insights into AWS cost optimization opportunities. It analyzes AWS resources to identify idle instances, untagged resources, EBS optimization candidates, and cost anomalies.

### Key Features
- **Cost Analysis**: Break down costs by AWS service
- **Idle Instance Detection**: Identify underutilized EC2 instances
- **Resource Tagging**: Find untagged EC2 instances and EBS volumes
- **EBS Optimization**: Identify unattached volumes and gp2 upgrade candidates
- **Cost Anomaly Detection**: Detect unusual cost spikes

## Setup and Installation

### Prerequisites
- Python 3.7+
- AWS credentials configured
- Required Python packages (see requirements.txt)

### Installation Steps

1. **Clone and setup the project:**
```bash
git clone <repository-url>
cd aws-cost-dashboard
pip install -r requirements.txt
```

2. **Configure environment variables:**
Create a `.env` file in the project root:
```env
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1
```

3. **Run the application:**
```bash
python app.py
```

The dashboard will be available at `http://localhost:5000`

## Flask API Endpoints

### Base URL
```
http://localhost:5000
```

### 1. Dashboard Home
**Endpoint:** `GET /`

**Description:** Renders the main dashboard page with all cost optimization widgets.

**Response:** HTML page with interactive charts and tables

**Example:**
```bash
curl http://localhost:5000/
```

### 2. Cost by Service
**Endpoint:** `GET /api/cost-by-service`

**Description:** Retrieves cost breakdown by AWS service for the last 30 days.

**Response Format:**
```json
{
  "Amazon Elastic Compute Cloud - Compute": 150.25,
  "Amazon Simple Storage Service": 45.80,
  "Amazon Relational Database Service": 75.30
}
```

**Example:**
```bash
curl http://localhost:5000/api/cost-by-service
```

**Error Response:**
```json
{
  "error": "Failed to retrieve cost data"
}
```

### 3. Idle Instances
**Endpoint:** `GET /api/idle-instances`

**Description:** Identifies potentially idle EC2 instances based on CPU utilization metrics.

**Response Format:**
```json
[
  {
    "InstanceId": "i-1234567890abcdef0",
    "Region": "us-east-1",
    "AvgCPU": 2.5,
    "MaxCPU": 8.2,
    "Reason": "Avg CPU (2.50%) < 5% and Max CPU (8.20%) < 10% over last 14 days"
  }
]
```

**Example:**
```bash
curl http://localhost:5000/api/idle-instances
```

### 4. Untagged Resources
**Endpoint:** `GET /api/untagged-resources`

**Description:** Finds EC2 instances and EBS volumes missing required tags.

**Response Format:**
```json
{
  "Instances": [
    {
      "ResourceId": "i-1234567890abcdef0",
      "ResourceType": "EC2 Instance",
      "Region": "us-east-1",
      "MissingTags": ["Project", "Owner"]
    }
  ],
  "Volumes": [
    {
      "ResourceId": "vol-1234567890abcdef0",
      "ResourceType": "EBS Volume",
      "Region": "us-east-1",
      "MissingTags": ["Project"]
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:5000/api/untagged-resources
```

### 5. EBS Optimization
**Endpoint:** `GET /api/ebs-optimization`

**Description:** Identifies EBS volumes that can be optimized (unattached volumes and gp2 upgrade candidates).

**Response Format:**
```json
{
  "UnattachedVolumes": [
    {
      "ResourceId": "vol-1234567890abcdef0",
      "ResourceType": "EBS Volume",
      "Region": "us-east-1",
      "SizeGiB": 100,
      "Reason": "Unattached (Available)"
    }
  ],
  "Gp2Volumes": [
    {
      "ResourceId": "vol-0987654321fedcba0",
      "ResourceType": "EBS Volume",
      "Region": "us-east-1",
      "SizeGiB": 50,
      "CurrentType": "gp2",
      "Reason": "Potential gp3 Upgrade Candidate"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:5000/api/ebs-optimization
```

### 6. Cost Anomalies
**Endpoint:** `GET /api/cost-anomalies`

**Description:** Detects cost anomalies by analyzing daily cost history using statistical methods.

**Response Format:**
```json
{
  "latest_date": "2024-01-15",
  "latest_cost": 250.75,
  "average_cost": 180.50,
  "std_dev": 25.30,
  "threshold": 243.75,
  "is_anomaly": true,
  "history_days": 60,
  "std_dev_threshold": 2.5
}
```

**Example:**
```bash
curl http://localhost:5000/api/cost-anomalies
```

## Core Modules

### 1. analyzer.py

The analyzer module provides high-level analysis functions that process data from the data fetcher.

#### Functions

##### `analyze_cost_data(days=30)`
Analyzes cost data for the specified number of days.

**Parameters:**
- `days` (int): Number of past days to analyze (default: 30)

**Returns:**
- `dict`: Cost breakdown by service, or `None` if fetching fails

**Example:**
```python
from analyzer import analyze_cost_data

# Analyze last 7 days of cost data
costs = analyze_cost_data(days=7)
if costs:
    for service, cost in costs.items():
        print(f"{service}: ${cost:.2f}")
```

##### `analyze_idle_instances(region=AWS_REGION)`
Identifies potentially idle EC2 instances based on CloudWatch metrics.

**Parameters:**
- `region` (str): AWS region to analyze (default: from AWS_REGION config)

**Returns:**
- `list`: List of idle instance dictionaries, or `None` if fetching fails

**Example:**
```python
from analyzer import analyze_idle_instances

# Find idle instances in us-west-2
idle_instances = analyze_idle_instances(region='us-west-2')
if idle_instances:
    print(f"Found {len(idle_instances)} idle instances")
```

##### `analyze_untagged_resources(required_tags=None, region=AWS_REGION)`
Finds resources missing required tags.

**Parameters:**
- `required_tags` (list, optional): List of required tag keys (default: ['Project', 'Owner'])
- `region` (str): AWS region to analyze

**Returns:**
- `dict`: Dictionary with 'Instances' and 'Volumes' lists, or `None` if fetching fails

**Example:**
```python
from analyzer import analyze_untagged_resources

# Find resources missing custom tags
untagged = analyze_untagged_resources(
    required_tags=['Environment', 'Team'],
    region='eu-west-1'
)
```

##### `analyze_ebs_optimization(region=AWS_REGION)`
Identifies EBS volumes that can be optimized.

**Parameters:**
- `region` (str): AWS region to analyze

**Returns:**
- `dict`: Dictionary with 'UnattachedVolumes' and 'Gp2Volumes' lists

**Example:**
```python
from analyzer import analyze_ebs_optimization

# Find EBS optimization opportunities
ebs_opts = analyze_ebs_optimization(region='ap-southeast-1')
if ebs_opts:
    print(f"Unattached volumes: {len(ebs_opts['UnattachedVolumes'])}")
    print(f"GP2 volumes: {len(ebs_opts['Gp2Volumes'])}")
```

##### `analyze_cost_anomalies(history_days=60, std_dev_threshold=2.5)`
Detects cost anomalies using statistical analysis.

**Parameters:**
- `history_days` (int): Days of historical data to analyze (default: 60)
- `std_dev_threshold` (float): Standard deviation threshold for anomaly detection (default: 2.5)

**Returns:**
- `dict`: Anomaly analysis results with cost statistics

**Example:**
```python
from analyzer import analyze_cost_anomalies

# Detect anomalies with custom parameters
anomaly_result = analyze_cost_anomalies(
    history_days=30,
    std_dev_threshold=2.0
)
if anomaly_result and anomaly_result['is_anomaly']:
    print(f"Cost anomaly detected on {anomaly_result['latest_date']}")
```

### 2. data_fetcher.py

The data fetcher module handles direct AWS API interactions to retrieve cost and resource data.

#### Constants

```python
# Idle instance detection parameters
IDLE_CHECK_PERIOD_DAYS = 14
IDLE_AVG_CPU_THRESHOLD = 5.0
IDLE_MAX_CPU_THRESHOLD = 10.0

# Required tags for compliance checking
REQUIRED_TAGS = ['Project', 'Owner']
```

#### Functions

##### `get_cost_by_service(days=30)`
Fetches cost data from AWS Cost Explorer grouped by service.

**Parameters:**
- `days` (int): Number of past days to fetch

**Returns:**
- `dict`: Service names mapped to costs, or `None` on error

**Example:**
```python
from data_fetcher import get_cost_by_service

# Get cost data for last 14 days
costs = get_cost_by_service(days=14)
```

##### `get_idle_ec2_instances(region=AWS_REGION)`
Identifies idle EC2 instances using CloudWatch CPU metrics.

**Parameters:**
- `region` (str): AWS region to check

**Returns:**
- `list`: List of idle instance information dictionaries

**Example:**
```python
from data_fetcher import get_idle_ec2_instances

# Check for idle instances in specific region
idle_instances = get_idle_ec2_instances(region='us-west-1')
```

##### `get_untagged_resources(required_tags=None, region=None)`
Finds EC2 instances and EBS volumes missing required tags.

**Parameters:**
- `required_tags` (list, optional): Required tag keys
- `region` (str): AWS region to check

**Returns:**
- `dict`: Contains 'Instances' and 'Volumes' lists

**Example:**
```python
from data_fetcher import get_untagged_resources

# Find resources missing specific tags
untagged = get_untagged_resources(
    required_tags=['Environment', 'CostCenter'],
    region='eu-central-1'
)
```

##### `get_daily_cost_history(days=60)`
Retrieves daily cost history for anomaly detection.

**Parameters:**
- `days` (int): Number of days of history to fetch

**Returns:**
- `dict`: Date strings mapped to daily costs

**Example:**
```python
from data_fetcher import get_daily_cost_history

# Get 30 days of cost history
daily_costs = get_daily_cost_history(days=30)
for date, cost in daily_costs.items():
    print(f"{date}: ${cost:.2f}")
```

##### `get_ebs_optimization_candidates(region=None)`
Finds EBS volumes that are candidates for optimization.

**Parameters:**
- `region` (str, optional): AWS region to check

**Returns:**
- `dict`: Contains 'UnattachedVolumes' and 'Gp2Volumes' lists

**Example:**
```python
from data_fetcher import get_ebs_optimization_candidates

# Find EBS optimization opportunities
candidates = get_ebs_optimization_candidates(region='ca-central-1')
```

### 3. aws_connector.py

The AWS connector module manages AWS authentication and client creation.

#### Global Variables

```python
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
```

#### Functions

##### `get_aws_session()`
Creates or returns the existing AWS session.

**Returns:**
- `boto3.Session`: AWS session object, or `None` if authentication fails

**Example:**
```python
from aws_connector import get_aws_session

session = get_aws_session()
if session:
    print(f"Session created for region: {session.region_name}")
```

##### `get_client(service_name, region_name=None)`
Creates AWS service clients with proper authentication.

**Parameters:**
- `service_name` (str): AWS service name ('ec2', 'ce', 'cloudwatch', etc.)
- `region_name` (str, optional): Override default region

**Returns:**
- `boto3.client`: AWS service client, or `None` if creation fails

**Example:**
```python
from aws_connector import get_client

# Get clients for different services
ec2_client = get_client('ec2', region_name='us-west-2')
ce_client = get_client('ce')  # Uses default region
cloudwatch_client = get_client('cloudwatch')

if ec2_client:
    # Use the client for EC2 operations
    response = ec2_client.describe_instances()
```

### 4. utils.py

Utility functions for common operations.

##### `_check_missing_tags(resource_tags_list, required_tags_set)`
Helper function to identify missing tags from AWS resource tag lists.

**Parameters:**
- `resource_tags_list` (list): List of tag dictionaries from AWS API
- `required_tags_set` (set): Set of required tag keys

**Returns:**
- `list`: List of missing tag keys

**Example:**
```python
from utils import _check_missing_tags

# Example AWS resource tags
resource_tags = [
    {'Key': 'Name', 'Value': 'web-server'},
    {'Key': 'Environment', 'Value': 'production'}
]
required_tags = {'Name', 'Environment', 'Owner', 'Project'}

missing = _check_missing_tags(resource_tags, required_tags)
print(f"Missing tags: {missing}")  # Output: ['Owner', 'Project']
```

## Frontend Components

### HTML Template (templates/index.html)

The main dashboard template provides a responsive layout with:
- Cost breakdown pie chart
- Idle instances table
- Untagged resources table
- EBS optimization candidates table
- Cost anomaly detection panel

### JavaScript Functions (static/script.js)

#### `fetchCostData()`
Fetches and renders the cost breakdown chart.

```javascript
// Automatically called on page load
// Renders Plotly.js pie chart with cost data
```

#### `fetchIdleInstances()`
Populates the idle instances table with data from the API.

```javascript
// Creates table rows with instance details
// Handles error states gracefully
```

#### `fetchUntaggedResources()`
Loads untagged resources data into the dashboard table.

```javascript
// Combines instances and volumes into unified table
// Shows missing tags for each resource
```

#### `fetchEbsOptimizationData()`
Displays EBS optimization opportunities.

```javascript
// Shows unattached volumes and gp2 upgrade candidates
// Provides actionable optimization insights
```

#### `fetchCostAnomalyData()`
Presents cost anomaly detection results.

```javascript
// Highlights unusual cost patterns
// Shows statistical thresholds and analysis
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AWS_ACCESS_KEY_ID` | AWS access key | None | Yes |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | None | Yes |
| `AWS_REGION` | Default AWS region | us-east-1 | No |

### Configuration Constants

#### Idle Instance Detection
```python
IDLE_CHECK_PERIOD_DAYS = 14      # CloudWatch metrics period
IDLE_AVG_CPU_THRESHOLD = 5.0     # Average CPU threshold (%)
IDLE_MAX_CPU_THRESHOLD = 10.0    # Maximum CPU threshold (%)
```

#### Required Tags
```python
REQUIRED_TAGS = ['Project', 'Owner']  # Customize as needed
```

#### Cost Anomaly Detection
```python
# Default parameters in analyze_cost_anomalies()
history_days = 60           # Days of historical data
std_dev_threshold = 2.5     # Standard deviation multiplier
```

## Usage Examples

### Complete Setup Example

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cat > .env << EOF
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
EOF

# 3. Run the application
python app.py
```

### Programmatic Usage

```python
# Example: Complete cost analysis workflow
from analyzer import (
    analyze_cost_data, 
    analyze_idle_instances, 
    analyze_cost_anomalies
)

# Get cost breakdown
print("=== Cost Analysis ===")
costs = analyze_cost_data(days=30)
if costs:
    total_cost = sum(costs.values())
    print(f"Total 30-day cost: ${total_cost:.2f}")
    
    # Show top 3 services by cost
    top_services = sorted(costs.items(), key=lambda x: x[1], reverse=True)[:3]
    for service, cost in top_services:
        print(f"  {service}: ${cost:.2f}")

# Find optimization opportunities
print("\n=== Optimization Opportunities ===")
idle_instances = analyze_idle_instances()
if idle_instances:
    print(f"Found {len(idle_instances)} idle instances")
    for instance in idle_instances[:3]:  # Show first 3
        print(f"  {instance['InstanceId']}: {instance['AvgCPU']:.1f}% avg CPU")

# Check for cost anomalies
print("\n=== Cost Anomaly Detection ===")
anomaly_result = analyze_cost_anomalies()
if anomaly_result:
    if anomaly_result['is_anomaly']:
        print(f"⚠️  Cost anomaly detected!")
        print(f"   Latest cost: ${anomaly_result['latest_cost']:.2f}")
        print(f"   Expected: ${anomaly_result['threshold']:.2f}")
    else:
        print("✅ No cost anomalies detected")
```

### Custom Region Analysis

```python
# Analyze multiple regions
from analyzer import analyze_idle_instances, analyze_untagged_resources

regions = ['us-east-1', 'us-west-2', 'eu-west-1']

for region in regions:
    print(f"\n=== Analysis for {region} ===")
    
    # Check idle instances
    idle = analyze_idle_instances(region=region)
    if idle:
        print(f"Idle instances: {len(idle)}")
    
    # Check untagged resources
    untagged = analyze_untagged_resources(region=region)
    if untagged:
        total_untagged = len(untagged['Instances']) + len(untagged['Volumes'])
        print(f"Untagged resources: {total_untagged}")
```

### API Integration Example

```python
import requests
import json

base_url = "http://localhost:5000"

# Get all dashboard data
def get_dashboard_data():
    endpoints = [
        '/api/cost-by-service',
        '/api/idle-instances', 
        '/api/untagged-resources',
        '/api/ebs-optimization',
        '/api/cost-anomalies'
    ]
    
    dashboard_data = {}
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            response.raise_for_status()
            dashboard_data[endpoint] = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {endpoint}: {e}")
            dashboard_data[endpoint] = None
    
    return dashboard_data

# Use the data
data = get_dashboard_data()
print(json.dumps(data, indent=2))
```

## Error Handling

### Common Error Scenarios

1. **AWS Authentication Failures**
   - Missing or invalid credentials
   - Insufficient IAM permissions
   - Region access issues

2. **API Rate Limiting**
   - CloudWatch API throttling
   - Cost Explorer quota limits

3. **Data Availability**
   - No CloudWatch metrics for new instances
   - Insufficient cost history for anomaly detection

### Error Response Format

```json
{
  "error": "Descriptive error message"
}
```

### Recommended IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ec2:DescribeInstances",
        "ec2:DescribeVolumes",
        "cloudwatch:GetMetricStatistics"
      ],
      "Resource": "*"
    }
  ]
}
```

### Debugging Tips

1. **Enable Debug Logging**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Test Individual Components**
   ```bash
   # Test data fetcher directly
   python data_fetcher.py
   
   # Test analyzer functions
   python analyzer.py
   
   # Test AWS connectivity
   python aws_connector.py
   ```

3. **Validate Environment**
   ```python
   import os
   print("AWS_ACCESS_KEY_ID:", "✓" if os.getenv("AWS_ACCESS_KEY_ID") else "✗")
   print("AWS_SECRET_ACCESS_KEY:", "✓" if os.getenv("AWS_SECRET_ACCESS_KEY") else "✗")
   print("AWS_REGION:", os.getenv("AWS_REGION", "us-east-1"))
   ```

This comprehensive documentation covers all public APIs, functions, and components of the AWS Cost Optimization Dashboard. For additional support or customization requests, please refer to the source code comments and logging output.