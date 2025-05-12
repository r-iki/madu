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

# Salin seluruh folder src ke app root
# This makes the src directory contents available at the app root
COPY src/ .

# Kumpulkan static files
RUN python manage.py collectstatic --noinput || echo "No static files to collect"

# Expose port yang akan digunakan oleh daphne
EXPOSE 8000

# Jalankan menggunakan daphne untuk ASGI/Channels support
CMD ["daphne", "core.asgi:application", "--bind", "0.0.0.0", "--port", "8000"]
