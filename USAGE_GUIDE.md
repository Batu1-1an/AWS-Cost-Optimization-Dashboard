# Usage Guide - AWS Cost Optimization Dashboard

## Table of Contents
- [Quick Start](#quick-start)
- [Step-by-Step Tutorials](#step-by-step-tutorials)
- [Common Use Cases](#common-use-cases)
- [Advanced Configurations](#advanced-configurations)
- [Integration Examples](#integration-examples)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Quick Start

### Prerequisites Checklist

Before you begin, ensure you have:

- [ ] **Python 3.7+** installed
- [ ] **AWS Account** with appropriate permissions
- [ ] **AWS CLI** configured (optional but recommended)
- [ ] **Git** for cloning the repository

### 5-Minute Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd aws-cost-dashboard

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your AWS credentials

# 5. Run the application
python app.py
```

### Environment Configuration

Create a `.env` file in the project root:

```env
# Required AWS Credentials
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1

# Optional Configuration
FLASK_ENV=development
FLASK_DEBUG=True
DASHBOARD_REFRESH_INTERVAL=300
LOG_LEVEL=INFO
```

### Verify Installation

1. Open your browser to `http://localhost:5000`
2. You should see the dashboard loading with widgets
3. Check that all widgets display data without errors

## Step-by-Step Tutorials

### Tutorial 1: First-Time Setup and AWS Permissions

#### Step 1: AWS IAM Setup

Create an IAM user with the following policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ce:GetCostAndUsage",
                "ce:GetRightsizingRecommendation",
                "ce:GetReservationCoverage",
                "ce:GetReservationPurchaseRecommendation",
                "ce:GetReservationUtilization",
                "ce:GetUsageReport"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeInstances",
                "ec2:DescribeVolumes",
                "ec2:DescribeRegions",
                "ec2:DescribeInstanceTypes"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "cloudwatch:GetMetricStatistics",
                "cloudwatch:ListMetrics"
            ],
            "Resource": "*"
        }
    ]
}
```

#### Step 2: Test Connectivity

```python
# test_aws_connection.py
from aws_connector import check_aws_connectivity

def main():
    print("Testing AWS connectivity...")
    checks, errors = check_aws_connectivity()
    
    if all(checks.values()):
        print("✅ All AWS services accessible!")
        return True
    else:
        print("❌ Some services are not accessible:")
        for service, status in checks.items():
            print(f"  {service}: {'✅' if status else '❌'}")
        
        if errors:
            print("\nErrors:")
            for error in errors:
                print(f"  - {error}")
        return False

if __name__ == "__main__":
    main()
```

Run the test:
```bash
python test_aws_connection.py
```

### Tutorial 2: Analyzing Your First Cost Report

#### Step 1: Understanding Cost Data

Access the cost analysis through the dashboard or programmatically:

```python
# cost_analysis_tutorial.py
from analyzer import analyze_cost_data, analyze_cost_anomalies
import json

def tutorial_cost_analysis():
    print("=== AWS Cost Analysis Tutorial ===\n")
    
    # 1. Get basic cost breakdown
    print("1. Fetching cost breakdown by service...")
    costs = analyze_cost_data(days=30)
    
    if costs:
        total_cost = sum(costs.values())
        print(f"   Total 30-day cost: ${total_cost:.2f}")
        print(f"   Number of services: {len(costs)}")
        
        # Show top 5 services
        top_services = sorted(costs.items(), key=lambda x: x[1], reverse=True)[:5]
        print("\n   Top 5 services by cost:")
        for service, cost in top_services:
            percentage = (cost / total_cost) * 100
            print(f"   • {service}: ${cost:.2f} ({percentage:.1f}%)")
    
    # 2. Anomaly detection
    print("\n2. Checking for cost anomalies...")
    anomalies = analyze_cost_anomalies(history_days=60)
    
    if anomalies:
        if anomalies['is_anomaly']:
            print("   ⚠️ Cost anomaly detected!")
            print(f"   Latest cost: ${anomalies['latest_cost']:.2f}")
            print(f"   Expected range: ${anomalies['threshold']:.2f}")
            print(f"   Deviation: {((anomalies['latest_cost'] / anomalies['threshold']) - 1) * 100:.1f}%")
        else:
            print("   ✅ No cost anomalies detected")
    
    # 3. Cost recommendations
    print("\n3. Cost optimization recommendations:")
    if costs:
        print("   Based on your cost data:")
        
        # Find expensive services for recommendations
        expensive_services = [s for s, c in costs.items() if c > total_cost * 0.1]
        if expensive_services:
            print(f"   • Focus on optimizing: {', '.join(expensive_services)}")
        
        # Check for small services that might be forgotten
        small_services = [s for s, c in costs.items() if c < 5 and c > 0]
        if small_services:
            print(f"   • Review necessity of: {', '.join(small_services[:3])}")

if __name__ == "__main__":
    tutorial_cost_analysis()
```

#### Step 2: Interpreting Results

The cost analysis will show:

- **Service Distribution**: Which AWS services are consuming the most budget
- **Anomaly Detection**: Unusual spending patterns that need investigation
- **Trend Analysis**: Whether costs are increasing or decreasing

### Tutorial 3: Identifying Idle Resources

#### Step 1: Basic Idle Instance Detection

```python
# idle_resources_tutorial.py
from analyzer import analyze_idle_instances, analyze_untagged_resources, analyze_ebs_optimization
from aws_regions import AWS_REGIONS

def tutorial_idle_resources():
    print("=== Idle Resources Detection Tutorial ===\n")
    
    # 1. Check idle instances in primary region
    print("1. Checking for idle EC2 instances...")
    idle_instances = analyze_idle_instances(region='us-east-1')
    
    if idle_instances:
        print(f"   Found {len(idle_instances)} potentially idle instances:")
        for instance in idle_instances[:3]:  # Show first 3
            print(f"   • {instance['InstanceId']}: {instance['AvgCPU']:.1f}% avg CPU")
            print(f"     Reason: {instance['Reason']}")
        
        # Calculate potential savings
        # Rough estimate: $0.05 per hour per instance
        potential_monthly_savings = len(idle_instances) * 0.05 * 24 * 30
        print(f"\n   💰 Potential monthly savings: ~${potential_monthly_savings:.2f}")
    else:
        print("   ✅ No idle instances found!")
    
    # 2. Check untagged resources
    print("\n2. Checking for untagged resources...")
    untagged = analyze_untagged_resources(region='us-east-1')
    
    if untagged:
        total_untagged = len(untagged['Instances']) + len(untagged['Volumes'])
        print(f"   Found {total_untagged} untagged resources:")
        print(f"   • Instances: {len(untagged['Instances'])}")
        print(f"   • Volumes: {len(untagged['Volumes'])}")
        
        if untagged['Instances']:
            print("   Sample untagged instances:")
            for instance in untagged['Instances'][:2]:
                print(f"   • {instance['ResourceId']}: Missing {instance['MissingTags']}")
    
    # 3. EBS optimization opportunities
    print("\n3. Checking EBS optimization opportunities...")
    ebs_opts = analyze_ebs_optimization(region='us-east-1')
    
    if ebs_opts:
        unattached_count = len(ebs_opts['UnattachedVolumes'])
        gp2_count = len(ebs_opts['Gp2Volumes'])
        
        print(f"   • Unattached volumes: {unattached_count}")
        print(f"   • GP2 volumes (upgrade candidates): {gp2_count}")
        
        # Calculate storage savings
        if ebs_opts['UnattachedVolumes']:
            total_unattached_size = sum(v['SizeGiB'] for v in ebs_opts['UnattachedVolumes'])
            monthly_cost = total_unattached_size * 0.10  # $0.10 per GB/month for GP2
            print(f"   💰 Potential savings from deleting unattached: ${monthly_cost:.2f}/month")

def tutorial_multi_region_analysis():
    print("\n=== Multi-Region Analysis ===\n")
    
    regions_to_check = ['us-east-1', 'us-west-2', 'eu-west-1']
    regional_summary = {}
    
    for region in regions_to_check:
        print(f"Analyzing {region}...")
        try:
            idle = analyze_idle_instances(region=region)
            untagged = analyze_untagged_resources(region=region)
            ebs = analyze_ebs_optimization(region=region)
            
            regional_summary[region] = {
                'idle_instances': len(idle) if idle else 0,
                'untagged_resources': (len(untagged['Instances']) + len(untagged['Volumes'])) if untagged else 0,
                'unattached_volumes': len(ebs['UnattachedVolumes']) if ebs else 0
            }
            print(f"   ✅ Complete")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            regional_summary[region] = None
    
    # Summary report
    print("\n=== Regional Summary ===")
    for region, data in regional_summary.items():
        if data:
            print(f"{region}:")
            print(f"   • Idle instances: {data['idle_instances']}")
            print(f"   • Untagged resources: {data['untagged_resources']}")
            print(f"   • Unattached volumes: {data['unattached_volumes']}")
        else:
            print(f"{region}: Analysis failed")

if __name__ == "__main__":
    tutorial_idle_resources()
    tutorial_multi_region_analysis()
```

## Common Use Cases

### Use Case 1: Monthly Cost Review

**Scenario**: CFO wants a monthly cost breakdown with recommendations

```python
# monthly_report.py
from analyzer import *
from datetime import datetime
import json

def generate_monthly_report():
    """Generate a comprehensive monthly cost report"""
    
    report_date = datetime.now().strftime("%Y-%m")
    report = {
        "report_date": report_date,
        "cost_analysis": {},
        "optimization_opportunities": {},
        "recommendations": [],
        "summary": {}
    }
    
    # 1. Cost Analysis
    costs = analyze_cost_data(days=30)
    if costs:
        total_cost = sum(costs.values())
        report["cost_analysis"] = {
            "total_cost": total_cost,
            "service_count": len(costs),
            "top_services": sorted(costs.items(), key=lambda x: x[1], reverse=True)[:10],
            "cost_distribution": costs
        }
    
    # 2. Anomaly Detection
    anomalies = analyze_cost_anomalies()
    if anomalies:
        report["cost_analysis"]["anomaly_detected"] = anomalies['is_anomaly']
        if anomalies['is_anomaly']:
            report["recommendations"].append({
                "type": "cost_spike",
                "priority": "high",
                "message": f"Cost spike detected: ${anomalies['latest_cost']:.2f} vs expected ${anomalies['threshold']:.2f}"
            })
    
    # 3. Optimization Opportunities
    idle_instances = analyze_idle_instances()
    if idle_instances:
        potential_savings = len(idle_instances) * 50  # Rough estimate
        report["optimization_opportunities"]["idle_instances"] = {
            "count": len(idle_instances),
            "estimated_monthly_savings": potential_savings
        }
        report["recommendations"].append({
            "type": "idle_instances",
            "priority": "medium",
            "message": f"Found {len(idle_instances)} idle instances. Potential savings: ${potential_savings}/month"
        })
    
    # 4. Compliance Check
    untagged = analyze_untagged_resources()
    if untagged:
        total_untagged = len(untagged['Instances']) + len(untagged['Volumes'])
        report["optimization_opportunities"]["untagged_resources"] = {
            "count": total_untagged,
            "instances": len(untagged['Instances']),
            "volumes": len(untagged['Volumes'])
        }
        
        if total_untagged > 10:
            report["recommendations"].append({
                "type": "compliance",
                "priority": "medium",
                "message": f"{total_untagged} resources are missing required tags"
            })
    
    # 5. Summary
    report["summary"] = {
        "total_recommendations": len(report["recommendations"]),
        "high_priority_items": len([r for r in report["recommendations"] if r["priority"] == "high"]),
        "potential_monthly_savings": sum([
            report["optimization_opportunities"].get("idle_instances", {}).get("estimated_monthly_savings", 0)
        ])
    }
    
    return report

def print_executive_summary(report):
    """Print an executive summary of the report"""
    
    print("=" * 60)
    print(f"AWS COST OPTIMIZATION REPORT - {report['report_date']}")
    print("=" * 60)
    
    if report["cost_analysis"]:
        cost = report["cost_analysis"]
        print(f"\n💰 COST SUMMARY")
        print(f"   Total Monthly Cost: ${cost['total_cost']:.2f}")
        print(f"   Active Services: {cost['service_count']}")
        
        if cost.get("anomaly_detected"):
            print("   ⚠️  Cost anomaly detected!")
    
    if report["optimization_opportunities"]:
        print(f"\n🎯 OPTIMIZATION OPPORTUNITIES")
        
        idle = report["optimization_opportunities"].get("idle_instances", {})
        if idle:
            print(f"   Idle Instances: {idle['count']} (${idle['estimated_monthly_savings']}/month potential savings)")
        
        untagged = report["optimization_opportunities"].get("untagged_resources", {})
        if untagged:
            print(f"   Untagged Resources: {untagged['count']} (compliance risk)")
    
    if report["recommendations"]:
        print(f"\n📋 RECOMMENDATIONS ({len(report['recommendations'])} items)")
        for i, rec in enumerate(report["recommendations"], 1):
            priority_icon = "🔴" if rec["priority"] == "high" else "🟡" if rec["priority"] == "medium" else "🟢"
            print(f"   {i}. {priority_icon} {rec['message']}")
    
    summary = report["summary"]
    print(f"\n📊 SUMMARY")
    print(f"   High Priority Items: {summary['high_priority_items']}")
    print(f"   Potential Monthly Savings: ${summary['potential_monthly_savings']}")
    print("=" * 60)

if __name__ == "__main__":
    report = generate_monthly_report()
    print_executive_summary(report)
    
    # Save detailed report
    with open(f"cost_report_{report['report_date']}.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\nDetailed report saved to: cost_report_{report['report_date']}.json")
```

### Use Case 2: Automated Cleanup Suggestions

**Scenario**: Automatically identify resources that can be safely cleaned up

```python
# cleanup_suggestions.py
from analyzer import *
from datetime import datetime, timedelta

def generate_cleanup_suggestions():
    """Generate automated cleanup suggestions with confidence scores"""
    
    suggestions = {
        "high_confidence": [],
        "medium_confidence": [],
        "manual_review": []
    }
    
    # 1. Unattached EBS Volumes (High confidence for cleanup)
    ebs_opts = analyze_ebs_optimization()
    if ebs_opts and ebs_opts['UnattachedVolumes']:
        for volume in ebs_opts['UnattachedVolumes']:
            suggestions["high_confidence"].append({
                "type": "unattached_volume",
                "resource_id": volume['ResourceId'],
                "region": volume['Region'],
                "size_gb": volume['SizeGiB'],
                "monthly_cost": volume['SizeGiB'] * 0.10,
                "action": "delete",
                "reason": "Volume has been unattached and unused"
            })
    
    # 2. Very idle instances (Medium confidence)
    idle_instances = analyze_idle_instances()
    if idle_instances:
        for instance in idle_instances:
            confidence = "high_confidence" if instance['AvgCPU'] < 1 else "medium_confidence"
            suggestions[confidence].append({
                "type": "idle_instance",
                "resource_id": instance['InstanceId'],
                "region": instance['Region'],
                "avg_cpu": instance['AvgCPU'],
                "action": "stop_or_terminate",
                "reason": f"Instance averaging {instance['AvgCPU']:.1f}% CPU usage"
            })
    
    # 3. GP2 to GP3 upgrades (Medium confidence)
    if ebs_opts and ebs_opts['Gp2Volumes']:
        for volume in ebs_opts['Gp2Volumes'][:10]:  # Limit to first 10
            suggestions["medium_confidence"].append({
                "type": "volume_upgrade",
                "resource_id": volume['ResourceId'],
                "region": volume['Region'],
                "size_gb": volume['SizeGiB'],
                "monthly_savings": volume['SizeGiB'] * 0.02,  # 20% savings
                "action": "upgrade_to_gp3",
                "reason": "GP3 offers better price/performance than GP2"
            })
    
    return suggestions

def print_cleanup_suggestions(suggestions):
    """Print formatted cleanup suggestions"""
    
    print("🧹 AWS RESOURCE CLEANUP SUGGESTIONS")
    print("=" * 50)
    
    for confidence_level, items in suggestions.items():
        if not items:
            continue
            
        print(f"\n{confidence_level.upper().replace('_', ' ')} ({len(items)} items)")
        print("-" * 30)
        
        total_savings = 0
        for item in items:
            if item['type'] == 'unattached_volume':
                print(f"🗑️  Delete Volume {item['resource_id']}")
                print(f"    Region: {item['region']}")
                print(f"    Size: {item['size_gb']} GB")
                print(f"    Monthly savings: ${item['monthly_cost']:.2f}")
                total_savings += item['monthly_cost']
                
            elif item['type'] == 'idle_instance':
                print(f"⏹️  Stop Instance {item['resource_id']}")
                print(f"    Region: {item['region']}")
                print(f"    CPU Usage: {item['avg_cpu']:.1f}%")
                print(f"    Reason: {item['reason']}")
                
            elif item['type'] == 'volume_upgrade':
                print(f"⬆️  Upgrade Volume {item['resource_id']}")
                print(f"    Region: {item['region']}")
                print(f"    GP2 → GP3 savings: ${item['monthly_savings']:.2f}/month")
                total_savings += item['monthly_savings']
            
            print()
        
        if total_savings > 0:
            print(f"💰 Total potential savings for this category: ${total_savings:.2f}/month")

def generate_cleanup_script(suggestions):
    """Generate AWS CLI commands for cleanup actions"""
    
    script_lines = [
        "#!/bin/bash",
        "# Auto-generated AWS cleanup script",
        f"# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "# WARNING: Review these commands carefully before executing!",
        "# Uncomment lines you want to execute",
        ""
    ]
    
    for confidence_level, items in suggestions.items():
        if not items:
            continue
            
        script_lines.append(f"# {confidence_level.upper()} suggestions")
        
        for item in items:
            if item['type'] == 'unattached_volume':
                script_lines.append(
                    f"# aws ec2 delete-volume --volume-id {item['resource_id']} --region {item['region']}"
                )
            elif item['type'] == 'idle_instance':
                script_lines.append(
                    f"# aws ec2 stop-instances --instance-ids {item['resource_id']} --region {item['region']}"
                )
            elif item['type'] == 'volume_upgrade':
                script_lines.append(
                    f"# aws ec2 modify-volume --volume-id {item['resource_id']} --volume-type gp3 --region {item['region']}"
                )
        
        script_lines.append("")
    
    return "\n".join(script_lines)

if __name__ == "__main__":
    suggestions = generate_cleanup_suggestions()
    print_cleanup_suggestions(suggestions)
    
    # Generate cleanup script
    script = generate_cleanup_script(suggestions)
    with open("cleanup_script.sh", "w") as f:
        f.write(script)
    
    print(f"\n📜 Cleanup script generated: cleanup_script.sh")
    print("   Review the script carefully before executing any commands!")
```

### Use Case 3: Cost Budget Alerts

**Scenario**: Set up automated cost monitoring with alerts

```python
# budget_monitor.py
from analyzer import analyze_cost_data, analyze_cost_anomalies
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import os

class BudgetMonitor:
    def __init__(self, monthly_budget=1000, alert_thresholds=[50, 80, 90]):
        self.monthly_budget = monthly_budget
        self.alert_thresholds = alert_thresholds  # Percentage thresholds
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'email': os.getenv('ALERT_EMAIL'),
            'password': os.getenv('ALERT_EMAIL_PASSWORD'),
            'recipients': os.getenv('ALERT_RECIPIENTS', '').split(',')
        }
    
    def check_budget_status(self):
        """Check current spending against budget"""
        
        # Get current month's spending (projected)
        costs = analyze_cost_data(days=30)
        if not costs:
            return None
        
        current_spend = sum(costs.values())
        
        # Project monthly spend based on current day of month
        from datetime import datetime
        current_day = datetime.now().day
        days_in_month = 30  # Simplified
        projected_monthly = (current_spend / current_day) * days_in_month
        
        budget_used_percent = (projected_monthly / self.monthly_budget) * 100
        
        status = {
            'current_spend': current_spend,
            'projected_monthly': projected_monthly,
            'budget': self.monthly_budget,
            'budget_used_percent': budget_used_percent,
            'days_elapsed': current_day,
            'alert_level': self._get_alert_level(budget_used_percent)
        }
        
        return status
    
    def _get_alert_level(self, percent_used):
        """Determine alert level based on percentage used"""
        if percent_used >= 90:
            return 'critical'
        elif percent_used >= 80:
            return 'warning'
        elif percent_used >= 50:
            return 'info'
        else:
            return 'ok'
    
    def check_anomalies(self):
        """Check for spending anomalies"""
        return analyze_cost_anomalies()
    
    def send_alert(self, status, anomaly_data=None):
        """Send email alert if thresholds are exceeded"""
        
        if status['alert_level'] == 'ok':
            return False
        
        subject = f"AWS Budget Alert - {status['alert_level'].upper()}"
        
        # Create email content
        body = f"""
AWS Cost Budget Alert

Current Status:
• Budget: ${self.monthly_budget:.2f}
• Current Spend: ${status['current_spend']:.2f}
• Projected Monthly: ${status['projected_monthly']:.2f}
• Budget Used: {status['budget_used_percent']:.1f}%
• Alert Level: {status['alert_level'].upper()}

Days elapsed in month: {status['days_elapsed']}
"""
        
        if anomaly_data and anomaly_data['is_anomaly']:
            body += f"""
⚠️ COST ANOMALY DETECTED:
• Latest daily cost: ${anomaly_data['latest_cost']:.2f}
• Expected range: ${anomaly_data['threshold']:.2f}
• Deviation: {((anomaly_data['latest_cost']/anomaly_data['threshold'])-1)*100:.1f}%
"""
        
        body += """
Recommendations:
1. Review your AWS Cost Explorer for detailed breakdown
2. Check for unexpected resource usage
3. Consider implementing cost controls if needed

Dashboard: http://your-dashboard-url.com
"""
        
        return self._send_email(subject, body)
    
    def _send_email(self, subject, body):
        """Send email using SMTP"""
        
        if not all([self.email_config['email'], self.email_config['password']]):
            print("Email credentials not configured")
            return False
        
        try:
            msg = MimeMultipart()
            msg['From'] = self.email_config['email']
            msg['To'] = ', '.join(self.email_config['recipients'])
            msg['Subject'] = subject
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['email'], self.email_config['password'])
            
            text = msg.as_string()
            server.sendmail(self.email_config['email'], self.email_config['recipients'], text)
            server.quit()
            
            print(f"Alert email sent to {len(self.email_config['recipients'])} recipients")
            return True
            
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    def run_monitoring_check(self):
        """Run complete monitoring check"""
        
        print("Running budget monitoring check...")
        
        # Check budget status
        status = self.check_budget_status()
        if not status:
            print("Could not retrieve cost data")
            return
        
        print(f"Budget Status: {status['alert_level'].upper()}")
        print(f"Projected monthly spend: ${status['projected_monthly']:.2f}")
        print(f"Budget used: {status['budget_used_percent']:.1f}%")
        
        # Check for anomalies
        anomaly_data = self.check_anomalies()
        if anomaly_data and anomaly_data['is_anomaly']:
            print("⚠️ Cost anomaly detected!")
        
        # Send alerts if needed
        if status['alert_level'] != 'ok':
            self.send_alert(status, anomaly_data)

