import logging
from datetime import datetime, timedelta
import pandas as pd
from aws_connector import get_client, AWS_REGION
from aws_regions import AWS_REGIONS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constants for Idle Instance Detection ---
# How far back to look for metrics (e.g., 14 days)
IDLE_CHECK_PERIOD_DAYS = 14
# Average CPU threshold (e.g., below 5%)
IDLE_AVG_CPU_THRESHOLD = 5.0
# Maximum CPU threshold (e.g., never above 10%)
IDLE_MAX_CPU_THRESHOLD = 10.0
# CloudWatch metric details
METRIC_NAME = 'CPUUtilization'
NAMESPACE = 'AWS/EC2'
STATISTICS = ['Average', 'Maximum']
# Period for CloudWatch metrics (e.g., 1 day) - adjust granularity vs. cost/API calls
CW_PERIOD_SECONDS = 86400 # 24 * 60 * 60

# --- Constants for Untagged Resource Detection ---
# Define the tags that are considered mandatory
REQUIRED_TAGS = ['Project', 'Owner'] # Example tags, adjust as needed

# --- Constants for S3 Analysis ---
# Storage classes that can be optimized
OPTIMIZABLE_STORAGE_CLASSES = ['STANDARD', 'REDUCED_REDUNDANCY']
# Target storage classes for optimization
RECOMMENDED_STORAGE_CLASSES = ['STANDARD_IA', 'GLACIER', 'DEEP_ARCHIVE']

def get_cost_by_service(days=30):
    """
    Fetches cost data grouped by service from AWS Cost Explorer.

    Args:
        days (int): The number of past days to fetch data for.

    Returns:
        dict: A dictionary with service names as keys and costs as values,
              or None if an error occurs.
    """
    ce_client = get_client('ce')
    if not ce_client:
        logging.error("Cost Explorer client is not available.")
        return None

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Format dates as YYYY-MM-DD strings
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    logging.info(f"Fetching cost data from {start_str} to {end_str}")

    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_str,
                'End': end_str
            },
            Granularity='MONTHLY', # Or DAILY if needed, adjust processing
            Metrics=['UnblendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                },
            ]
        )

        costs_by_service = {}
        for result in response.get('ResultsByTime', []):
            for group in result.get('Groups', []):
                service_name = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                if cost > 0: # Only include services with non-zero cost
                    costs_by_service[service_name] = costs_by_service.get(service_name, 0) + cost

        # Round costs for readability
        costs_by_service = {k: round(v, 2) for k, v in costs_by_service.items()}
        logging.info(f"Successfully fetched costs for {len(costs_by_service)} services.")
        return costs_by_service

    except Exception as e:
        logging.error(f"Error fetching cost data from Cost Explorer: {e}")
        return None


