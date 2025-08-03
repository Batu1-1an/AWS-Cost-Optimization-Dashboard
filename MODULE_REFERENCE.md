# Module Reference Documentation

## analyzer.py - Cost Analysis Engine

### Overview
The `analyzer.py` module serves as the high-level analysis layer, providing intelligent processing of raw AWS data. It implements business logic for cost optimization recommendations and trend analysis.

### Module Structure
```python
analyzer.py
├── analyze_cost_data()          # Cost trend analysis
├── analyze_idle_instances()     # EC2 utilization analysis  
├── analyze_untagged_resources() # Compliance analysis
├── analyze_ebs_optimization()   # Storage optimization
└── analyze_cost_anomalies()     # Statistical anomaly detection
```

### Detailed Function Reference

#### `analyze_cost_data(days=30)`

**Purpose**: Analyzes AWS cost patterns and provides service-level breakdown with trend insights.

**Algorithm**:
1. Fetches cost data from Cost Explorer
2. Aggregates costs by service
3. Filters out zero-cost services
4. Rounds values for presentation

**Advanced Usage**:
```python
from analyzer import analyze_cost_data
import matplotlib.pyplot as plt

# Multi-period analysis
periods = [7, 14, 30, 60]
cost_trends = {}

for period in periods:
    costs = analyze_cost_data(days=period)
    if costs:
        cost_trends[f"{period}_days"] = {
            'total': sum(costs.values()),
            'services': len(costs),
            'top_service': max(costs.items(), key=lambda x: x[1])
        }

# Calculate growth rates
if cost_trends.get('30_days') and cost_trends.get('60_days'):
    monthly_growth = (
        cost_trends['30_days']['total'] / 
        (cost_trends['60_days']['total'] / 2) - 1
    ) * 100
    print(f"Monthly cost growth: {monthly_growth:.1f}%")
```

**Integration with Other Modules**:
```python
# Combined with anomaly detection
from analyzer import analyze_cost_data, analyze_cost_anomalies

costs = analyze_cost_data(days=30)
anomalies = analyze_cost_anomalies(history_days=60)

if costs and anomalies:
    if anomalies['is_anomaly']:
        print(f"Alert: Cost spike detected!")
        print(f"Current total: ${sum(costs.values()):.2f}")
        print(f"Expected: ${anomalies['threshold']:.2f}")
```

#### `analyze_idle_instances(region=AWS_REGION)`

**Purpose**: Identifies underutilized EC2 instances using CloudWatch metrics analysis.

**Detection Criteria**:
- Average CPU < 5% over 14-day period
- Maximum CPU < 10% over 14-day period
- Instance must be in 'running' state

**Advanced Configuration**:
```python
# Custom thresholds (modify in data_fetcher.py)
import data_fetcher

# Temporarily override constants
original_avg_threshold = data_fetcher.IDLE_AVG_CPU_THRESHOLD
original_max_threshold = data_fetcher.IDLE_MAX_CPU_THRESHOLD

data_fetcher.IDLE_AVG_CPU_THRESHOLD = 2.0  # More aggressive
data_fetcher.IDLE_MAX_CPU_THRESHOLD = 5.0

try:
    idle_instances = analyze_idle_instances()
    # Process results...
finally:
    # Restore original values
    data_fetcher.IDLE_AVG_CPU_THRESHOLD = original_avg_threshold
    data_fetcher.IDLE_MAX_CPU_THRESHOLD = original_max_threshold
```

