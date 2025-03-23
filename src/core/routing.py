from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from dashboard.consumers import SensorConsumer,SensorControlConsumer

application = ProtocolTypeRouter({
    "websocket": URLRouter([
        path("ws/sensor/", SensorConsumer.as_asgi()),
        path("ws/sensor-control/", SensorControlConsumer.as_asgi()),
    ]),
})