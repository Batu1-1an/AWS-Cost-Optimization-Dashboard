# AWS Cost Optimization Dashboard

A comprehensive Flask-based web application for monitoring and optimizing AWS costs. This dashboard provides real-time insights into your AWS spending, identifies cost optimization opportunities, and helps you maintain control over your cloud expenses.

## 🚀 Features

- **💰 Cost Analysis**: Real-time cost breakdown by AWS service with trend analysis
- **🔍 Idle Resource Detection**: Identify underutilized EC2 instances based on CloudWatch metrics
- **🏷️ Compliance Monitoring**: Find resources missing required tags
- **💾 EBS Optimization**: Discover unattached volumes and GP2→GP3 upgrade opportunities
- **📊 Anomaly Detection**: Statistical analysis to detect unusual spending patterns
- **📈 Interactive Dashboard**: Modern, responsive web interface with real-time updates
- **🔔 Alert System**: Email notifications for budget thresholds and anomalies
- **📱 Multi-Platform**: Supports deployment on various platforms (Docker, AWS, Kubernetes)

## 📚 Documentation

This project includes comprehensive documentation covering all aspects of installation, usage, and deployment:

### 📖 Core Documentation

| Document | Description |
|----------|-------------|
| **[API Documentation](API_DOCUMENTATION.md)** | Complete API reference with examples and response formats |
| **[Module Reference](MODULE_REFERENCE.md)** | Detailed technical documentation for all Python modules |
| **[Frontend Documentation](FRONTEND_DOCUMENTATION.md)** | HTML, CSS, and JavaScript implementation guide |
| **[Usage Guide](USAGE_GUIDE.md)** | Step-by-step tutorials and common use cases |
| **[Deployment Guide](DEPLOYMENT_GUIDE.md)** | Production deployment for Docker, AWS, and Kubernetes |

### 🎯 Quick Navigation

**For Developers:**
- [Module Reference](MODULE_REFERENCE.md) - Technical implementation details
- [API Documentation](API_DOCUMENTATION.md) - REST API endpoints and integration
- [Frontend Documentation](FRONTEND_DOCUMENTATION.md) - UI components and customization

