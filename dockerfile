# Gunakan Python sebagai base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE = 1
ENV PYTHONUNBUFFERED = 1

# Set working directory ke /app
WORKDIR /app

# Salin file requirements.txt dan install dependencies
COPY src/requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Salin seluruh folder src

COPY src .

# Kumpulkan static files (opsional)
RUN python manage.py collectstatic --noinput || echo "No static files to collect"

# Opsional: expose port 8000
EXPOSE 8000

# Jalankan server Django dengan binding ke semua interface
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
