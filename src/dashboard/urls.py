from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('setup/', views.sensor_setup_view, name='sensor_setup'),
    path('database/', views.database_view, name='database'),
    path('update-sensor-data/', views.update_sensor_data, name='update-sensor-data'),
    path('update-data-name-batch/', views.update_data_name_batch, name='update-data-name-batch'),
    path('delete-data-id/', views.delete_data_id, name='delete-data-id'),
    
    # ESP32 Control URLs
    path('esp32/', views.esp32_control_view, name='esp32_control'),
    path('esp32/serial/', views.esp32_serial_monitor, name='esp32_serial_monitor'),
    path('esp32/command/', views.esp32_command, name='esp32_command'),
    path('esp32/wifi-config/', views.esp32_wifi_config, name='esp32_wifi_config'),
    path('esp32/device-config/', views.esp32_device_config, name='esp32_device_config'),
    path('esp32/readings/', views.esp32_sensor_readings, name='esp32_sensor_readings'),
    path('esp32/start-measurement/', views.esp32_start_measurement, name='esp32_start_measurement'),
    path('esp32/status/', views.esp32_get_status, name='esp32_get_status'),
    
    # ESP32 Device Management URLs
    path('esp32/dashboard/', views.esp32_dashboard, name='esp32_dashboard'),
    path('esp32/add/', views.esp32_add, name='esp32_add'),
    path('esp32/connect/<int:device_id>/', views.esp32_connect, name='esp32_connect'),
    path('esp32/connect/', views.esp32_connect, name='esp32_connect_new'),
    path('esp32/settings/<int:device_id>/', views.esp32_settings, name='esp32_settings'),
    path('esp32/data/<int:device_id>/', views.esp32_data, name='esp32_data'),
    path('esp32/bluetooth-wifi/', views.bluetooth_wifi_config_view, name='bluetooth_wifi_config'),
    
    # ESP32 API Endpoints
    path('esp32/api/update-connection/', views.esp32_update_connection, name='esp32_update_connection'),
    path('esp32/api/update-wifi/', views.esp32_update_wifi, name='esp32_update_wifi'),
    path('esp32/api/save-data/', views.esp32_save_data, name='esp32_save_data'),
]
