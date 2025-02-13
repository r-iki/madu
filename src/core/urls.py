"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from sensors.views import sensor_data_api
from dashboard.views import update_sensor_data

urlpatterns = [
    path("__reload__/", include("django_browser_reload.urls")),
    path('accounts/', include('allauth.urls')),
    path('admin/', admin.site.urls),
    path('api/sensor-data/', sensor_data_api, name='sensor-data-api'),
    path('accounts/', include('accounts.urls')),
    path('update-sensor/', update_sensor_data, name='update_sensor'),
]

from dashboard.views import dashboard_view

urlpatterns += [
    path('', dashboard_view, name='dashboard'),
]


from django.conf.urls import handler404
handler404 = 'core.views.custom_404_view'

from . import views
urlpatterns += [
    path('send-test-email/', views.send_test_email),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)