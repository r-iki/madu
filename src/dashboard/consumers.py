import json
from channels.generic.websocket import AsyncWebsocketConsumer
from sensors.models import SpectralReading
from django.utils.timezone import now

class SensorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("sensor_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("sensor_group", self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        # Simpan ke database
        spectral_reading = SpectralReading.objects.create(
            name=data.get("name", "Unknown"),
            uv_410=data.get("uv_410", 0),
            uv_435=data.get("uv_435", 0),
            uv_460=data.get("uv_460", 0),
            uv_485=data.get("uv_485", 0),
            uv_510=data.get("uv_510", 0),
            uv_535=data.get("uv_535", 0),
            vis_560=data.get("vis_560", 0),
            vis_585=data.get("vis_585", 0),
            vis_645=data.get("vis_645", 0),
            vis_705=data.get("vis_705", 0),
            vis_900=data.get("vis_900", 0),
            vis_940=data.get("vis_940", 0),
            nir_610=data.get("nir_610", 0),
            nir_680=data.get("nir_680", 0),
            nir_730=data.get("nir_730", 0),
            nir_760=data.get("nir_760", 0),
            nir_810=data.get("nir_810", 0),
            nir_860=data.get("nir_860", 0),
            timestamp=now(),
        )

        # Broadcast data ke frontend setelah tersimpan
        await self.channel_layer.group_send(
            "sensor_group",
            {
                "type": "sensor.update",
                "data": data
            }
        )

    async def sensor_update(self, event):
        await self.send(text_data=json.dumps(event["data"]))
