# Docker Deployment Guide

Complete guide for deploying the YouTube Transcript API using Docker.

## 🚀 Quick Start

### Using Docker Compose (Recommended)

```bash
# 1. Clone or navigate to the project
cd youtube-transcript-api-example

# 2. (Optional) Configure proxy credentials
cp .env.example .env
# Edit .env and add your Webshare credentials

# 3. Build and run
docker-compose up -d

# 4. Access the application
# Web UI: http://localhost:9585
# API Docs: http://localhost:9585/api/docs
# Health Check: http://localhost:9585/api/health
```

### Using Docker Only

```bash
# 1. Build the image
docker build -t youtube-transcript-api:latest .

# 2. Run without proxy
docker run -d \
  --name youtube-transcript-api \
  -p 9585:8000 \
  youtube-transcript-api:latest

# 3. Or run with proxy (recommended)
docker run -d \
  --name youtube-transcript-api \
  -p 9585:8000 \
  -e WEBSHARE_PROXY_USERNAME=your_username \
  -e WEBSHARE_PROXY_PASSWORD=your_password \
  youtube-transcript-api:latest
```

## 📚 Accessing Swagger Documentation

Once running, visit:
```
http://localhost:9585/api/docs
```

The interactive Swagger UI provides:
- Complete API documentation
- Try-it-out functionality for all endpoints
- Request/response schemas
- Example payloads

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `WEBSHARE_PROXY_USERNAME` | No | Webshare proxy username (recommended for reliability) |
| `WEBSHARE_PROXY_PASSWORD` | No | Webshare proxy password (recommended for reliability) |

### Port Configuration

By default, the container exposes port 8000 internally, mapped to 9585 externally.

To change the external port:
```bash
# Using docker-compose
# Edit docker-compose.yml: "YOUR_PORT:8000"

# Using docker run
docker run -p YOUR_PORT:8000 youtube-transcript-api:latest
```

## 🏥 Health Checks

The container includes built-in health checks:

```bash
# Check container health
docker ps

# Manual health check
curl http://localhost:9585/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0"
}
```

## 🎯 API Endpoints

### 1. Get Transcript
```
POST /api/transcript
```

Request body:
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "language": "en"  // optional
}
```

### 2. List Available Transcripts
```
POST /api/transcript/list
```

Request body:
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

### 3. Health Check
```
GET /api/health
```

## 🔐 Proxy Configuration (Recommended)

YouTube blocks transcript requests from many IPs. For reliable operation:

1. Create a [Webshare account](https://www.webshare.io/?referral_code=w0xno53eb50g)
2. Purchase a **Residential** proxy package
3. Get credentials from [Proxy Settings](https://dashboard.webshare.io/proxy/settings)
4. Add to `.env` file or pass as environment variables

## 📦 Production Deployment

### Docker Compose with Restart Policy

The included `docker-compose.yml` has `restart: unless-stopped` configured:

```yaml
services:
  youtube-transcript-api:
    restart: unless-stopped
    # ... other configuration
```

This ensures the container restarts automatically after:
- System reboots
- Docker daemon restarts
- Container crashes

### Resource Limits

Add resource limits for production:

```yaml
services:
  youtube-transcript-api:
    # ... existing config
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

### Reverse Proxy (Nginx)

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:9585;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🐳 Container Management

### View Logs
```bash
# Using docker-compose
docker-compose logs -f

# Using docker
docker logs -f youtube-transcript-api
```

### Stop Container
```bash
# Using docker-compose
docker-compose down

# Using docker
docker stop youtube-transcript-api
docker rm youtube-transcript-api
```

### Restart Container
```bash
# Using docker-compose
docker-compose restart

# Using docker
docker restart youtube-transcript-api
```

### Update to Latest Version
```bash
# Using docker-compose
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Using docker
docker stop youtube-transcript-api
docker rm youtube-transcript-api
docker build --no-cache -t youtube-transcript-api:latest .
docker run -d --name youtube-transcript-api -p 9585:8000 youtube-transcript-api:latest
```

## 🌍 Deploy Anywhere

### AWS EC2
```bash
# 1. SSH to your EC2 instance
ssh -i your-key.pem ubuntu@your-instance-ip

# 2. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 3. Clone and deploy
git clone your-repo-url
cd youtube-transcript-api-example
docker-compose up -d
```

### Digital Ocean
```bash
# 1. Create a Docker Droplet
# 2. SSH to droplet
# 3. Clone and deploy
git clone your-repo-url
cd youtube-transcript-api-example
docker-compose up -d
```

### Google Cloud Run
```bash
# 1. Build and push to GCR
docker build -t gcr.io/YOUR_PROJECT/youtube-transcript-api .
docker push gcr.io/YOUR_PROJECT/youtube-transcript-api

# 2. Deploy to Cloud Run
gcloud run deploy youtube-transcript-api \
  --image gcr.io/YOUR_PROJECT/youtube-transcript-api \
  --platform managed \
  --port 8000 \
  --set-env-vars WEBSHARE_PROXY_USERNAME=xxx,WEBSHARE_PROXY_PASSWORD=xxx
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: youtube-transcript-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: youtube-transcript-api
  template:
    metadata:
      labels:
        app: youtube-transcript-api
    spec:
      containers:
      - name: youtube-transcript-api
        image: youtube-transcript-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: WEBSHARE_PROXY_USERNAME
          valueFrom:
            secretKeyRef:
              name: proxy-credentials
              key: username
        - name: WEBSHARE_PROXY_PASSWORD
          valueFrom:
            secretKeyRef:
              name: proxy-credentials
              key: password
---
apiVersion: v1
kind: Service
metadata:
  name: youtube-transcript-api
spec:
  selector:
    app: youtube-transcript-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## 🔍 Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose logs

# Check if port is already in use
lsof -i :9585

# Try different port
docker-compose down
# Edit docker-compose.yml: "9586:8000"
docker-compose up -d
```

