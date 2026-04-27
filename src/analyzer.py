import logging
from .data_fetcher import (
    get_cost_by_service, get_idle_ec2_instances, get_untagged_resources,
    get_ebs_optimization_candidates, get_daily_cost_history, get_s3_bucket_analysis
)
import numpy as np
from .aws_connector import AWS_REGION

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

def analyze_s3_optimization(region=None):
    """
    Analyzes S3 buckets for cost optimization opportunities.
    
    Args:
        region (str): AWS region to analyze. If None, uses default region.
    
    Returns:
        dict: Dictionary containing S3 analysis results or None if analysis fails.
    """
    logging.info("Starting S3 optimization analysis.")
    
    # Fetch S3 bucket data
    s3_data = get_s3_bucket_analysis(region)
    if s3_data is None:
        logging.error("Failed to retrieve S3 bucket data for analysis.")
        return None
    
    try:
        # Analyze the data further
        analysis_result = {
            'summary': s3_data['summary'],
            'buckets': s3_data['buckets'],
            'optimization_opportunities': s3_data['optimization_opportunities'],
            'priority_recommendations': _prioritize_s3_recommendations(s3_data),
            'cost_analysis': _calculate_s3_cost_impact(s3_data)
        }
        
        logging.info(f"S3 analysis complete. Found {len(s3_data['optimization_opportunities'])} optimization opportunities across {s3_data['summary']['buckets_analyzed']} buckets.")
        return analysis_result
        
    except Exception as e:
        logging.error(f"Error during S3 analysis: {str(e)}")
        return None

def _prioritize_s3_recommendations(s3_data):
    """
    Helper function to prioritize S3 optimization recommendations by potential impact.
    """
    recommendations = []
    
    for bucket in s3_data['buckets']:
        bucket_name = bucket['name']
        bucket_size = bucket['size_gb']
        opportunities = bucket['optimization']['opportunities']
        
        for opportunity in opportunities:
            priority_score = _calculate_priority_score(bucket_size, opportunity)
            
            recommendation = {
                'bucket_name': bucket_name,
                'bucket_size_gb': bucket_size,
                'type': opportunity['type'],
                'description': opportunity['description'],
                'recommended_action': opportunity['recommended_action'],
                'potential_savings_percent': opportunity['potential_savings_percent'],
                'priority_score': priority_score,
                'priority_level': _get_priority_level(priority_score)
            }
            recommendations.append(recommendation)
    
    # Sort by priority score (highest first)
    recommendations.sort(key=lambda x: x['priority_score'], reverse=True)
    
    return recommendations

def _calculate_priority_score(bucket_size_gb, opportunity):
    """
    Calculate a priority score for an S3 optimization opportunity.
    Higher score = higher priority.
    """
    base_score = 0
    
    # Size factor (larger buckets get higher priority)
    if bucket_size_gb > 100:  # > 100GB
        base_score += 50
    elif bucket_size_gb > 10:  # > 10GB
        base_score += 30
    elif bucket_size_gb > 1:  # > 1GB
        base_score += 15
    else:
        base_score += 5
    
    # Savings potential factor
    savings_percent = opportunity.get('potential_savings_percent', 0)
    base_score += savings_percent
    
    # Opportunity type factor
    type_weights = {
        'deprecated_storage_class': 40,  # High priority - deprecated features
        'storage_class_optimization': 25,  # Medium-high priority
        'missing_lifecycle_policy': 20   # Medium priority
    }
    
    opportunity_type = opportunity.get('type', '')
    base_score += type_weights.get(opportunity_type, 10)
    
    return min(base_score, 100)  # Cap at 100

def _get_priority_level(priority_score):
    """
    Convert priority score to human-readable priority level.
    """
    if priority_score >= 80:
        return 'Critical'
    elif priority_score >= 60:
        return 'High'
    elif priority_score >= 40:
        return 'Medium'
    else:
        return 'Low'

def _calculate_s3_cost_impact(s3_data):
    """
    Calculate the potential cost impact of S3 optimizations.
    """
    total_potential_savings = 0
    savings_by_type = {}
    
    for bucket in s3_data['buckets']:
        bucket_savings = bucket['optimization']['potential_monthly_savings_usd']
        total_potential_savings += bucket_savings
        
        for opportunity in bucket['optimization']['opportunities']:
            opp_type = opportunity['type']
            if opp_type not in savings_by_type:
                savings_by_type[opp_type] = {
                    'count': 0,
                    'potential_savings': 0
                }
            savings_by_type[opp_type]['count'] += 1
            # Rough estimate based on bucket size and savings percentage
            estimated_savings = bucket['size_gb'] * 0.023 * (opportunity['potential_savings_percent'] / 100)
            savings_by_type[opp_type]['potential_savings'] += estimated_savings
    
    return {
        'total_monthly_savings_usd': round(total_potential_savings, 2),
        'annual_savings_usd': round(total_potential_savings * 12, 2),
        'savings_breakdown': savings_by_type,
        'roi_analysis': {
            'implementation_effort': 'Low to Medium',
            'time_to_savings': 'Immediate (within 24 hours)',
            'risk_level': 'Very Low'
        }
    }

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