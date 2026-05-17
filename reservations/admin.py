from django.contrib import admin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'parking_space',
        'car_number',
        'start_time',
        'end_time',
        'status',
        'price_per_hour',
        'total_price',
        'is_paid',
        'overtime_is_paid',
    )
    list_filter = (
        'status',
        'is_paid',
        'overtime_is_paid',
        'parking_space__parking_lot',
        'parking_space__space_type',
    )
    search_fields = ('car_number', 'user__username', 'parking_space__number')
    readonly_fields = ('access_token', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': (
                'user',
                'parking_space',
                'vehicle',
                'tariff',
                'car_number',
                'start_time',
                'end_time',
                'status',
            )
        }),
        ('Фінанси', {
            'fields': (
                'price_per_hour',
                'total_price',
                'overtime_fee',
                'final_price',
            )
        }),
        ('Оплата', {
            'fields': (
                'is_paid',
                'paid_at',
                'overtime_is_paid',
                'overtime_paid_at',
                'payment_note',
            )
        }),
        ('Службова інформація', {
            'fields': (
                'access_token',
                'check_in_time',
                'check_out_time',
                'created_at',
                'updated_at',
            )
        }),
    )
