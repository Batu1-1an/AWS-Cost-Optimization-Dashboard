# Deployment Guide - AWS Cost Optimization Dashboard

## Table of Contents
- [Deployment Options](#deployment-options)
- [Production Setup](#production-setup)
- [Container Deployment](#container-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Security Configuration](#security-configuration)
- [Monitoring and Logging](#monitoring-and-logging)
- [Maintenance and Updates](#maintenance-and-updates)
- [Backup and Recovery](#backup-and-recovery)

## Deployment Options

### Overview of Deployment Methods

| Method | Complexity | Cost | Scalability | Maintenance |
|--------|------------|------|-------------|-------------|
| Local Development | Low | Free | N/A | Manual |
| Docker Container | Medium | Low | Medium | Medium |
| AWS EC2 | Medium | Low-Medium | High | Medium |
| AWS ECS/Fargate | High | Medium | Very High | Low |
| Kubernetes | Very High | High | Very High | High |

### Quick Comparison

**Local Development**
- ✅ Fast setup, free
- ❌ Not suitable for production

**Docker Container**
- ✅ Consistent environment, easy deployment
- ✅ Works on any Docker-compatible platform
- ❌ Requires container orchestration for HA

**AWS EC2**
- ✅ Full control, cost-effective
- ✅ Easy scaling
- ❌ Manual maintenance required

**AWS ECS/Fargate**
- ✅ Managed service, auto-scaling
- ✅ No server management
- ❌ Higher cost, AWS vendor lock-in

## Production Setup

### Prerequisites for Production

1. **Infrastructure Requirements**
   - Virtual machine or container with 1 GB RAM minimum
   - 10 GB disk space
   - Stable internet connection
   - SSL certificate for HTTPS

2. **AWS Requirements**
   - IAM user/role with appropriate permissions
   - Cost Explorer enabled (may take 24 hours)
   - CloudWatch metrics enabled
   - Multi-region access if needed

3. **Security Requirements**
   - Firewall configuration
   - HTTPS/TLS encryption
   - Authentication mechanism
   - Regular security updates

### Production Environment Setup

#### 1. Environment Variables

Create a production `.env` file:

```bash
# Production environment configuration
# AWS Configuration
AWS_ACCESS_KEY_ID=your_production_access_key
AWS_SECRET_ACCESS_KEY=your_production_secret_key
AWS_REGION=us-east-1

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-super-secret-key-here

# Dashboard Configuration
DASHBOARD_REFRESH_INTERVAL=300
CACHE_TTL=300
MAX_WORKERS=4

# Security
DASHBOARD_API_KEY=your-api-key-here
ALLOWED_HOSTS=yourdomain.com,dashboard.company.com

# Monitoring
LOG_LEVEL=INFO
METRICS_ENABLED=true

# Database (if using)
DATABASE_URL=postgresql://user:pass@localhost/costdashboard

# Email Alerts
SMTP_SERVER=smtp.company.com
SMTP_PORT=587
ALERT_EMAIL=alerts@company.com
ALERT_EMAIL_PASSWORD=your_email_password
ALERT_RECIPIENTS=cfo@company.com,ops@company.com
```

#### 2. Production Server Setup

**Option A: Traditional Server Setup**

```bash
#!/bin/bash
# production_setup.sh

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3 python3-pip python3-venv nginx supervisor

# Create application user
sudo useradd -m -s /bin/bash costdashboard
sudo su - costdashboard

# Clone and setup application
git clone https://github.com/yourorg/aws-cost-dashboard.git
cd aws-cost-dashboard

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Copy production configuration
cp .env.production .env

# Test the application
python app.py  # Should start without errors
```

**Option B: Gunicorn with Supervisor**

Create `/etc/supervisor/conf.d/costdashboard.conf`:

```ini
[program:costdashboard]
command=/home/costdashboard/aws-cost-dashboard/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 app:app
directory=/home/costdashboard/aws-cost-dashboard
user=costdashboard
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/costdashboard.log
environment=PATH="/home/costdashboard/aws-cost-dashboard/venv/bin"
```

Start the service:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start costdashboard
```

#### 3. Nginx Configuration

Create `/etc/nginx/sites-available/costdashboard`:

```nginx
server {
    listen 80;
    server_name dashboard.yourcompany.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name dashboard.yourcompany.com;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/dashboard.crt;
    ssl_certificate_key /etc/ssl/private/dashboard.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files
    location /static {
        alias /home/costdashboard/aws-cost-dashboard/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }

    # Rate limiting
    limit_req zone=api burst=10 nodelay;
    limit_req_status 429;
}

# Rate limiting configuration
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/m;
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/costdashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Container Deployment

### Docker Setup

#### 1. Dockerfile

```dockerfile
# Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:5000/health')"

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
```

#### 2. Docker Compose for Production

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  costdashboard:
    build: .
    container_name: aws-cost-dashboard
    restart: unless-stopped
    ports:
      - "8000:5000"
    environment:
      - FLASK_ENV=production
      - FLASK_DEBUG=False
    env_file:
      - .env.production
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    networks:
      - dashboard-network
    depends_on:
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:6-alpine
    container_name: dashboard-redis
    restart: unless-stopped
    volumes:
      - redis-data:/data
    networks:
      - dashboard-network
    command: redis-server --appendonly yes

  nginx:
    image: nginx:alpine
    container_name: dashboard-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl:ro
      - ./static:/var/www/static:ro
    networks:
      - dashboard-network
    depends_on:
      - costdashboard

volumes:
  redis-data:

networks:
  dashboard-network:
    driver: bridge
```

#### 3. Build and Deploy

```bash
# Build the image
docker build -t aws-cost-dashboard:latest .

# Run with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f costdashboard
```

## Cloud Deployment

### AWS EC2 Deployment

#### 1. Launch EC2 Instance

**Using AWS CLI:**

```bash
# Create security group
aws ec2 create-security-group \
    --group-name cost-dashboard-sg \
    --description "Security group for Cost Dashboard"

# Add ingress rules
aws ec2 authorize-security-group-ingress \
    --group-name cost-dashboard-sg \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-name cost-dashboard-sg \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-name cost-dashboard-sg \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0

# Launch instance
aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1d0 \
    --count 1 \
    --instance-type t3.small \
    --key-name your-key-pair \
    --security-groups cost-dashboard-sg \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=cost-dashboard}]'
```

#### 2. User Data Script

```bash
#!/bin/bash
# EC2 User Data Script

# Update system
yum update -y

# Install dependencies
yum install -y python3 python3-pip git nginx

# Install Docker
amazon-linux-extras install docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Clone repository
cd /home/ec2-user
git clone https://github.com/yourorg/aws-cost-dashboard.git
chown -R ec2-user:ec2-user aws-cost-dashboard

# Setup environment
cd aws-cost-dashboard
cp .env.example .env.production

# Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Setup log rotation
echo '/home/ec2-user/aws-cost-dashboard/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    copytruncate
}' > /etc/logrotate.d/costdashboard
```

### AWS ECS/Fargate Deployment

#### 1. Task Definition

```json
{
  "family": "cost-dashboard",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::123456789012:role/costDashboardTaskRole",
  "containerDefinitions": [
    {
      "name": "cost-dashboard",
      "image": "your-account.dkr.ecr.us-east-1.amazonaws.com/cost-dashboard:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "FLASK_ENV",
          "value": "production"
        },
        {
          "name": "AWS_REGION",
          "value": "us-east-1"
        }
      ],
      "secrets": [
        {
          "name": "AWS_ACCESS_KEY_ID",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:cost-dashboard/aws-creds:AWS_ACCESS_KEY_ID::"
        },
        {
          "name": "AWS_SECRET_ACCESS_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:cost-dashboard/aws-creds:AWS_SECRET_ACCESS_KEY::"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/cost-dashboard",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:5000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

#### 2. Service Definition

```bash
# Create ECS service
aws ecs create-service \
    --cluster cost-dashboard-cluster \
    --service-name cost-dashboard-service \
    --task-definition cost-dashboard:1 \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-12345,subnet-67890],securityGroups=[sg-abcdef],assignPublicIp=ENABLED}" \
    --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/cost-dashboard/1234567890123456,containerName=cost-dashboard,containerPort=5000
```

### Kubernetes Deployment

#### 1. Namespace and ConfigMap

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cost-dashboard

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cost-dashboard-config
  namespace: cost-dashboard
data:
  FLASK_ENV: "production"
  AWS_REGION: "us-east-1"
  DASHBOARD_REFRESH_INTERVAL: "300"
  LOG_LEVEL: "INFO"
```

#### 2. Secret for AWS Credentials

```yaml
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: aws-credentials
  namespace: cost-dashboard
type: Opaque
data:
  AWS_ACCESS_KEY_ID: <base64-encoded-access-key>
  AWS_SECRET_ACCESS_KEY: <base64-encoded-secret-key>
```

#### 3. Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cost-dashboard
  namespace: cost-dashboard
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cost-dashboard
  template:
    metadata:
      labels:
        app: cost-dashboard
    spec:
      containers:
      - name: cost-dashboard
        image: your-registry/cost-dashboard:latest
        ports:
        - containerPort: 5000
        envFrom:
        - configMapRef:
            name: cost-dashboard-config
        - secretRef:
            name: aws-credentials
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: cost-dashboard-service
  namespace: cost-dashboard
spec:
  selector:
    app: cost-dashboard
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5000
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: cost-dashboard-ingress
  namespace: cost-dashboard
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - dashboard.yourcompany.com
    secretName: cost-dashboard-tls
  rules:
  - host: dashboard.yourcompany.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: cost-dashboard-service
            port:
              number: 80
```

## Security Configuration

### 1. Authentication and Authorization

#### Basic Authentication

```python
# auth.py
from flask import request, abort, session
from functools import wraps
import os
import hashlib

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # API Key authentication
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key == os.getenv('DASHBOARD_API_KEY'):
            return f(*args, **kwargs)
        
        # Session-based authentication
        if 'authenticated' in session:
            return f(*args, **kwargs)
        
        # Basic auth fallback
        auth = request.authorization
        if auth and check_credentials(auth.username, auth.password):
            session['authenticated'] = True
            return f(*args, **kwargs)
        
        abort(401)
    return decorated_function

def check_credentials(username, password):
    """Check username/password against environment variables"""
    expected_username = os.getenv('DASHBOARD_USERNAME')
    expected_password_hash = os.getenv('DASHBOARD_PASSWORD_HASH')
    
    if not expected_username or not expected_password_hash:
        return False
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return username == expected_username and password_hash == expected_password_hash

# Apply to routes
@app.route('/api/<path:path>')
@require_auth
def api_proxy(path):
    # API endpoint logic
    pass
```

#### OAuth Integration

```python
# oauth_config.py
from authlib.integrations.flask_client import OAuth
import os

oauth = OAuth()

# Configure OAuth provider (example: Google)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

@app.route('/login')
def login():
    redirect_uri = url_for('auth_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/callback')
def auth_callback():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')
    
    # Check if user is authorized
    allowed_emails = os.getenv('ALLOWED_EMAILS', '').split(',')
    if user_info['email'] not in allowed_emails:
        abort(403)
    
    session['user'] = user_info
    return redirect('/')
```

### 2. Network Security

#### Firewall Configuration

```bash
# UFW (Ubuntu Firewall) configuration
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow specific IPs only (optional)
sudo ufw allow from 10.0.0.0/8 to any port 22

# Enable firewall
sudo ufw enable
```

#### SSL/TLS Configuration

```bash
# Generate self-signed certificate (for testing)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Or use Let's Encrypt (recommended for production)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d dashboard.yourcompany.com
```

### 3. Secrets Management

#### AWS Secrets Manager Integration

```python
# secrets_manager.py
import boto3
import json
import os

def get_secret(secret_name, region_name="us-east-1"):
    """Retrieve secret from AWS Secrets Manager"""
    
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret = get_secret_value_response['SecretString']
        return json.loads(secret)
    except Exception as e:
        print(f"Error retrieving secret {secret_name}: {e}")
        return None

# Load secrets on startup
def load_secrets():
    """Load secrets and update environment variables"""
    secrets = get_secret("cost-dashboard/secrets")
    if secrets:
        for key, value in secrets.items():
            os.environ[key] = value

# Call during app initialization
load_secrets()
```

## Monitoring and Logging

### 1. Application Monitoring

#### Health Checks

```python
# health.py
from flask import jsonify
import psutil
import time
from datetime import datetime
from aws_connector import get_aws_session

@app.route('/health')
def health_check():
    """Comprehensive health check endpoint"""
    start_time = time.time()
    
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': os.getenv('APP_VERSION', 'unknown'),
        'checks': {}
    }
    
    # Basic application health
    health_status['checks']['application'] = True
    
    # AWS connectivity
    try:
        session = get_aws_session()
        if session:
            # Try a simple STS call
            sts = session.client('sts')
            sts.get_caller_identity()
            health_status['checks']['aws_connectivity'] = True
        else:
            health_status['checks']['aws_connectivity'] = False
            health_status['status'] = 'degraded'
    except Exception as e:
        health_status['checks']['aws_connectivity'] = False
        health_status['status'] = 'unhealthy'
        health_status['error'] = str(e)
    
    # System resources
    health_status['checks']['memory_usage'] = psutil.virtual_memory().percent
    health_status['checks']['cpu_usage'] = psutil.cpu_percent(interval=1)
    health_status['checks']['disk_usage'] = psutil.disk_usage('/').percent
    
    # Response time
    health_status['response_time_ms'] = (time.time() - start_time) * 1000
    
    # Set HTTP status code based on health
    status_code = 200 if health_status['status'] == 'healthy' else 503
    
    return jsonify(health_status), status_code

@app.route('/metrics')
def metrics():
    """Prometheus-compatible metrics endpoint"""
    metrics_data = []
    
    # Custom metrics
    metrics_data.append('# HELP cost_dashboard_requests_total Total requests')
    metrics_data.append('# TYPE cost_dashboard_requests_total counter')
    metrics_data.append(f'cost_dashboard_requests_total {get_request_count()}')
    
    metrics_data.append('# HELP cost_dashboard_aws_api_calls_total Total AWS API calls')
    metrics_data.append('# TYPE cost_dashboard_aws_api_calls_total counter')
    metrics_data.append(f'cost_dashboard_aws_api_calls_total {get_aws_api_count()}')
    
    return '\n'.join(metrics_data), 200, {'Content-Type': 'text/plain'}
```

#### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'cost-dashboard'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### 2. Logging Configuration

#### Structured Logging

```python
# logging_config.py
import logging
import json
import sys
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'region'):
            log_entry['region'] = record.region
        
        return json.dumps(log_entry)

def setup_logging():
    """Configure application logging"""
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
    
    # Remove default handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    log_file = os.getenv('LOG_FILE')
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
    
    return logger

# Initialize logging
logger = setup_logging()
```

#### Centralized Logging with ELK Stack

```yaml
# docker-compose.logging.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.15.0
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data

  kibana:
    image: docker.elastic.co/kibana/kibana:7.15.0
    container_name: kibana
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

  logstash:
    image: docker.elastic.co/logstash/logstash:7.15.0
    container_name: logstash
    volumes:
      - ./logstash/config:/usr/share/logstash/pipeline
    ports:
      - "5044:5044"
    depends_on:
      - elasticsearch

volumes:
  elasticsearch-data:
```

## Maintenance and Updates

### 1. Automated Deployment Pipeline

#### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest
      
      - name: Run tests
        run: pytest tests/
      
      - name: Security scan
        run: |
          pip install bandit
          bandit -r . -x tests/

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: cost-dashboard
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')
    steps:
      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster cost-dashboard-cluster \
            --service cost-dashboard-service \
            --force-new-deployment
```

### 2. Database Migrations

#### Simple Migration System

```python
# migrations.py
import os
import json
from datetime import datetime

class MigrationManager:
    def __init__(self, data_dir='./data'):
        self.data_dir = data_dir
        self.migrations_dir = os.path.join(data_dir, 'migrations')
        os.makedirs(self.migrations_dir, exist_ok=True)
    
    def create_migration(self, name, up_func, down_func):
        """Create a new migration"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        migration_id = f"{timestamp}_{name}"
        
        migration = {
            'id': migration_id,
            'name': name,
            'created_at': datetime.now().isoformat(),
            'up': up_func.__name__,
            'down': down_func.__name__
        }
        
        # Save migration metadata
        with open(os.path.join(self.migrations_dir, f"{migration_id}.json"), 'w') as f:
            json.dump(migration, f, indent=2)
        
        # Save migration code
        with open(os.path.join(self.migrations_dir, f"{migration_id}.py"), 'w') as f:
            f.write(f"# Migration: {name}\n")
            f.write(f"# Created: {migration['created_at']}\n\n")
            f.write("def up():\n")
            f.write(f"    {up_func.__name__}()\n\n")
            f.write("def down():\n")
            f.write(f"    {down_func.__name__}()\n")
    
    def run_migrations(self):
        """Run pending migrations"""
        executed_migrations = self._get_executed_migrations()
        available_migrations = self._get_available_migrations()
        
        pending = [m for m in available_migrations if m not in executed_migrations]
        
        for migration_id in sorted(pending):
            self._execute_migration(migration_id)
            self._mark_migration_executed(migration_id)
    
    def _get_executed_migrations(self):
        """Get list of executed migrations"""
        executed_file = os.path.join(self.data_dir, 'executed_migrations.json')
        if os.path.exists(executed_file):
            with open(executed_file, 'r') as f:
                return json.load(f)
        return []
    
    def _mark_migration_executed(self, migration_id):
        """Mark migration as executed"""
        executed = self._get_executed_migrations()
        executed.append(migration_id)
        
        executed_file = os.path.join(self.data_dir, 'executed_migrations.json')
        with open(executed_file, 'w') as f:
            json.dump(executed, f, indent=2)

# Example migration
def add_cost_alerts_table():
    """Add cost alerts configuration table"""
    # Implementation for adding new feature
    pass

def remove_cost_alerts_table():
    """Remove cost alerts configuration table"""
    # Implementation for rollback
    pass

# Register migration
migration_manager = MigrationManager()
migration_manager.create_migration(
    'add_cost_alerts', 
    add_cost_alerts_table, 
    remove_cost_alerts_table
)
```

### 3. Backup and Monitoring

#### Automated Backup Script

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/cost-dashboard"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="cost-dashboard-backup-$DATE"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup application data
tar -czf "$BACKUP_DIR/$BACKUP_NAME-data.tar.gz" \
    /home/costdashboard/aws-cost-dashboard/data/ \
    /home/costdashboard/aws-cost-dashboard/logs/ \
    /home/costdashboard/aws-cost-dashboard/.env

# Backup configuration
tar -czf "$BACKUP_DIR/$BACKUP_NAME-config.tar.gz" \
    /etc/nginx/sites-available/costdashboard \
    /etc/supervisor/conf.d/costdashboard.conf

# Upload to S3 (optional)
if [ "$UPLOAD_TO_S3" = "true" ]; then
    aws s3 cp "$BACKUP_DIR/$BACKUP_NAME-data.tar.gz" "s3://your-backup-bucket/cost-dashboard/"
    aws s3 cp "$BACKUP_DIR/$BACKUP_NAME-config.tar.gz" "s3://your-backup-bucket/cost-dashboard/"
fi

# Cleanup old backups (keep last 30 days)
find "$BACKUP_DIR" -name "cost-dashboard-backup-*" -mtime +30 -delete

echo "Backup completed: $BACKUP_NAME"
```

#### Monitoring Script

```bash
#!/bin/bash
# monitor.sh

DASHBOARD_URL="https://dashboard.yourcompany.com"
ALERT_EMAIL="alerts@yourcompany.com"

# Check if dashboard is responding
if ! curl -f -s "$DASHBOARD_URL/health" > /dev/null; then
    echo "Dashboard health check failed" | mail -s "Cost Dashboard Alert" "$ALERT_EMAIL"
    exit 1
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "Disk usage is at $DISK_USAGE%" | mail -s "Disk Space Alert" "$ALERT_EMAIL"
fi

# Check memory usage
MEMORY_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [ "$MEMORY_USAGE" -gt 90 ]; then
    echo "Memory usage is at $MEMORY_USAGE%" | mail -s "Memory Alert" "$ALERT_EMAIL"
fi

# Check if service is running
if ! systemctl is-active --quiet costdashboard; then
    echo "Cost Dashboard service is not running" | mail -s "Service Alert" "$ALERT_EMAIL"
    systemctl restart costdashboard
fi

echo "Monitoring check completed successfully"
```

## Backup and Recovery

### 1. Data Backup Strategy

#### Configuration Backup

```python
# backup_manager.py
import os
import json
import tarfile
import boto3
from datetime import datetime, timedelta

class BackupManager:
    def __init__(self, backup_dir='/backup', s3_bucket=None):
        self.backup_dir = backup_dir
        self.s3_bucket = s3_bucket
        self.s3_client = boto3.client('s3') if s3_bucket else None
        os.makedirs(backup_dir, exist_ok=True)
    
    def create_backup(self):
        """Create a complete system backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"cost-dashboard-backup-{timestamp}"
        backup_path = os.path.join(self.backup_dir, f"{backup_name}.tar.gz")
        
        # Files to backup
        backup_files = [
            './data/',
            './logs/',
            './.env',
            './config/',
        ]
        
        # Create tar archive
        with tarfile.open(backup_path, 'w:gz') as tar:
            for file_path in backup_files:
                if os.path.exists(file_path):
                    tar.add(file_path, arcname=os.path.basename(file_path))
        
        # Upload to S3 if configured
        if self.s3_client and self.s3_bucket:
            s3_key = f"backups/{backup_name}.tar.gz"
            self.s3_client.upload_file(backup_path, self.s3_bucket, s3_key)
        
        # Cleanup old backups
        self._cleanup_old_backups()
        
        return backup_path
    
    def restore_backup(self, backup_file):
        """Restore from backup file"""
        if not os.path.exists(backup_file):
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        # Extract backup
        with tarfile.open(backup_file, 'r:gz') as tar:
            tar.extractall(path='.')
        
        print(f"Backup restored from {backup_file}")
    
    def _cleanup_old_backups(self, keep_days=30):
        """Remove backups older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        for filename in os.listdir(self.backup_dir):
            if filename.startswith('cost-dashboard-backup-'):
                file_path = os.path.join(self.backup_dir, filename)
                file_date = datetime.fromtimestamp(os.path.getctime(file_path))
                
                if file_date < cutoff_date:
                    os.remove(file_path)
                    print(f"Removed old backup: {filename}")

# Usage
backup_manager = BackupManager(s3_bucket='your-backup-bucket')
backup_path = backup_manager.create_backup()
```

### 2. Disaster Recovery

#### Recovery Procedures

```bash
#!/bin/bash
# disaster_recovery.sh

set -e

BACKUP_BUCKET="your-backup-bucket"
RECOVERY_DIR="/tmp/recovery"
APP_DIR="/home/costdashboard/aws-cost-dashboard"

echo "Starting disaster recovery process..."

# Create recovery directory
mkdir -p "$RECOVERY_DIR"
cd "$RECOVERY_DIR"

# Download latest backup from S3
echo "Downloading latest backup..."
LATEST_BACKUP=$(aws s3 ls "s3://$BACKUP_BUCKET/backups/" --recursive | sort | tail -n 1 | awk '{print $4}')
aws s3 cp "s3://$BACKUP_BUCKET/$LATEST_BACKUP" ./

# Stop services
echo "Stopping services..."
sudo systemctl stop costdashboard
sudo systemctl stop nginx

# Backup current installation (just in case)
sudo tar -czf "/tmp/current-installation-$(date +%Y%m%d_%H%M%S).tar.gz" "$APP_DIR"

# Extract backup
echo "Extracting backup..."
tar -xzf "$(basename "$LATEST_BACKUP")" -C "$APP_DIR"

# Restore file permissions
sudo chown -R costdashboard:costdashboard "$APP_DIR"
sudo chmod +x "$APP_DIR"/*.py

# Reinstall dependencies (if needed)
cd "$APP_DIR"
source venv/bin/activate
pip install -r requirements.txt

# Restart services
echo "Restarting services..."
sudo systemctl start costdashboard
sudo systemctl start nginx

# Verify recovery
sleep 10
if curl -f http://localhost/health; then
    echo "✅ Disaster recovery completed successfully"
else
    echo "❌ Recovery verification failed"
    exit 1
fi

# Cleanup
rm -rf "$RECOVERY_DIR"
echo "Recovery process completed"
```

This comprehensive deployment guide covers all aspects of deploying the AWS Cost Optimization Dashboard in various environments, from simple local setups to complex Kubernetes deployments. It includes security best practices, monitoring configurations, and disaster recovery procedures to ensure a robust production deployment.