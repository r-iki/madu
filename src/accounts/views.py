from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from .forms import ProfileForm  
from .models import Profile
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount

@login_required
def profile_view(request):
    user = request.user
    try:
        profile = user.profile
    except ObjectDoesNotExist:
        # Buat profil jika tidak ada
        profile = Profile.objects.create(user=user)
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
        except ObjectDoesNotExist:
            # Buat profil otomatis jika tidak ada
            profile = Profile.objects.create(user=request.user)
    # Mengambil data profil pengguna dari user terkait
    profile = request.user.profile
    context = {
        'profile': profile
    }
    return render(request, 'account/profile.html', context)

@login_required
def edit_profile(request):
    profile = request.user.profile
    socialaccounts = SocialAccount.objects.filter(user=request.user)  # Ambil akun sosial yang terhubung
    social_accounts_data = [
        {
            'provider': account.provider,
            'icon_url': get_social_icon_url(account.provider),
        }
        for account in socialaccounts
    ]
    if request.method == 'POST':
        # Update user fields
        request.user.username = request.POST.get('username', request.user.username)
        request.user.email = request.POST.get('email', request.user.email)

        # Tangani full name (pisahkan menjadi first_name dan last_name)
        full_name = request.POST.get('full_name', '').strip()
        if full_name:
            name_parts = full_name.split(' ', 1)  # Pisahkan nama depan dan nama belakang
            request.user.first_name = name_parts[0]
            request.user.last_name = name_parts[1] if len(name_parts) > 1 else ''

        request.user.save()

        # Update profile fields
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        # Gabungkan first_name dan last_name untuk ditampilkan di form
        full_name = f"{request.user.first_name} {request.user.last_name}".strip()
        form = ProfileForm(instance=profile)
    return render(request, 'account/edit_profile.html', {
        'form': form,
        'profile': profile,
        'full_name': full_name,
        'social_accounts_data': social_accounts_data,  # Kirim data akun sosial ke template
    })

def get_social_icon_url(provider):
    icons = {
        'google': 'https://logos-world.net/wp-content/uploads/2020/09/Google-Symbol.png',
        'facebook': 'https://upload.wikimedia.org/wikipedia/commons/5/51/Facebook_f_logo_%282019%29.svg',
        'twitter': 'https://upload.wikimedia.org/wikipedia/en/6/60/Twitter_Logo_as_of_2021.svg',
    }
    return icons.get(provider, 'https://via.placeholder.com/40')  # Default icon