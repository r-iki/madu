from django.apps import AppConfig


class MlConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ml'
    
    def ready(self):
        # Import signals to register them
        import ml.signals
