from django.shortcuts import render
from sensors.models import SpectralReading
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from accounts.models import Profile


@login_required
def dashboard_view(request):
    # Ambil data terakhir untuk inisialisasi
    user_profile = Profile.objects.get(user=request.user)
    user = request.user 

    latest_data = SpectralReading.objects.last()
    context = {
        "user_name": request.user.username,
        "bio": user_profile.bio,
        "email": user.email,
        "profile_picture": user_profile.image.url if user_profile.image else None,



        'spectral_data': {
            # Ultraviolet (AS72653)
            'uv_410': latest_data.uv_410 if latest_data else 0,
            'uv_435': latest_data.uv_435 if latest_data else 0,
            'uv_460': latest_data.uv_460 if latest_data else 0,
            'uv_485': latest_data.uv_485 if latest_data else 0,
            'uv_510': latest_data.uv_510 if latest_data else 0,
            'uv_535': latest_data.uv_535 if latest_data else 0,
            # Visible (AS72652)
            'vis_560': latest_data.vis_560 if latest_data else 0,
            'vis_585': latest_data.vis_585 if latest_data else 0,
            'vis_645': latest_data.vis_645 if latest_data else 0,
            'vis_705': latest_data.vis_705 if latest_data else 0,
            'vis_900': latest_data.vis_900 if latest_data else 0,
            'vis_940': latest_data.vis_940 if latest_data else 0,
            # Near Infrared (AS72651)
            'nir_610': latest_data.nir_610 if latest_data else 0,
            'nir_680': latest_data.nir_680 if latest_data else 0,
            'nir_730': latest_data.nir_730 if latest_data else 0,
            'nir_760': latest_data.nir_760 if latest_data else 0,
            'nir_810': latest_data.nir_810 if latest_data else 0,
            'nir_860': latest_data.nir_860 if latest_data else 0,
        }
    }
    return render(request, 'dashboard.html', context)