**Multi-Region Analysis**:
```python
from analyzer import analyze_idle_instances
from aws_regions import AWS_REGIONS

idle_summary = {}
total_idle = 0

for region in AWS_REGIONS:
    try:
        idle_instances = analyze_idle_instances(region=region)
        if idle_instances:
            idle_summary[region] = {
                'count': len(idle_instances),
                'instances': idle_instances
            }
            total_idle += len(idle_instances)
        print(f"✓ {region}: {len(idle_instances) if idle_instances else 0} idle")
    except Exception as e:
        print(f"✗ {region}: Error - {e}")

print(f"\nTotal idle instances across all regions: {total_idle}")

# Identify worst regions
if idle_summary:
    worst_regions = sorted(
        idle_summary.items(), 
        key=lambda x: x[1]['count'], 
        reverse=True
    )[:3]
    
    print("\nTop 3 regions with most idle instances:")
    for region, data in worst_regions:
        print(f"  {region}: {data['count']} instances")
```

#### `analyze_untagged_resources(required_tags=None, region=AWS_REGION)`

**Purpose**: Ensures compliance with tagging policies across EC2 instances and EBS volumes.

**Default Tags**: `['Project', 'Owner']`

**Compliance Reporting**:
```python
from analyzer import analyze_untagged_resources

# Custom compliance check
compliance_tags = ['Environment', 'CostCenter', 'Owner', 'Project']
regions_to_check = ['us-east-1', 'us-west-2', 'eu-west-1']

compliance_report = {
    'total_resources': 0,
    'compliant_resources': 0,
    'non_compliant': [],
    'by_region': {}
}

for region in regions_to_check:
    untagged = analyze_untagged_resources(
        required_tags=compliance_tags,
        region=region
    )
    
    if untagged:
        region_total = len(untagged['Instances']) + len(untagged['Volumes'])
        compliance_report['total_resources'] += region_total
        compliance_report['non_compliant'].extend(untagged['Instances'])
        compliance_report['non_compliant'].extend(untagged['Volumes'])
        
        compliance_report['by_region'][region] = {
            'instances': len(untagged['Instances']),
            'volumes': len(untagged['Volumes']),
            'total': region_total
        }

# Calculate compliance percentage
if compliance_report['total_resources'] > 0:
    compliance_rate = (
        1 - len(compliance_report['non_compliant']) / 
        compliance_report['total_resources']
    ) * 100
    print(f"Overall compliance rate: {compliance_rate:.1f}%")
```

#### `analyze_ebs_optimization(region=AWS_REGION)`

**Purpose**: Identifies cost optimization opportunities for EBS volumes.

**Optimization Categories**:
1. **Unattached Volumes**: Available for deletion
2. **GP2 Volumes**: Candidates for GP3 migration

**Cost Impact Analysis**:
```python
from analyzer import analyze_ebs_optimization

# EBS optimization with cost calculation
def calculate_ebs_savings(region):
    candidates = analyze_ebs_optimization(region=region)
    if not candidates:
        return None
    
    savings_estimate = {
        'unattached_savings': 0,
        'gp3_upgrade_savings': 0,
        'total_savings': 0
    }
    
    # Estimate unattached volume savings (full cost elimination)
    # GP2 pricing: ~$0.10 per GB per month
    for volume in candidates['UnattachedVolumes']:
        monthly_cost = volume['SizeGiB'] * 0.10
        savings_estimate['unattached_savings'] += monthly_cost
    
    # Estimate GP3 upgrade savings (~20% cost reduction)
    for volume in candidates['Gp2Volumes']:
        current_cost = volume['SizeGiB'] * 0.10
        gp3_cost = volume['SizeGiB'] * 0.08
        savings_estimate['gp3_upgrade_savings'] += (current_cost - gp3_cost)
    
    savings_estimate['total_savings'] = (
        savings_estimate['unattached_savings'] + 
        savings_estimate['gp3_upgrade_savings']
    )
    
    return savings_estimate

# Multi-region savings analysis
total_savings = 0
for region in ['us-east-1', 'us-west-2']:
    savings = calculate_ebs_savings(region)
    if savings:
        print(f"{region} potential monthly savings: ${savings['total_savings']:.2f}")
        total_savings += savings['total_savings']

print(f"Total potential monthly savings: ${total_savings:.2f}")
print(f"Annual savings potential: ${total_savings * 12:.2f}")
```

