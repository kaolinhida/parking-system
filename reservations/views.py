import math
from datetime import datetime
from decimal import Decimal

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

    if request.method == 'POST':
        form = ReservationForm(request.POST)

        if form.is_valid():
            reservation = Reservation(
                user=request.user,
                parking_space=parking_space,
                tariff=tariff,
                car_number=form.cleaned_data['car_number'].upper(),
                start_time=start_datetime,
                end_time=end_datetime,
                price_per_hour=price_per_hour,
                total_price=total_price,
                status=Reservation.STATUS_ACTIVE,
            )

            try:
                reservation.full_clean()
                reservation.save()
                return redirect('accounts:profile')
            except ValidationError as error:
                form.add_error(None, error)
    else:
        form = ReservationForm()

    return render(request, 'reservations/create_reservation.html', {
        'form': form,
        'parking_space': parking_space,
        'tariff': tariff,
        'start_datetime': start_datetime,
        'end_datetime': end_datetime,
        'duration_hours': duration_hours,
        'total_price': total_price,
    })