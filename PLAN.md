# Project: AWS Cost Optimization Dashboard

**Goal:** Develop a web application that connects to AWS, fetches cost and resource utilization data, analyzes it to show cost breakdowns by service and identify potentially idle EC2 instances, and presents this information via a web dashboard.

**Core Components & Workflow:**

1.  **Project Setup:**
    *   Standard Python project structure (modules, templates, static files).
    *   Virtual environment for dependency management.
    *   `requirements.txt` listing necessary libraries (`boto3`, `Flask` (or `FastAPI`), `plotly`/`Chart.js`, `python-dotenv`, `pytest`, `moto`).
    *   Initialize Git repository.

2.  **AWS Interaction (`aws_connector.py`):**
    *   Securely handle AWS credentials (environment variables strongly recommended via `.env` file and `python-dotenv`). **No hardcoded keys.**
    *   Use `boto3` to establish sessions with necessary AWS services (Cost Explorer, EC2, CloudWatch).

3.  **Data Fetching (`data_fetcher.py`):**
    *   **Cost per Service:** Query AWS Cost Explorer API (`get_cost_and_usage`) grouping by `SERVICE` for a defined period (e.g., last 30 days).
    *   **Idle EC2 Identification:**
        *   Fetch all running EC2 instances (`describe_instances`).
        *   For each instance, fetch relevant CloudWatch metrics (e.g., `CPUUtilization`, potentially `NetworkIn`/`NetworkOut`) over a recent period (e.g., 14 days).
        *   *Initial Idle Criteria (Example):* Average `CPUUtilization` < 5% AND Maximum `CPUUtilization` < 10% over the period. (This can be refined).

4.  **Analysis (`analyzer.py`):**
    *   Process data returned by the fetcher.
    *   Aggregate costs per service.
    *   Apply the idle criteria logic to the EC2 instance metrics to generate a list of potentially idle instances.
    *   Format results for easy consumption by the web application.

5.  **Web Application (`app.py`):**
    *   Use Flask (or FastAPI) as the web framework.
    *   Define routes:
        *   `/`: Main dashboard view.
        *   `/api/cost-by-service`: Endpoint to provide data for the service cost chart.
        *   `/api/idle-instances`: Endpoint to provide data for the idle instances table.
    *   Use Jinja2 templates (if Flask) to render HTML.

6.  **Frontend (`templates/`, `static/`):**
    *   HTML templates for the dashboard layout.
    *   CSS for basic styling.
    *   JavaScript using a charting library (like Plotly.js or Chart.js) to fetch data from the API endpoints and render visualizations (e.g., pie chart for costs, table for idle instances).

7.  **Testing (`tests/`):**
    *   **Unit Tests:**
        *   Focus on testing individual functions within `analyzer.py` and potentially helper functions in `data_fetcher.py` and `aws_connector.py`.
        *   Use a testing framework like `pytest`.
        *   Mock AWS calls using libraries like `moto` to simulate AWS responses without needing actual credentials or incurring costs during tests. This allows testing the logic of data processing and analysis in isolation.
        *   Test edge cases and different data scenarios for the analysis logic (e.g., no idle instances found, various cost distributions).
    *   **Integration Tests:**
        *   Test the interaction between components, particularly the flow from API endpoints in `app.py` through the `analyzer` and `data_fetcher`.
        *   Can also use `moto` to mock the AWS backend for controlled integration tests.
        *   Test API endpoint responses for correctness based on mocked data.
    *   **Setup:** Add `pytest` and `moto` to `requirements.txt`. Create a `tests/` directory.

**High-Level Flow Diagram:**

```mermaid
graph TD
    A[User -> Browser] --> B[Web App (Flask/FastAPI)];
    B --> C{API Routes};
    C -- Request Data --> D[Analyzer];
    D --> E[Data Fetcher];
    E -- Uses Credentials --> F[AWS Connector (boto3)];
    F -- Calls --> G[AWS APIs (Cost Explorer, EC2, CloudWatch)];
    G -- Returns Data --> F;
    F -- Raw Data --> E;
    E -- Processed Data --> D;
    D -- Formatted Data --> C;
    C -- JSON Data --> H[Frontend JS (Charts/Tables)];
    H -- Renders --> A;

    subgraph Python Backend
        B; C; D; E; F;
    end

    subgraph AWS Cloud
        G;
    end

    subgraph User Interface
        A; H;
    end

    subgraph Testing [Testing (pytest, moto)]
        T1[Unit Tests] --> D;
        T1 --> E;
        T2[Integration Tests] --> C;
        T2 --> D;
        T2 --> E;
    end

    style Testing fill:#f9f,stroke:#333,stroke-width:2px