#### `analyze_cost_anomalies(history_days=60, std_dev_threshold=2.5)`

**Purpose**: Detects unusual cost patterns using statistical analysis.

**Algorithm**:
1. Fetch daily cost history
2. Calculate baseline statistics (mean, std dev)
3. Compare latest cost against threshold
4. Flag anomalies exceeding threshold

**Advanced Anomaly Detection**:
```python
from analyzer import analyze_cost_anomalies
import numpy as np
from datetime import datetime, timedelta

def advanced_anomaly_analysis():
    # Multiple detection methods
    results = {}
    
    # Standard deviation method (conservative)
    conservative = analyze_cost_anomalies(
        history_days=90, 
        std_dev_threshold=3.0
    )
    
    # Aggressive detection
    aggressive = analyze_cost_anomalies(
        history_days=30, 
        std_dev_threshold=2.0
    )
    
    # Store results
    results['conservative'] = conservative
    results['aggressive'] = aggressive
    
    # Trend analysis
    if conservative and aggressive:
        # Calculate trend direction
        short_term_avg = aggressive['average_cost']
        long_term_avg = conservative['average_cost']
        
        trend = "INCREASING" if short_term_avg > long_term_avg else "DECREASING"
        trend_magnitude = abs(short_term_avg - long_term_avg) / long_term_avg * 100
        
        results['trend'] = {
            'direction': trend,
            'magnitude': trend_magnitude
        }
        
        # Risk assessment
        risk_factors = []
        if conservative['is_anomaly']:
            risk_factors.append("Sustained high cost pattern")
        if aggressive['is_anomaly']:
            risk_factors.append("Recent cost spike")
        if trend_magnitude > 10:
            risk_factors.append(f"Significant {trend.lower()} trend")
            
        results['risk_assessment'] = {
            'level': 'HIGH' if len(risk_factors) >= 2 else 'MEDIUM' if risk_factors else 'LOW',
            'factors': risk_factors
        }
    
    return results

# Usage
analysis = advanced_anomaly_analysis()
if analysis.get('risk_assessment'):
    risk = analysis['risk_assessment']
    print(f"Risk Level: {risk['level']}")
    for factor in risk['factors']:
        print(f"  - {factor}")
```

### Error Handling and Resilience

```python
from analyzer import *
import logging

def robust_analysis_pipeline(region='us-east-1'):
    """
    Demonstrates robust error handling for analyzer functions
    """
    results = {
        'costs': None,
        'idle_instances': None,
        'untagged_resources': None,
        'ebs_optimization': None,
        'cost_anomalies': None,
        'errors': []
    }
    
    # Cost analysis with retry logic
    for attempt in range(3):
        try:
            results['costs'] = analyze_cost_data(days=30)
            break
        except Exception as e:
            logging.warning(f"Cost analysis attempt {attempt + 1} failed: {e}")
            if attempt == 2:
                results['errors'].append(f"Cost analysis failed: {e}")
    
    # Idle instance analysis
    try:
        results['idle_instances'] = analyze_idle_instances(region=region)
    except Exception as e:
        results['errors'].append(f"Idle instance analysis failed: {e}")
    
    # Continue with other analyses...
    try:
        results['untagged_resources'] = analyze_untagged_resources(region=region)
    except Exception as e:
        results['errors'].append(f"Untagged resource analysis failed: {e}")
    
    try:
        results['ebs_optimization'] = analyze_ebs_optimization(region=region)
    except Exception as e:
        results['errors'].append(f"EBS optimization analysis failed: {e}")
    
    try:
        results['cost_anomalies'] = analyze_cost_anomalies()
    except Exception as e:
        results['errors'].append(f"Cost anomaly analysis failed: {e}")
    
    # Generate summary
    successful_analyses = sum(1 for k, v in results.items() 
                            if k != 'errors' and v is not None)
    
    print(f"Analysis completed: {successful_analyses}/5 successful")
    if results['errors']:
        print("Errors encountered:")
        for error in results['errors']:
            print(f"  - {error}")
    
    return results
```

