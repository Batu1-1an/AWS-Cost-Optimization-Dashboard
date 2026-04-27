<div align="center">
  <h1>AWS Cost Optimization Dashboard</h1>
  <p><em>Real-time visibility into AWS spend, idle resources, and savings opportunities — served through a clean, interactive web dashboard.</em></p>
  <p>
    <img src="https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python" alt="Python 3.8+">
    <img src="https://img.shields.io/badge/Flask-3.x-lightgrey?style=flat-square&logo=flask" alt="Flask">
    <img src="https://img.shields.io/badge/boto3-AWS_SDK-orange?style=flat-square&logo=amazonaws" alt="boto3">
    <img src="https://img.shields.io/badge/Plotly.js-charts-3cb4e6?style=flat-square&logo=plotly" alt="Plotly.js">
    <img src="https://img.shields.io/badge/pytest-moto-009a4e?style=flat-square&logo=pytest" alt="pytest + moto">
    <img src="https://img.shields.io/badge/License-Apache_2.0-brightgreen?style=flat-square" alt="Apache 2.0">
  </p>
</div>

---

## Why This Dashboard?

Organizations waste an estimated **30–45%** of their cloud spend on underutilized resources, orphaned storage, and missing governance. AWS native consoles are powerful but fragmented — hopping between Cost Explorer, EC2, CloudWatch, S3, and Trusted Advisor makes it hard to see the full picture.

This dashboard consolidates the six most impactful cost-analysis signals into a single Flask web application. Point it at your account and get an instant, actionable view of where money is going and where it can be saved.

## Features

| Module | Detection Logic & Output |
|--------|--------------------------|
| **Cost Explorer** | 30-day spend breakdown by service via `ce:GetCostAndUsage`. Returns `{ServiceName: cost}`. Zero-cost services are filtered out automatically. |
| **Idle EC2 Detection** | Queries 14 days of CloudWatch `CPUUtilization` metrics for every running instance. Flags instances where avg CPU < 5% **and** max CPU < 10%. Returns instance ID, region, metrics, and a human-readable reason. |
| **Tag Governance** | Scans all EC2 instances (any state) and EBS volumes against a configurable required-tag list (default: `Project`, `Owner`). Returns resource ID, type, and the specific missing tags. |
| **EBS Optimization** | Discovers unattached (available) volumes wasting money, and gp2 volumes eligible for a no-cost gp3 upgrade. Returns size, region, and upgrade reason. |
| **S3 Optimization** | Analyzes every bucket for deprecated `REDUCED_REDUNDANCY` storage, missing lifecycle policies, and STANDARD→STANDARD_IA transition candidates. Scores each opportunity by priority (Critical / High / Medium / Low) and projects monthly and annual savings. |
| **Anomaly Detection** | Fetches 60 days of daily cost history from Cost Explorer. Compares the latest day against a rolling mean ± 2.5σ threshold. Flags spikes automatically with date, cost, average, and threshold details. |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AWS Account                                  │
│  ┌──────────┐  ┌─────────┐  ┌───────────┐  ┌──────────┐           │
│  │Cost      │  │EC2      │  │CloudWatch │  │S3        │           │
│  │Explorer  │  │Describe*│  │GetMetric  │  │List*     │           │
│  └────┬─────┘  └────┬────┘  └─────┬─────┘  └────┬─────┘           │
│       │              │             │              │                 │
└───────┼──────────────┼─────────────┼──────────────┼─────────────────┘
        │              │             │              │
        ▼              ▼             ▼              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  aws_connector.py  ───  boto3 Session / Client Factory              │
