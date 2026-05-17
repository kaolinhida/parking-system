from decimal import Decimal

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import F, Sum
from django.shortcuts import render
from django.utils import timezone

from parkings.models import ParkingLot, ParkingSpace
from reservations.models import Reservation


@staff_member_required
def dashboard_home(request):
    now = timezone.now()

    # Автоматично завершуємо активні бронювання, які вже минули,
    # якщо автомобіль не був підтверджений як такий, що заїхав на парковку.
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
        .order_by('-created_at')
    )

    # Для фінансових розрахунків скасовані бронювання не враховуємо.
    financial_reservations = reservations.exclude(
        status=Reservation.STATUS_CANCELLED
    )

    total_parking_lots = ParkingLot.objects.count()
    active_parking_lots = ParkingLot.objects.filter(is_active=True).count()

    total_spaces = ParkingSpace.objects.count()
    active_spaces = ParkingSpace.objects.filter(is_active=True).count()

    total_reservations = reservations.count()
    active_reservations = reservations.filter(status=Reservation.STATUS_ACTIVE).count()
    checked_in_reservations_count = reservations.filter(status=Reservation.STATUS_CHECKED_IN).count()
    completed_reservations = reservations.filter(status=Reservation.STATUS_COMPLETED).count()
    cancelled_reservations = reservations.filter(status=Reservation.STATUS_CANCELLED).count()

    total_base_sum = financial_reservations.aggregate(
        total=Sum('total_price')
    )['total'] or Decimal('0.00')

    stored_overtime_sum = financial_reservations.aggregate(
        total=Sum('overtime_fee')
    )['total'] or Decimal('0.00')

    live_overtime_sum = Decimal('0.00')
    live_overtime_count = 0

    checked_in_reservations = list(
        reservations.filter(status=Reservation.STATUS_CHECKED_IN)
    )

    for reservation in checked_in_reservations:
        reservation.current_overtime_hours = 0
        reservation.current_overtime_fee = Decimal('0.00')

        if reservation.end_time and now > reservation.end_time:
            reservation.current_overtime_hours = reservation.overtime_hours(now)
            reservation.current_overtime_fee = reservation.calculate_overtime_fee(now)

            live_overtime_sum += reservation.current_overtime_fee
            live_overtime_count += 1

    total_overtime_sum = stored_overtime_sum + live_overtime_sum

    final_sum = Decimal('0.00')

    for reservation in financial_reservations:
        if reservation.final_price is not None:
            final_sum += reservation.final_price
        else:
            final_sum += reservation.total_price

    # Додаємо поточні борги авто, які ще перебувають на парковці.
    final_sum += live_overtime_sum

    latest_reservations = reservations[:10]
    occupied_reservations = checked_in_reservations[:10]

    return render(request, 'dashboard/home.html', {
        'now': now,

        'total_parking_lots': total_parking_lots,
        'active_parking_lots': active_parking_lots,

        'total_spaces': total_spaces,
        'active_spaces': active_spaces,

        'total_reservations': total_reservations,
        'active_reservations': active_reservations,
        'checked_in_reservations_count': checked_in_reservations_count,
        'completed_reservations': completed_reservations,
        'cancelled_reservations': cancelled_reservations,

        'total_base_sum': total_base_sum,
        'stored_overtime_sum': stored_overtime_sum,
        'live_overtime_sum': live_overtime_sum,
        'total_overtime_sum': total_overtime_sum,
        'live_overtime_count': live_overtime_count,
        'final_sum': final_sum,

        'latest_reservations': latest_reservations,
        'occupied_reservations': occupied_reservations,
    })