### Performance Optimization

```python
import concurrent.futures
import time

def parallel_region_analysis(regions=None):
    """
    Analyze multiple regions in parallel for better performance
    """
    if regions is None:
        from aws_regions import AWS_REGIONS
        regions = AWS_REGIONS[:5]  # Limit to first 5 regions
    
    def analyze_region(region):
        start_time = time.time()
        try:
            # Run all analyses for this region
            idle = analyze_idle_instances(region=region)
            untagged = analyze_untagged_resources(region=region)
            ebs = analyze_ebs_optimization(region=region)
            
            execution_time = time.time() - start_time
            
            return {
                'region': region,
                'idle_instances': len(idle) if idle else 0,
                'untagged_instances': len(untagged['Instances']) if untagged else 0,
                'untagged_volumes': len(untagged['Volumes']) if untagged else 0,
                'unattached_volumes': len(ebs['UnattachedVolumes']) if ebs else 0,
                'gp2_volumes': len(ebs['Gp2Volumes']) if ebs else 0,
                'execution_time': execution_time,
                'success': True
            }
        except Exception as e:
            return {
                'region': region,
                'error': str(e),
                'success': False,
                'execution_time': time.time() - start_time
            }
    
    # Execute in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_region = {
            executor.submit(analyze_region, region): region 
            for region in regions
        }
        
        results = []
        for future in concurrent.futures.as_completed(future_to_region):
            result = future.result()
            results.append(result)
    
    # Sort by region name
    results.sort(key=lambda x: x['region'])
    
    # Print summary
    successful_regions = [r for r in results if r.get('success')]
    failed_regions = [r for r in results if not r.get('success')]
    
    print(f"Parallel analysis completed:")
    print(f"  Successful: {len(successful_regions)} regions")
    print(f"  Failed: {len(failed_regions)} regions")
    print(f"  Average execution time: {sum(r['execution_time'] for r in results) / len(results):.2f}s")
    
    if successful_regions:
        print(f"\nRegion Summary:")
        for result in successful_regions:
            print(f"  {result['region']}: "
                  f"{result['idle_instances']} idle, "
                  f"{result['untagged_instances']} untagged instances, "
                  f"{result['unattached_volumes']} unattached volumes")
    
    return results
```

---

## data_fetcher.py - AWS Data Integration Layer

### Overview
The `data_fetcher.py` module handles direct interactions with AWS APIs, implementing efficient data retrieval with error handling and rate limiting considerations.

### Architecture
```
data_fetcher.py
├── AWS Cost Explorer Integration
│   ├── get_cost_by_service()
│   └── get_daily_cost_history()
├── EC2 Resource Management
│   ├── get_idle_ec2_instances()
│   └── get_untagged_resources()
├── EBS Storage Analysis
│   └── get_ebs_optimization_candidates()
└── CloudWatch Metrics Integration
```

### Configuration Constants

```python
# Configurable thresholds for different use cases
THRESHOLDS = {
    'conservative': {
        'IDLE_AVG_CPU_THRESHOLD': 10.0,
        'IDLE_MAX_CPU_THRESHOLD': 20.0,
        'IDLE_CHECK_PERIOD_DAYS': 30
    },
    'aggressive': {
        'IDLE_AVG_CPU_THRESHOLD': 2.0,
        'IDLE_MAX_CPU_THRESHOLD': 5.0,
        'IDLE_CHECK_PERIOD_DAYS': 7
    },
    'standard': {
        'IDLE_AVG_CPU_THRESHOLD': 5.0,
        'IDLE_MAX_CPU_THRESHOLD': 10.0,
        'IDLE_CHECK_PERIOD_DAYS': 14
    }
}
```

### Detailed Function Reference

#### `get_cost_by_service(days=30)`

**Implementation Details**:
- Uses AWS Cost Explorer `get_cost_and_usage` API
- Groups by SERVICE dimension
- Filters zero-cost services automatically
- Handles pagination for large datasets

