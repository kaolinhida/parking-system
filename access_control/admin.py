from django.contrib import admin

from .models import AccessLog


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = (
        'created_at',
        'action',
        'result',
        'reservation',
        'access_token',
        'performed_by',
    )
    list_filter = ('action', 'result', 'created_at')
    search_fields = (
        'access_token',
        'reservation__car_number',
        'reservation__parking_space__number',
        'reservation__parking_space__parking_lot__name',
        'performed_by__username',
    )
    readonly_fields = (
        'reservation',
        'access_token',
        'action',
        'result',
        'message',
        'performed_by',
        'created_at',
    )