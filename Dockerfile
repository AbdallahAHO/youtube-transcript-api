# Multi-stage build for optimized image size
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# Production stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY app.py .
COPY templates/ templates/
COPY .env* ./

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Add virtual environment to PATH
ENV PATH="/opt/venv/bin:$PATH"

# Environment variables with safe fallbacks
ENV PYTHONUNBUFFERED=${PYTHONUNBUFFERED:-1} \
    PYTHONDONTWRITEBYTECODE=${PYTHONDONTWRITEBYTECODE:-1} \
    PORT=${PORT:-9585} \
    FLASK_ENV=${FLASK_ENV:-production} \
    FLASK_DEBUG=${FLASK_DEBUG:-false} \
    GUNICORN_WORKERS=${GUNICORN_WORKERS:-4} \
    GUNICORN_TIMEOUT=${GUNICORN_TIMEOUT:-120}

# Expose port (dynamic via ARG/ENV)
ARG PORT=9585
EXPOSE ${PORT}

# Health check using curl (more reliable)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-9585}/api/health || exit 1

# Run with gunicorn using environment variables
CMD gunicorn --bind ${GUNICORN_BIND:-0.0.0.0:${PORT:-9585}} \
    --workers ${GUNICORN_WORKERS:-4} \
    --timeout ${GUNICORN_TIMEOUT:-120} \
    --access-logfile - \
    --error-logfile - \
    app:app
