#!/bin/bash
# This script runs at container startup to import ML models from R2 storage

echo "Starting container initialization..."

# Change to the src directory
cd /app/src

# Import ML models from Cloudflare R2
echo "Importing ML models from Cloudflare R2..."
python manage.py import_models_from_r2

# Start the application with the command passed to the script
echo "Starting application..."
exec "$@"