def get_idle_ec2_instances(region=AWS_REGION):
    """
    Identifies potentially idle EC2 instances based on CloudWatch CPU metrics.

    Args:
        region (str): The AWS region to check instances in.

    Returns:
        list: A list of dictionaries, each representing an idle instance,
              or None if an error occurs.
    """
    ec2_client = get_client('ec2', region_name=region)
    cw_client = get_client('cloudwatch', region_name=region)

    if not ec2_client or not cw_client:
        logging.error(f"EC2 or CloudWatch client not available for region {region}.")
        return None

    idle_instances = []
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=IDLE_CHECK_PERIOD_DAYS)

    logging.info(f"Checking for idle EC2 instances in region {region}...")

    try:
        # Paginate through instances if necessary
        paginator = ec2_client.get_paginator('describe_instances')
        instance_pages = paginator.paginate(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )

        for page in instance_pages:
            for reservation in page.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    instance_id = instance['InstanceId']
                    logging.debug(f"Checking instance: {instance_id}")

                    try:
                        # Get CloudWatch metrics
                        metric_data = cw_client.get_metric_statistics(
                            Namespace=NAMESPACE,
                            MetricName=METRIC_NAME,
                            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=CW_PERIOD_SECONDS,
                            Statistics=STATISTICS,
                            Unit='Percent'
                        )

                        datapoints = metric_data.get('Datapoints', [])
                        if not datapoints:
                            logging.warning(f"No {METRIC_NAME} data found for instance {instance_id} in the period.")
                            continue # Skip if no data

                        # Use pandas for easier calculation
                        df = pd.DataFrame(datapoints)
                        avg_cpu = df['Average'].mean()
                        max_cpu = df['Maximum'].max()

                        logging.debug(f"Instance {instance_id}: Avg CPU = {avg_cpu:.2f}%, Max CPU = {max_cpu:.2f}%")

                        # Check idle criteria
                        if avg_cpu < IDLE_AVG_CPU_THRESHOLD and max_cpu < IDLE_MAX_CPU_THRESHOLD:
                            idle_info = {
                                "InstanceId": instance_id,
                                "Region": region,
                                "AvgCPU": avg_cpu,
                                "MaxCPU": max_cpu, # Include max for context
                                "Reason": f"Avg CPU ({avg_cpu:.2f}%) < {IDLE_AVG_CPU_THRESHOLD}% and Max CPU ({max_cpu:.2f}%) < {IDLE_MAX_CPU_THRESHOLD}% over last {IDLE_CHECK_PERIOD_DAYS} days"
                            }
                            idle_instances.append(idle_info)
                            logging.info(f"Identified potentially idle instance: {instance_id}")

                    except Exception as cw_error:
                        logging.error(f"Error fetching CloudWatch metrics for instance {instance_id}: {cw_error}")
                        # Continue to the next instance

        logging.info(f"Found {len(idle_instances)} potentially idle instances in region {region}.")
        return idle_instances

    except Exception as e:
        logging.error(f"Error describing EC2 instances in region {region}: {e}")
        return None

from utils import _check_missing_tags # Ensure import is here

# Remove the old function definition below

def get_untagged_resources(required_tags=None, region=None): # Corrected signature from previous attempt
    """
    Finds EC2 instances and EBS volumes missing specified required tags.

    Args:
        required_tags (list, optional): A list of tag keys that must be present.
                                        Defaults to REQUIRED_TAGS constant.
        region (str): The AWS region to check resources in.

    Returns:
        dict: A dictionary containing lists of untagged 'Instances' and 'Volumes',
              or None if an error occurs. Each item includes the resource ID and missing tags.
    """
    ec2_client = get_client('ec2', region_name=region or AWS_REGION)
    if not ec2_client:
        logging.error(f"EC2 client not available for region {region}.")
        return None

    if required_tags is None:
        required_tags = REQUIRED_TAGS
    required_tags_set = set(required_tags)
    if not required_tags_set:
        logging.warning("No required tags specified for untagged resource check.")
        return {'Instances': [], 'Volumes': []}

    untagged_resources = {'Instances': [], 'Volumes': []}
    logging.info(f"Checking for resources missing tags {required_tags} in region {region or AWS_REGION}...")

    # --- Check EC2 Instances ---
    try:
        logging.debug("Checking EC2 instances for missing tags...")
        paginator_inst = ec2_client.get_paginator('describe_instances')
        # Include non-running instances as well, as they might still need tags
        instance_pages = paginator_inst.paginate(
             Filters=[{'Name': 'instance-state-name', 'Values': ['pending', 'running', 'shutting-down', 'stopped', 'stopping']}]
        )

        for page in instance_pages:
            for reservation in page.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    instance_id = instance['InstanceId']
                    tags = instance.get('Tags', [])
                    missing_tags = _check_missing_tags(tags, required_tags_set)
                    if missing_tags:
                        untagged_resources['Instances'].append({
                            'ResourceId': instance_id,
                            'ResourceType': 'EC2 Instance',
                            'Region': region,
                            'MissingTags': missing_tags
                        })
                        logging.debug(f"Instance {instance_id} missing tags: {missing_tags}")

    except Exception as e:
        logging.error(f"Error describing EC2 instances for tag check in region {region or AWS_REGION}: {e}")
        # Continue to check volumes if possible, but maybe return partial results or None?
        # For now, let's return None if instance check fails significantly
        return None

    # --- Check EBS Volumes ---
    try:
        logging.debug("Checking EBS volumes for missing tags...")
        paginator_vol = ec2_client.get_paginator('describe_volumes')
        # Check all volumes, regardless of state (attached/unattached)
        volume_pages = paginator_vol.paginate()

        for page in volume_pages:
            for volume in page.get('Volumes', []):
                volume_id = volume['VolumeId']
                tags = volume.get('Tags', [])
                missing_tags = _check_missing_tags(tags, required_tags_set)
                if missing_tags:
                    untagged_resources['Volumes'].append({
                        'ResourceId': volume_id,
                        'ResourceType': 'EBS Volume',
                        'Region': region,
                        'MissingTags': missing_tags
                    })
                    logging.debug(f"Volume {volume_id} missing tags: {missing_tags}")

    except Exception as e:
        logging.error(f"Error describing EBS volumes for tag check in region {region or AWS_REGION}: {e}")
        # Allow returning partial results if instances were checked successfully
        # but volumes failed. The caller can decide how to handle this.
        # If instance check also failed, we would have returned None already.

    logging.info(f"Found {len(untagged_resources['Instances'])} untagged instances and {len(untagged_resources['Volumes'])} untagged volumes in region {region or AWS_REGION}.")
    return untagged_resources


