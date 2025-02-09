from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import SpectralReading
import json

@csrf_exempt
def sensor_data_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validasi data
            required_fields = ['name', 'v410', 'v440', 'v470', 'v510', 'v550', 
                              'v583', 'n680', 'n705', 'n730', 'n760', 'n810', 'n860',
                              'u350', 'u385', 'u420', 'u450', 'u475', 'u600']
            
            if not all(field in data for field in required_fields):
                return JsonResponse({'status': 'error', 'message': 'Missing fields'}, status=400)
            
            # Simpan ke database
            reading = SpectralReading.objects.create(
                name=data['name'],
                v410=data['v410'],
                v440=data['v440'],
                v470=data['v470'],
                v510=data['v510'],
                v550=data['v550'],
                v583=data['v583'],
                n680=data['n680'],
                n705=data['n705'],
                n730=data['n730'],
                n760=data['n760'],
                n810=data['n810'],
                n860=data['n860'],
                u350=data['u350'],
                u385=data['u385'],
                u420=data['u420'],
                u450=data['u450'],
                u475=data['u475'],
                u600=data['u600'],
            )
            
            return JsonResponse({'status': 'success', 'id': reading.id})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)