│       │                                                             │
│       ▼                                                             │
│  data_fetcher.py   ───  Raw API calls (CE, EC2, CW, S3)            │
│       │                                                             │
│       ▼                                                             │
│  analyzer.py       ───  Aggregation, anomaly math, scoring          │
│       │                                                             │
│       ▼                                                             │
│  app.py            ───  Flask routes (/) + (/api/*)                │
│       │                                                             │
└───────┼─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────┐
│  templates/index.html  ───  Server-rendered dashboard shell         │
│       +                                                             │
│  static/style.css     ───  Card layout, tables, badges              │
│  static/script.js     ───  Fetch + Plotly.js chart rendering        │
└─────────────────────────────────────────────────────────────────────┘
```

## Screenshots

<div align="center">
  <table>
    <tr>
      <td align="center"><strong>Cost Explorer</strong></td>
      <td align="center"><strong>Idle Instances</strong></td>
      <td align="center"><strong>S3 Optimization</strong></td>
    </tr>
    <tr>
      <td><img src="https://via.placeholder.com/320x200/1a1a2e/e94560?text=Cost+Explorer+Pie+Chart" alt="Cost Explorer" width="320"></td>
      <td><img src="https://via.placeholder.com/320x200/16213e/0f3460?text=Idle+EC2+Table" alt="Idle EC2" width="320"></td>
      <td><img src="https://via.placeholder.com/320x200/1a1a2e/e94560?text=S3+Priority+List" alt="S3 Optimization" width="320"></td>
    </tr>
    <tr>
      <td><em>Interactive Plotly.js pie chart breaking down spend by service</em></td>
      <td><em>Tabular view of chronically underutilized instances with CPU metrics</em></td>
      <td><em>Priority-scored recommendations with projected savings</em></td>
    </tr>
  </table>
</div>

## Quick Start

```bash
git clone https://github.com/Batu1-1an/AWS-Cost-Optimization-Dashboard.git
cd AWS-Cost-Optimization-Dashboard

python -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

echo "AWS_ACCESS_KEY_ID=AKIA..." >> .env
echo "AWS_SECRET_ACCESS_KEY=..." >> .env
echo "AWS_REGION=us-east-1" >> .env

python -m src.app
```

Open **http://127.0.0.1:5000** in your browser.

## Configuration

### IAM Policy (Minimum Required)

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

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AWS_ACCESS_KEY_ID` | Yes | — | IAM access key |
| `AWS_SECRET_ACCESS_KEY` | Yes | — | IAM secret key |
| `AWS_REGION` | No | `us-east-1` | Default region for API calls |
| `FLASK_DEBUG` | No | `False` | Enable Flask hot-reloading & verbose logging |

### Detection Thresholds

All tunable constants live at the top of `src/data_fetcher.py`:

| Constant | Default | Controls |
|----------|---------|----------|
| `IDLE_CHECK_PERIOD_DAYS` | `14` | CloudWatch metric lookback window |
| `IDLE_AVG_CPU_THRESHOLD` | `5.0` | Average CPU % below which an instance is flagged |
| `IDLE_MAX_CPU_THRESHOLD` | `10.0` | Maximum CPU % never exceeded for idle flag |
| `REQUIRED_TAGS` | `['Project', 'Owner']` | Tag keys checked by governance scanner |
| `std_dev_threshold` | `2.5` | Sigma multiplier in anomaly detection (`analyzer.py`) |
| `CW_PERIOD_SECONDS` | `86400` | CloudWatch metric aggregation period (24 h) |

## API Reference

| Endpoint | Method | Response |
|----------|--------|----------|
| `/` | `GET` | Dashboard HTML |
| `/api/cost-by-service` | `GET` | `{"ServiceName": cost, …}` |
| `/api/idle-instances` | `GET` | `[{"InstanceId", "Region", "AvgCPU", "MaxCPU", "Reason"}, …]` |
| `/api/untagged-resources` | `GET` | `{"Instances": […], "Volumes": […]}` |
| `/api/ebs-optimization` | `GET` | `{"UnattachedVolumes": […], "Gp2Volumes": […]}` |
| `/api/s3-optimization` | `GET` | `{"summary": {}, "buckets": […], "priority_recommendations": […], "cost_analysis": {}}` |
| `/api/cost-anomalies` | `GET` | `{"latest_date", "latest_cost", "is_anomaly", "average_cost", "std_dev", "threshold", …}` |

All API endpoints return `500 {"error": "..."}` on failure. Errors are logged server-side with `logging`.

## Testing

The entire test suite uses **moto** to mock AWS services — tests run with zero real credentials and incur **no AWS costs**.

```bash
python -m pytest -v
```

### Coverage

| Module | Tests | What's Covered |
|--------|-------|----------------|
| `test_utils.py` | 9 parametrized cases | Missing tags, empty sets, `None` input, case sensitivity |
| `test_data_fetcher.py` | Cost Explorer, EC2, EBS, S3, CloudWatch | Mocked responses, zero-cost filtering, pagination, error handling, empty accounts, mixed idle/active/no-metrics instances |
| `test_analyzer.py` | Analyzer orchestration | Success/failure passthrough, anomaly math (flagged, not flagged, insufficient data, fetch failure) |
| `test_app.py` | All 6 API routes + index | 200 success paths, 500 error paths for every endpoint |

## Project Structure

```
.
├── src/
│   ├── __init__.py
│   ├── app.py                  # Flask routes & entrypoint
│   ├── analyzer.py             # Analysis orchestration, anomaly detection, S3 scoring
│   ├── aws_connector.py        # boto3 session / client factory
│   ├── aws_regions.py          # Region constant list
│   ├── data_fetcher.py         # All AWS API calls (CE, EC2, CW, S3)
│   └── utils.py                # Tag-checking helper
├── static/
│   ├── style.css               # Dashboard layout (cards, tables, badges)
│   └── script.js               # Fetch logic & Plotly.js chart rendering
├── templates/
│   └── index.html              # Main dashboard shell
├── tests/
│   ├── __init__.py
│   ├── test_analyzer.py
│   ├── test_app.py
│   ├── test_data_fetcher.py
│   └── test_utils.py
├── .env                        # Credentials (gitignored — DO NOT COMMIT)
├── .gitignore
├── requirements.txt            # Python dependencies
├── PLAN.md                     # Original project plan
├── LICENSE                     # Apache 2.0
└── README.md
```

## License

Distributed under the **Apache License 2.0**. See [LICENSE](LICENSE) for the full text.

---

<div align="center">
  <sub>Built with Flask, boto3, and Plotly.js · Maintained by <a href="https://github.com/Batu1-1an">@Batu1-1an</a></sub>
  <br>
  <sub>Found an issue? <a href="https://github.com/Batu1-1an/AWS-Cost-Optimization-Dashboard/issues">Open a GitHub issue</a></sub>
</div>
