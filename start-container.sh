#!/bin/bash
# This script runs at container startup to import ML models from R2 storage

echo "=================================================="
echo "Starting container initialization on $(date)"
echo "=================================================="

# Change to the src directory
cd /app/src

# Detect if we're running on Heroku
if [ -n "$DYNO" ]; then
  echo "Detected Heroku environment!"
  echo "Enabling cloud-only mode for ML models"
  export FORCE_R2=true
  export ML_CLOUD_ONLY=true
  echo "ML models will be loaded directly from cloud storage without downloading"
fi

# Maximum number of download attempts
MAX_ATTEMPTS=3
attempt=1
success=false

while [ $attempt -le $MAX_ATTEMPTS ] && [ "$success" = false ]; do
  echo ""
  echo "Attempt $attempt/$MAX_ATTEMPTS: Importing ML models from Cloudflare R2..."
  
  # Import ML models from Cloudflare R2 with verification
  if [ $attempt -gt 1 ]; then
    echo "Using force flag to ensure complete re-download..."
    python manage.py import_models_from_r2 --retry 3 --verify --force
  else
    python manage.py import_models_from_r2 --retry 3 --verify
  fi
  
  # Verify all required models were downloaded and can be loaded
  echo "Verifying ML models can be properly loaded..."
  if python verify_models.py; then
    echo "✅ All models verified successfully!"
    success=true
  else
    echo "❌ Model verification failed on attempt $attempt"
    
    # Special handling for Heroku environment
    if [ -n "$DYNO" ] && [ $attempt -ge $MAX_ATTEMPTS ]; then
      echo "On Heroku with persistent model loading failures."
      echo "Will continue anyway and rely on direct R2 loading at runtime."
      break
    fi
    
    attempt=$((attempt+1))
    
    if [ $attempt -le $MAX_ATTEMPTS ]; then
      echo "Waiting 5 seconds before retrying..."
      sleep 5
    fi
  fi
done

if [ "$success" = false ]; then
  echo ""
  echo "WARNING: Failed to verify all models after $MAX_ATTEMPTS attempts."
  
  if [ -n "$DYNO" ]; then
    echo "Running on Heroku with R2 priority mode enabled."
    echo "The application will attempt to load models directly from R2 at runtime."
    echo "This should resolve the 'Scaler not loaded' error in previous deployments."
  else
    echo "The application may still function if it can load models from R2 on demand."
    echo "Check the logs for specific errors."
  fi
  echo ""
fi

# Start the application with the command passed to the script
echo "===================================================="
echo "Starting application at $(date)"
echo "===================================================="
exec "$@"
