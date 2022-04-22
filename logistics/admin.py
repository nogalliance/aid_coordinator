from django.contrib import admin

from logistics.filters import UsedChoicesFieldListFilter
from logistics.models import Claim, Location, Shipment


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'country')
    list_filter = (
        ('country', UsedChoicesFieldListFilter),
    )
    ordering = ('name',)


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'when', 'current_location', 'is_delivered')
    list_filter = ('is_delivered',)
    date_hierarchy = 'when'
    ordering = ('when',)


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ('offered_item', 'requested_item', 'amount', 'shipment')
    list_filter = ('shipment', 'shipment__is_delivered')
    ordering = ('shipment',)
