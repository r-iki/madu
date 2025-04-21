from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import User
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

        try:
            # Ambil data dari provider sosial (Google atau GitHub)
            extra_data = sociallogin.account.extra_data
            provider = sociallogin.account.provider
            
            # Log data untuk debugging
            print(f"Provider: {provider}")
            print(f"Extra data: {extra_data}")
            
            # Ambil avatar URL berdasarkan provider
            avatar_url = None
            if provider == 'google':
                avatar_url = extra_data.get('picture')
            elif provider == 'github':
                avatar_url = extra_data.get('avatar_url')

            # Buat atau perbarui profil pengguna
            if avatar_url:
                profile, created = Profile.objects.get_or_create(user=user)
                profile.google_avatar_url = avatar_url
                profile.save()
                
        except Exception as e:
            print(f"Error saving social profile: {e}")
            # Don't prevent user creation if profile saving fails

        return user
