"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.
"""

import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Inisialisasi Django sebelum mengimpor aplikasi lain
django.setup()

# Import setelah django.setup()
from dashboard import consumers

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter([
        path("ws/sensor/", consumers.SensorConsumer.as_asgi()),
    ]),
})
