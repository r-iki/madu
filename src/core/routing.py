# This file is provided for compatibility with the ASGI_APPLICATION setting
# The actual WebSocket routing is handled in asgi.py
import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

# Import from other apps
from dashboard.routing import websocket_urlpatterns as dashboard_websocket_urlpatterns
from ml.routing import websocket_urlpatterns as ml_websocket_urlpatterns

# Combine websocket patterns
combined_websocket_urlpatterns = dashboard_websocket_urlpatterns + ml_websocket_urlpatterns

# Create application
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            combined_websocket_urlpatterns
        )
    ),
})