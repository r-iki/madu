# Use Python as base image
FROM python:3.12-slim

# Set environment variables - disables bytecode generation and buffering
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONFAULTHANDLER=1
ENV PYTHONHASHSEED=random

# Increase pip timeout to handle poor network conditions
ENV PIP_DEFAULT_TIMEOUT=100
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies first
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    git \
    libffi-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements.txt ml-requirements.txt ./

# Install Python dependencies step-by-step for better error visibility
RUN pip install --upgrade pip && \
    pip install wheel setuptools

# Install ML dependencies first to handle core dependencies
RUN pip install --no-cache-dir --verbose -r ml-requirements.txt

# Install the rest of the requirements
RUN pip install --no-cache-dir --verbose -r requirements.txt || (echo "ERROR in requirements.txt" && cat requirements.txt && exit 1)

# Set environment to use cloud-only mode
ENV ML_CLOUD_ONLY=true

# Create directory structure with src intact
WORKDIR /app
COPY src /app/src

# Set Python path to include src directory
ENV PYTHONPATH=/app:$PYTHONPATH

# Add src to PATH for manage.py access
ENV PATH=/app/src:$PATH

# Kumpulkan static files
RUN cd src && python manage.py collectstatic --noinput || echo "No static files to collect"

# Expose port yang akan digunakan oleh daphne
EXPOSE 8000

# Copy startup script and make it executable
COPY start-container.sh /app/start-container.sh
RUN chmod +x /app/start-container.sh

# Change to app directory
WORKDIR /app

# Run startup script which will import ML models and then start daphne
CMD ["/app/start-container.sh", "cd", "/app/src", "&&", "daphne", "core.asgi:application", "--bind", "0.0.0.0", "--port", "${PORT:-8000}"]
