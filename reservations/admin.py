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
    )
    list_filter = ('status', 'parking_space__parking_lot', 'parking_space__space_type')
    search_fields = ('car_number', 'user__username', 'parking_space__number')
    readonly_fields = ('created_at', 'updated_at')