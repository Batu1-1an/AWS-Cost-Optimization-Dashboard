<div align="center">
  <h1>AWS Cost Optimization Dashboard</h1>
  <p>A Flask-powered web dashboard that analyzes your AWS account for cost-saving opportunities — idle instances, untagged resources, EBS and S3 optimization, and cost anomaly detection.</p>

  <p>
    <img src="https://img.shields.io/badge/python-3.8%2B-blue?style=flat&logo=python" alt="Python 3.8+">
    <img src="https://img.shields.io/badge/flask-3.x-lightgrey?style=flat&logo=flask" alt="Flask">
    <img src="https://img.shields.io/badge/boto3-AWS_SDK-orange?style=flat&logo=amazonaws" alt="boto3">
    <img src="https://img.shields.io/badge/plotly.js-charts-3cb4e6?style=flat&logo=plotly" alt="Plotly.js">
    <img src="https://img.shields.io/badge/tests-pytest%20%7C%20moto-green?style=flat" alt="pytest + moto">
    <img src="https://img.shields.io/badge/license-Apache--2.0-brightgreen?style=flat" alt="Apache 2.0">
  </p>
</div>

---

## Overview

Connect the dashboard to your AWS account and get an instant bird's-eye view of cost distribution, underutilized resources, governance gaps, and potential savings — all served through a clean web interface with interactive charts and tables.

| Module | What it does |
|--------|-------------|
| **Cost Explorer** | Breaks down spend by service (30-day lookback) |
| **Idle EC2 Detection** | Flags instances with chronically low CPU via CloudWatch metrics |
| **Tag Governance** | Scans EC2 + EBS for missing required tags |
| **EBS Optimization** | Finds unattached volumes and gp2→gp3 upgrade candidates |
| **S3 Optimization** | Analyzes storage classes, lifecycle policies, and savings potential |
| **Anomaly Detection** | Statistical spike detection (std-dev based) on daily cost history |

## Features

- **Interactive cost pie chart** — see which services drive your monthly bill
- **Idle instance table** — instances with avg CPU < 5 % and max CPU < 10 % over 14 days
- **Untagged resource scanner** — configurable required tags (`Project`, `Owner`, etc.)
- **EBS candidates dashboard** — unattached volumes + gp2 volumes flagged for upgrade
- **S3 storage analysis** — detects `REDUCED_REDUNDANCY` usage, missing lifecycle policies, and recommends `STANDARD_IA` transitions with priority scoring
- **Cost anomaly alerts** — compares latest daily cost against a rolling mean ± 2.5σ threshold
- **Fully mocked test suite** — `pytest` + `moto` means zero AWS cost during development

## Tech Stack