# Usage example
if __name__ == "__main__":
    # Set up monitoring with $1000 monthly budget
    monitor = BudgetMonitor(monthly_budget=1000)
    monitor.run_monitoring_check()
```

## Advanced Configurations

### Custom Metrics and Thresholds

```python
# custom_config.py
import os

class CustomConfig:
    """Advanced configuration for custom deployments"""
    
    # Idle Instance Detection
    IDLE_DETECTION = {
        'check_period_days': int(os.getenv('IDLE_CHECK_DAYS', '14')),
        'cpu_thresholds': {
            'conservative': {'avg': 10.0, 'max': 20.0},
            'standard': {'avg': 5.0, 'max': 10.0},
            'aggressive': {'avg': 2.0, 'max': 5.0}
        },
        'additional_metrics': ['NetworkIn', 'NetworkOut', 'DiskReadOps', 'DiskWriteOps'],
        'confidence_scoring': True
    }
    
    # Cost Anomaly Detection
    ANOMALY_DETECTION = {
        'history_days': int(os.getenv('ANOMALY_HISTORY_DAYS', '60')),
        'std_dev_threshold': float(os.getenv('ANOMALY_STD_DEV', '2.5')),
        'minimum_cost_threshold': float(os.getenv('MIN_COST_THRESHOLD', '10.0')),
        'detection_methods': ['statistical', 'trend_based', 'pattern_recognition']
    }
    
    # Tagging Requirements
    TAGGING_REQUIREMENTS = {
        'required_tags': os.getenv('REQUIRED_TAGS', 'Project,Owner,Environment').split(','),
        'optional_tags': os.getenv('OPTIONAL_TAGS', 'CostCenter,Department').split(','),
        'exempted_resources': os.getenv('TAG_EXEMPTIONS', '').split(','),
        'auto_tag_defaults': {
            'CreatedBy': 'CostDashboard',
            'LastChecked': lambda: datetime.now().isoformat()
        }
    }
    
    # Regional Configuration
    REGIONAL_CONFIG = {
        'primary_regions': os.getenv('PRIMARY_REGIONS', 'us-east-1,us-west-2').split(','),
        'secondary_regions': os.getenv('SECONDARY_REGIONS', 'eu-west-1,ap-southeast-1').split(','),
        'excluded_regions': os.getenv('EXCLUDED_REGIONS', '').split(','),
        'region_specific_thresholds': {
            'us-east-1': {'idle_cpu_threshold': 5.0},
            'eu-west-1': {'idle_cpu_threshold': 3.0}  # More aggressive in EU
        }
    }
    
    # Dashboard Configuration
    DASHBOARD_CONFIG = {
        'refresh_interval': int(os.getenv('REFRESH_INTERVAL', '300')),  # seconds
        'cache_ttl': int(os.getenv('CACHE_TTL', '60')),  # seconds
        'max_table_rows': int(os.getenv('MAX_TABLE_ROWS', '100')),
        'enable_real_time': os.getenv('ENABLE_REAL_TIME', 'true').lower() == 'true',
        'theme': os.getenv('DASHBOARD_THEME', 'light')
    }

