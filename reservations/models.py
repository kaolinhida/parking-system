import math
import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

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
        verbose_name='Загальна вартість'
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

        super().save(*args, **kwargs)