def get_daily_cost_history(days=60):
    """
    Fetches total daily cost data from AWS Cost Explorer for anomaly detection.

    Args:
        days (int): The number of past days to fetch data for.

    Returns:
        dict: A dictionary with dates (YYYY-MM-DD strings) as keys and
              total costs as values, or None if an error occurs.
    """
    ce_client = get_client('ce')
    if not ce_client:
        logging.error("Cost Explorer client is not available.")
        return None

    # Go back `days + 1` to ensure we have enough data for comparison
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Format dates as YYYY-MM-DD strings
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    logging.info(f"Fetching daily cost history from {start_str} to {end_str}")

    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_str,
                'End': end_str
            },
            Granularity='DAILY', # Fetch daily data
            Metrics=['UnblendedCost']
            # No GroupBy needed for total daily cost
        )

        daily_costs = {}
        for result in response.get('ResultsByTime', []):
            date_str = result['TimePeriod']['Start']
            cost = float(result['Total']['UnblendedCost']['Amount'])
            daily_costs[date_str] = round(cost, 2)

        logging.info(f"Successfully fetched daily costs for {len(daily_costs)} days.")
        # Sort by date, although Cost Explorer usually returns it sorted
        return dict(sorted(daily_costs.items()))

    except Exception as e:
        logging.error(f"Error fetching daily cost history from Cost Explorer: {e}")
        return None

