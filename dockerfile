# Gunakan Python sebagai base image
FROM python:3.12-slim



# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory ke /app
WORKDIR /app

# Install system dependencies for some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Explicitly install joblib and scikit-learn first
RUN pip install --upgrade pip && \
    pip install joblib==1.3.2 scikit-learn==1.2.2

# Install other dependencies
COPY requirements.txt ml-requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
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
