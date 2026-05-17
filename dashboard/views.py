from decimal import Decimal

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.db.models import Count, F, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from parkings.models import ParkingLot, ParkingSpace, Tariff
from reservations.models import Reservation
from .forms import ParkingGridForm, ParkingSpaceEditForm, TariffForm


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

def get_row_label(index):
    return chr(ord('A') + index)


@staff_member_required
def create_parking_grid(request):
    if request.method == 'POST':
        form = ParkingGridForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                parking = ParkingLot.objects.create(
                    name=form.cleaned_data['name'],
                    address=form.cleaned_data['address'],
                    description=form.cleaned_data.get('description', ''),
                    latitude=form.cleaned_data.get('latitude'),
                    longitude=form.cleaned_data.get('longitude'),
                    is_active=True,
                )

                default_space_type = form.cleaned_data['default_space_type']

                Tariff.objects.create(
                    parking_lot=parking,
                    space_type=default_space_type,
                    price_per_hour=form.cleaned_data['price_per_hour'],
                    is_active=True,
                )

                rows = form.cleaned_data['rows']
                columns = form.cleaned_data['columns']

                spaces = []

                for row_index in range(rows):
                    row_label = get_row_label(row_index)

                    for column_number in range(1, columns + 1):
                        space_number = f'{row_label}{column_number}'

                        spaces.append(
                            ParkingSpace(
                                parking_lot=parking,
                                space_type=default_space_type,
                                number=space_number,
                                row=row_index + 1,
                                column=column_number,
                                is_active=True,
                            )
                        )

                ParkingSpace.objects.bulk_create(spaces)

            messages.success(
                request,
                f'Парковку "{parking.name}" успішно створено. Згенеровано {rows * columns} паркомісць.'
            )

            return redirect('parkings:parking_detail', parking.id)
    else:
        form = ParkingGridForm()

    return render(request, 'dashboard/create_parking_grid.html', {
        'form': form,
    })

@staff_member_required
def dashboard_parking_list(request):
    parkings = (
        ParkingLot.objects
        .annotate(spaces_count=Count('spaces'))
        .order_by('name')
    )

    return render(request, 'dashboard/parking_list.html', {
        'parkings': parkings,
    })


@staff_member_required
def dashboard_parking_spaces(request, parking_id):
    parking = get_object_or_404(ParkingLot, id=parking_id)

    spaces = (
        parking.spaces
        .select_related('space_type')
        .order_by('row', 'column')
    )

    rows = {}

    for space in spaces:
        rows.setdefault(space.row, []).append(space)

    parking_rows = [
        {
            'row_number': row_number,
            'spaces': row_spaces,
        }
        for row_number, row_spaces in rows.items()
    ]

    return render(request, 'dashboard/parking_spaces.html', {
        'parking': parking,
        'parking_rows': parking_rows,
    })


@staff_member_required
def dashboard_space_edit(request, space_id):
    space = get_object_or_404(
        ParkingSpace.objects.select_related('parking_lot', 'space_type'),
        id=space_id
    )

    if request.method == 'POST':
        form = ParkingSpaceEditForm(request.POST, instance=space)

        if form.is_valid():
            form.save()

            messages.success(request, 'Дані паркомісця успішно оновлено.')
            return redirect('dashboard:parking_spaces', parking_id=space.parking_lot.id)
    else:
        form = ParkingSpaceEditForm(instance=space)

    return render(request, 'dashboard/space_edit.html', {
        'form': form,
        'space': space,
    })


@staff_member_required
def dashboard_tariff_list(request):
    tariffs = (
        Tariff.objects
        .select_related('parking_lot', 'space_type')
        .order_by('parking_lot__name', 'space_type__name')
    )

    return render(request, 'dashboard/tariff_list.html', {
        'tariffs': tariffs,
    })


@staff_member_required
def dashboard_tariff_add(request):
    if request.method == 'POST':
        form = TariffForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(request, 'Тариф успішно створено.')
            return redirect('dashboard:tariff_list')
    else:
        form = TariffForm()

    return render(request, 'dashboard/tariff_form.html', {
        'form': form,
        'title': 'Створити тариф',
        'submit_label': 'Створити тариф',
    })


@staff_member_required
def dashboard_tariff_edit(request, tariff_id):
    tariff = get_object_or_404(
        Tariff.objects.select_related('parking_lot', 'space_type'),
        id=tariff_id
    )

    if request.method == 'POST':
        form = TariffForm(request.POST, instance=tariff)

        if form.is_valid():
            form.save()

            messages.success(request, 'Тариф успішно оновлено.')
            return redirect('dashboard:tariff_list')
    else:
        form = TariffForm(instance=tariff)

    return render(request, 'dashboard/tariff_form.html', {
        'form': form,
        'tariff': tariff,
        'title': 'Редагувати тариф',
        'submit_label': 'Зберегти зміни',
    })