def get_ebs_optimization_candidates(region=None):
    """
    Finds EBS volumes that are optimization candidates:
    1. Unattached (State='available')
    2. Using gp2 type (potential gp3 upgrade candidate)

    Args:
        region (str, optional): The AWS region to check volumes in. Defaults to AWS_REGION.

    Returns:
        dict: A dictionary containing lists of 'UnattachedVolumes' and 'Gp2Volumes',
              or None if an error occurs.
    """
    target_region = region or AWS_REGION
    ec2_client = get_client('ec2', region_name=target_region)
    if not ec2_client:
        logging.error(f"EC2 client not available for region {target_region}.")
        return None

    optimization_candidates = {'UnattachedVolumes': [], 'Gp2Volumes': []}
    logging.info(f"Checking for EBS optimization candidates in region {target_region}...")

    try:
        paginator = ec2_client.get_paginator('describe_volumes')
        volume_pages = paginator.paginate() # Get all volumes

        for page in volume_pages:
            for volume in page.get('Volumes', []):
                volume_id = volume['VolumeId']
                volume_state = volume['State']
                volume_type = volume['VolumeType']
                volume_size = volume['Size'] # Size in GiB

                # Check if unattached
                if volume_state == 'available':
                    optimization_candidates['UnattachedVolumes'].append({
                        'ResourceId': volume_id,
                        'ResourceType': 'EBS Volume',
                        'Region': target_region,
                        'SizeGiB': volume_size,
                        'Reason': 'Unattached (Available)'
                    })
                    logging.debug(f"Volume {volume_id} is unattached.")

                # Check if gp2 (potential gp3 candidate)
                # Note: Further analysis needed to confirm gp3 is cheaper/better.
                # This just flags them.
                if volume_type == 'gp2':
                    optimization_candidates['Gp2Volumes'].append({
                        'ResourceId': volume_id,
                        'ResourceType': 'EBS Volume',
                        'Region': target_region,
                        'SizeGiB': volume_size,
                        'CurrentType': 'gp2',
                        'Reason': 'Potential gp3 Upgrade Candidate'
                    })
                    logging.debug(f"Volume {volume_id} is gp2 type.")

    except Exception as e:
        logging.error(f"Error describing EBS volumes for optimization check in region {target_region}: {e}")
        return None # Return None on error

    logging.info(f"Found {len(optimization_candidates['UnattachedVolumes'])} unattached volumes and {len(optimization_candidates['Gp2Volumes'])} gp2 volumes.")
    return optimization_candidates

def get_s3_bucket_analysis(region=None):
    """
    Fetches S3 bucket information and analyzes storage optimization opportunities.
    
    Args:
        region (str): AWS region to analyze. If None, uses default region.
        
    Returns:
        dict: Dictionary containing bucket analysis data or None if error occurs.
    """
    s3_client = get_client('s3', region)
    if not s3_client:
        logging.error("S3 client is not available.")
        return None
        
    try:
        # Get list of all buckets
        response = s3_client.list_buckets()
        buckets = response.get('Buckets', [])
        
        bucket_analysis = []
        total_size = 0
        total_objects = 0
        optimization_opportunities = []
        
        for bucket in buckets:
            bucket_name = bucket['Name']
            logging.info(f"Analyzing bucket: {bucket_name}")
            
            try:
                # Get bucket location
                bucket_location = s3_client.get_bucket_location(Bucket=bucket_name)
                bucket_region = bucket_location.get('LocationConstraint') or 'us-east-1'
                
                # Get bucket size and object count
                bucket_info = _get_bucket_size_and_count(s3_client, bucket_name)
                
                # Get storage class distribution
                storage_class_dist = _get_bucket_storage_classes(s3_client, bucket_name)
                
                # Check for lifecycle policies
                has_lifecycle = _check_bucket_lifecycle(s3_client, bucket_name)
                
                # Analyze optimization opportunities
                bucket_optimization = _analyze_bucket_optimization(
                    bucket_name, bucket_info, storage_class_dist, has_lifecycle
                )
                
                bucket_data = {
                    'name': bucket_name,
                    'region': bucket_region,
                    'size_gb': bucket_info['size_gb'],
                    'object_count': bucket_info['object_count'],
                    'storage_classes': storage_class_dist,
                    'has_lifecycle_policy': has_lifecycle,
                    'optimization': bucket_optimization
                }
                
                bucket_analysis.append(bucket_data)
                total_size += bucket_info['size_gb']
                total_objects += bucket_info['object_count']
                
                if bucket_optimization['opportunities']:
                    optimization_opportunities.extend(bucket_optimization['opportunities'])
                    
            except Exception as e:
                logging.warning(f"Could not analyze bucket {bucket_name}: {str(e)}")
                continue
                
        return {
            'buckets': bucket_analysis,
            'summary': {
                'total_buckets': len(buckets),
                'total_size_gb': total_size,
                'total_objects': total_objects,
                'buckets_analyzed': len(bucket_analysis),
                'optimization_opportunities_count': len(optimization_opportunities)
            },
            'optimization_opportunities': optimization_opportunities
        }
        
    except Exception as e:
        logging.error(f"Error fetching S3 bucket analysis: {str(e)}")
        return None

