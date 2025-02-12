import json
from channels.generic.websocket import AsyncWebsocketConsumer
from sensors.models import SpectralReading
from django.utils.timezone import now
from asgiref.sync import sync_to_async


class SensorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("sensor_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("sensor_group", self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        # Simpan ke database secara async
        spectral_reading = await self.save_spectral_reading(data)

        # Broadcast data ke frontend setelah tersimpan
        await self.channel_layer.group_send(
            "sensor_group",
            {
                "type": "sensor.update",
                "data": {
                    "id": spectral_reading.id,
                    "name": spectral_reading.name,
                    "timestamp": spectral_reading.timestamp.isoformat(),
                    "uv_410": spectral_reading.uv_410,
                    "uv_435": spectral_reading.uv_435,
                    "uv_460": spectral_reading.uv_460,
                    "uv_485": spectral_reading.uv_485,
                    "uv_510": spectral_reading.uv_510,
                    "uv_535": spectral_reading.uv_535,
                    "vis_560": spectral_reading.vis_560,
                    "vis_585": spectral_reading.vis_585,
                    "vis_645": spectral_reading.vis_645,
                    "vis_705": spectral_reading.vis_705,
                    "vis_900": spectral_reading.vis_900,
                    "vis_940": spectral_reading.vis_940,
                    "nir_610": spectral_reading.nir_610,
                    "nir_680": spectral_reading.nir_680,
                    "nir_730": spectral_reading.nir_730,
                    "nir_760": spectral_reading.nir_760,
                    "nir_810": spectral_reading.nir_810,
                    "nir_860": spectral_reading.nir_860,
                },
            },
        )

    async def sensor_update(self, event):
        """Mengirimkan update ke frontend."""
        await self.send(text_data=json.dumps(event["data"]))

    @sync_to_async
    def save_spectral_reading(self, data):
        """Menyimpan data ke database dalam thread sinkron."""
        return SpectralReading.objects.create(
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
