from django.core.mail import send_mail

send_mail(
    'Test Email dari Django',
    'Halo, ini test email dari Django menggunakan Gmail.',
    'rikimchd@gmail.com',
    ['mail@riki.my.id'],
    fail_silently=False,
)
