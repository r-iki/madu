from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/ml/', consumers.MLTestConsumer.as_asgi()),
]
