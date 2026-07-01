# Use a slim Python 3.12 image
FROM python:3.12-slim

# Install system dependencies (needed for FAISS, building c-extensions, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for lightning-fast dependency resolution
RUN pip install uv

WORKDIR /app

# Copy dependency files first to leverage Docker cache
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
# We don't need a virtualenv in Docker, so we install to system
RUN uv pip install --system -r pyproject.toml

# Copy the rest of the backend source code
COPY backend/app /app/app

# Expose the FastAPI port
EXPOSE 8000

# Run the FastAPI server using Uvicorn
CMD ["uvicorn", "app.main:create_app", "--host", "0.0.0.0", "--port", "8000", "--factory"]
