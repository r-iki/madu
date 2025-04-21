from django.urls import path
from .views import database_view, esp32_dashboard, esp32_connect, esp32_settings, esp32_add, esp32_data, esp32_update_connection, esp32_update_wifi, esp32_save_data

urlpatterns = [
    path('database/', database_view, name='database'),
    
    # ESP32 Management URLs
    path('esp32/', esp32_dashboard, name='esp32_dashboard'),
    path('esp32/add/', esp32_add, name='esp32_add'),
    path('esp32/connect/', esp32_connect, name='esp32_connect_new'),
    path('esp32/connect/<int:device_id>/', esp32_connect, name='esp32_connect'),
    path('esp32/settings/<int:device_id>/', esp32_settings, name='esp32_settings'),
    path('esp32/data/<int:device_id>/', esp32_data, name='esp32_data'),
    
    # ESP32 API Endpoints
    path('esp32/api/update-connection/', esp32_update_connection, name='esp32_update_connection'),
    path('esp32/api/update-wifi/', esp32_update_wifi, name='esp32_update_wifi'),
    path('esp32/api/save-data/', esp32_save_data, name='esp32_save_data'),
]
