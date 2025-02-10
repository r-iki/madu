import json
from channels.generic.websocket import AsyncWebsocketConsumer

class SensorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Pastikan self.channel_layer sudah terisi dari konfigurasi CHANNEL_LAYERS
        await self.channel_layer.group_add("sensor_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("sensor_group", self.channel_name)

    async def receive(self, event):
        # Proses data yang diterima...
        await self.send(text_data=json.dumps(event['data']))

