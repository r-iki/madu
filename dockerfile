# Gunakan Python sebagai base image
FROM python:3.12-slim



# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory ke /app
WORKDIR /app

# Salin file requirements.txt dan install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

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
CMD ["daphne", "core.asgi:application", "--bind", "0.0.0.0", "--port", "8000"]
