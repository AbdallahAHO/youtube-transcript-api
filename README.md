# YouTube Transcript API

A production-ready Flask REST API for fetching YouTube video transcripts with support for multiple deployment methods (Docker, Coolify, manual), proxy configuration, and comprehensive documentation via Swagger UI.

## ✨ Features

- 🎯 **Fetch transcripts** from any YouTube video with auto-generated or manual captions
- 🌍 **Multi-language support** with automatic language detection
- 📦 **Export formats**: Text, JSON with timestamps
- 🔐 **Proxy support** to bypass YouTube IP blocking (Webshare integration)
- 📊 **Interactive API docs** via Swagger UI
- 🚀 **Production-ready** with rate limiting, CORS, health checks
- 🐳 **Multiple deployment options**: Docker, docker-compose, Coolify, manual
- ⚡ **Fast caching** with in-memory transcript storage
- 📱 **Modern UI** with clean interface

## 🚀 Quick Start

### Using Docker Compose (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/youtube-transcript-api.git
cd youtube-transcript-api

# 2. Configure environment (optional but recommended)
cp .env.example .env
# Edit .env and add Webshare proxy credentials

# 3. Start the service
docker-compose up -d

# 4. Access the application
# Web UI: http://localhost:9585
# API Docs: http://localhost:9585/api/docs
```

### Manual Setup

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
make install
# or: pip install -r requirements.txt

# 3. Configure proxy (optional)
cp .env.example .env
# Edit .env with your credentials

# 4. Run the application
make run
# or: python app.py
```

Visit http://localhost:9585

## 📚 Documentation

### API Endpoints

#### **GET /** - Web Interface
Access the modern web UI for transcript fetching

#### **POST /api/transcript** - Get Transcript
Fetch transcript for a YouTube video

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "language": "en"  // optional, defaults to manual transcript or auto-generated
}
```

**Response:**
```json
{
  "video_id": "VIDEO_ID",
  "language": "English",
  "language_code": "en",
  "is_generated": false,
  "transcript": [
    {
      "text": "Hello everyone",
      "start": 0.0,
      "duration": 2.5
    }
  ],
  "metadata": {
    "title": "Video Title",
    "channel": "Channel Name",
    "duration": 600,
    "view_count": 10000
  },
  "available_languages": [...],
  "from_cache": false
}
```

#### **POST /api/transcript/list** - List Available Transcripts
Get all available transcript languages for a video

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

#### **GET /api/health** - Health Check
```json
{
  "status": "healthy",
  "version": "1.0"
}
```

### Interactive API Documentation

Visit http://localhost:9585/api/docs for the full Swagger UI with:
- Try-it-out functionality
- Complete request/response schemas
- Example payloads
- Authentication testing

## 🔧 Configuration

### Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
# Application Configuration
PORT=9585

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=false

# Webshare Proxy Configuration (Recommended)
WEBSHARE_PROXY_USERNAME=your_username
WEBSHARE_PROXY_PASSWORD=your_password

# Python Configuration
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1

# Gunicorn Configuration
GUNICORN_WORKERS=4
GUNICORN_TIMEOUT=120
GUNICORN_BIND=0.0.0.0:9585
```

### Proxy Setup (Recommended)

YouTube blocks transcript requests from many IPs. For reliable operation:

