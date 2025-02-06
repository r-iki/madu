from django.db import models

class HoneyData(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    honey_type = models.CharField(max_length=50, choices=[
        ('Hutan', 'Hutan'),
        ('Peternakan', 'Peternakan'),
        ('Lulut', 'Lulut'),
    ])
    spectrum_readings = models.JSONField()
    manual_label = models.CharField(max_length=100, blank=True, null=True)  # Label manual dari pengguna

    def __str__(self):
        return f"{self.timestamp} - {self.honey_type} ({self.manual_label})"
