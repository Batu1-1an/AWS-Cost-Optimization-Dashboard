import logging
from data_fetcher import (
    get_cost_by_service, get_idle_ec2_instances, get_untagged_resources,
    get_ebs_optimization_candidates, get_daily_cost_history # Import new fetcher functions
)
import numpy as np # For standard deviation calculation
from aws_connector import AWS_REGION # Import default region for convenience

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def analyze_cost_data(days=30):
    """
    Analyzes cost data by fetching it from the data_fetcher.
    Currently, it just returns the fetched data.

    Args:
        days (int): The number of past days to analyze data for.

    Returns:
        dict: A dictionary of costs by service, or None if fetching fails.
    """
    logging.info(f"Starting cost data analysis for the last {days} days.")
    cost_data = get_cost_by_service(days=days)
    if cost_data is None:
        logging.error("Failed to retrieve cost data for analysis.")
        return None
    # Future: Add more complex analysis here if needed (e.g., trend detection)
    logging.info("Cost data analysis complete.")
    return cost_data

def analyze_idle_instances(region=AWS_REGION):
    """
    Analyzes EC2 instances to find idle ones by fetching data from data_fetcher.
    Currently, it just returns the fetched list.

    Args:
        region (str): The AWS region to analyze instances in.

    Returns:
        list: A list of potentially idle instances, or None if fetching fails.
    """
    logging.info(f"Starting idle instance analysis for region {region}.")
    idle_instances = get_idle_ec2_instances(region=region)
    if idle_instances is None:
        logging.error("Failed to retrieve idle instance data for analysis.")
        return None
    # Future: Add more complex analysis or filtering here if needed
    logging.info(f"Idle instance analysis complete. Found {len(idle_instances)} potential candidates.")
    return idle_instances

def analyze_untagged_resources(required_tags=None, region=AWS_REGION):
    """
    Analyzes resources to find untagged ones by fetching data from data_fetcher.
    Currently, it just returns the fetched list.

    Args:
        required_tags (list, optional): A list of tag keys that must be present.
                                        Defaults to fetcher's default.
        region (str): The AWS region to analyze resources in.

    Returns:
        dict: A dictionary containing lists of untagged 'Instances' and 'Volumes',
              or None if fetching fails.
    """
    logging.info(f"Starting untagged resource analysis for region {region}.")
    untagged_resources = get_untagged_resources(required_tags=required_tags, region=region)
    if untagged_resources is None:
        logging.error("Failed to retrieve untagged resource data for analysis.")
        return None
    # Future: Add more complex analysis or filtering here if needed
    logging.info(f"Untagged resource analysis complete. Found {len(untagged_resources.get('Instances',[]))} instances, {len(untagged_resources.get('Volumes',[]))} volumes.")
    return untagged_resources

def analyze_ebs_optimization(region=AWS_REGION):
    """
    Analyzes EBS volumes to find optimization candidates using data_fetcher.
    Currently, it just returns the fetched list.

    Args:
        region (str): The AWS region to analyze volumes in.

    Returns:
        dict: A dictionary containing lists of 'UnattachedVolumes' and 'Gp2Volumes',
              or None if fetching fails.
    """
    logging.info(f"Starting EBS optimization analysis for region {region}.")
    ebs_opts = get_ebs_optimization_candidates(region=region)
    if ebs_opts is None:
        logging.error("Failed to retrieve EBS optimization data for analysis.")
        return None
    # Future: Add more complex analysis (e.g., cost comparison for gp2->gp3)
    logging.info(f"EBS optimization analysis complete. Found {len(ebs_opts.get('UnattachedVolumes',[]))} unattached, {len(ebs_opts.get('Gp2Volumes',[]))} gp2 volumes.")
    return ebs_opts

