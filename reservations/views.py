import math
from datetime import datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from parkings.models import ParkingSpace, Tariff
from .forms import ReservationForm
from .models import Reservation


def calculate_duration_hours(start_time, end_time):
    duration = end_time - start_time
    hours = duration.total_seconds() / 3600

    return max(1, math.ceil(hours))


@login_required
def create_reservation(request, space_id):
    parking_space = get_object_or_404(
        ParkingSpace.objects.select_related('parking_lot', 'space_type'),
        id=space_id,
        is_active=True
    )

    date_value = request.GET.get('date')
    start_value = request.GET.get('start_time')
    end_value = request.GET.get('end_time')

    if not date_value or not start_value or not end_value:
        return redirect('parkings:parking_detail', parking_space.parking_lot.id)

    try:
        selected_date = datetime.strptime(date_value, '%Y-%m-%d').date()
        selected_start_time = datetime.strptime(start_value, '%H:%M').time()
        selected_end_time = datetime.strptime(end_value, '%H:%M').time()

        start_datetime = timezone.make_aware(
            datetime.combine(selected_date, selected_start_time)
        )
        end_datetime = timezone.make_aware(
            datetime.combine(selected_date, selected_end_time)
        )
    except ValueError:
        return redirect('parkings:parking_detail', parking_space.parking_lot.id)

    if end_datetime <= start_datetime:
        return redirect('parkings:parking_detail', parking_space.parking_lot.id)

    tariff = get_object_or_404(
        Tariff,
        parking_lot=parking_space.parking_lot,
        space_type=parking_space.space_type,
        is_active=True
    )

    duration_hours = calculate_duration_hours(start_datetime, end_datetime)
    price_per_hour = tariff.price_per_hour
    total_price = Decimal(duration_hours) * price_per_hour

    user_vehicles = request.user.vehicles.filter(is_active=True)

    if request.method == 'POST':
        form = ReservationForm(request.POST, user=request.user)

        if form.is_valid():
            selected_vehicle = form.cleaned_data['vehicle']

            reservation = Reservation(
                user=request.user,
                parking_space=parking_space,
                vehicle=selected_vehicle,
                tariff=tariff,
                car_number=selected_vehicle.license_plate,
                start_time=start_datetime,
                end_time=end_datetime,
                price_per_hour=price_per_hour,
                total_price=total_price,
                status=Reservation.STATUS_ACTIVE,
            )

            try:
                reservation.full_clean()
                reservation.save()
                messages.success(request, 'Бронювання успішно створено.')
                return redirect('accounts:profile')
            except ValidationError as error:
                form.add_error(None, error)
    else:
        form = ReservationForm(user=request.user)

    return render(request, 'reservations/create_reservation.html', {
        'form': form,
        'parking_space': parking_space,
        'tariff': tariff,
        'start_datetime': start_datetime,
        'end_datetime': end_datetime,
        'duration_hours': duration_hours,
        'total_price': total_price,
        'has_vehicles': user_vehicles.exists(),
    })


@login_required
def cancel_reservation(request, reservation_id):
    reservation = get_object_or_404(
        Reservation,
        id=reservation_id,
        user=request.user
    )

    if request.method != 'POST':
        return redirect('accounts:profile')

    if reservation.status != Reservation.STATUS_ACTIVE:
        messages.error(request, 'Можна скасувати тільки активне бронювання.')
        return redirect('accounts:profile')

    reservation.status = Reservation.STATUS_CANCELLED
    reservation.save()

    messages.success(request, 'Бронювання успішно скасовано.')
    return redirect('accounts:profile')