from django.urls import path
from .views import profile_view, edit_profile

urlpatterns = [
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', edit_profile, name='edit_profile')
]
