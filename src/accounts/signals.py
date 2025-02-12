from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from accounts.models import Profile
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.models import EmailAddress
from allauth.core.exceptions import ImmediateHttpResponse
from django.http import HttpResponseRedirect

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        # Jika User sudah ada dan disimpan kembali, simpan juga Profile-nya
        instance.profile.save()


class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        email = sociallogin.user.email
        if not email:
            return  # Tidak ada email, lanjutkan proses normal

        try:
            # Periksa apakah email sudah digunakan oleh pengguna lain
            existing_user = EmailAddress.objects.get(email=email, verified=True).user
            if existing_user:
                # Kaitkan akun sosial dengan pengguna yang sudah ada
                sociallogin.connect(request, existing_user)
                raise ImmediateHttpResponse(HttpResponseRedirect("/accounts/profile/"))
        except EmailAddress.DoesNotExist:
            pass  # Jika email belum digunakan, lanjutkan login
