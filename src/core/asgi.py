"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.
"""

import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Inisialisasi Django sebelum mengimpor aplikasi lain
django.setup()

# Import setelah django.setup()
from dashboard.routing import websocket_urlpatterns as dashboard_websocket_urlpatterns
from ml.routing import websocket_urlpatterns as ml_websocket_urlpatterns

# Gabungkan pola URL WebSocket dari kedua aplikasi
combined_websocket_urlpatterns = dashboard_websocket_urlpatterns + ml_websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            combined_websocket_urlpatterns
        )
    ),
})
