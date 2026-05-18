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

    overtime_debt_count = 0
    overtime_debt_sum = 0
    unpaid_base_count = 0
    unpaid_overtime_count = 0

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

        if reservation.overtime_fee_display:
            overtime_debt_count += 1
            overtime_debt_sum += reservation.overtime_fee_display

            if not reservation.overtime_is_paid:
                unpaid_overtime_count += 1

        if (
            reservation.status != Reservation.STATUS_CANCELLED
            and not reservation.is_paid
        ):
            unpaid_base_count += 1

    profile_messages = []

    if active_count:
        profile_messages.append({
            'level': 'info',
            'title': 'Активне бронювання',
            'text': f'У вас є активні бронювання: {active_count}. Перевірте час початку та QR-код для доступу.',
        })

    if checked_in_count:
        profile_messages.append({
            'level': 'info',
            'title': 'Авто на парковці',
            'text': f'Автомобілі зараз перебувають на парковці: {checked_in_count}. Після виїзду оператор підтвердить завершення.',
        })

    if overtime_debt_count:
        profile_messages.append({
            'level': 'warning',
            'title': 'Є доплата за перевищення часу',
            'text': f'Зафіксовано доплати у {overtime_debt_count} бронюваннях на суму {overtime_debt_sum} грн.',
        })

    if unpaid_base_count:
        profile_messages.append({
            'level': 'warning',
            'title': 'Базова оплата очікується',
            'text': f'Базова оплата не позначена як оплачена у {unpaid_base_count} бронюваннях.',
        })

    if unpaid_overtime_count:
        profile_messages.append({
            'level': 'warning',
            'title': 'Доплата не оплачена',
            'text': f'Є неоплачені доплати за перевищення часу: {unpaid_overtime_count}.',
        })

    if not profile_messages:
        profile_messages.append({
            'level': 'success',
            'title': 'Усе гаразд',
            'text': 'Немає активних проблем, боргів або неоплачених доплат.',
        })

    return render(request, 'accounts/profile.html', {
        'reservations': reservations,
        'profile_messages': profile_messages,
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
