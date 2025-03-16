from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from .models import Profile

class MyAccountAdapter(DefaultAccountAdapter):
    def authenticate(self, request, **credentials):
        login = credentials.get("username") or credentials.get("email")
        password = credentials.get("password")

        if login:
            # Cari user berdasarkan username atau email
            user = User.objects.filter(username=login).first() or User.objects.filter(email=login).first()
            if user and user.check_password(password):
                return user

        return None

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        # Ambil data dari Google
        extra_data = sociallogin.account.extra_data
        google_avatar_url = extra_data.get('picture')  # URL gambar profil dari Google

        # Buat atau perbarui profil pengguna
        profile, created = Profile.objects.get_or_create(user=user)
        if google_avatar_url:
            profile.google_avatar_url = google_avatar_url
            profile.save()

        return user
