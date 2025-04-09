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

@login_required
def sensor_setup_view(request):
    """
    View untuk merender halaman pengaturan sensor AS7265X.
    """
    return render(request, 'partials/dashboard/setup.html')

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
                        value = str(value).strip() if value else "Unknown"  # Hapus spasi di awal/akhir
                        words = value.split()  # Pisahkan nama berdasarkan spasi
                        print(f"DEBUG: Name = {value}, Words = {words}")  # Debugging
                        reading.kode = '-'.join([word[0].upper() for word in words if word])  # Ambil huruf pertama dari setiap kata
                        print(f"DEBUG: Generated Kode = {reading.kode}")  # Debugging
                    elif field == 'timestamp':  # Konversi string ke datetime
                        try:
                            value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            return JsonResponse({'status': 'error', 'message': 'Format timestamp tidak valid'}, status=400)
                    setattr(reading, field, value)

            reading.save()

            return JsonResponse({'status': 'success', 'message': 'Data berhasil diperbarui!', 'kode': reading.kode})
        except SpectralReading.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Data tidak ditemukan'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Metode tidak diizinkan'}, status=405)

@csrf_exempt
def update_data_name_batch(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ids = data.get('ids', [])  # Ambil daftar ID
            new_name = data.get('name', None)  # Ambil nama baru

            if not ids or not new_name:
                return JsonResponse({'status': 'error', 'message': 'IDs atau nama baru tidak ditemukan'}, status=400)

            # Perbarui nama dan kode untuk semua ID yang diberikan
            readings = SpectralReading.objects.filter(id__in=ids)
            updated_count = 0

            for reading in readings:
                reading.name = new_name
                words = new_name.split()  # Pisahkan nama berdasarkan spasi
                reading.kode = '-'.join([word[0].upper() for word in words if word])  # Ambil huruf pertama dari setiap kata
                reading.save()
                updated_count += 1

            if updated_count == 0:
                return JsonResponse({'status': 'error', 'message': 'Tidak ada data yang diperbarui'}, status=404)

            return JsonResponse({'status': 'success', 'message': f'{updated_count} data berhasil diperbarui!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Metode tidak diizinkan'}, status=405)


@csrf_exempt
def delete_data_id(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            sensor_id = data.get('id')
            
            # Use the correct model (SpectralReading)
            SpectralReading.objects.filter(id=sensor_id).delete()
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})