from django.contrib import admin

from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        'brand',
        'model',
        'license_plate',
        'user',
        'vehicle_type',
        'color',
        'year',
        'is_active',
    )
    list_filter = ('vehicle_type', 'color', 'is_active')
    search_fields = ('brand', 'model', 'license_plate', 'user__username')