def analyze_cost_anomalies(history_days=60, std_dev_threshold=2.5):
    """
    Analyzes daily cost history to find anomalies (significant spikes).
    Uses a simple standard deviation approach.

    Args:
        history_days (int): How many days of history to fetch for analysis.
        std_dev_threshold (float): How many standard deviations above the mean
                                   the latest cost must be to be considered an anomaly.

    Returns:
        dict: Information about the latest cost and whether it's anomalous,
              or None if fetching or analysis fails.
              Example: {'latest_date': '2024-01-10', 'latest_cost': 150.5,
                        'average_cost': 100.0, 'std_dev': 15.0,
                        'threshold': 137.5, 'is_anomaly': True}
    """
    logging.info(f"Starting cost anomaly analysis using last {history_days} days.")
    daily_costs = get_daily_cost_history(days=history_days)

    if daily_costs is None or len(daily_costs) < 2: # Need at least 2 points for std dev
        logging.error("Insufficient daily cost data for anomaly analysis.")
        return None

    # Convert costs to a list/array for calculation
    costs = list(daily_costs.values())
    dates = list(daily_costs.keys())

    # Use all but the most recent day for calculating baseline mean/std dev
    if len(costs) > 1:
        baseline_costs = np.array(costs[:-1])
        average_cost = np.mean(baseline_costs)
        std_dev = np.std(baseline_costs)
    else: # Handle edge case with only 1 day (cannot calculate baseline)
        average_cost = costs[0]
        std_dev = 0

    latest_date = dates[-1]
    latest_cost = costs[-1]

    # Calculate the anomaly threshold
    anomaly_threshold = average_cost + (std_dev * std_dev_threshold)

    # Check if the latest cost exceeds the threshold
    is_anomaly = latest_cost > anomaly_threshold and std_dev > 0 # Avoid flagging if std dev is 0

    result = {
        'latest_date': latest_date,
        'latest_cost': latest_cost,
        'average_cost': round(average_cost, 2),
        'std_dev': round(std_dev, 2),
        'threshold': round(anomaly_threshold, 2),
        'is_anomaly': is_anomaly,
        'history_days': history_days,
        'std_dev_threshold': std_dev_threshold
    }

    if is_anomaly:
        logging.warning(f"Cost anomaly detected! Date: {latest_date}, Cost: ${latest_cost:.2f}, Threshold: ${anomaly_threshold:.2f}")
    else:
        logging.info("No cost anomaly detected.")

    return result

# Example usage (optional, for testing this module directly)
if __name__ == '__main__':
    logging.info("--- Testing Analyzer ---")

    print("\nAnalyzing Cost Data...")
    costs = analyze_cost_data(days=7)
    if costs:
        print("Analyzed Costs by Service (Last 7 Days):")
        for service, cost in costs.items():
            print(f"  {service}: ${cost:.2f}")
    else:
        print("Could not analyze cost data.")

    print("\nAnalyzing Idle Instances...")
    idle = analyze_idle_instances()
    if idle is not None:
        print(f"Analyzed Idle Instances in {AWS_REGION}: {len(idle)} found.")
        for inst in idle:
            print(f"  ID: {inst['InstanceId']}")
    else:
        print("Could not analyze idle instance data.")

    print("\nAnalyzing Untagged Resources...")
    untagged = analyze_untagged_resources()
    if untagged is not None:
        print(f"Analyzed Untagged Instances in {AWS_REGION}: {len(untagged.get('Instances',[]))} found.")
        for inst in untagged.get('Instances', []):
            print(f"  ID: {inst['ResourceId']}, Missing: {inst['MissingTags']}")
        print(f"Analyzed Untagged Volumes in {AWS_REGION}: {len(untagged.get('Volumes',[]))} found.")
        for vol in untagged.get('Volumes', []):
             print(f"  ID: {vol['ResourceId']}, Missing: {vol['MissingTags']}")
    else:
        print("Could not analyze untagged resource data.")

    print("\nAnalyzing EBS Optimization Candidates...")
    ebs_opts = analyze_ebs_optimization()
    if ebs_opts is not None:
        print(f"Analyzed Unattached Volumes in {AWS_REGION}: {len(ebs_opts.get('UnattachedVolumes',[]))} found.")
        for vol in ebs_opts.get('UnattachedVolumes', []):
            print(f"  ID: {vol['ResourceId']}, Size: {vol['SizeGiB']} GiB")
        print(f"Analyzed GP2 Volumes in {AWS_REGION}: {len(ebs_opts.get('Gp2Volumes',[]))} found.")
        for vol in ebs_opts.get('Gp2Volumes', []):
             print(f"  ID: {vol['ResourceId']}, Size: {vol['SizeGiB']} GiB")
    else:
        print("Could not analyze EBS optimization data.")

    print("\nAnalyzing Cost Anomalies...")
    anomaly_result = analyze_cost_anomalies()
    if anomaly_result:
        print(f"  Latest Date: {anomaly_result['latest_date']}")
        print(f"  Latest Cost: ${anomaly_result['latest_cost']:.2f}")
        print(f"  Avg Cost (prev {anomaly_result['history_days']-1} days): ${anomaly_result['average_cost']:.2f}")
        print(f"  Std Dev: ${anomaly_result['std_dev']:.2f}")
        print(f"  Threshold: ${anomaly_result['threshold']:.2f}")
        print(f"  Is Anomaly: {anomaly_result['is_anomaly']}")
    else:
        print("Could not perform cost anomaly analysis.")


    logging.info("--- Analyzer Test Complete ---")