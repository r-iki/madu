from django.db.models.signals import post_save
from django.dispatch import receiver
import logging
from .models import MLTestData

logger = logging.getLogger(__name__)

@receiver(post_save, sender=MLTestData)
def handle_ml_test_data_saved(sender, instance, created, **kwargs):
    """
    Signal handler for when a new ML test is saved
    """
    if created:
        logger.info(f"New ML test data saved: {instance.id} - {instance.test_name}")
        # Additional processing can be added here if needed
