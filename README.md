# ML Model Cloud Storage

This project uses Cloudflare R2 storage for ML models, allowing models to be loaded directly from cloud storage without requiring local downloads, similar to how static files and media files are handled.

## Cloud-Only Mode

By default, the application is configured to use "cloud-only" mode for ML models, where:

1. Models are loaded directly from Cloudflare R2 cloud storage
2. No local copies are saved to disk
3. This is especially useful for ephemeral environments like Heroku where local filesystem changes may not persist

### Environment Variables

You can control model storage behavior using the following environment variables:

- `ML_CLOUD_ONLY`: Set to "true" (default) for cloud-only mode, "false" to enable local caching of models
- `FORCE_R2`: Set to "true" to force using R2 storage even in development mode

### Heroku Deployment

On Heroku, cloud-only mode is automatically enabled to solve the "Scaler not loaded" error that was previously occurring due to Heroku's ephemeral filesystem.

## Implementation Details

The `ModelStorageManager` class handles loading and saving ML models from cloud storage:

- Loads models directly from Cloudflare R2 using memory buffers
- Can optionally save a local copy for caching purposes when not in cloud-only mode
- Falls back to local filesystem only when cloud storage fails and cloud-only mode is disabled

## Project Dependencies

The project uses Python 3.12 (as specified in `.python-version`) and depends on several packages organized into categories:

### Main Requirements File

The `requirements.txt` file contains all dependencies organized by functionality:

- Django web framework and extensions
- Asynchronous and WebSocket support
- Web server and middleware components
- Database adapters for PostgreSQL
- Authentication and security
- Configuration and environment management
- HTTP and API tools
- Cloud storage via boto3 and Cloudflare R2
- Machine learning dependencies (basic ones are included here and in ml-requirements.txt)

### ML-Specific Requirements

ML-specific dependencies are in `ml-requirements.txt` for better organization:

- Core ML packages (scikit-learn, numpy, pandas, joblib)
- Data visualization tools
- Cloud storage for ML models

### Development Setup

To install all requirements:

```bash
pip install -r requirements.txt
pip install -r ml-requirements.txt
```

For production deployment:
- The Dockerfile handles installing both requirement files
- Heroku uses both files via `Procfile`

## Testing

You can verify cloud-only operation using:

```
python src/test_cloud_only_mode.py
```

This will confirm that models can be loaded directly from cloud storage without requiring local files.
