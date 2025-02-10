from django import forms
from .models import Profile

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'image']  # sesuaikan dengan field yang Anda miliki di model Profile
