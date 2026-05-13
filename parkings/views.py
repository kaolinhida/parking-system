from django.db.models import Count
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from reservations.models import Reservation
from .models import ParkingLot, Tariff


def parking_list(request):
    parkings = (
        ParkingLot.objects
        .filter(is_active=True)
        .annotate(spaces_count=Count('spaces'))
        .order_by('name')
    )

    return render(request, 'parkings/parking_list.html', {
        'parkings': parkings,
    })


def parking_detail(request, parking_id):
    parking = get_object_or_404(ParkingLot, id=parking_id, is_active=True)

    now = timezone.now()

    occupied_space_ids = set(
        Reservation.objects.filter(
            parking_space__parking_lot=parking,
            status=Reservation.STATUS_ACTIVE,
            start_time__lte=now,
            end_time__gt=now,
        ).values_list('parking_space_id', flat=True)
    )

    tariffs = Tariff.objects.filter(
        parking_lot=parking,
        is_active=True,
    ).select_related('space_type')

    tariff_by_type_id = {
        tariff.space_type_id: tariff
        for tariff in tariffs
    }

    spaces = (
        parking.spaces
        .select_related('space_type')
        .order_by('row', 'column')
    )

    rows = {}

    for space in spaces:
        space.tariff = tariff_by_type_id.get(space.space_type_id)

        if not space.is_active:
            space.display_status = 'inactive'
            space.display_status_label = 'Неактивне'
        elif space.id in occupied_space_ids:
            space.display_status = 'occupied'
            space.display_status_label = 'Зайняте'
        else:
            space.display_status = 'available'
            space.display_status_label = 'Вільне'

        rows.setdefault(space.row, []).append(space)

    parking_rows = [
        {
            'row_number': row_number,
            'spaces': row_spaces,
        }
        for row_number, row_spaces in rows.items()
    ]

    return render(request, 'parkings/parking_detail.html', {
        'parking': parking,
        'parking_rows': parking_rows,
        'now': now,
    })