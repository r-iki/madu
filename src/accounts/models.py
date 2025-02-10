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

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Tambahkan field tambahan sesuai kebutuhan
    bio = models.TextField(blank=True)
    image = models.ImageField(upload_to=images_file_upload, default='default-profile.png')

    def __str__(self):
        return f"{self.user.username}'s profile"
