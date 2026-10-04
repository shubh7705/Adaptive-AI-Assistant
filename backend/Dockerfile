# ==============================================================================
# Adaptive Chat AI - High-Performance, Minimal Backend Dockerfile
# ==============================================================================

# Stage 1: Runtime Base (Debian Bookworm Slim for glibc compatibility)
FROM python:3.11-slim-bookworm

# Avoid interactive prompts during apt installs
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    PYTHONPATH=/app \
    HF_HOME=/home/appuser/.cache/huggingface

# Install only essential runtime C libraries (libgomp1 for FAISS OpenMP, libpq5 for PostgreSQL)
# Clean apt caches immediately to minimize layer size
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy statically compiled uv binary from official image (avoids pip overhead)
COPY --from=ghcr.io/astral-sh/uv:0.6.2 /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency specifications first to leverage Docker layer caching
COPY pyproject.toml uv.lock ./

# Install trimmed dependencies directly to system Python without wheel caching
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy backend application source, anchors dataset, and persistent ChromaDB index
COPY backend/app /app/app
COPY backend/dataset /app/dataset
COPY backend/data /app/data

# Create and switch to non-root application user for container security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose FastAPI HTTP port
EXPOSE 8000

# Container healthcheck using lightweight standard-library python urllib
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# Launch Uvicorn ASGI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
