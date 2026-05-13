from django.db import models


class ParkingLot(models.Model):
    name = models.CharField(max_length=100, verbose_name='Назва парковки')
    address = models.CharField(max_length=255, verbose_name='Адреса')
    description = models.TextField(blank=True, verbose_name='Опис')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата створення')

    class Meta:
        verbose_name = 'Парковка'
        verbose_name_plural = 'Парковки'
        ordering = ['name']

    def __str__(self):
        return self.name


class ParkingSpaceType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Назва типу')
    description = models.TextField(blank=True, verbose_name='Опис')
    is_active = models.BooleanField(default=True, verbose_name='Активний')

    class Meta:
        verbose_name = 'Тип паркомісця'
        verbose_name_plural = 'Типи паркомісць'
        ordering = ['name']

    def __str__(self):
        return self.name


class ParkingSpace(models.Model):
    parking_lot = models.ForeignKey(
        ParkingLot,
        on_delete=models.CASCADE,
        related_name='spaces',
        verbose_name='Парковка'
    )
    space_type = models.ForeignKey(
        ParkingSpaceType,
        on_delete=models.PROTECT,
        related_name='spaces',
        verbose_name='Тип місця'
    )
    number = models.CharField(max_length=20, verbose_name='Номер місця')
    row = models.PositiveIntegerField(verbose_name='Ряд')
    column = models.PositiveIntegerField(verbose_name='Колонка')
    is_active = models.BooleanField(default=True, verbose_name='Активне')

    class Meta:
        verbose_name = 'Паркомісце'
        verbose_name_plural = 'Паркомісця'
        ordering = ['parking_lot', 'row', 'column']
        constraints = [
            models.UniqueConstraint(
                fields=['parking_lot', 'number'],
                name='unique_space_number_per_parking'
            ),
            models.UniqueConstraint(
                fields=['parking_lot', 'row', 'column'],
                name='unique_space_position_per_parking'
            ),
        ]

    def __str__(self):
        return f'{self.parking_lot.name} — {self.number}'


class Tariff(models.Model):
    parking_lot = models.ForeignKey(
        ParkingLot,
        on_delete=models.CASCADE,
        related_name='tariffs',
        verbose_name='Парковка'
    )
    space_type = models.ForeignKey(
        ParkingSpaceType,
        on_delete=models.PROTECT,
        related_name='tariffs',
        verbose_name='Тип місця'
    )
    price_per_hour = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Ціна за годину'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активний')

    class Meta:
        verbose_name = 'Тариф'
        verbose_name_plural = 'Тарифи'
        ordering = ['parking_lot', 'space_type']
        constraints = [
            models.UniqueConstraint(
                fields=['parking_lot', 'space_type'],
                name='unique_tariff_per_parking_and_type'
            )
        ]

    def __str__(self):
        return f'{self.parking_lot.name} — {self.space_type.name}: {self.price_per_hour} грн/год'