| Technology | Purpose |
|-----------|---------|
| [Python](https://python.org) 3.8+ | Runtime |
| [Flask](https://flask.palletsprojects.com) | Web framework & API |
| [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) | AWS SDK (Cost Explorer, EC2, CloudWatch, S3) |
| [Plotly.js](https://plotly.com/javascript/) | Client-side charts (pie, bar) |
| [pandas](https://pandas.pydata.org) | Data aggregation & metric analysis |
| [NumPy](https://numpy.org) | Standard deviation for anomaly detection |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Environment variable management |
| [pytest](https://pytest.org) | Test runner |
| [moto](https://github.com/getmoto/moto) | AWS API mocking for tests |

## Prerequisites

- Python 3.8 or later
- An AWS account with **Cost Explorer** enabled
- IAM credentials with the permissions listed below
- `pip` and `venv` available on your system

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/Batu1-1an/AWS-Cost-Optimization-Dashboard.git
cd AWS-Cost-Optimization-Dashboard

# 2. Create and activate a virtual environment
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

## Configuration

### Environment Variables

Create a `.env` file in the project root (it is already in `.gitignore`):

```dotenv
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1
```

If you prefer not to use a `.env` file, set the same variables in your shell environment.

### IAM Permissions

Attach the following minimum policy to the IAM user / role:

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
        "cloudwatch:GetMetricStatistics",
        "s3:ListAllMyBuckets",
        "s3:GetBucketLocation",
        "s3:ListBucket",
        "s3:GetBucketLifecycleConfiguration"
      ],
      "Resource": "*"
    }
  ]
}
```

### Tuning detection parameters

All thresholds live at the top of `data_fetcher.py`:

| Constant | Default | Controls |
|----------|---------|----------|
| `IDLE_CHECK_PERIOD_DAYS` | 14 | CloudWatch lookback window |
| `IDLE_AVG_CPU_THRESHOLD` | 5.0 | Average CPU % for idle flag |
| `IDLE_MAX_CPU_THRESHOLD` | 10.0 | Maximum CPU % for idle flag |
| `REQUIRED_TAGS` | `[Project, Owner]` | Tags checked by the governance scanner |
| `std_dev_threshold` | 2.5 | σ multiplier for anomaly detection (`analyze_cost_anomalies`) |

## Usage

Start the development server:

```bash
python -m src.app
```

Open **http://127.0.0.1:5000** in your browser.

### API Endpoints

| Endpoint | Method | Returns |
|----------|--------|---------|
| `/` | GET | Dashboard HTML |
| `/api/cost-by-service` | GET | `{ "ServiceName": cost, ... }` |
| `/api/idle-instances` | GET | `[ { InstanceId, Region, AvgCPU, Reason }, ... ]` |
| `/api/untagged-resources` | GET | `{ Instances: [...], Volumes: [...] }` |
| `/api/ebs-optimization` | GET | `{ UnattachedVolumes: [...], Gp2Volumes: [...] }` |
| `/api/s3-optimization` | GET | `{ summary, buckets, priority_recommendations, cost_analysis }` |
| `/api/cost-anomalies` | GET | `{ latest_date, latest_cost, is_anomaly, ... }` |

### Debug mode

Set `FLASK_DEBUG=True` in your `.env` to enable hot-reloading and verbose logging.

## Project Structure

```
.
├── src/
│   ├── __init__.py
│   ├── app.py                 # Flask routes & application entrypoint
│   ├── analyzer.py            # Analysis orchestration layer
│   ├── aws_connector.py       # boto3 session / client factory
│   ├── aws_regions.py         # AWS region constants
│   ├── data_fetcher.py        # AWS API calls (CE, EC2, CloudWatch, S3)
│   └── utils.py               # Shared helpers (tag checking)
├── static/
│   ├── style.css              # Dashboard styling (cards, tables, badges)
│   └── script.js              # Frontend logic (Plotly charts, table rendering)
├── templates/
│   └── index.html             # Main dashboard template
├── tests/
│   ├── __init__.py
│   ├── test_analyzer.py       # Unit tests for analysis logic
│   ├── test_app.py            # API endpoint integration tests
│   ├── test_data_fetcher.py   # Mocked AWS data-fetching tests
│   └── test_utils.py          # Utility function tests
├── .env                       # Credentials (DO NOT COMMIT)
├── .gitignore
├── requirements.txt           # Python dependencies
├── PLAN.md                    # Original project plan
├── LICENSE
└── README.md
```

## Testing

All tests use [moto](https://github.com/getmoto/moto) to mock AWS services, so they run **without real credentials or incurring any AWS cost**.

```bash
# From the project root with the virtual environment active
python -m pytest -v
```

Test coverage includes:

- **Cost Explorer** — mocked responses, zero-cost filtering, API error handling
- **Idle EC2** — mixed idle/active/no-metrics instances, empty accounts, pagination errors
- **Untagged resources** — fully/missing/no-tag instances and volumes, custom tag sets, empty accounts, API failures
- **EBS optimization** — unattached volumes, gp2 detection, root volumes, API errors
- **Daily cost history** — sorted results, zero-cost days, error handling
- **Cost anomaly detection** — anomaly flagged, anomaly not flagged, insufficient data, fetch failure
- **Utils** — parametrized tag-checking logic (9 cases covering missing tags, empty sets, case sensitivity)
- **App routes** — all 6 API endpoints tested for both success and failure, index route verified

## License

Distributed under the Apache License 2.0. See [LICENSE](LICENSE) for the full text.