def apply_custom_config():
    """Apply custom configuration to the application"""
    
    # Update data_fetcher constants
    import data_fetcher
    config = CustomConfig()
    
    # Apply idle detection config
    profile = os.getenv('IDLE_PROFILE', 'standard')
    if profile in config.IDLE_DETECTION['cpu_thresholds']:
        thresholds = config.IDLE_DETECTION['cpu_thresholds'][profile]
        data_fetcher.IDLE_AVG_CPU_THRESHOLD = thresholds['avg']
        data_fetcher.IDLE_MAX_CPU_THRESHOLD = thresholds['max']
    
    data_fetcher.IDLE_CHECK_PERIOD_DAYS = config.IDLE_DETECTION['check_period_days']
    
    # Apply tagging config
    data_fetcher.REQUIRED_TAGS = config.TAGGING_REQUIREMENTS['required_tags']
    
    print(f"Configuration applied:")
    print(f"  Idle profile: {profile}")
    print(f"  Required tags: {config.TAGGING_REQUIREMENTS['required_tags']}")
    print(f"  Check period: {config.IDLE_DETECTION['check_period_days']} days")

if __name__ == "__main__":
    apply_custom_config()
```

### Multi-Account Setup

```python
# multi_account_setup.py
from aws_connector import get_cross_account_client
import json

