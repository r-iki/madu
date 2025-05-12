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

## Testing

You can verify cloud-only operation using:

```
python src/test_cloud_only_mode.py
```

This will confirm that models can be loaded directly from cloud storage without requiring local files.
