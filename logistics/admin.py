from django.contrib import admin

from logistics.models import Claim, Shipment


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'when', 'is_delivered')
    list_filter = ('is_delivered',)
    date_hierarchy = 'when'
    ordering = ('when',)


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ('offered_item', 'requested_item', 'amount', 'shipment')
    list_filter = ('shipment', 'shipment__is_delivered')
    ordering = ('shipment',)
