# Production Deployment Guide

Complete guide for deploying YouTube Transcript API to production with all best practices.

## 🎯 Production Checklist

### Before Deployment
- [ ] Run all tests: `make test`
- [ ] Run linting: `make lint`
- [ ] Check security: `bandit -r app.py`
- [ ] Review environment variables
- [ ] Configure proxy credentials (recommended)
- [ ] Set up monitoring and logging
- [ ] Configure rate limiting
- [ ] Enable HTTPS

### Security Considerations
- [ ] Keep dependencies updated
- [ ] Use environment variables for secrets
- [ ] Enable CORS only for trusted domains (production)
- [ ] Configure rate limiting appropriately
- [ ] Use HTTPS in production
- [ ] Implement proper authentication (if needed)
- [ ] Regular security audits

## 🔧 Production Configuration

### Environment Variables

```bash
# Required for proxy (recommended for reliability)
WEBSHARE_PROXY_USERNAME=your_username
WEBSHARE_PROXY_PASSWORD=your_password

# Optional: Custom configuration
FLASK_ENV=production
LOG_LEVEL=INFO
```

### Rate Limiting

Current limits (configured in `app.py`):
- Global: 200 requests/day, 50 requests/hour
- Transcript endpoint: 30 requests/minute
- List transcripts: 60 requests/minute

Adjust in `app.py` for your needs:
```python
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["YOUR_LIMITS_HERE"],
    storage_uri="memory://"  # Or use Redis: "redis://localhost:6379"
)
```

### CORS Configuration

Current: Allows all origins (`*`) - **Change for production!**

Update in `app.py`:
```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://yourdomain.com"],  # Specify your domains
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

## 🚀 Deployment Options

### Option 1: Docker (Recommended)

```bash
# Build and run with docker-compose
docker-compose up -d

# Or with Docker directly
docker build -t youtube-transcript-api .
docker run -d \
  -p 9585:8000 \
  -e WEBSHARE_PROXY_USERNAME=xxx \
  -e WEBSHARE_PROXY_PASSWORD=xxx \
  --restart unless-stopped \
  youtube-transcript-api
```

### Option 2: Systemd Service

Create `/etc/systemd/system/youtube-transcript-api.service`:

```ini
[Unit]
Description=YouTube Transcript API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/youtube-transcript-api
Environment="PATH=/opt/youtube-transcript-api/venv/bin"
EnvironmentFile=/opt/youtube-transcript-api/.env
ExecStart=/opt/youtube-transcript-api/venv/bin/gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120 \
    --access-logfile /var/log/youtube-transcript-api/access.log \
    --error-logfile /var/log/youtube-transcript-api/error.log \
    app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable youtube-transcript-api
sudo systemctl start youtube-transcript-api
```

### Option 3: Cloud Platforms

#### Heroku
```bash
# Create Procfile
echo "web: gunicorn --bind 0.0.0.0:\$PORT --workers 4 --timeout 120 app:app" > Procfile

# Deploy
heroku create youtube-transcript-api
git push heroku main
heroku config:set WEBSHARE_PROXY_USERNAME=xxx
heroku config:set WEBSHARE_PROXY_PASSWORD=xxx
```

#### Google Cloud Run
```bash
gcloud run deploy youtube-transcript-api \
  --image gcr.io/PROJECT_ID/youtube-transcript-api \
  --platform managed \
  --port 8000 \
  --set-env-vars WEBSHARE_PROXY_USERNAME=xxx,WEBSHARE_PROXY_PASSWORD=xxx
```

#### AWS ECS/Fargate
See `DOCKER.md` for detailed Kubernetes and AWS deployment guides.

## 📊 Monitoring & Logging

### Structured Logging

The app uses Python's logging module. Configure level via environment:

```bash
export LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Application Metrics

Monitor these metrics:
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Cache hit rate
- API quota usage

### Health Checks

Endpoint: `GET /api/health`

Configure in your load balancer:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Log Aggregation

Forward logs to centralized service:

**Using Docker:**
```yaml
services:
  youtube-transcript-api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**Using Systemd:**
```bash
journalctl -u youtube-transcript-api -f
```

## 🔒 Security Best Practices

### 1. HTTPS Only
```nginx
# Nginx configuration
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. API Authentication (Optional)

Add API key authentication:

```python
from functools import wraps
from flask import request

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != os.getenv('API_KEY'):
            return {'error': 'Invalid API key'}, 401
        return f(*args, **kwargs)
    return decorated_function

# Apply to endpoints
@ns_transcript.route('')
class TranscriptResource(Resource):
    @require_api_key
    def post(self):
        # ...
```

### 3. Secrets Management

**AWS Secrets Manager:**
```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])
```

**HashiCorp Vault:**
```python
import hvac

client = hvac.Client(url='http://vault:8200')
secret = client.secrets.kv.v2.read_secret_version(path='youtube-api')
```

## ⚡ Performance Optimization

### 1. Gunicorn Workers

Calculate optimal workers:
```python
workers = (2 * cpu_cores) + 1
```

For 4 cores: `--workers 9`

### 2. Redis Cache (Optional)

Replace in-memory cache with Redis:

```python
import redis

redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0
)

# Use for caching
redis_client.setex(f'transcript:{video_id}', 3600, json.dumps(data))
```

### 3. CDN for Static Assets

Serve UI through CDN:
- Cloudflare
- AWS CloudFront
- Fastly

### 4. Connection Pooling

Configure gunicorn:
```bash
gunicorn \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --worker-class gthread \
  --threads 2 \
  --worker-connections 1000 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --timeout 120 \
  app:app
```

## 🔄 Zero-Downtime Deployment

### Using Docker

```bash
# Build new image
docker build -t youtube-transcript-api:v2 .

# Start new container
docker run -d --name api-v2 -p 8001:8000 youtube-transcript-api:v2

# Health check
curl http://localhost:8001/api/health

# Update load balancer to point to new container
# Remove old container
docker stop api-v1
docker rm api-v1
```

### Using Systemd

```bash
# Build new version
cd /opt/youtube-transcript-api
git pull
source venv/bin/activate
pip install -r requirements.txt

# Reload without downtime
sudo systemctl reload youtube-transcript-api
```

## 📈 Scaling

### Horizontal Scaling

**With Docker Compose:**
```bash
docker-compose up --scale youtube-transcript-api=3
```

**With Kubernetes:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: youtube-transcript-api
spec:
  replicas: 3
  # ... rest of deployment config
```

### Load Balancing

**Nginx:**
```nginx
upstream youtube_api {
    server localhost:8001;
    server localhost:8002;
    server localhost:8003;
}

server {
    location / {
        proxy_pass http://youtube_api;
    }
}
```

## 🆘 Troubleshooting

### High Memory Usage
- Reduce gunicorn workers
- Implement cache size limits
- Check for memory leaks: `memory_profiler`

### High CPU Usage
- Review rate limits
- Optimize video metadata fetching
- Add caching for metadata

### Slow Response Times
- Check proxy configuration
- Optimize database queries (if using DB)
- Increase cache TTL

### Rate Limit Errors
- Configure appropriate limits
- Use Redis for distributed rate limiting
- Implement graceful degradation

## 📞 Support & Maintenance

### Regular Tasks
- [ ] Weekly: Review logs and metrics
- [ ] Monthly: Update dependencies
- [ ] Quarterly: Security audit
- [ ] Annually: Disaster recovery drill

### Backup Strategy
- Database backups (if applicable)
- Configuration backups
- Secrets backup (encrypted)

### Disaster Recovery
- Document recovery procedures
- Test restoration process
- Maintain off-site backups

---

**Production Ready! 🎉**
