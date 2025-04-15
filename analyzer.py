import logging
from data_fetcher import (
    get_cost_by_service, get_idle_ec2_instances, get_untagged_resources,
    get_ebs_optimization_candidates # Import new fetcher function
)
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


    logging.info("--- Analyzer Test Complete ---")