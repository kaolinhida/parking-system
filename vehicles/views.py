from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import VehicleForm
from .models import Vehicle


@login_required
def vehicle_list(request):
    vehicles = (
        Vehicle.objects
        .filter(user=request.user, is_active=True)
        .order_by('-created_at')
    )

    return render(request, 'vehicles/vehicle_list.html', {
        'vehicles': vehicles,
    })


@login_required
def vehicle_add(request):
    if request.method == 'POST':
        form = VehicleForm(request.POST, request.FILES)

        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.user = request.user
            vehicle.save()

            return redirect('vehicles:vehicle_list')
    else:
        form = VehicleForm()

    return render(request, 'vehicles/vehicle_form.html', {
        'form': form,
    })