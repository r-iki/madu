from django.test import TestCase
from rest_framework.test import APIClient

class SensorDataAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_post_sensor_data(self):
        data = {
            "name": "ESP32-TEST",
            # Ultraviolet (AS72653)
            "uv_410": 12.34,
            "uv_435": 15.67,
            "uv_460": 18.90,
            "uv_485": 22.11,
            "uv_510": 25.43,
            "uv_535": 28.76,
            # Visible (AS72652)
            "vis_560": 31.09,
            "vis_585": 34.32,
            "vis_645": 37.65,
            "vis_705": 40.98,
            "vis_900": 44.21,
            "vis_940": 47.54,
            # Near Infrared (AS72651)
            "nir_610": 10.12,
            "nir_680": 13.45,
            "nir_730": 16.78,
            "nir_760": 20.11,
            "nir_810": 23.44,
            "nir_860": 26.77,
        }
        response = self.client.post('/api/sensor-data/', data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertIn("sensor_name", response.data)
