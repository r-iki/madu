from django.shortcuts import render, redirect
# from sensors.models import HoneyData
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request):
#     honey_data = HoneyData.objects.all()
    
#     if request.method == "POST":
#         data_id = request.POST.get("data_id")
#         manual_label = request.POST.get("manual_label")
        
#         # Simpan label manual ke database
#         honey_entry = HoneyData.objects.get(id=data_id)
#         honey_entry.manual_label = manual_label
#         honey_entry.save()
        
#         return redirect('dashboard')

    return render(request, 'dashboard.html')
