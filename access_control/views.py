from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.permissions import gate_access_required, payment_admin_required
from reservations.models import Reservation
from .forms import AccessCodeForm, AccessLogFilterForm
from .models import AccessLog


def create_access_log(reservation, access_token, action, result, message, user):
    performed_by = user if user.is_authenticated else None

    AccessLog.objects.create(
        reservation=reservation,
        access_token=str(access_token) if access_token else '',
        action=action,
        result=result,
        message=message,
        performed_by=performed_by,
    )


QR_NOT_FOUND_MESSAGE = 'QR-код не знайдено: бронювання за цим кодом не існує.'


def get_check_in_unavailable_reason(reservation, now):
    if reservation.status == Reservation.STATUS_CANCELLED:
        return 'В’їзд неможливий: бронювання скасоване.'

    if reservation.status == Reservation.STATUS_COMPLETED:
        return 'В’їзд неможливий: бронювання вже завершене.'

    if reservation.check_in_time is not None or reservation.status == Reservation.STATUS_CHECKED_IN:
        return 'В’їзд неможливий: автомобіль уже заїхав на парковку.'

    if reservation.status != Reservation.STATUS_ACTIVE:
        return 'В’їзд неможливий: бронювання не є активним.'

    if now < reservation.start_time:
        return 'В’їзд неможливий: бронювання ще не почалося.'

    if now > reservation.end_time:
        return 'В’їзд неможливий: час бронювання вже завершився.'

    return 'В’їзд неможливий: поточний час не входить у період бронювання.'


def get_check_out_unavailable_reason(reservation):
    if reservation.status == Reservation.STATUS_CANCELLED:
        return 'Виїзд неможливий: бронювання скасоване.'

    if reservation.status == Reservation.STATUS_COMPLETED or reservation.check_out_time is not None:
        return 'Виїзд неможливий: бронювання вже завершене.'

    if reservation.check_in_time is None:
        return 'Виїзд неможливий: автомобіль ще не заїхав, тому виїзд неможливий.'

    if reservation.status != Reservation.STATUS_CHECKED_IN:
        return 'Виїзд неможливий: автомобіль не перебуває на парковці.'

    return 'Виїзд неможливий для поточного стану бронювання.'


def get_scan_unavailable_reason(reservation, now):
    if reservation.status == Reservation.STATUS_CHECKED_IN:
        return get_check_out_unavailable_reason(reservation)

    return get_check_in_unavailable_reason(reservation, now)


@gate_access_required
def access_control_home(request):
    form = AccessCodeForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        access_token = form.cleaned_data['access_token']
        return redirect('access_control:reservation_detail', access_token=access_token)

    return render(request, 'access_control/home.html', {
        'form': form,
    })


