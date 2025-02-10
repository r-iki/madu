from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from .forms import ProfileForm  
from .models import Profile

@login_required
def profile_view(request):
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

def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user.profile)
    return render(request, 'accounts/edit_profile.html', {'form': form})