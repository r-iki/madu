from django.urls import path
from . import views

urlpatterns = [
    # API endpoints
    path('api/predict/', views.ml_predict_api, name='ml_predict_api'),
    
    # Web views
    path('', views.ml_dashboard, name='ml_dashboard'),
    path('tests/', views.ml_test_list, name='ml_test_list'),
    path('tests/<int:pk>/', views.ml_test_detail, name='ml_test_detail'),
    path('models/', views.ml_model_list, name='ml_model_list'),
    
    # Diagnostics
    path('diagnostics/', views.ml_diagnostics, name='ml_diagnostics'),
]
