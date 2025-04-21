from django.db import models
from django.contrib.auth.models import User
import json

# Create your models here.
class ESP32Settings(models.Model):
    """Model to store user-specific ESP32 settings"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='esp32_settings')
    name = models.CharField(max_length=100, default="My ESP32")
    device_id = models.CharField(max_length=50, blank=True, null=True)
    wifi_ssid = models.CharField(max_length=100, blank=True, null=True)
    wifi_password = models.CharField(max_length=100, blank=True, null=True)
    integration_time = models.IntegerField(default=100)  # in ms
    gain = models.FloatField(default=1.0)
    led_brightness = models.IntegerField(default=50)  # 0-100%
    sampling_interval = models.IntegerField(default=1000)  # in ms
    is_connected = models.BooleanField(default=False)
    last_connected = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s ESP32 - {self.name}"

class DynamicSensor(models.Model):
    """Model to define different types of sensors"""
    name = models.CharField(max_length=100)
    sensor_type = models.CharField(max_length=50)
    unit = models.CharField(max_length=20, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} ({self.sensor_type})"

class DynamicSensorData(models.Model):
    """Model to store dynamic sensor readings from ESP32"""
    esp32 = models.ForeignKey(ESP32Settings, on_delete=models.CASCADE, related_name='sensor_data')
    timestamp = models.DateTimeField(auto_now_add=True)
    sensor = models.ForeignKey(DynamicSensor, on_delete=models.CASCADE, related_name='readings')
    value = models.FloatField()
    json_data = models.TextField(blank=True, null=True)  # For storing additional JSON data
    
    def __str__(self):
        return f"{self.sensor.name} reading from {self.esp32.name} at {self.timestamp}"
    
    def set_json_data(self, data_dict):
        self.json_data = json.dumps(data_dict)
    
    def get_json_data(self):
        if self.json_data:
            return json.loads(self.json_data)
        return {}
