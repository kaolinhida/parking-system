import math

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.db.models import F
from django.utils import timezone

from reservations.models import Reservation
from .forms import RegisterForm


def register(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile')

    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('accounts:profile')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {
        'form': form,
    })


@login_required
def profile(request):
    now = timezone.now()

    Reservation.objects.filter(
        user=request.user,
        status=Reservation.STATUS_ACTIVE,
        end_time__lt=now,
        check_in_time__isnull=True,
    ).update(
        status=Reservation.STATUS_COMPLETED,
        final_price=F('total_price'),
        overtime_fee=0
    )

    reservations = (
        Reservation.objects
        .filter(user=request.user)
        .select_related(
            'parking_space',
            'parking_space__parking_lot',
            'parking_space__space_type',
            'vehicle',
        )
        .order_by('-created_at')
    )

    active_count = reservations.filter(status=Reservation.STATUS_ACTIVE).count()
    checked_in_count = reservations.filter(status=Reservation.STATUS_CHECKED_IN).count()
    cancelled_count = reservations.filter(status=Reservation.STATUS_CANCELLED).count()
    completed_count = reservations.filter(status=Reservation.STATUS_COMPLETED).count()

    for reservation in reservations:
        reservation.overtime_hours_display = 0
        reservation.overtime_fee_display = reservation.overtime_fee
        reservation.final_price_display = reservation.final_price or reservation.total_price

        if (
            reservation.status == Reservation.STATUS_CHECKED_IN
            and reservation.end_time
            and now > reservation.end_time
        ):
            reservation.overtime_hours_display = reservation.overtime_hours(now)
            reservation.overtime_fee_display = reservation.calculate_overtime_fee(now)
            reservation.final_price_display = reservation.total_price + reservation.overtime_fee_display

        if reservation.status == Reservation.STATUS_COMPLETED:
            reservation.overtime_hours_display = reservation.overtime_hours(reservation.check_out_time)
            reservation.overtime_fee_display = reservation.overtime_fee
            reservation.final_price_display = reservation.final_price or reservation.total_price

    return render(request, 'accounts/profile.html', {
        'reservations': reservations,
        'active_count': active_count,
        'checked_in_count': checked_in_count,
        'cancelled_count': cancelled_count,
        'completed_count': completed_count,
    })


@login_required
def logout_user(request):
    if request.method == 'POST':
        logout(request)
        return redirect('core:home')

    return redirect('accounts:profile')