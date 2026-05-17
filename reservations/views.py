import math
from datetime import datetime
from decimal import Decimal
from io import BytesIO

import qrcode
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from parkings.models import ParkingSpace, Tariff
from .forms import ReservationForm
from .models import Reservation


def calculate_duration_hours(start_time, end_time):
    duration = end_time - start_time
    hours = duration.total_seconds() / 3600

    return max(1, math.ceil(hours))


def parse_get_datetime(date_value, start_value, end_value):
    if not date_value or not start_value or not end_value:
        return None, None

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

        if end_datetime <= start_datetime:
            return None, None

        return start_datetime, end_datetime
    except ValueError:
        return None, None


@login_required
def create_reservation(request, space_id):
    parking_space = get_object_or_404(
        ParkingSpace.objects.select_related('parking_lot', 'space_type'),
        id=space_id,
        is_active=True
    )

    tariff = get_object_or_404(
        Tariff,
        parking_lot=parking_space.parking_lot,
        space_type=parking_space.space_type,
        is_active=True
    )

    user_vehicles = request.user.vehicles.filter(is_active=True)

    date_value = request.GET.get('date')
    start_value = request.GET.get('start_time')
    end_value = request.GET.get('end_time')

    initial = {}

    if date_value:
        initial['date'] = date_value

    if start_value:
        initial['start_time'] = start_value

    if end_value:
        initial['end_time'] = end_value

    start_datetime, end_datetime = parse_get_datetime(
        date_value,
        start_value,
        end_value
    )

    duration_hours = None
    total_price = None

    if start_datetime and end_datetime:
        duration_hours = calculate_duration_hours(start_datetime, end_datetime)
        total_price = Decimal(duration_hours) * tariff.price_per_hour

    if request.method == 'POST':
        form = ReservationForm(request.POST, user=request.user)

        if form.is_valid():
            selected_vehicle = form.cleaned_data['vehicle']
            start_datetime = form.cleaned_data['start_datetime']
            end_datetime = form.cleaned_data['end_datetime']

            duration_hours = calculate_duration_hours(start_datetime, end_datetime)
            total_price = Decimal(duration_hours) * tariff.price_per_hour

            reservation = Reservation(
                user=request.user,
                parking_space=parking_space,
                vehicle=selected_vehicle,
                tariff=tariff,
                car_number=selected_vehicle.license_plate,
                start_time=start_datetime,
                end_time=end_datetime,
                price_per_hour=tariff.price_per_hour,
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
        form = ReservationForm(user=request.user, initial=initial)

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

@login_required
def reservation_qr_page(request, reservation_id):
    reservation = get_object_or_404(
        Reservation.objects.select_related(
            'parking_space',
            'parking_space__parking_lot',
            'parking_space__space_type',
            'vehicle',
        ),
        id=reservation_id,
        user=request.user
    )

    return render(request, 'reservations/reservation_qr.html', {
        'reservation': reservation,
    })


@login_required
def reservation_qr_image(request, reservation_id):
    reservation = get_object_or_404(
        Reservation,
        id=reservation_id,
        user=request.user
    )

    if not reservation.access_token:
        reservation.save()

    access_url = request.build_absolute_uri(
        reverse('access_control:reservation_detail', args=[reservation.access_token])
    )

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )

    qr.add_data(access_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color='black', back_color='white')

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return HttpResponse(buffer.getvalue(), content_type='image/png')