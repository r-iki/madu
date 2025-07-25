from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import SpectralReading
import json

@csrf_exempt
def sensor_data_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validate data: ensure all required fields are present
            required_fields = [
                'name',
                # Ultraviolet (AS72653)
                'uv_410', 'uv_435', 'uv_460', 'uv_485', 'uv_510', 'uv_535',
                # Visible (AS72652)
                'vis_560', 'vis_585', 'vis_645', 'vis_705', 'vis_900', 'vis_940',
                # Near Infrared (AS72651)
                'nir_610', 'nir_680', 'nir_730', 'nir_760', 'nir_810', 'nir_860',
                # Temperature
                'temperature'
            ]
            
            if not all(field in data for field in required_fields):
                return JsonResponse({'status': 'error', 'message': 'Missing fields'}, status=400)
            
            # Save data to the database
            reading = SpectralReading.objects.create(
                name=data['name'],
                # Ultraviolet
                uv_410=data['uv_410'],
                uv_435=data['uv_435'],
                uv_460=data['uv_460'],
                uv_485=data['uv_485'],
                uv_510=data['uv_510'],
                uv_535=data['uv_535'],
                # Visible
                vis_560=data['vis_560'],
                vis_585=data['vis_585'],
                vis_645=data['vis_645'],
                vis_705=data['vis_705'],
                vis_900=data['vis_900'],
                vis_940=data['vis_940'],
                # Near Infrared
                nir_610=data['nir_610'],
                nir_680=data['nir_680'],
                nir_730=data['nir_730'],
                nir_760=data['nir_760'],
                nir_810=data['nir_810'],
                nir_860=data['nir_860'],
                # Temperature
                temperature=data['temperature']
            )
            
            # Sertakan kode dalam respons
            return JsonResponse({'status': 'success', 'id': reading.id, 'kode': reading.kode})
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

@csrf_exempt
def get_sensor_data(request):
    if request.method == 'GET':
        try:
            readings = SpectralReading.objects.all().values(
                'id', 'name', 'kode', 'timestamp',
                'uv_410', 'uv_435', 'uv_460', 'uv_485', 'uv_510', 'uv_535',
                'vis_560', 'vis_585', 'vis_645', 'vis_705', 'vis_900', 'vis_940',
                'nir_610', 'nir_680', 'nir_730', 'nir_760', 'nir_810', 'nir_860',
                'temperature'
            )
            return JsonResponse(list(readings), safe=False)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)