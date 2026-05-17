from decimal import Decimal

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import F, Sum
from django.shortcuts import render
from django.utils import timezone

from reservations.models import Reservation
from .forms import ReportFilterForm


@staff_member_required
def reports_home(request):
    now = timezone.now()

    Reservation.objects.filter(
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
        .select_related(
            'user',
            'parking_space',
            'parking_space__parking_lot',
            'parking_space__space_type',
            'vehicle',
        )
        .order_by('-start_time')
    )

    form = ReportFilterForm(request.GET or None)

    if form.is_valid():
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        parking_lot = form.cleaned_data.get('parking_lot')
        status = form.cleaned_data.get('status')

        if date_from:
            reservations = reservations.filter(start_time__date__gte=date_from)

        if date_to:
            reservations = reservations.filter(start_time__date__lte=date_to)

        if parking_lot:
            reservations = reservations.filter(parking_space__parking_lot=parking_lot)

        if status:
            reservations = reservations.filter(status=status)

    total_count = reservations.count()
    active_count = reservations.filter(status=Reservation.STATUS_ACTIVE).count()
    checked_in_count = reservations.filter(status=Reservation.STATUS_CHECKED_IN).count()
    completed_count = reservations.filter(status=Reservation.STATUS_COMPLETED).count()
    cancelled_count = reservations.filter(status=Reservation.STATUS_CANCELLED).count()

    financial_reservations = reservations.exclude(
        status=Reservation.STATUS_CANCELLED
    )

    total_base_sum = financial_reservations.aggregate(
        total=Sum('total_price')
    )['total'] or Decimal('0.00')

    stored_overtime_sum = financial_reservations.aggregate(
        total=Sum('overtime_fee')
    )['total'] or Decimal('0.00')

    live_overtime_sum = Decimal('0.00')
    live_overtime_count = 0

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

            live_overtime_sum += reservation.overtime_fee_display
            live_overtime_count += 1

        if reservation.status == Reservation.STATUS_COMPLETED:
            reservation.overtime_hours_display = reservation.overtime_hours(reservation.check_out_time)
            reservation.overtime_fee_display = reservation.overtime_fee
            reservation.final_price_display = reservation.final_price or reservation.total_price

    final_sum = Decimal('0.00')

    for reservation in financial_reservations:
        if reservation.final_price is not None:
            final_sum += reservation.final_price
        else:
            final_sum += reservation.total_price

    final_sum += live_overtime_sum

    total_overtime_sum = stored_overtime_sum + live_overtime_sum

    return render(request, 'reports/home.html', {
        'form': form,
        'now': now,
        'reservations': reservations,

        'total_count': total_count,
        'active_count': active_count,
        'checked_in_count': checked_in_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,

        'total_base_sum': total_base_sum,
        'stored_overtime_sum': stored_overtime_sum,
        'live_overtime_sum': live_overtime_sum,
        'total_overtime_sum': total_overtime_sum,
        'live_overtime_count': live_overtime_count,
        'final_sum': final_sum,
    })