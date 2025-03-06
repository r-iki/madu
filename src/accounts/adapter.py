from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_email
from django.contrib.auth import get_user_model

class MyAccountAdapter(DefaultAccountAdapter):
    def authenticate(self, request, **credentials):
        User = get_user_model()
        login = credentials.get("username")  # Bisa username atau email
        password = credentials.get("password")

        if login:
            # Cari user berdasarkan username atau email
            user = User.objects.filter(username=login).first() or User.objects.filter(email=login).first()
            if user and user.check_password(password):
                return user

        return None