**Extended Usage**:
```python
from data_fetcher import get_cost_by_service
from datetime import datetime, timedelta

# Custom date range analysis
def get_cost_comparison(current_days=30, previous_days=30):
    """Compare current period vs previous period costs"""
    
    # Current period
    current_costs = get_cost_by_service(days=current_days)
    
    # For previous period, we need custom implementation
    # This is a simplified example
    ce_client = get_client('ce')
    if not ce_client or not current_costs:
        return None
    
    end_date = datetime.now() - timedelta(days=current_days)
    start_date = end_date - timedelta(days=previous_days)
    
    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        previous_costs = {}
        for result in response.get('ResultsByTime', []):
            for group in result.get('Groups', []):
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                if cost > 0:
                    previous_costs[service] = previous_costs.get(service, 0) + cost
        
        # Calculate changes
        comparison = {}
        all_services = set(current_costs.keys()) | set(previous_costs.keys())
        
        for service in all_services:
            current = current_costs.get(service, 0)
            previous = previous_costs.get(service, 0)
            
            if previous > 0:
                change_pct = ((current - previous) / previous) * 100
            else:
                change_pct = float('inf') if current > 0 else 0
            
            comparison[service] = {
                'current': current,
                'previous': previous,
                'change_amount': current - previous,
                'change_percent': change_pct
            }
        
        return comparison
        
    except Exception as e:
        logging.error(f"Error in cost comparison: {e}")
        return None

# Usage
comparison = get_cost_comparison()
if comparison:
    print("Cost Changes by Service:")
    for service, data in sorted(comparison.items(), 
                               key=lambda x: abs(x[1]['change_amount']), 
                               reverse=True)[:10]:
        if abs(data['change_amount']) > 1:  # Only show significant changes
            print(f"  {service}: ${data['change_amount']:+.2f} "
                  f"({data['change_percent']:+.1f}%)")
```

#### `get_idle_ec2_instances(region=AWS_REGION)`

**CloudWatch Integration**:
- Retrieves CPU utilization metrics over configurable period
- Uses pandas for statistical analysis
- Handles missing metrics gracefully

