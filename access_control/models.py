from django.conf import settings
from django.db import models

from reservations.models import Reservation


class AccessLog(models.Model):
    ACTION_SCAN = 'scan'
    ACTION_CHECK_IN = 'check_in'
    ACTION_CHECK_OUT = 'check_out'

    ACTION_CHOICES = [
        (ACTION_SCAN, 'Перевірка QR-коду'),
        (ACTION_CHECK_IN, 'Підтвердження в’їзду'),
        (ACTION_CHECK_OUT, 'Підтвердження виїзду'),
    ]

    RESULT_ALLOWED = 'allowed'
    RESULT_DENIED = 'denied'
    RESULT_SUCCESS = 'success'
    RESULT_ERROR = 'error'
    RESULT_INFO = 'info'

    RESULT_CHOICES = [
        (RESULT_ALLOWED, 'Доступ дозволено'),
        (RESULT_DENIED, 'Доступ заборонено'),
        (RESULT_SUCCESS, 'Успішно'),
        (RESULT_ERROR, 'Помилка'),
        (RESULT_INFO, 'Інформація'),
    ]

    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='access_logs',
        verbose_name='Бронювання'
    )

    access_token = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Токен доступу'
    )

    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name='Дія'
    )

    result = models.CharField(
        max_length=20,
        choices=RESULT_CHOICES,
        verbose_name='Результат'
    )

    message = models.TextField(
        blank=True,
        verbose_name='Повідомлення'
    )

    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='access_logs',
        verbose_name='Виконав'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата і час'
    )

    class Meta:
        verbose_name = 'Журнал доступу'
        verbose_name_plural = 'Журнал доступу'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_action_display()} — {self.get_result_display()}'