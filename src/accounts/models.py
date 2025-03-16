import pathlib
import uuid
from django.db import models
from django.contrib.auth.models import User

def images_file_upload(instance, filepath):
    instance_id=instance.id
    if not instance_id:
        instance_id=1
    filepath = pathlib.Path(filepath).resolve()
    filename=str(uuid.uuid1())
    ext=filepath.suffix
    print(instance,filepath)
    return f'accounts/{instance_id}/{filename}{ext}'

def csv_file_upload(instance,filepath):
    instance_id=instance.id
    if not instance_id:
        instance_id=1
    filepath=pathlib.Path(filepath).resolve()
    filename=str(uuid.uuid1())
    ext=filepath.suffixes
    return f'accounts/{instance_id}/{filename}{ext}'




class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)  # Untuk upload gambar
    google_avatar_url = models.URLField(blank=True, null=True)  # URL gambar dari Google

    def __str__(self):
        return f"Profile of {self.user.username}"