class MultiAccountAnalyzer:
    def __init__(self, accounts_config_file):
        with open(accounts_config_file, 'r') as f:
            self.accounts = json.load(f)
    
    def analyze_all_accounts(self):
        """Analyze costs across all configured accounts"""
        
        results = {}
        
        for account in self.accounts:
            account_id = account['account_id']
            account_name = account['name']
            role_name = account['role_name']
            
            print(f"Analyzing account: {account_name} ({account_id})")
            
            try:
                # Get Cost Explorer client for this account
                ce_client = get_cross_account_client('ce', account_id, role_name)
                
                if ce_client:
                    # Get cost data using the cross-account client
                    costs = self._get_account_costs(ce_client)
                    results[account_name] = {
                        'account_id': account_id,
                        'costs': costs,
                        'status': 'success'
                    }
                else:
                    results[account_name] = {
                        'account_id': account_id,
                        'status': 'failed',
                        'error': 'Could not assume role'
                    }
                    
            except Exception as e:
                results[account_name] = {
                    'account_id': account_id,
                    'status': 'failed',
                    'error': str(e)
                }
        
        return results
    
    def _get_account_costs(self, ce_client):
        """Get cost data for a specific account"""
        from datetime import datetime, timedelta
        
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
        
        costs = {}
        for result in response.get('ResultsByTime', []):
            for group in result.get('Groups', []):
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                if cost > 0:
                    costs[service] = costs.get(service, 0) + cost
        
        return costs

