from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Tambahkan field tambahan sesuai kebutuhan
    bio = models.TextField(blank=True)
    image = models.ImageField(upload_to='profile_images/', default='default-profile.png')

    def __str__(self):
        return f"{self.user.username}'s profile"