**Custom Metrics Analysis**:
```python
from data_fetcher import get_client
import pandas as pd
from datetime import datetime, timedelta

def get_comprehensive_instance_metrics(instance_id, region, days=14):
    """
    Get comprehensive metrics for detailed analysis
    """
    cw_client = get_client('cloudwatch', region_name=region)
    if not cw_client:
        return None
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    
    metrics_to_fetch = [
        'CPUUtilization',
        'NetworkIn',
        'NetworkOut',
        'DiskReadOps',
        'DiskWriteOps'
    ]
    
    instance_metrics = {}
    
    for metric_name in metrics_to_fetch:
        try:
            response = cw_client.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName=metric_name,
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour intervals
                Statistics=['Average', 'Maximum'],
                Unit='Percent' if 'CPU' in metric_name else 'Count'
            )
            
            if response.get('Datapoints'):
                df = pd.DataFrame(response['Datapoints'])
                instance_metrics[metric_name] = {
                    'avg_value': df['Average'].mean(),
                    'max_value': df['Maximum'].max(),
                    'data_points': len(df),
                    'recent_trend': df['Average'].tail(24).mean()  # Last 24 hours
                }
        except Exception as e:
            logging.warning(f"Failed to get {metric_name} for {instance_id}: {e}")
    
    return instance_metrics

def advanced_idle_detection(region=AWS_REGION):
    """
    Advanced idle detection using multiple metrics
    """
    ec2_client = get_client('ec2', region_name=region)
    if not ec2_client:
        return None
    
    idle_candidates = []
    
    try:
        paginator = ec2_client.get_paginator('describe_instances')
        for page in paginator.paginate(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        ):
            for reservation in page.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    instance_id = instance['InstanceId']
                    instance_type = instance['InstanceType']
                    
                    # Get comprehensive metrics
                    metrics = get_comprehensive_instance_metrics(instance_id, region)
                    
                    if metrics and 'CPUUtilization' in metrics:
                        cpu_data = metrics['CPUUtilization']
                        
                        # Multi-criteria evaluation
                        is_idle = (
                            cpu_data['avg_value'] < 5.0 and
                            cpu_data['max_value'] < 15.0 and
                            cpu_data['data_points'] >= 24  # At least 24 hours of data
                        )
                        
                        # Additional checks if available
                        if 'NetworkIn' in metrics and 'NetworkOut' in metrics:
                            network_activity = (
                                metrics['NetworkIn']['avg_value'] + 
                                metrics['NetworkOut']['avg_value']
                            )
                            # Very low network activity adds to idle confidence
                            if network_activity < 1000:  # Less than 1KB/hour average
                                is_idle = is_idle and True
                        
                        if is_idle:
                            idle_candidates.append({
                                'InstanceId': instance_id,
                                'InstanceType': instance_type,
                                'Region': region,
                                'Metrics': metrics,
                                'ConfidenceScore': calculate_idle_confidence(metrics)
                            })
    
    except Exception as e:
        logging.error(f"Error in advanced idle detection: {e}")
        return None
    
    return idle_candidates

def calculate_idle_confidence(metrics):
    """Calculate confidence score for idle detection"""
    score = 0
    
    if 'CPUUtilization' in metrics:
        cpu = metrics['CPUUtilization']
        # Lower CPU = higher confidence
        if cpu['avg_value'] < 1:
            score += 40
        elif cpu['avg_value'] < 3:
            score += 30
        elif cpu['avg_value'] < 5:
            score += 20
        
        # Consistent low usage
        if cpu['max_value'] < 10:
            score += 20
    
    # Sufficient data points
    if metrics.get('CPUUtilization', {}).get('data_points', 0) >= 48:
        score += 20
    
    # Network activity
    if 'NetworkIn' in metrics and 'NetworkOut' in metrics:
        total_network = (
            metrics['NetworkIn']['avg_value'] + 
            metrics['NetworkOut']['avg_value']
        )
        if total_network < 500:
            score += 20
    
    return min(score, 100)  # Cap at 100%
```

#### `get_untagged_resources(required_tags=None, region=None)`

**Bulk Tagging Operations**:
```python
from data_fetcher import get_untagged_resources, get_client

def bulk_tag_resources(resources, tags_to_apply, region, dry_run=True):
    """
    Apply tags to multiple resources at once
    """
    ec2_client = get_client('ec2', region_name=region)
    if not ec2_client:
        return None
    
    results = {
        'success': [],
        'failed': [],
        'skipped': []
    }
    
    # Group resources by type for efficient tagging
    instances = [r for r in resources if r['ResourceType'] == 'EC2 Instance']
    volumes = [r for r in resources if r['ResourceType'] == 'EBS Volume']
    
    # Tag instances
    if instances:
        instance_ids = [inst['ResourceId'] for inst in instances]
        try:
            if not dry_run:
                ec2_client.create_tags(
                    Resources=instance_ids,
                    Tags=[{'Key': k, 'Value': v} for k, v in tags_to_apply.items()]
                )
            results['success'].extend(instance_ids)
            print(f"{'Would tag' if dry_run else 'Tagged'} {len(instance_ids)} instances")
        except Exception as e:
            results['failed'].extend([(id, str(e)) for id in instance_ids])
            print(f"Failed to tag instances: {e}")
    
    # Tag volumes
    if volumes:
        volume_ids = [vol['ResourceId'] for vol in volumes]
        try:
            if not dry_run:
                ec2_client.create_tags(
                    Resources=volume_ids,
                    Tags=[{'Key': k, 'Value': v} for k, v in tags_to_apply.items()]
                )
            results['success'].extend(volume_ids)
            print(f"{'Would tag' if dry_run else 'Tagged'} {len(volume_ids)} volumes")
        except Exception as e:
            results['failed'].extend([(id, str(e)) for id in volume_ids])
            print(f"Failed to tag volumes: {e}")
    
    return results

# Usage example
untagged = get_untagged_resources(
    required_tags=['Project', 'Owner'], 
    region='us-east-1'
)

if untagged:
    all_untagged = untagged['Instances'] + untagged['Volumes']
    
    # Apply default tags
    default_tags = {
        'Project': 'DefaultProject',
        'Owner': 'SystemAdmin',
        'AutoTagged': 'true'
    }
    
    # Dry run first
    print("Dry run results:")
    bulk_tag_resources(all_untagged, default_tags, 'us-east-1', dry_run=True)
    
    # Uncomment to actually apply tags
    # bulk_tag_resources(all_untagged, default_tags, 'us-east-1', dry_run=False)
```