# accounts_config.json example:
accounts_config_example = {
    "accounts": [
        {
            "account_id": "123456789012",
            "name": "Production",
            "role_name": "CostAnalysisRole",
            "primary_region": "us-east-1"
        },
        {
            "account_id": "123456789013", 
            "name": "Development",
            "role_name": "CostAnalysisRole",
            "primary_region": "us-west-2"
        },
        {
            "account_id": "123456789014",
            "name": "Staging", 
            "role_name": "CostAnalysisRole",
            "primary_region": "us-east-1"
        }
    ]
}
```

## Integration Examples

### Slack Integration

```python
# slack_integration.py
import requests
import json
from datetime import datetime

class SlackNotifier:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
    
    def send_cost_alert(self, cost_data, threshold_exceeded=False):
        """Send cost alert to Slack"""
        
        total_cost = sum(cost_data.values()) if cost_data else 0
        top_services = sorted(cost_data.items(), key=lambda x: x[1], reverse=True)[:3]
        
        color = "danger" if threshold_exceeded else "good"
        
        message = {
            "attachments": [
                {
                    "color": color,
                    "title": "🏦 AWS Cost Report",
                    "fields": [
                        {
                            "title": "Total Monthly Cost",
                            "value": f"${total_cost:.2f}",
                            "short": True
                        },
                        {
                            "title": "Top Services",
                            "value": "\n".join([f"• {svc}: ${cost:.2f}" for svc, cost in top_services]),
                            "short": True
                        }
                    ],
                    "footer": "AWS Cost Dashboard",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }
        
        response = requests.post(self.webhook_url, json=message)
        return response.status_code == 200
    
    def send_optimization_alert(self, idle_instances, untagged_resources):
        """Send optimization opportunities to Slack"""
        
        message = {
            "text": "🎯 AWS Optimization Opportunities Found!",
            "attachments": [
                {
                    "color": "warning",
                    "fields": [
                        {
                            "title": "Idle Instances",
                            "value": f"{len(idle_instances)} instances found",
                            "short": True
                        },
                        {
                            "title": "Untagged Resources", 
                            "value": f"{len(untagged_resources.get('Instances', [])) + len(untagged_resources.get('Volumes', []))} resources",
                            "short": True
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(self.webhook_url, json=message)
        return response.status_code == 200
```

### Terraform Integration

```hcl
# terraform/aws-cost-dashboard.tf
# IAM Role for the Cost Dashboard
resource "aws_iam_role" "cost_dashboard_role" {
  name = "CostDashboardRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for Cost Dashboard
resource "aws_iam_policy" "cost_dashboard_policy" {
  name        = "CostDashboardPolicy"
  description = "Policy for AWS Cost Dashboard"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ce:GetCostAndUsage",
          "ce:GetRightsizingRecommendation",
          "ce:GetReservationCoverage",
          "ce:GetReservationPurchaseRecommendation",
          "ce:GetReservationUtilization",
          "ce:GetUsageReport"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:DescribeVolumes", 
          "ec2:DescribeRegions",
          "ec2:DescribeInstanceTypes"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:ListMetrics"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach policy to role
resource "aws_iam_role_policy_attachment" "cost_dashboard_policy_attachment" {
  role       = aws_iam_role.cost_dashboard_role.name
  policy_arn = aws_iam_policy.cost_dashboard_policy.arn
}

# EC2 Instance for hosting the dashboard
resource "aws_instance" "cost_dashboard" {
  ami           = "ami-0c55b159cbfafe1d0"  # Amazon Linux 2
  instance_type = "t3.micro"
  
  iam_instance_profile = aws_iam_instance_profile.cost_dashboard_profile.name
  
  vpc_security_group_ids = [aws_security_group.cost_dashboard_sg.id]
  
  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    app_repo = var.github_repo_url
  }))
  
  tags = {
    Name = "AWS Cost Dashboard"
    Project = "CostOptimization"
    Environment = var.environment
  }
}

# Security Group
resource "aws_security_group" "cost_dashboard_sg" {
  name_prefix = "cost-dashboard-"
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Instance Profile
resource "aws_iam_instance_profile" "cost_dashboard_profile" {
  name = "cost-dashboard-profile"
  role = aws_iam_role.cost_dashboard_role.name
}
```

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: "Failed to retrieve cost data"

**Symptoms:**
- Cost chart shows error message
- API returns 500 error

**Solutions:**
```bash
# 1. Check AWS credentials
python -c "
from aws_connector import get_aws_session
session = get_aws_session()
if session:
    print('✅ Session OK')
    sts = session.client('sts')
    identity = sts.get_caller_identity()
    print(f'Identity: {identity}')
else:
    print('❌ Session failed')
"

# 2. Test Cost Explorer permissions
python -c "
from aws_connector import get_client
from datetime import datetime, timedelta
ce_client = get_client('ce')
if ce_client:
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost']
        )
        print('✅ Cost Explorer access OK')
    except Exception as e:
        print(f'❌ Cost Explorer error: {e}')
"

# 3. Check IAM permissions
aws iam simulate-principal-policy \
    --policy-source-arn $(aws sts get-caller-identity --query Arn --output text) \
    --action-names ce:GetCostAndUsage \
    --resource-arns "*"
```

#### Issue 2: "No idle instances found" (when you expect some)

**Diagnosis:**
```python
# debug_idle_detection.py
from data_fetcher import get_idle_ec2_instances, get_client
import pandas as pd
from datetime import datetime, timedelta

def debug_idle_detection(region='us-east-1'):
    print(f"Debugging idle detection in {region}...")
    
    # 1. Check if there are running instances
    ec2_client = get_client('ec2', region_name=region)
    if not ec2_client:
        print("❌ Cannot get EC2 client")
        return
    
    try:
        response = ec2_client.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        
        running_instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                running_instances.append(instance['InstanceId'])
        
        print(f"✅ Found {len(running_instances)} running instances")
        
        if not running_instances:
            print("No running instances to analyze")
            return
        
        # 2. Check CloudWatch metrics for first instance
        cw_client = get_client('cloudwatch', region_name=region)
        if not cw_client:
            print("❌ Cannot get CloudWatch client")
            return
        
        test_instance = running_instances[0]
        print(f"Testing metrics for instance: {test_instance}")
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=14)
        
        response = cw_client.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'InstanceId', 'Value': test_instance}],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,  # 1 day
            Statistics=['Average', 'Maximum']
        )
        
        datapoints = response.get('Datapoints', [])
        print(f"✅ Found {len(datapoints)} CloudWatch datapoints")
        
        if datapoints:
            df = pd.DataFrame(datapoints)
            avg_cpu = df['Average'].mean()
            max_cpu = df['Maximum'].max()
            print(f"Instance {test_instance}:")
            print(f"  Average CPU: {avg_cpu:.2f}%")
            print(f"  Maximum CPU: {max_cpu:.2f}%")
            
            # Check thresholds
            from data_fetcher import IDLE_AVG_CPU_THRESHOLD, IDLE_MAX_CPU_THRESHOLD
            print(f"Thresholds: avg < {IDLE_AVG_CPU_THRESHOLD}%, max < {IDLE_MAX_CPU_THRESHOLD}%")
            
            is_idle = avg_cpu < IDLE_AVG_CPU_THRESHOLD and max_cpu < IDLE_MAX_CPU_THRESHOLD
            print(f"Would be classified as idle: {is_idle}")
        else:
            print("❌ No CloudWatch data available")
            print("Possible causes:")
            print("  - Instance is too new (< 24 hours)")
            print("  - CloudWatch agent not running")
            print("  - Metrics not enabled")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_idle_detection()
```

#### Issue 3: Dashboard not loading/blank page

**Diagnosis:**
```bash
# Check Flask application
python -c "
import app
print('Flask app imported successfully')
try:
    with app.app.test_client() as client:
        response = client.get('/')
        print(f'Homepage status: {response.status_code}')
        
        response = client.get('/api/cost-by-service')
        print(f'API status: {response.status_code}')
except Exception as e:
    print(f'Error: {e}')
"

# Check static files
ls -la static/
curl -I http://localhost:5000/static/style.css
curl -I http://localhost:5000/static/script.js

# Check browser console for JavaScript errors
# Open browser dev tools (F12) and look for errors in console
```

## Best Practices

### Security Best Practices

1. **Use IAM Roles instead of hardcoded credentials**
```python
# Good: Use IAM roles
session = boto3.Session()
client = session.client('ec2')

# Avoid: Hardcoded credentials
# client = boto3.client('ec2', 
#     aws_access_key_id='AKIA...',
#     aws_secret_access_key='...'
# )
```

2. **Implement least privilege access**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ce:GetCostAndUsage",
                "ec2:DescribeInstances",
                "cloudwatch:GetMetricStatistics"
            ],
            "Resource": "*"
        }
    ]
}
```

3. **Secure the dashboard**
```python
# Add authentication middleware
from flask import request, abort
import os

def require_auth():
    api_key = request.headers.get('X-API-Key')
    if api_key != os.getenv('DASHBOARD_API_KEY'):
        abort(401)

@app.before_request
def before_request():
    if request.endpoint and request.endpoint.startswith('api_'):
        require_auth()
```

### Performance Best Practices

1. **Implement caching**
```python
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=128)
def cached_cost_data(days, cache_key):
    return get_cost_by_service(days=days)

def get_cached_cost_data(days=30):
    # Cache key changes every hour
    cache_key = datetime.now().strftime('%Y%m%d%H')
    return cached_cost_data(days, cache_key)
```

2. **Use async operations for multiple regions**
```python
import asyncio
import concurrent.futures

async def analyze_multiple_regions_async(regions):
    loop = asyncio.get_event_loop()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        tasks = [
            loop.run_in_executor(executor, analyze_idle_instances, region)
            for region in regions
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
    return dict(zip(regions, results))
```

3. **Optimize API calls**
```python
# Batch API calls when possible
def get_multiple_metrics(instance_ids, region):
    cw_client = get_client('cloudwatch', region_name=region)
    
    # Use batch requests instead of individual calls
    batch_size = 20
    results = {}
    
    for i in range(0, len(instance_ids), batch_size):
        batch = instance_ids[i:i + batch_size]
        # Process batch...
        
    return results
```

### Monitoring Best Practices

1. **Set up health checks**
```python
@app.route('/health')
def health_check():
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'checks': {}
    }
    
    # Check AWS connectivity
    try:
        session = get_aws_session()
        health_status['checks']['aws_session'] = bool(session)
    except:
        health_status['checks']['aws_session'] = False
        health_status['status'] = 'unhealthy'
    
    return jsonify(health_status)
```

2. **Implement logging**
```python
import logging
import sys

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cost_dashboard.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Use throughout application
logger.info("Starting cost analysis", extra={'region': region, 'days': days})
```

3. **Monitor performance metrics**
```python
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} completed in {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.2f}s: {e}")
            raise
    return wrapper

@monitor_performance
def analyze_cost_data(days=30):
    # Function implementation...
```

This comprehensive usage guide provides practical examples and best practices for effectively using the AWS Cost Optimization Dashboard in various scenarios and environments.