# Gunakan Python sebagai base image
FROM python:3.12-slim

# Set environment
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory ke src
WORKDIR /app

# Salin file requirements.txt
COPY src/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh folder src
COPY src .

# Jalankan server Django
CMD ["python", "manage.py", "runserver", "madu.software:8000"]