### Performance and Rate Limiting

```python
import time
from functools import wraps

def rate_limited(max_calls_per_second=10):
    """
    Decorator to implement rate limiting for AWS API calls
    """
    min_interval = 1.0 / max_calls_per_second
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator

# Apply to data fetcher functions
@rate_limited(max_calls_per_second=5)
def rate_limited_get_cost_by_service(days=30):
    return get_cost_by_service(days)

# Batch processing with rate limiting
def process_multiple_regions_safely(regions, operation, **kwargs):
    """
    Process multiple regions with automatic rate limiting
    """
    results = {}
    
    for i, region in enumerate(regions):
        if i > 0:
            # Add delay between regions to avoid rate limits
            time.sleep(1)
        
        try:
            print(f"Processing {region}...")
            result = operation(region=region, **kwargs)
            results[region] = result
            print(f"✓ {region} completed")
        except Exception as e:
            print(f"✗ {region} failed: {e}")
            results[region] = None
    
    return results
```

---

## aws_connector.py - Authentication and Client Management

### Overview
The `aws_connector.py` module provides a centralized authentication layer with session management, credential validation, and client factory methods.

### Session Management

```python
# Advanced session management with role assumption
from aws_connector import get_aws_session, get_client
import boto3

def get_cross_account_client(service_name, account_id, role_name, region=None):
    """
    Get a client for cross-account access using role assumption
    """
    base_session = get_aws_session()
    if not base_session:
        return None
    
    try:
        sts_client = base_session.client('sts')
        
        # Assume role in target account
        assumed_role = sts_client.assume_role(
            RoleArn=f"arn:aws:iam::{account_id}:role/{role_name}",
            RoleSessionName=f"CostDashboard-{int(time.time())}"
        )
        
        credentials = assumed_role['Credentials']
        
        # Create session with assumed role credentials
        cross_account_session = boto3.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'],
            region_name=region or base_session.region_name
        )
        
        return cross_account_session.client(service_name)
        
    except Exception as e:
        logging.error(f"Failed to assume role {role_name} in account {account_id}: {e}")
        return None

# Multi-account cost analysis
def multi_account_cost_analysis(accounts_config):
    """
    Analyze costs across multiple AWS accounts
    
    accounts_config = [
        {'account_id': '123456789012', 'role_name': 'CostAnalysisRole', 'name': 'Production'},
        {'account_id': '123456789013', 'role_name': 'CostAnalysisRole', 'name': 'Development'}
    ]
    """
    total_costs = {}
    
    for account in accounts_config:
        print(f"Analyzing account: {account['name']}")
        
        ce_client = get_cross_account_client(
            'ce', 
            account['account_id'], 
            account['role_name']
        )
        
        if ce_client:
            try:
                # Use the same logic as get_cost_by_service but with cross-account client
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                
                response = ce_client.get_cost_and_usage(
                    TimePeriod={
                        'Start': start_date.strftime('%Y-%m-%d'),
                        'End': end_date.strftime('%Y-%m-%d')
                    },
                    Granularity='MONTHLY',
                    Metrics=['UnblendedCost'],
                    GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
                )
                
                account_total = 0
                for result in response.get('ResultsByTime', []):
                    for group in result.get('Groups', []):
                        cost = float(group['Metrics']['UnblendedCost']['Amount'])
                        account_total += cost
                
                total_costs[account['name']] = account_total
                print(f"  Total cost: ${account_total:.2f}")
                
            except Exception as e:
                print(f"  Error: {e}")
                total_costs[account['name']] = None
    
    return total_costs
```