### Transcript Fetching Fails
- **Symptom**: YouTube blocking errors
- **Solution**: Configure proxy credentials (see Proxy Configuration section)

### Health Check Fails
```bash
# Check if app is running
docker exec youtube-transcript-api ps aux

# Test health endpoint manually
docker exec youtube-transcript-api curl http://localhost:8000/api/health
```

## 📊 Monitoring

### Basic Monitoring
```bash
# Resource usage
docker stats youtube-transcript-api

# Container status
docker ps -a | grep youtube-transcript-api
```

### Production Monitoring

Consider adding:
- **Prometheus** for metrics collection
- **Grafana** for visualization
- **Loki** for log aggregation
- **Alertmanager** for alerts

## 🔒 Security Best Practices

1. **Never commit `.env` files** - Already in `.gitignore`
2. **Use secrets management** in production (AWS Secrets Manager, etc.)
3. **Run as non-root user** - Already configured in Dockerfile
4. **Keep image updated** - Regularly rebuild with latest base images
5. **Use HTTPS** - Configure reverse proxy with SSL certificates

## 📏 Image Details

- **Base Image**: python:3.11-slim
- **Size**: ~200MB (optimized with multi-stage build)
- **Architecture**: Multi-stage build for minimal size
- **User**: Runs as non-root user (appuser, UID 1000)
- **Workers**: 4 gunicorn workers
- **Timeout**: 120 seconds

## 🎓 Best Practices

1. **Always use docker-compose** for easier management
2. **Configure proxy credentials** for reliable operation
3. **Monitor logs** regularly for errors
4. **Set resource limits** in production
5. **Use health checks** for automatic recovery
6. **Keep credentials in `.env`** file (never in code)
7. **Update regularly** for security patches

## 🚀 CI/CD Pipeline

This project includes automated CI/CD with GitHub Actions that builds and publishes Docker images.

### Automated Builds

The workflow (`.github/workflows/docker-publish.yml`) automatically:

1. **Builds and tests** on every push and pull request
2. **Publishes to registries** on:
   - Push to `main`/`master` branch
   - Release creation
   - Version tags (e.g., `v1.0.0`)

### Published Registries

Images are automatically published to:
- **GitHub Container Registry**: `ghcr.io/<username>/youtube-transcript-api-example`
- **Docker Hub** (on releases): `<username>/youtube-transcript-api`

### Setup CI/CD

#### 1. GitHub Container Registry (Automatic)
No setup needed! GHCR uses `GITHUB_TOKEN` automatically.

#### 2. Docker Hub (Optional)
To enable Docker Hub publishing:

1. Create a [Docker Hub account](https://hub.docker.com)
2. Create an access token: Account Settings → Security → New Access Token
3. Add secrets to your GitHub repository:
   - Go to: Settings → Secrets and variables → Actions
   - Add `DOCKER_USERNAME` (your Docker Hub username)
   - Add `DOCKER_PASSWORD` (your Docker Hub access token)

### Using Published Images

#### From GitHub Container Registry
```bash
# Pull latest
docker pull ghcr.io/<username>/youtube-transcript-api-example:latest

# Pull specific version
docker pull ghcr.io/<username>/youtube-transcript-api-example:v1.0.0

# Run
docker run -d -p 9585:8000 \
  -e WEBSHARE_PROXY_USERNAME=xxx \
  -e WEBSHARE_PROXY_PASSWORD=xxx \
  ghcr.io/<username>/youtube-transcript-api-example:latest
```

#### From Docker Hub
```bash
# Pull latest
docker pull <username>/youtube-transcript-api:latest

# Run
docker run -d -p 9585:8000 \
  -e WEBSHARE_PROXY_USERNAME=xxx \
  -e WEBSHARE_PROXY_PASSWORD=xxx \
  <username>/youtube-transcript-api:latest
```

### Image Tags

The CI/CD creates multiple tags:

| Tag | When | Example |
|-----|------|---------|
| `latest` | Main/master branch | `latest` |
| `v{version}` | Release | `v1.0.0` |
| `v{major}.{minor}` | Release | `v1.0` |
| `v{major}` | Release | `v1` |
| `{branch}-{sha}` | Any branch | `main-abc123f` |

### Manual Workflow Trigger

To manually trigger the workflow:
1. Go to: Actions → Build and Publish Docker Images
2. Click "Run workflow"
3. Select branch and click "Run workflow"

### Multi-Platform Support

Images are built for:
- `linux/amd64` (Intel/AMD)
- `linux/arm64` (Apple Silicon, ARM servers)

### Build Cache

The workflow uses GitHub Actions cache to speed up builds:
- First build: ~5-10 minutes
- Subsequent builds: ~2-3 minutes

## 📝 Support

For issues:
- Check logs: `docker-compose logs -f`
- Visit Swagger docs: http://localhost:9585/api/docs
- Review health: http://localhost:9585/api/health
- Check proxy configuration in `.env`
- Review CI/CD: GitHub Actions tab

---

**Happy Deploying! 🚀**
