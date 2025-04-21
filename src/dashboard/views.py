from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from sensors.models import SpectralReading
from django.http import JsonResponse
import json
from datetime import datetime
from .models import ESP32Settings, DynamicSensor, DynamicSensorData
from django.utils import timezone

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

@login_required
def database_view(request):
    """
    View untuk merender tabel sensor.
    """
    readings = SpectralReading.objects.order_by('-timestamp')  # Ambil 50 data terbaru
    context = {
        'readings': readings,
    }
    return render(request,'tabelData.html', context)

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

@login_required
def esp32_dashboard(request):
    """
    Main ESP32 dashboard view showing all user's ESP32 devices and their status
    """
    esp32_devices = ESP32Settings.objects.filter(user=request.user)
    context = {
        'esp32_devices': esp32_devices,
    }
    return render(request, 'esp32/dashboard.html', context)

@login_required
def esp32_connect(request, device_id=None):
    """
    View for connecting to ESP32 via Bluetooth and setting up WiFi
    """
    if device_id:
        esp32 = get_object_or_404(ESP32Settings, id=device_id, user=request.user)
    else:
        esp32 = None
    
    context = {
        'esp32': esp32,
    }
    return render(request, 'esp32/connect.html', context)

@login_required
def esp32_settings(request, device_id):
    """
    View for configuring ESP32 settings
    """
    esp32 = get_object_or_404(ESP32Settings, id=device_id, user=request.user)
    
    if request.method == 'POST':
        esp32.name = request.POST.get('name', esp32.name)
        esp32.integration_time = int(request.POST.get('integration_time', esp32.integration_time))
        esp32.gain = float(request.POST.get('gain', esp32.gain))
        esp32.led_brightness = int(request.POST.get('led_brightness', esp32.led_brightness))
        esp32.sampling_interval = int(request.POST.get('sampling_interval', esp32.sampling_interval))
        esp32.save()
        return redirect('esp32_dashboard')
    
    context = {
        'esp32': esp32,
    }
    return render(request, 'esp32/settings.html', context)

@login_required
def esp32_add(request):
    """
    View for adding a new ESP32 device
    """
    if request.method == 'POST':
        name = request.POST.get('name', 'My ESP32')
        esp32 = ESP32Settings.objects.create(
            user=request.user,
            name=name
        )
        return redirect('esp32_connect', device_id=esp32.id)
    
    return render(request, 'esp32/add.html')

@login_required
def esp32_data(request, device_id):
    """
    View for showing sensor data from a specific ESP32
    """
    esp32 = get_object_or_404(ESP32Settings, id=device_id, user=request.user)
    sensors = DynamicSensor.objects.filter(readings__esp32=esp32).distinct()
    
    # Get the latest readings for each sensor
    latest_readings = {}
    for sensor in sensors:
        reading = DynamicSensorData.objects.filter(
            esp32=esp32, 
            sensor=sensor
        ).order_by('-timestamp').first()
        if reading:
            latest_readings[sensor.id] = reading
    
    context = {
        'esp32': esp32,
        'sensors': sensors,
        'latest_readings': latest_readings,
    }
    return render(request, 'esp32/data.html', context)

@csrf_exempt
def esp32_update_connection(request):
    """
    API endpoint for updating ESP32 connection status
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected = data.get('connected', False)
            
            esp32 = ESP32Settings.objects.get(id=device_id)
            esp32.is_connected = connected
            if connected:
                esp32.last_connected = timezone.now()
            esp32.save()
            
            return JsonResponse({'status': 'success'})
        except ESP32Settings.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Device not found'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid method'})

@csrf_exempt
def esp32_update_wifi(request):
    """
    API endpoint for updating ESP32 WiFi settings
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            wifi_ssid = data.get('wifi_ssid')
            wifi_password = data.get('wifi_password')
            
            esp32 = ESP32Settings.objects.get(id=device_id)
            esp32.wifi_ssid = wifi_ssid
            esp32.wifi_password = wifi_password
            esp32.save()
            
            return JsonResponse({'status': 'success'})
        except ESP32Settings.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Device not found'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid method'})

@csrf_exempt
def esp32_save_data(request):
    """
    API endpoint for saving sensor data from ESP32
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            sensor_readings = data.get('readings', [])
            
            esp32 = ESP32Settings.objects.get(id=device_id)
            saved_readings = []
            
            for reading in sensor_readings:
                sensor_name = reading.get('sensor_name')
                sensor_type = reading.get('sensor_type')
                value = reading.get('value')
                unit = reading.get('unit', '')
                
                # Get or create sensor
                sensor, created = DynamicSensor.objects.get_or_create(
                    name=sensor_name,
                    sensor_type=sensor_type,
                    defaults={'unit': unit}
                )
                
                # Save reading
                sensor_data = DynamicSensorData.objects.create(
                    esp32=esp32,
                    sensor=sensor,
                    value=value
                )
                
                # Save additional data if present
                additional_data = reading.get('additional_data')
                if additional_data:
                    sensor_data.set_json_data(additional_data)
                    sensor_data.save()
                
                saved_readings.append({
                    'id': sensor_data.id,
                    'sensor': sensor_name,
                    'value': value,
                    'timestamp': sensor_data.timestamp.isoformat()
                })
            
            return JsonResponse({'status': 'success', 'readings': saved_readings})
        except ESP32Settings.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Device not found'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid method'})