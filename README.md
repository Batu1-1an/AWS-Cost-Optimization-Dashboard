# AWS Cost Optimization Dashboard

## Description

This project provides a web-based dashboard to help visualize AWS costs and identify potential optimization opportunities within your AWS account. It fetches data using the AWS SDK (boto3) and presents it using Flask and Plotly.js.

## Features

*   **Cost Breakdown by Service:** Displays a pie chart showing the cost distribution across different AWS services for the last 30 days (by default).
*   **Idle EC2 Instance Identification:** Lists EC2 instances that have shown low average and maximum CPU utilization over a defined period (default: 14 days), suggesting they might be underutilized or idle.
*   **Untagged Resource Identification:** Lists EC2 instances and EBS volumes that are missing a predefined set of essential tags (e.g., 'Project', 'Owner'), aiding in cost allocation and resource management.
*   **EBS Volume Optimization Candidates:**
    *   Identifies unattached EBS volumes (state: 'available').
    *   Flags volumes using the older `gp2` type as potential candidates for migration to `gp3`.
*   **Cost Anomaly Detection:** Performs a basic daily cost anomaly check by comparing the latest day's cost against the average and standard deviation of the preceding period (default: 60 days history, 2.5 std dev threshold). Highlights potential unexpected cost spikes.
*   **Web Interface:** Simple dashboard built with Flask and rendered in your browser.

## Setup & Installation

### Prerequisites

*   Python 3.x (developed with 3.11, but should work with recent 3.x versions)
*   pip (Python package installer)
*   Git (for cloning, optional if you already have the code)

### Steps

1.  **Clone the Repository (Optional):**
    ```bash
    git clone https://github.com/Batu1-1an/AWS-Cost-Optimization-Dashboard.git
    cd AWS-Cost-Optimization-Dashboard
    ```

2.  **Create a Virtual Environment:**
    It's highly recommended to use a virtual environment to manage dependencies.
    ```bash
    python -m venv .venv
    ```

3.  **Activate the Virtual Environment:**
    *   **Windows (PowerShell/CMD):**
        ```powershell
        .\.venv\Scripts\Activate.ps1
        # or for CMD: .\.venv\Scripts\activate.bat
        ```
    *   **Linux/macOS (Bash/Zsh):**
        ```bash
        source .venv/bin/activate
        ```
    You should see `(.venv)` prefixed to your shell prompt.

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  **AWS Credentials:**
    *   Create a file named `.env` in the project's root directory.
    *   Add your AWS credentials and preferred region to this file:
        ```dotenv
        # AWS Credentials - Replace with your actual keys
        # Ensure this file is included in .gitignore and NEVER committed to version control!
        AWS_ACCESS_KEY_ID="YOUR_AWS_ACCESS_KEY_ID"
        AWS_SECRET_ACCESS_KEY="YOUR_AWS_SECRET_ACCESS_KEY"
        AWS_REGION="us-east-1" # Or your preferred default region
        ```
    *   **IMPORTANT:** The `.gitignore` file is configured to ignore `.env`. **Never commit your `.env` file containing credentials to version control.**

2.  **IAM Permissions:**
    The AWS IAM user or role associated with the credentials needs the following minimum permissions:
    *   `ce:GetCostAndUsage` (for Cost Explorer data)
    *   `ec2:DescribeInstances` (for EC2 instance details and tags)
    *   `ec2:DescribeVolumes` (for EBS volume details and tags)
    *   `cloudwatch:GetMetricStatistics` (for EC2 CPU utilization)

## Running the Application

1.  Ensure your virtual environment is activated.
2.  Make sure your `.env` file is configured correctly.
3.  Run the Flask development server:
    ```bash
    python app.py
    ```
4.  Open your web browser and navigate to `http://127.0.0.1:5000/` (or the URL provided in the terminal output).

## Running Tests

1.  Ensure your virtual environment is activated.
2.  Run the test suite using pytest:
    ```bash
    python -m pytest -v
    ```
    *   Tests use `moto` to mock AWS services, so they don't require live AWS credentials or incur costs.
    *   Some tests related to volume tagging might be marked as `xfail` (expected failure) due to potential state leakage issues in `moto`'s volume handling between tests.

## Project Structure

```
.
├── .git/               # Git repository data
├── .gitignore          # Specifies intentionally untracked files that Git should ignore
├── .pytest_cache/      # Pytest cache directory
├── __pycache__/        # Python bytecode cache
├── static/             # Static files (CSS, JavaScript)
│   ├── script.js       # Frontend JavaScript for fetching data and rendering charts/tables
│   └── style.css       # CSS for styling the dashboard
├── templates/          # HTML templates (rendered by Flask)
│   └── index.html      # Main dashboard HTML structure
├── tests/              # Unit and integration tests
│   ├── test_analyzer.py
│   ├── test_app.py
│   ├── test_data_fetcher.py
│   └── test_utils.py
├── .env                # Local environment variables (AWS credentials - DO NOT COMMIT)
├── PLAN.md             # Initial project plan outline
├── README.md           # This file
├── analyzer.py         # Contains functions for analyzing fetched data
├── app.py              # Main Flask application file (routes, server logic)
├── aws_connector.py    # Handles AWS session and client creation using Boto3
├── aws_regions.py      # List of AWS regions (currently informational)
├── data_fetcher.py     # Contains functions to fetch data from AWS APIs
├── requirements.txt    # Python package dependencies
└── utils.py            # Utility functions (e.g., tag checking)
```

## Future Enhancements

*   **Reserved Instance / Savings Plan Analysis:** Analyze RI/SP coverage, utilization, and potential savings.
*   **S3 Analysis:** Implement checks for S3 storage class optimization and lifecycle policies.
*   **Granular Filtering:** Add UI options to filter cost and resource data by tags, regions, instance types, etc.
*   **Extended Untagged Resources:** Scan additional resource types (RDS, S3, Load Balancers) for missing tags.
*   **Configuration File:** Move settings like `REQUIRED_TAGS`, anomaly thresholds, and idle criteria to a configuration file instead of hardcoding.
*   **More Robust Anomaly Detection:** Implement more sophisticated time-series analysis for anomaly detection.
*   **User Authentication:** Add user login/authentication if deploying for multiple users.
*   **Deployment:** Instructions/scripts for deploying to a server or cloud platform.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.