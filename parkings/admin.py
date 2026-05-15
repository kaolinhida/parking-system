from django.contrib import admin

from .models import ParkingLot, ParkingSpaceType, ParkingSpace, Tariff


@admin.register(ParkingLot)
class ParkingLotAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'latitude', 'longitude', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'address')


@admin.register(ParkingSpaceType)
class ParkingSpaceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(ParkingSpace)
class ParkingSpaceAdmin(admin.ModelAdmin):
    list_display = ('number', 'parking_lot', 'space_type', 'row', 'column', 'is_active')
    list_filter = ('parking_lot', 'space_type', 'is_active')
    search_fields = ('number', 'parking_lot__name')


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = ('parking_lot', 'space_type', 'price_per_hour', 'is_active')
    list_filter = ('parking_lot', 'space_type', 'is_active')
    search_fields = ('parking_lot__name', 'space_type__name')