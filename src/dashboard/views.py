from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from sensors.models import SpectralReading
from django.http import JsonResponse
import json
from datetime import datetime

@login_required
def dashboard_view(request):
    # Ambil 50 data terbaru
    readings = SpectralReading.objects.order_by('-timestamp')

    context = {
        'readings': readings,
    }
    return render(request, 'dashboard.html', context)
from django.http import JsonResponse
import json

@csrf_exempt
def update_sensor_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            reading_id = data.pop('id', None)  # Ambil ID, hapus dari data untuk mencegah update tidak disengaja

            if not reading_id:
                return JsonResponse({'status': 'error', 'message': 'ID tidak ditemukan'}, status=400)

            reading = SpectralReading.objects.get(id=reading_id)

            # Hapus data yang tidak valid
            data.pop("null", None)  # Hapus key "null" jika ada

            # Perbarui hanya field yang dikirim dalam request
            for field, value in data.items():
                if hasattr(reading, field):  # Pastikan field ada dalam model
                    if field == 'name':  # Pastikan 'name' selalu string
                        value = str(value) if value else "Unknown"
                    elif field == 'timestamp':  # Konversi string ke datetime
                        try:
                            value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            return JsonResponse({'status': 'error', 'message': 'Format timestamp tidak valid'}, status=400)
                    setattr(reading, field, value)

            reading.save()

            return JsonResponse({'status': 'success', 'message': 'Data berhasil diperbarui!'})
        except SpectralReading.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Data tidak ditemukan'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Metode tidak diizinkan'}, status=405)
