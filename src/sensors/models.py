from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class SpectralReading(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    
    # Ultraviolet (AS72653)
    uv_410 = models.FloatField()
    uv_435 = models.FloatField()
    uv_460 = models.FloatField()
    uv_485 = models.FloatField()
    uv_510 = models.FloatField()
    uv_535 = models.FloatField()
    
    # Visible (AS72652)
    vis_560 = models.FloatField()
    vis_585 = models.FloatField()
    vis_645 = models.FloatField()
    vis_705 = models.FloatField()
    vis_900 = models.FloatField()
    vis_940 = models.FloatField()
    
    # Near Infrared (AS72651)
    nir_610 = models.FloatField()
    nir_680 = models.FloatField()
    nir_730 = models.FloatField()
    nir_760 = models.FloatField()
    nir_810 = models.FloatField()
    nir_860 = models.FloatField()
    
    # Temperature
    temperature = models.FloatField(default=0.0)  # Add a default value
    
    def __str__(self):
        return f"{self.name} - {self.timestamp}"
    
@receiver(post_save, sender=SpectralReading)
def send_sensor_update(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "sensor_group",
        {
            "type": "sensor.update",
            "data": {
                "timestamp": instance.timestamp.isoformat(),
                "name": instance.name,
                "uv_410": instance.uv_410,
                "uv_435": instance.uv_435,
                "uv_460": instance.uv_460,
                "uv_485": instance.uv_485,
                "uv_510": instance.uv_510,
                "uv_535": instance.uv_535,
                "vis_560": instance.vis_560,
                "vis_585": instance.vis_585,
                "vis_645": instance.vis_645,
                "vis_705": instance.vis_705,
                "vis_900": instance.vis_900,
                "vis_940": instance.vis_940,
                "nir_610": instance.nir_610,
                "nir_680": instance.nir_680,
                "nir_730": instance.nir_730,
                "nir_760": instance.nir_760,
                "nir_810": instance.nir_810,
                "nir_860": instance.nir_860,
                "temperature": instance.temperature,  # Updated field name
            },
        },
    )