### Client Factory with Retry Logic

```python
from aws_connector import get_client
import boto3
from botocore.exceptions import ClientError, BotoCoreError
import time

def get_resilient_client(service_name, region_name=None, max_retries=3):
    """
    Get AWS client with built-in retry logic and error handling
    """
    for attempt in range(max_retries):
        try:
            client = get_client(service_name, region_name)
            if client:
                # Test the client with a simple operation
                if service_name == 'ec2':
                    client.describe_regions(MaxResults=1)
                elif service_name == 'ce':
                    # Cost Explorer doesn't have a simple test operation
                    pass
                elif service_name == 'cloudwatch':
                    client.list_metrics(MaxRecords=1)
                
                return client
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['Throttling', 'RequestLimitExceeded']:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Rate limited, waiting {wait_time:.1f}s before retry...")
                time.sleep(wait_time)
            else:
                print(f"Client error: {e}")
                break
        except Exception as e:
            print(f"Unexpected error getting {service_name} client: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
    
    return None

# Client connection health check
def check_aws_connectivity():
    """
    Comprehensive AWS connectivity and permissions check
    """
    checks = {
        'session': False,
        'sts': False,
        'ec2': False,
        'cost_explorer': False,
        'cloudwatch': False
    }
    
    errors = []
    
    # Check session creation
    try:
        session = get_aws_session()
        if session:
            checks['session'] = True
            print("✓ AWS session created successfully")
        else:
            errors.append("Failed to create AWS session")
    except Exception as e:
        errors.append(f"Session creation error: {e}")
    
    # Check STS (identity)
    try:
        sts_client = get_client('sts')
        if sts_client:
            identity = sts_client.get_caller_identity()
            checks['sts'] = True
            print(f"✓ AWS identity confirmed: {identity.get('Arn', 'Unknown')}")
    except Exception as e:
        errors.append(f"STS check failed: {e}")
    
    # Check EC2 permissions
    try:
        ec2_client = get_client('ec2')
        if ec2_client:
            ec2_client.describe_regions(MaxResults=1)
            checks['ec2'] = True
            print("✓ EC2 permissions verified")
    except Exception as e:
        errors.append(f"EC2 check failed: {e}")
    
    # Check Cost Explorer permissions
    try:
        ce_client = get_client('ce')
        if ce_client:
            # Try a simple cost query
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1)
            
            ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost']
            )
            checks['cost_explorer'] = True
            print("✓ Cost Explorer permissions verified")
    except Exception as e:
        errors.append(f"Cost Explorer check failed: {e}")
    
    # Check CloudWatch permissions
    try:
        cw_client = get_client('cloudwatch')
        if cw_client:
            cw_client.list_metrics(MaxRecords=1)
            checks['cloudwatch'] = True
            print("✓ CloudWatch permissions verified")
    except Exception as e:
        errors.append(f"CloudWatch check failed: {e}")
    
    # Summary
    successful_checks = sum(checks.values())
    total_checks = len(checks)
    
    print(f"\nConnectivity Summary: {successful_checks}/{total_checks} checks passed")
    
    if errors:
        print("\nErrors encountered:")
        for error in errors:
            print(f"  ✗ {error}")
    
    return checks, errors
```

This comprehensive module reference provides detailed implementation examples, advanced usage patterns, and production-ready code snippets for each component of the AWS Cost Optimization Dashboard. The documentation includes error handling, performance optimization, and real-world integration scenarios.