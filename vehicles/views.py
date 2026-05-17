from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from reservations.models import Reservation
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

            messages.success(request, 'Автомобіль успішно додано.')
            return redirect('vehicles:vehicle_list')
    else:
        form = VehicleForm()

    return render(request, 'vehicles/vehicle_form.html', {
        'form': form,
        'is_edit': False,
    })


@login_required
def vehicle_edit(request, vehicle_id):
    vehicle = get_object_or_404(
        Vehicle,
        id=vehicle_id,
        user=request.user,
        is_active=True
    )

    if request.method == 'POST':
        form = VehicleForm(request.POST, request.FILES, instance=vehicle)

        if form.is_valid():
            form.save()

            messages.success(request, 'Дані автомобіля успішно оновлено.')
            return redirect('vehicles:vehicle_list')
    else:
        form = VehicleForm(instance=vehicle)

    return render(request, 'vehicles/vehicle_form.html', {
        'form': form,
        'vehicle': vehicle,
        'is_edit': True,
    })


@login_required
def vehicle_deactivate(request, vehicle_id):
    vehicle = get_object_or_404(
        Vehicle,
        id=vehicle_id,
        user=request.user,
        is_active=True
    )

    if request.method != 'POST':
        return redirect('vehicles:vehicle_list')

    has_active_reservations = vehicle.reservations.filter(
        status__in=[
            Reservation.STATUS_ACTIVE,
            Reservation.STATUS_CHECKED_IN,
        ]
    ).exists()

    if has_active_reservations:
        messages.error(
            request,
            'Неможливо видалити авто з гаража, поки воно має активне бронювання або перебуває на парковці.'
        )
        return redirect('vehicles:vehicle_list')

    vehicle.is_active = False
    vehicle.save()

    messages.success(request, 'Автомобіль видалено з гаража.')
    return redirect('vehicles:vehicle_list')