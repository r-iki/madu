from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .forms import ProfileForm  

@login_required
def profile_view(request):
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