1. **Create account**: [Webshare](https://www.webshare.io/?referral_code=w0xno53eb50g)
2. **Purchase proxies**: Select **"Residential"** proxy package (NOT "Proxy Server" or "Static Residential")
3. **Get credentials**: [Proxy Settings](https://dashboard.webshare.io/proxy/settings)
4. **Configure**: Add credentials to `.env` file

**Without proxy:**
- ✅ List available transcript languages
- ❌ Fetch transcript content (may be blocked)

**With proxy:**
- ✅ Full functionality
- ✅ Reliable transcript fetching
- ✅ No IP blocking

## 🐳 Deployment

### Docker

```bash
# Build and run
docker build -t youtube-transcript-api .
docker run -d \
  -p 9585:9585 \
  -e PORT=9585 \
  -e WEBSHARE_PROXY_USERNAME=xxx \
  -e WEBSHARE_PROXY_PASSWORD=xxx \
  --name youtube-transcript-api \
  youtube-transcript-api
```

### Docker Compose

```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Coolify / Nixpacks

This project includes `nixpacks.toml` for seamless deployment to Coolify or any nixpacks-based platform:

1. **Connect repository** to Coolify
2. **Set environment variables** in Coolify dashboard:
   - `PORT=9585`
   - `WEBSHARE_PROXY_USERNAME=xxx`
   - `WEBSHARE_PROXY_PASSWORD=xxx`
3. **Deploy** - nixpacks will automatically detect and build

### Production Deployment

#### Systemd Service

Create `/etc/systemd/system/youtube-transcript-api.service`:

```ini
[Unit]
Description=YouTube Transcript API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/youtube-transcript-api
EnvironmentFile=/opt/youtube-transcript-api/.env
ExecStart=/opt/youtube-transcript-api/venv/bin/gunicorn \
    --bind 0.0.0.0:9585 \
    --workers 4 \
    --timeout 120 \
    app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable youtube-transcript-api
sudo systemctl start youtube-transcript-api
```

#### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:9585;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 🛠️ Development

### Setup Development Environment

```bash
# Install development dependencies
make setup-dev

# Or manually
pip install -r requirements-dev.txt
pre-commit install
```

### Available Make Commands

```bash
make help           # Show all available commands
make install        # Install production dependencies
make setup-dev      # Complete development setup
make test           # Run tests with coverage
make lint           # Run linting checks
make format         # Format code with black and isort
make clean          # Clean up generated files
make run            # Run development server
make run-prod       # Run production server with gunicorn
make docker-build   # Build Docker image
make docker-run     # Run Docker container
```

### Running Tests

```bash
# Run all tests with coverage
make test

# Run specific test file
pytest tests/test_api.py

# Run with verbose output
pytest -vv

# Generate coverage report
pytest --cov-report=html --cov-report=term
```

### Code Quality

```bash
# Format code
make format

# Run linting
make lint

# Run pre-commit hooks
make pre-commit
```

## 🔒 Security

- ✅ Non-root user in Docker containers
- ✅ Environment variables for secrets (never committed)
- ✅ Rate limiting enabled (30 req/min for transcripts)
- ✅ CORS configured (update for production domains)
- ✅ Input validation on all endpoints
- ✅ Security headers and timeouts
- ✅ Regular dependency updates via Dependabot

### Production Security Checklist

- [ ] Configure CORS for specific domains only
- [ ] Use HTTPS with valid SSL certificates
- [ ] Store secrets in proper secret management (AWS Secrets Manager, etc.)
- [ ] Enable authentication if needed
- [ ] Configure Redis for distributed rate limiting
- [ ] Set up monitoring and alerting
- [ ] Regular security audits

## 📊 Monitoring & Logs

### Health Check

```bash
curl http://localhost:9585/api/health
```

### Logs

```bash
# Docker Compose
docker-compose logs -f

# Docker
docker logs -f youtube-transcript-api

# Systemd
journalctl -u youtube-transcript-api -f
```

### Metrics

Monitor these endpoints:
- `/api/health` - Service health
- Container resource usage: `docker stats youtube-transcript-api`

## 🎯 Supported URL Formats

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/embed/VIDEO_ID`
- `VIDEO_ID` (direct video ID)

## 🔍 Troubleshooting

### "YouTube blocked the request" Error
- **Cause**: YouTube blocking your IP
- **Solution**: Configure Webshare proxy credentials in `.env`

### Port Already in Use
```bash
# Find process using port 9585
lsof -ti:9585 | xargs kill -9

# Or change port in .env
PORT=9586
```

### Container Won't Start
```bash
# Check logs
docker-compose logs

# Verify .env file exists
ls -la .env

# Check if all required env vars are set
docker-compose config
```

### Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## 🏗️ Architecture

```
youtube-transcript-api/
├── app.py                  # Main Flask application
├── templates/              # Web UI templates
│   └── index.html
├── tests/                  # Test suite
│   ├── conftest.py
│   └── test_api.py
├── .env.example            # Environment template
├── Dockerfile              # Multi-stage production build
├── docker-compose.yml      # Docker Compose configuration
├── nixpacks.toml          # Coolify/Nixpacks config
├── Makefile               # Development commands
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
└── pyproject.toml         # Python project config
```

## 📝 Technologies

- **Backend**: Flask 3.0, Flask-RESTX (Swagger), Gunicorn
- **API**: YouTube Transcript API, yt-dlp
- **Proxy**: Webshare integration
- **Rate Limiting**: Flask-Limiter
- **Testing**: pytest, pytest-flask
- **Code Quality**: black, isort, flake8, bandit
- **Deployment**: Docker, nixpacks, systemd

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`make test`)
5. Run linting (`make lint`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 🙏 Acknowledgments

- [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) - Core transcript fetching
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Video metadata extraction
- [Webshare](https://www.webshare.io) - Proxy service for bypassing restrictions

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/youtube-transcript-api/issues)
- **Documentation**: See `DOCKER.md`, `PRODUCTION.md`, `SETUP.md` for detailed guides
- **API Docs**: http://localhost:9585/api/docs

---

**Built with ❤️ for the developer community**
