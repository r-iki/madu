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

# Install Python dependencies in a single layer to reduce image size
RUN pip install --upgrade pip && \
    pip install wheel && \
    pip install setuptools && \
    pip install joblib==1.3.2 scikit-learn==1.2.2 && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r ml-requirements.txt

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

# Change to src directory and run daphne
WORKDIR /app/src
CMD ["python", "-m", "daphne", "core.asgi:application", "--bind", "0.0.0.0", "--port", "8000"]
