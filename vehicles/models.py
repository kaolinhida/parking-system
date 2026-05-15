from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Vehicle(models.Model):
    TYPE_CAR = 'car'
    TYPE_ELECTRIC = 'electric'
    TYPE_MOTORCYCLE = 'motorcycle'
    TYPE_MINIBUS = 'minibus'
    TYPE_TRUCK = 'truck'
    TYPE_OTHER = 'other'

    VEHICLE_TYPE_CHOICES = [
        (TYPE_CAR, 'Легковий автомобіль'),
        (TYPE_ELECTRIC, 'Електромобіль'),
        (TYPE_MOTORCYCLE, 'Мотоцикл'),
        (TYPE_MINIBUS, 'Мікроавтобус'),
        (TYPE_TRUCK, 'Вантажний автомобіль'),
        (TYPE_OTHER, 'Інше'),
    ]

    COLOR_WHITE = 'white'
    COLOR_BLACK = 'black'
    COLOR_GRAY = 'gray'
    COLOR_SILVER = 'silver'
    COLOR_RED = 'red'
    COLOR_BLUE = 'blue'
    COLOR_GREEN = 'green'
    COLOR_YELLOW = 'yellow'
    COLOR_BROWN = 'brown'
    COLOR_OTHER = 'other'

    COLOR_CHOICES = [
        (COLOR_WHITE, 'Білий'),
        (COLOR_BLACK, 'Чорний'),
        (COLOR_GRAY, 'Сірий'),
        (COLOR_SILVER, 'Сріблястий'),
        (COLOR_RED, 'Червоний'),
        (COLOR_BLUE, 'Синій'),
        (COLOR_GREEN, 'Зелений'),
        (COLOR_YELLOW, 'Жовтий'),
        (COLOR_BROWN, 'Коричневий'),
        (COLOR_OTHER, 'Інший'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vehicles',
        verbose_name='Користувач'
    )
    brand = models.CharField(max_length=100, verbose_name='Марка')
    model = models.CharField(max_length=100, verbose_name='Модель')
    license_plate = models.CharField(max_length=20, verbose_name='Номерний знак')
    year = models.PositiveIntegerField(verbose_name='Рік випуску')
    vehicle_type = models.CharField(
        max_length=20,
        choices=VEHICLE_TYPE_CHOICES,
        verbose_name='Тип транспорту'
    )
    color = models.CharField(
        max_length=20,
        choices=COLOR_CHOICES,
        verbose_name='Колір'
    )
    photo = models.ImageField(
        upload_to='vehicles/',
        blank=True,
        null=True,
        verbose_name='Фото автомобіля'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активний')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата створення')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата оновлення')

    class Meta:
        verbose_name = 'Автомобіль'
        verbose_name_plural = 'Автомобілі'
        ordering = ['brand', 'model']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'license_plate'],
                name='unique_vehicle_plate_per_user'
            )
        ]

    def __str__(self):
        return f'{self.brand} {self.model} — {self.license_plate}'

    def clean(self):
        current_year = timezone.now().year

        if self.year < 1950 or self.year > current_year + 1:
            raise ValidationError('Вкажіть коректний рік випуску автомобіля.')

    def save(self, *args, **kwargs):
        if self.license_plate:
            self.license_plate = self.license_plate.upper().replace(' ', '')

        super().save(*args, **kwargs)