import math

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
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
    ).update(status=Reservation.STATUS_COMPLETED)

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
        reservation.overtime_fee_display = 0

        if (
            reservation.status == Reservation.STATUS_CHECKED_IN
            and reservation.end_time
            and now > reservation.end_time
        ):
            duration = now - reservation.end_time
            overtime_seconds = duration.total_seconds()
            overtime_hours = math.ceil(overtime_seconds / 3600)
            reservation.overtime_hours_display = max(1, overtime_hours)
            reservation.overtime_fee_display = reservation.overtime_hours_display * reservation.price_per_hour

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