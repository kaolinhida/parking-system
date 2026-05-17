import math
import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from parkings.models import ParkingSpace, Tariff


class Reservation(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_CHECKED_IN = 'checked_in'
    STATUS_CANCELLED = 'cancelled'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Активне'),
        (STATUS_CHECKED_IN, 'Авто на парковці'),
        (STATUS_CANCELLED, 'Скасоване'),
        (STATUS_COMPLETED, 'Завершене'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name='Користувач'
    )

    parking_space = models.ForeignKey(
        ParkingSpace,
        on_delete=models.PROTECT,
        related_name='reservations',
        verbose_name='Паркомісце'
    )

    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reservations',
        verbose_name='Автомобіль'
    )

    tariff = models.ForeignKey(
        Tariff,
        on_delete=models.PROTECT,
        related_name='reservations',
        verbose_name='Тариф'
    )

    car_number = models.CharField(max_length=20, verbose_name='Номер автомобіля')

    start_time = models.DateTimeField(verbose_name='Час початку')
    end_time = models.DateTimeField(verbose_name='Час завершення')

    price_per_hour = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Ціна за годину'
    )

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Вартість бронювання'
    )

    overtime_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Доплата за перевищення часу'
    )

    final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Фінальна вартість'
    )

    is_paid = models.BooleanField(
        default=False,
        verbose_name='Базову вартість оплачено'
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата оплати базової вартості'
    )

    overtime_is_paid = models.BooleanField(
        default=False,
        verbose_name='Доплату оплачено'
    )

    overtime_paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата оплати доплати'
    )

    payment_note = models.TextField(
        blank=True,
        verbose_name='Примітка щодо оплати'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        verbose_name='Статус'
    )

    access_token = models.UUIDField(
        unique=True,
        editable=False,
        null=True,
        blank=True,
        verbose_name='Токен доступу'
    )

    check_in_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Час в’їзду'
    )

    check_out_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Час виїзду'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата створення')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата оновлення')

    class Meta:
        verbose_name = 'Бронювання'
        verbose_name_plural = 'Бронювання'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.parking_space} — {self.car_number}'

    def duration_hours(self):
        if not self.start_time or not self.end_time:
            return 0

        duration = self.end_time - self.start_time
        hours = duration.total_seconds() / 3600

        return max(1, math.ceil(hours))

    def calculate_total_price(self):
        return Decimal(self.duration_hours()) * self.price_per_hour

    def overtime_hours(self, reference_time=None):
        if not self.end_time:
            return 0

        if reference_time is None:
            reference_time = self.check_out_time or timezone.now()

        if reference_time <= self.end_time:
            return 0

        duration = reference_time - self.end_time
        hours = duration.total_seconds() / 3600

        return max(1, math.ceil(hours))

    def calculate_overtime_fee(self, reference_time=None):
        return Decimal(self.overtime_hours(reference_time)) * self.price_per_hour

    def calculate_final_price(self, reference_time=None):
        return self.total_price + self.calculate_overtime_fee(reference_time)

    def clean(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError('Час завершення має бути пізніше часу початку.')

        if self.parking_space and self.tariff:
            if self.tariff.parking_lot != self.parking_space.parking_lot:
                raise ValidationError('Тариф не відповідає вибраній парковці.')

            if self.tariff.space_type != self.parking_space.space_type:
                raise ValidationError('Тариф не відповідає типу вибраного паркомісця.')

        if self.parking_space and self.start_time and self.end_time:
            overlapping_reservations = Reservation.objects.filter(
                parking_space=self.parking_space,
                status__in=[
                    self.STATUS_ACTIVE,
                    self.STATUS_CHECKED_IN,
                ],
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
            ).exclude(pk=self.pk)

            if overlapping_reservations.exists():
                raise ValidationError('Це паркомісце вже заброньоване на вибраний проміжок часу.')

    def save(self, *args, **kwargs):
        if not self.access_token:
            self.access_token = uuid.uuid4()

        if self.tariff:
            self.price_per_hour = self.tariff.price_per_hour

        if self.price_per_hour and self.start_time and self.end_time:
            self.total_price = self.calculate_total_price()

        if self.is_paid and not self.paid_at:
            self.paid_at = timezone.now()
        elif not self.is_paid:
            self.paid_at = None

        if self.overtime_is_paid and not self.overtime_paid_at:
            self.overtime_paid_at = timezone.now()
        elif not self.overtime_is_paid:
            self.overtime_paid_at = None

        super().save(*args, **kwargs)