def _get_bucket_size_and_count(s3_client, bucket_name):
    """
    Helper function to get bucket size and object count using CloudWatch metrics.
    Falls back to listing objects if metrics are not available.
    """
    cw_client = get_client('cloudwatch')
    
    try:
        if cw_client:
            # Try to get size from CloudWatch metrics
            end_time = datetime.now()
            start_time = end_time - timedelta(days=2)
            
            # Get bucket size in bytes
            size_response = cw_client.get_metric_statistics(
                Namespace='AWS/S3',
                MetricName='BucketSizeBytes',
                Dimensions=[
                    {'Name': 'BucketName', 'Value': bucket_name},
                    {'Name': 'StorageType', 'Value': 'StandardStorage'}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # Daily
                Statistics=['Average']
            )
            
            # Get object count
            count_response = cw_client.get_metric_statistics(
                Namespace='AWS/S3',
                MetricName='NumberOfObjects',
                Dimensions=[
                    {'Name': 'BucketName', 'Value': bucket_name},
                    {'Name': 'StorageType', 'Value': 'AllStorageTypes'}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # Daily
                Statistics=['Average']
            )
            
            size_datapoints = size_response.get('Datapoints', [])
            count_datapoints = count_response.get('Datapoints', [])
            
            if size_datapoints and count_datapoints:
                latest_size = max(size_datapoints, key=lambda x: x['Timestamp'])
                latest_count = max(count_datapoints, key=lambda x: x['Timestamp'])
                
                return {
                    'size_gb': latest_size['Average'] / (1024**3),  # Convert to GB
                    'object_count': int(latest_count['Average'])
                }
    except Exception as e:
        logging.warning(f"Could not get CloudWatch metrics for {bucket_name}: {str(e)}")
    
    # Fallback: estimate by listing objects (limited to first 1000 for performance)
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1000)
        objects = response.get('Contents', [])
        
        total_size = sum(obj.get('Size', 0) for obj in objects)
        object_count = response.get('KeyCount', 0)
        
        # If there are more objects, this is an underestimate
        if response.get('IsTruncated', False):
            object_count = f"{object_count}+"
            
        return {
            'size_gb': total_size / (1024**3),
            'object_count': object_count
        }
    except Exception as e:
        logging.warning(f"Could not list objects for {bucket_name}: {str(e)}")
        return {'size_gb': 0, 'object_count': 0}

def _get_bucket_storage_classes(s3_client, bucket_name):
    """
    Helper function to get storage class distribution for a bucket.
    """
    try:
        storage_classes = {}
        
        # List a sample of objects to analyze storage classes
        response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1000)
        objects = response.get('Contents', [])
        
        for obj in objects:
            storage_class = obj.get('StorageClass', 'STANDARD')
            storage_classes[storage_class] = storage_classes.get(storage_class, 0) + 1
            
        return storage_classes
    except Exception as e:
        logging.warning(f"Could not get storage classes for {bucket_name}: {str(e)}")
        return {}

def _check_bucket_lifecycle(s3_client, bucket_name):
    """
    Helper function to check if a bucket has lifecycle policies configured.
    """
    try:
        s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
        return True
    except s3_client.exceptions.NoSuchLifecycleConfiguration:
        return False
    except Exception as e:
        logging.warning(f"Could not check lifecycle policy for {bucket_name}: {str(e)}")
        return False

