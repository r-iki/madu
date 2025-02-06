# Create your views here.
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import HoneyData
import json

@csrf_exempt
def save_sensor_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            honey_type = data.get('honey_type')
            spectrum_readings = data.get('spectrum_readings')

            HoneyData.objects.create(honey_type=honey_type, spectrum_readings=spectrum_readings)
            return JsonResponse({"message": "Data berhasil disimpan"}, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
