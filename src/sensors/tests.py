from django.test import TestCase
from rest_framework.test import APIClient



class SensorDataAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_post_sensor_data(self):
        data = {
    "name": "ESP32-TEST",
    "v410": 12.34,
    "v440": 15.67,
    "v470": 18.90,
    "v510": 22.11,
    "v550": 25.43,
    "v583": 28.76,
    "n680": 31.09,
    "n705": 34.32,
    "n730": 37.65,
    "n760": 40.98,
    "n810": 44.21,
    "n860": 47.54,
    "u350": 10.12,
    "u385": 13.45,
    "u420": 16.78,
    "u450": 20.11,
    "u475": 23.44,
    "u600": 26.77,
        }
        response = self.client.post('/api/sensor-data/', data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertIn("sensor_name", response.data)
