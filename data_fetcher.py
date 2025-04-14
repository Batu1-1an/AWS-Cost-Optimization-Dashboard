import logging
from datetime import datetime, timedelta
import pandas as pd
from aws_connector import get_client, AWS_REGION

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


def _check_missing_tags(resource_tags_list, required_tags_set):
    """Helper function to find missing tags from a list of tag dictionaries."""
    if not resource_tags_list: # Handle case where 'Tags' key might be missing entirely
        return list(required_tags_set) # All required tags are missing

    # Convert [{'Key': k, 'Value': v}, ...] to a set of keys {'k', ...}
    present_tags_set = {tag['Key'] for tag in resource_tags_list}
    missing = list(required_tags_set - present_tags_set)
    return missing

def get_untagged_resources(required_tags=None, region=AWS_REGION):
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
    ec2_client = get_client('ec2', region_name=region)
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
    logging.info(f"Checking for resources missing tags {required_tags} in region {region}...")

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
        logging.error(f"Error describing EC2 instances for tag check in region {region}: {e}")
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
        logging.error(f"Error describing EBS volumes for tag check in region {region}: {e}")
        # Allow returning partial results if instances were checked successfully
        # but volumes failed. The caller can decide how to handle this.
        # If instance check also failed, we would have returned None already.

    logging.info(f"Found {len(untagged_resources['Instances'])} untagged instances and {len(untagged_resources['Volumes'])} untagged volumes.")
    return untagged_resources

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
    untagged = get_untagged_resources()
    if untagged is not None:
        print(f"Found {len(untagged['Instances'])} untagged instances in {AWS_REGION}:")
        for inst in untagged['Instances']:
            print(f"  ID: {inst['ResourceId']}, Missing: {inst['MissingTags']}")
        print(f"Found {len(untagged['Volumes'])} untagged volumes in {AWS_REGION}:")
        for vol in untagged['Volumes']:
             print(f"  ID: {vol['ResourceId']}, Missing: {vol['MissingTags']}")
    else:
        print("Could not fetch untagged resource data.")


    logging.info("--- Data Fetcher Test Complete ---")