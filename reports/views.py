import csv
from decimal import Decimal

from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from accounts.permissions import parking_admin_required
from reservations.models import Reservation
from .forms import ReportFilterForm


def complete_expired_active_reservations(now):
    Reservation.objects.filter(
        status=Reservation.STATUS_ACTIVE,
        end_time__lt=now,
        check_in_time__isnull=True,
    ).update(
        status=Reservation.STATUS_COMPLETED,
        final_price=F('total_price'),
        overtime_fee=0
    )

def get_report_reservations():
    return (
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


def apply_report_filters(reservations, form):
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

    return reservations


def prepare_report_reservation_display(reservations, now):
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

    return live_overtime_sum, live_overtime_count


@parking_admin_required
def reports_home(request):
    now = timezone.now()
    complete_expired_active_reservations(now)

    form = ReportFilterForm(request.GET or None)
    reservations = apply_report_filters(get_report_reservations(), form)

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

    live_overtime_sum, live_overtime_count = prepare_report_reservation_display(
        reservations,
        now
    )

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


@parking_admin_required
def reports_export_csv(request):
    now = timezone.now()
    complete_expired_active_reservations(now)

    form = ReportFilterForm(request.GET or None)
    reservations = apply_report_filters(get_report_reservations(), form)
    prepare_report_reservation_display(reservations, now)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="parking_report.csv"'
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow([
        'Користувач',
        'Парковка',
        'Місце',
        'Номер авто',
        'Дата початку',
        'Дата завершення',
        'Статус',
        'Базова сума',
        'Доплата',
        'Фінальна сума',
    ])

    def format_money(value):
        if value in (None, ''):
            return ''

        return f'{value:.2f}'

    for reservation in reservations:
        final_price = ''

        if reservation.status != Reservation.STATUS_CANCELLED:
            final_price = reservation.final_price_display

        writer.writerow([
            reservation.user.username,
            reservation.parking_space.parking_lot.name,
            reservation.parking_space.number,
            reservation.car_number,
            timezone.localtime(reservation.start_time).strftime('%d.%m.%Y %H:%M'),
            timezone.localtime(reservation.end_time).strftime('%d.%m.%Y %H:%M'),
            reservation.get_status_display(),
            format_money(reservation.total_price),
            format_money(reservation.overtime_fee_display),
            format_money(final_price),
        ])

    return response
