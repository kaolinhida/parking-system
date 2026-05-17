from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

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
    reservations = (
        Reservation.objects
        .filter(user=request.user)
        .select_related(
            'parking_space',
            'parking_space__parking_lot',
            'parking_space__space_type',
        )
        .order_by('-created_at')
    )

    active_count = reservations.filter(status=Reservation.STATUS_ACTIVE).count()
    checked_in_count = reservations.filter(status=Reservation.STATUS_CHECKED_IN).count()
    cancelled_count = reservations.filter(status=Reservation.STATUS_CANCELLED).count()
    completed_count = reservations.filter(status=Reservation.STATUS_COMPLETED).count()

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