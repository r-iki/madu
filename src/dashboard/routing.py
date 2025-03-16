from django.urls import re_path,path
from .consumers import SensorConsumer,SensorControlConsumer

websocket_urlpatterns = [
    path("ws/sensor/", SensorConsumer.as_asgi()),
    re_path(r'ws/sensor-control/$', SensorControlConsumer.as_asgi()),
]