@gate_access_required
def access_logs(request):
    filter_form = AccessLogFilterForm(request.GET or None)

    logs = (
        AccessLog.objects
        .select_related(
            'reservation',
            'reservation__parking_space',
            'reservation__parking_space__parking_lot',
            'performed_by',
        )
        .order_by('-created_at')
    )

    if filter_form.is_valid():
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        action = filter_form.cleaned_data.get('action')
        result = filter_form.cleaned_data.get('result')
        car_number = filter_form.cleaned_data.get('car_number')
        parking_lot = filter_form.cleaned_data.get('parking_lot')

        if date_from:
            start_at = timezone.make_aware(
                timezone.datetime.combine(date_from, timezone.datetime.min.time())
            )
            logs = logs.filter(created_at__gte=start_at)

        if date_to:
            end_at = timezone.make_aware(
                timezone.datetime.combine(date_to, timezone.datetime.max.time())
            )
            logs = logs.filter(created_at__lte=end_at)

        if action:
            logs = logs.filter(action=action)

        if result:
            logs = logs.filter(result=result)

        if car_number:
            logs = logs.filter(reservation__car_number__icontains=car_number)

        if parking_lot:
            logs = logs.filter(
                reservation__parking_space__parking_lot=parking_lot
            )

    paginator = Paginator(logs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    query_params = request.GET.copy()
    query_params.pop('page', None)

    return render(request, 'access_control/logs.html', {
        'filter_form': filter_form,
        'logs': page_obj,
        'page_obj': page_obj,
        'query_params': query_params.urlencode(),
    })


@gate_access_required
def reservation_detail(request, access_token):
    reservation = (
        Reservation.objects
        .select_related(
            'user',
            'parking_space',
            'parking_space__parking_lot',
            'parking_space__space_type',
            'vehicle',
        )
        .filter(access_token=access_token)
        .first()
    )

    if reservation is None:
        create_access_log(
            reservation=None,
            access_token=access_token,
            action=AccessLog.ACTION_SCAN,
            result=AccessLog.RESULT_DENIED,
            message=QR_NOT_FOUND_MESSAGE,
            user=request.user,
        )

        return render(request, 'access_control/reservation_not_found.html', {
            'access_token': access_token,
        })

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

    overtime_hours = 0
    overtime_fee = reservation.overtime_fee
    final_price = reservation.final_price or reservation.total_price

    if reservation.status == Reservation.STATUS_CHECKED_IN and now > reservation.end_time:
        overtime_hours = reservation.overtime_hours(now)
        overtime_fee = reservation.calculate_overtime_fee(now)
        final_price = reservation.total_price + overtime_fee

    if reservation.status == Reservation.STATUS_COMPLETED:
        overtime_hours = reservation.overtime_hours(reservation.check_out_time)
        overtime_fee = reservation.overtime_fee
        final_price = reservation.final_price or reservation.total_price + overtime_fee

    if can_check_in:
        log_result = AccessLog.RESULT_ALLOWED
        log_message = 'QR-код перевірено. Бронювання активне, в’їзд дозволено.'
    elif can_check_out:
        log_result = AccessLog.RESULT_ALLOWED
        log_message = 'QR-код перевірено. Автомобіль перебуває на парковці, доступне підтвердження виїзду.'
    else:
        log_result = AccessLog.RESULT_DENIED
        log_message = f'QR-код перевірено. {get_scan_unavailable_reason(reservation, now)}'

    create_access_log(
        reservation=reservation,
        access_token=access_token,
        action=AccessLog.ACTION_SCAN,
        result=log_result,
        message=log_message,
        user=request.user,
    )

    reservation_logs = reservation.access_logs.select_related('performed_by')[:10]

    return render(request, 'access_control/reservation_detail.html', {
        'reservation': reservation,
        'now': now,
        'can_check_in': can_check_in,
        'can_check_out': can_check_out,
        'access_unavailable_reason': None if log_result != AccessLog.RESULT_DENIED else get_scan_unavailable_reason(reservation, now),
        'overtime_hours': overtime_hours,
        'overtime_fee': overtime_fee,
        'final_price': final_price,
        'reservation_logs': reservation_logs,
    })


@gate_access_required
def check_in(request, access_token):
    reservation = (
        Reservation.objects
        .filter(access_token=access_token)
        .first()
    )

    if reservation is None:
        create_access_log(
            reservation=None,
            access_token=access_token,
            action=AccessLog.ACTION_CHECK_IN,
            result=AccessLog.RESULT_DENIED,
            message=QR_NOT_FOUND_MESSAGE,
            user=request.user,
        )
        messages.error(request, QR_NOT_FOUND_MESSAGE)
        return redirect('access_control:home')

    if request.method != 'POST':
        return redirect('access_control:reservation_detail', access_token=access_token)

    now = timezone.now()

    if reservation.status != Reservation.STATUS_ACTIVE:
        reason = get_check_in_unavailable_reason(reservation, now)
        create_access_log(
            reservation=reservation,
            access_token=access_token,
            action=AccessLog.ACTION_CHECK_IN,
            result=AccessLog.RESULT_DENIED,
            message=reason,
            user=request.user,
        )

        messages.error(request, reason)
        return redirect('access_control:reservation_detail', access_token=access_token)

    if reservation.check_in_time is not None:
        reason = get_check_in_unavailable_reason(reservation, now)
        create_access_log(
            reservation=reservation,
            access_token=access_token,
            action=AccessLog.ACTION_CHECK_IN,
            result=AccessLog.RESULT_DENIED,
            message=reason,
            user=request.user,
        )

        messages.error(request, reason)
        return redirect('access_control:reservation_detail', access_token=access_token)

    if not (reservation.start_time <= now <= reservation.end_time):
        reason = get_check_in_unavailable_reason(reservation, now)
        create_access_log(
            reservation=reservation,
            access_token=access_token,
            action=AccessLog.ACTION_CHECK_IN,
            result=AccessLog.RESULT_DENIED,
            message=reason,
            user=request.user,
        )

        messages.error(request, reason)
        return redirect('access_control:reservation_detail', access_token=access_token)

    reservation.check_in_time = now
    reservation.status = Reservation.STATUS_CHECKED_IN
    reservation.save()

    create_access_log(
        reservation=reservation,
        access_token=access_token,
        action=AccessLog.ACTION_CHECK_IN,
        result=AccessLog.RESULT_SUCCESS,
        message='В’їзд підтверджено. Автомобіль позначено як такий, що заїхав на парковку.',
        user=request.user,
    )

    messages.success(request, 'В’їзд підтверджено. Автомобіль позначено як такий, що заїхав на парковку.')
    return redirect('access_control:reservation_detail', access_token=access_token)


@gate_access_required
def check_out(request, access_token):
    reservation = (
        Reservation.objects
        .filter(access_token=access_token)
        .first()
    )

    if reservation is None:
        create_access_log(
            reservation=None,
            access_token=access_token,
            action=AccessLog.ACTION_CHECK_OUT,
            result=AccessLog.RESULT_DENIED,
            message=QR_NOT_FOUND_MESSAGE,
            user=request.user,
        )
        messages.error(request, QR_NOT_FOUND_MESSAGE)
        return redirect('access_control:home')

    if request.method != 'POST':
        return redirect('access_control:reservation_detail', access_token=access_token)

    if reservation.status != Reservation.STATUS_CHECKED_IN:
        reason = get_check_out_unavailable_reason(reservation)
        create_access_log(
            reservation=reservation,
            access_token=access_token,
            action=AccessLog.ACTION_CHECK_OUT,
            result=AccessLog.RESULT_DENIED,
            message=reason,
            user=request.user,
        )

        messages.error(request, reason)
        return redirect('access_control:reservation_detail', access_token=access_token)

    if reservation.check_out_time is not None:
        reason = get_check_out_unavailable_reason(reservation)
        create_access_log(
            reservation=reservation,
            access_token=access_token,
            action=AccessLog.ACTION_CHECK_OUT,
            result=AccessLog.RESULT_DENIED,
            message=reason,
            user=request.user,
        )

        messages.error(request, reason)
        return redirect('access_control:reservation_detail', access_token=access_token)

    now = timezone.now()

    overtime_fee = reservation.calculate_overtime_fee(now)
    final_price = reservation.total_price + overtime_fee

    reservation.check_out_time = now
    reservation.overtime_fee = overtime_fee
    reservation.final_price = final_price
    reservation.status = Reservation.STATUS_COMPLETED
    reservation.save()

    create_access_log(
        reservation=reservation,
        access_token=access_token,
        action=AccessLog.ACTION_CHECK_OUT,
        result=AccessLog.RESULT_SUCCESS,
        message=f'Виїзд підтверджено. Фінальна вартість: {final_price} грн. Доплата: {overtime_fee} грн.',
        user=request.user,
    )

    if overtime_fee > 0:
        messages.warning(
            request,
            f'Виїзд підтверджено. За перевищення часу нараховано доплату: {overtime_fee} грн.'
        )
    else:
        messages.success(request, 'Виїзд підтверджено. Бронювання завершено без доплати.')

    return redirect('access_control:reservation_detail', access_token=access_token)


@payment_admin_required
def mark_paid(request, access_token):
    reservation = get_object_or_404(Reservation, access_token=access_token)

    if request.method != 'POST':
        return redirect('access_control:reservation_detail', access_token=access_token)

    if reservation.is_paid:
        messages.info(request, 'Базову вартість уже позначено як оплачену.')
        return redirect('access_control:reservation_detail', access_token=access_token)

    reservation.is_paid = True
    reservation.save(update_fields=['is_paid', 'paid_at', 'updated_at'])

    messages.success(request, 'Базову вартість бронювання позначено як оплачену.')
    return redirect('access_control:reservation_detail', access_token=access_token)


@payment_admin_required
def mark_overtime_paid(request, access_token):
    reservation = get_object_or_404(Reservation, access_token=access_token)

    if request.method != 'POST':
        return redirect('access_control:reservation_detail', access_token=access_token)

    if reservation.overtime_fee <= 0:
        messages.info(request, 'Для цього бронювання доплата не потрібна.')
        return redirect('access_control:reservation_detail', access_token=access_token)

    if reservation.overtime_is_paid:
        messages.info(request, 'Доплату вже позначено як оплачену.')
        return redirect('access_control:reservation_detail', access_token=access_token)

    reservation.overtime_is_paid = True
    reservation.save(update_fields=['overtime_is_paid', 'overtime_paid_at', 'updated_at'])

    messages.success(request, 'Доплату за перевищення часу позначено як оплачену.')
    return redirect('access_control:reservation_detail', access_token=access_token)
