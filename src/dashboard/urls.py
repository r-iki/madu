from django.urls import path
from .views import database_view

urlpatterns = [
    path('database/', database_view, name='database'),
]
