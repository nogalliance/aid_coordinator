from admin_wizard.admin import UpdateAction
from django.contrib import admin
from django.http import HttpRequest
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from import_export.admin import ExportActionModelAdmin

from logistics.filters import UsedChoicesFieldListFilter
from logistics.forms import AssignToShipmentForm
from logistics.models import Claim, Location, Shipment
from logistics.resources import ClaimExportResource


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'country', 'admin_email', 'admin_phone',
                    'is_collection_point', 'is_distribution_point')
    list_filter = (
        ('country', UsedChoicesFieldListFilter),
    )
    ordering = ('name',)

    @admin.display(description=_('contact email'))
    def admin_email(self, location: Location):
        if not location.email:
            return None

        return format_html(
            '<a href="mailto:{email}">{email}</a>',
            email=location.email
        )

    @admin.display(description=_('contact phone'))
    def admin_phone(self, location: Location):
        if not location.phone:
            return None

        return format_html(
            '<a href="tel:{phone}">{phone}</a>',
            phone=location.phone
        )


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'when', 'current_location', 'is_delivered')
    list_filter = ('is_delivered',)
    date_hierarchy = 'when'
    ordering = ('when',)
    search_fields = ('name', 'current_location__name', 'current_location__city', 'current_location__country')


@admin.register(Claim)
class ClaimAdmin(ExportActionModelAdmin):
    list_display = ('amount', 'admin_offered_item', 'admin_requested_item', 'shipment')
    list_filter = ('shipment', 'shipment__is_delivered',
                   ('offered_item__offer__contact__organisation', admin.RelatedOnlyFieldListFilter),
                   ('requested_item__request__contact__organisation', admin.RelatedOnlyFieldListFilter))
    search_fields = ('offered_item__brand', 'offered_item__model',
                     'requested_item__brand', 'requested_item__model',
                     'offered_item__offer__contact__organisation__name',
                     'requested_item__request__contact__organisation__name')
    ordering = ('shipment',)
    actions = (
        UpdateAction(form_class=AssignToShipmentForm, title=_('Assign to shipment')),
    )
    resource_class = ClaimExportResource

    def get_queryset(self, request: HttpRequest):
        qs = super().get_queryset(request)
        qs = qs.prefetch_related('offered_item__offer__contact__organisation',
                                 'requested_item__request__contact__organisation',
                                 'shipment')
        return qs

    @admin.display(description=_('offered item'))
    def admin_offered_item(self, claim: Claim):
        return format_html('<b>{item}</b><br>{offer}', item=claim.offered_item, offer=claim.offered_item.offer)

    @admin.display(description=_('requested item'))
    def admin_requested_item(self, claim: Claim):
        if claim.requested_item_id:
            return format_html('<b>{item}</b><br>{request}', item=claim.requested_item,
                               request=claim.requested_item.request)
        else:
            return mark_safe('<b>Preemptive shipment</b><br>'
                             'Just ship it to a distribution point')
