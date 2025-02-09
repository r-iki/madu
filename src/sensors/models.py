from django.db import models

class SpectralReading(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=50)
    
    # Visible Light
    v410 = models.FloatField()
    v440 = models.FloatField()
    v470 = models.FloatField()
    v510 = models.FloatField()
    v550 = models.FloatField()
    v583 = models.FloatField()
    
    # Near Infrared
    n680 = models.FloatField()
    n705 = models.FloatField()
    n730 = models.FloatField()
    n760 = models.FloatField()
    n810 = models.FloatField()
    n860 = models.FloatField()
    
    # Ultraviolet
    u350 = models.FloatField()
    u385 = models.FloatField()
    u420 = models.FloatField()
    u450 = models.FloatField()
    u475 = models.FloatField()
    u600 = models.FloatField()
    
    
    def __str__(self):
        return f"{self.name} - {self.timestamp}"