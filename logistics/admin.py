from admin_wizard.admin import UpdateAction
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from logistics.filters import UsedChoicesFieldListFilter
from logistics.forms import AssignToShipmentForm
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
    search_fields = ('name', 'current_location__name', 'current_location__city', 'current_location__country')


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ('offered_item', 'requested_item', 'amount', 'shipment')
    list_filter = ('shipment', 'shipment__is_delivered')
    ordering = ('shipment',)
    actions = (
        UpdateAction(form_class=AssignToShipmentForm, title=_('Assign to shipment')),
    )
