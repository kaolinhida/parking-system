from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from reservations.models import Reservation
from .forms import AccessCodeForm


@staff_member_required
def access_control_home(request):
    form = AccessCodeForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        access_token = form.cleaned_data['access_token']
        return redirect('access_control:reservation_detail', access_token=access_token)

    return render(request, 'access_control/home.html', {
        'form': form,
    })


@staff_member_required
def reservation_detail(request, access_token):
    reservation = get_object_or_404(
        Reservation.objects.select_related(
            'user',
            'parking_space',
            'parking_space__parking_lot',
            'parking_space__space_type',
            'vehicle',
        ),
        access_token=access_token
    )

    now = timezone.now()

    can_check_in = (
        reservation.status == Reservation.STATUS_ACTIVE
        and reservation.check_in_time is None
        and reservation.start_time <= now <= reservation.end_time
    )

    can_check_out = (
        reservation.status == Reservation.STATUS_CHECKED_IN
        and reservation.check_in_time is not None
        and reservation.check_out_time is None
    )

    return render(request, 'access_control/reservation_detail.html', {
        'reservation': reservation,
        'now': now,
        'can_check_in': can_check_in,
        'can_check_out': can_check_out,
    })


@staff_member_required
def check_in(request, access_token):
    reservation = get_object_or_404(Reservation, access_token=access_token)

    if request.method != 'POST':
        return redirect('access_control:reservation_detail', access_token=access_token)

    now = timezone.now()

    if reservation.status != Reservation.STATUS_ACTIVE:
        messages.error(request, 'В’їзд неможливий: бронювання не є активним.')
        return redirect('access_control:reservation_detail', access_token=access_token)

    if reservation.check_in_time is not None:
        messages.error(request, 'В’їзд уже було підтверджено раніше.')
        return redirect('access_control:reservation_detail', access_token=access_token)

    if not (reservation.start_time <= now <= reservation.end_time):
        messages.error(request, 'В’їзд неможливий: поточний час не входить у період бронювання.')
        return redirect('access_control:reservation_detail', access_token=access_token)

    reservation.check_in_time = now
    reservation.status = Reservation.STATUS_CHECKED_IN
    reservation.save()

    messages.success(request, 'В’їзд підтверджено. Автомобіль позначено як такий, що заїхав на парковку.')
    return redirect('access_control:reservation_detail', access_token=access_token)


@staff_member_required
def check_out(request, access_token):
    reservation = get_object_or_404(Reservation, access_token=access_token)

    if request.method != 'POST':
        return redirect('access_control:reservation_detail', access_token=access_token)

    if reservation.status != Reservation.STATUS_CHECKED_IN:
        messages.error(request, 'Виїзд неможливий: автомобіль ще не позначено як такий, що заїхав.')
        return redirect('access_control:reservation_detail', access_token=access_token)

    if reservation.check_out_time is not None:
        messages.error(request, 'Виїзд уже було підтверджено раніше.')
        return redirect('access_control:reservation_detail', access_token=access_token)

    reservation.check_out_time = timezone.now()
    reservation.status = Reservation.STATUS_COMPLETED
    reservation.save()

    messages.success(request, 'Виїзд підтверджено. Бронювання завершено.')
    return redirect('access_control:reservation_detail', access_token=access_token)