**For DevOps/Infrastructure:**
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Production deployment strategies
- [Security Configuration](DEPLOYMENT_GUIDE.md#security-configuration) - Authentication and security
- [Monitoring Setup](DEPLOYMENT_GUIDE.md#monitoring-and-logging) - Logging and health checks

**For End Users:**
- [Usage Guide](USAGE_GUIDE.md) - Getting started and tutorials
- [Common Use Cases](USAGE_GUIDE.md#common-use-cases) - Practical examples
- [Troubleshooting](USAGE_GUIDE.md#troubleshooting) - Problem resolution

## 🚀 Quick Start

### Prerequisites

- Python 3.7+
- AWS Account with Cost Explorer enabled
- Valid AWS credentials

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

# 4. Configure environment
cp .env.example .env
# Edit .env with your AWS credentials

# 5. Run the application
python app.py
```

Open your browser to `http://localhost:5000` to access the dashboard.

### Docker Quick Start

```bash
# Using Docker Compose
docker-compose up -d

# Or build and run manually
docker build -t aws-cost-dashboard .
docker run -p 5000:5000 --env-file .env aws-cost-dashboard
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Flask API      │    │   AWS Services  │
│   (HTML/CSS/JS) │◄──►│   (Python)       │◄──►│   (Cost/EC2/CW) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Dashboard     │    │   Data Analysis  │    │   Monitoring    │
│   Widgets       │    │   Modules        │    │   & Alerts      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Core Components

- **`app.py`**: Flask application and API endpoints
- **`analyzer.py`**: High-level analysis functions and business logic
- **`data_fetcher.py`**: AWS API integration and data retrieval
- **`aws_connector.py`**: Authentication and session management
- **`templates/`**: HTML templates for the dashboard
- **`static/`**: CSS, JavaScript, and other frontend assets

## 📊 Dashboard Features

### Cost Analysis
- **Service Breakdown**: Interactive pie charts showing cost distribution
- **Trend Analysis**: Historical cost patterns and projections
- **Anomaly Detection**: Statistical analysis to identify cost spikes

### Resource Optimization
- **Idle Instances**: CPU utilization analysis across 14-day periods
- **Untagged Resources**: Compliance monitoring for required tags
- **EBS Optimization**: Unattached volumes and upgrade recommendations

### Monitoring & Alerts
- **Real-time Updates**: Automatic dashboard refresh
- **Email Notifications**: Budget alerts and cost anomalies
- **Health Monitoring**: System status and AWS connectivity checks

## 🔧 Configuration

### Environment Variables

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1

# Application Settings
FLASK_ENV=production
DASHBOARD_REFRESH_INTERVAL=300
LOG_LEVEL=INFO

# Security
DASHBOARD_API_KEY=your_api_key
ALLOWED_HOSTS=yourdomain.com

# Alerts
SMTP_SERVER=smtp.company.com
ALERT_EMAIL=alerts@company.com
ALERT_RECIPIENTS=team@company.com
```

### Customization Options

- **Thresholds**: Customize idle detection and anomaly sensitivity
- **Tags**: Configure required tags for compliance monitoring
- **Regions**: Specify which AWS regions to analyze
- **Styling**: Modify CSS for custom branding and themes

## 🔐 Security

### Authentication
- API key authentication for programmatic access
- Session-based authentication for web interface
- OAuth integration support (Google, SAML, etc.)

### Network Security
- HTTPS/TLS encryption
- Rate limiting and request throttling
- Firewall configuration guidance

### AWS Permissions
Minimum required IAM permissions:
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
        "cloudwatch:GetMetricStatistics"
      ],
      "Resource": "*"
    }
  ]
}
```

## 📈 Monitoring

### Health Checks
- Application health endpoint (`/health`)
- AWS connectivity verification
- System resource monitoring

### Metrics
- Prometheus-compatible metrics endpoint (`/metrics`)
- Custom business metrics (cost trends, optimization opportunities)
- Performance and error tracking

### Logging
- Structured JSON logging
- Configurable log levels
- Integration with ELK stack and CloudWatch

## 🚀 Deployment Options

| Platform | Complexity | Best For |
|----------|------------|----------|
| **Local Development** | ⭐ | Testing and development |
| **Docker** | ⭐⭐ | Quick deployment, consistent environments |
| **AWS EC2** | ⭐⭐⭐ | Cost-effective production deployment |
| **AWS ECS/Fargate** | ⭐⭐⭐⭐ | Managed, scalable deployment |
| **Kubernetes** | ⭐⭐⭐⭐⭐ | Enterprise-grade, highly scalable |

See the [Deployment Guide](DEPLOYMENT_GUIDE.md) for detailed instructions for each platform.

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Code formatting
black .
flake8 .

# Security scanning
bandit -r .
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help

1. **Documentation**: Check the comprehensive docs in this repository
2. **Issues**: Create a GitHub issue for bugs or feature requests
3. **Discussions**: Use GitHub Discussions for questions and community support

### Common Issues

- **AWS Permissions**: Ensure your IAM user/role has the required permissions
- **Cost Explorer**: Enable Cost Explorer in your AWS account (may take 24 hours)
- **CloudWatch Metrics**: Verify that detailed monitoring is enabled for EC2 instances

### Troubleshooting

See the [Troubleshooting Guide](USAGE_GUIDE.md#troubleshooting) for solutions to common problems.

## 🙏 Acknowledgments

- AWS SDK for Python (Boto3)
- Flask web framework
- Plotly.js for interactive charts
- All contributors and community members

---

## 📋 Project Status

- ✅ Core functionality complete
- ✅ Comprehensive documentation
- ✅ Multiple deployment options
- ✅ Security features implemented
- ✅ Monitoring and alerting
- 🔄 Ongoing: Community feedback and enhancements

**Ready for production use** with ongoing maintenance and feature development.

For detailed information about any aspect of this project, please refer to the specific documentation files listed above.