def _analyze_bucket_optimization(bucket_name, bucket_info, storage_classes, has_lifecycle):
    """
    Helper function to analyze optimization opportunities for a bucket.
    """
    opportunities = []
    potential_savings = 0
    
    # Check for objects in STANDARD storage that could be moved to IA
    standard_objects = storage_classes.get('STANDARD', 0)
    if standard_objects > 0 and bucket_info['size_gb'] > 0.1:  # Only suggest for buckets > 100MB
        opportunities.append({
            'type': 'storage_class_optimization',
            'description': f'Consider moving {standard_objects} STANDARD objects to STANDARD_IA for long-term storage',
            'potential_savings_percent': 45,  # STANDARD_IA is ~45% cheaper than STANDARD
            'recommended_action': 'Implement lifecycle policy to transition to STANDARD_IA after 30 days'
        })
        potential_savings += bucket_info['size_gb'] * 0.023 * 0.45  # Rough calculation
    
    # Check for REDUCED_REDUNDANCY storage (deprecated)
    rr_objects = storage_classes.get('REDUCED_REDUNDANCY', 0)
    if rr_objects > 0:
        opportunities.append({
            'type': 'deprecated_storage_class',
            'description': f'{rr_objects} objects using deprecated REDUCED_REDUNDANCY storage',
            'potential_savings_percent': 20,
            'recommended_action': 'Migrate to STANDARD or STANDARD_IA storage class'
        })
    
    # Check for missing lifecycle policies
    if not has_lifecycle and bucket_info['size_gb'] > 1:  # Suggest for buckets > 1GB
        opportunities.append({
            'type': 'missing_lifecycle_policy',
            'description': 'No lifecycle policy configured for automatic storage class transitions',
            'potential_savings_percent': 30,
            'recommended_action': 'Configure lifecycle policy for automatic cost optimization'
        })
        potential_savings += bucket_info['size_gb'] * 0.023 * 0.30
    
    return {
        'opportunities': opportunities,
        'potential_monthly_savings_usd': round(potential_savings, 2)
    }

# Example usage (optional, for testing this module directly)
if __name__ == '__main__':
    logging.info("--- Testing Data Fetcher ---")

    print("\nFetching Cost Data...")
    costs = get_cost_by_service(days=7)
    if costs:
        print("Costs by Service (Last 7 Days):")
        for service, cost in costs.items():
            print(f"  {service}: ${cost:.2f}")
    else:
        print("Could not fetch cost data.")

    print("\nFetching Idle Instances...")
    idle = get_idle_ec2_instances()
    if idle is not None:
        print(f"Found {len(idle)} potentially idle instances in {AWS_REGION}:")
        for inst in idle:
            print(f"  ID: {inst['InstanceId']}, Avg CPU: {inst['AvgCPU']:.2f}%, Max CPU: {inst['MaxCPU']:.2f}%")
    else:
        print("Could not fetch idle instance data.")

    print("\nFetching Untagged Resources...")
    untagged = get_untagged_resources(region='us-west-2')  # Example with a specific region
    if untagged is not None:
        print(f"Found {len(untagged['Instances'])} untagged instances in us-west-2:")
        for inst in untagged['Instances']:
            print(f"  ID: {inst['ResourceId']}, Missing: {inst['MissingTags']}")
        print(f"Found {len(untagged['Volumes'])} untagged volumes in {AWS_REGION}:")
        for vol in untagged['Volumes']:
             print(f"  ID: {vol['ResourceId']}, Missing: {vol['MissingTags']}")
    else:
        print("Could not fetch untagged resource data.")

    print("\nFetching EBS Optimization Candidates...")
    ebs_opts = get_ebs_optimization_candidates()
    if ebs_opts is not None:
        print(f"Found {len(ebs_opts['UnattachedVolumes'])} unattached volumes in {AWS_REGION}:")
        for vol in ebs_opts['UnattachedVolumes']:
            print(f"  ID: {vol['ResourceId']}, Size: {vol['SizeGiB']} GiB")
        print(f"Found {len(ebs_opts['Gp2Volumes'])} gp2 volumes in {AWS_REGION}:")
        for vol in ebs_opts['Gp2Volumes']:
             print(f"  ID: {vol['ResourceId']}, Size: {vol['SizeGiB']} GiB")
    else:
        print("Could not fetch EBS optimization data.")

    print("\nFetching Daily Cost History...")
    daily_history = get_daily_cost_history(days=7)
    if daily_history:
        print("Daily Costs (Last 7 Days):")
        for date, cost in daily_history.items():
            print(f"  {date}: ${cost:.2f}")
    else:
        print("Could not fetch daily cost history.")


    logging.info("--- Data Fetcher Test Complete ---")