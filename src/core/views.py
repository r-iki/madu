# views.py

from django.shortcuts import render

def custom_404_view(request, exception):
    return render(request, '404.html', status=404)


from django.core.mail import send_mail
from django.http import HttpResponse

def send_test_email(request):
    send_mail(
        subject='Test Email Django',
        message='Halo! Ini adalah email percobaan dari Django.',
        from_email='rikimchd@gmail.com',  # Ganti dengan Gmail Anda
        recipient_list=['mail@riki.my.id'],  # Ganti dengan penerima
        fail_silently=False,
    )
    return HttpResponse("Email telah dikirim!")
