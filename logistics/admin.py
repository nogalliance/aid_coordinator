from django.contrib import admin
from django.http import HttpRequest
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from import_export.admin import ExportActionModelAdmin, ImportExportActionModelAdmin
from logistics.filters import UsedChoicesFieldListFilter

# from logistics.forms import AssignToShipmentForm
from logistics.models import EquipmentData, Location, Shipment, ShipmentItem
from logistics.resources import EquipmentDataResource
from supply_demand.admin.base import CompactInline

static_import_icon = static("img/import.png")
static_export_icon = static("img/export.png")


@admin.register(EquipmentData)
class EquipmentDataAdmin(ImportExportActionModelAdmin):
    list_display = ("brand", "model", "admin_weight", "admin_size")
    ordering = ("brand", "model")
    resource_class = EquipmentDataResource

    @admin.display(description=_("weight"), ordering="weight")
    def admin_weight(self, item: EquipmentData):
        if item.weight:
            return f"{item.weight} kg"
        else:
            return "-"

    @admin.display(description=_("size (W*H*D)"), ordering="width,height,depth")
    def admin_size(self, item: EquipmentData):
        if item.width or item.height or item.depth:
            return f'{item.width or "?"} x {item.height or "?"} x {item.depth or "?"} cm'
        else:
            return "-"


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "country",
        "admin_email",
        "admin_phone",
        "admin_is_collection_point",
        "admin_is_distribution_point",
        "managed_by",
    )
    list_filter = (
        ("country", UsedChoicesFieldListFilter),
        "is_collection_point",
        "is_distribution_point",
    )
    ordering = ("name",)

    @admin.display(description=_("contact email"), ordering="email")
    def admin_email(self, location: Location):
        if not location.email:
            return None

        return format_html('<a href="mailto:{email}">{email}</a>', email=location.email)

    @admin.display(description=_("contact phone"), ordering="phone")
    def admin_phone(self, location: Location):
        if not location.phone:
            return None

        return format_html('<a href="tel:{phone}">{phone}</a>', phone=location.phone)

    @admin.display(
        boolean=True,
        ordering="is_collection_point",
        description=mark_safe(
            '<img alt="Is collection point" style="height: 1.5em; margin: -0.4em" src="' + static_import_icon + '">'
        ),
    )
    def admin_is_collection_point(self, location: Location):
        return location.is_collection_point

    @admin.display(
        boolean=True,
        ordering="is_distribution_point",
        description=mark_safe(
            '<img alt="Is distribution point" style="height: 1.5em; margin: -0.4em" src="' + static_export_icon + '">'
        ),
    )
    def admin_is_distribution_point(self, location: Location):
        return location.is_distribution_point


class ShipmentItemInlineAdmin(CompactInline):
    model = ShipmentItem
    extra = 0
    readonly_fields = ("offered_item", "amount")

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("shipment")
        return qs


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("name", "when", "from_location", "to_location", "is_delivered")
    list_filter = (
        "is_delivered",
        "from_location",
        "to_location",
    )
    date_hierarchy = "when"
    ordering = ("when",)
    search_fields = (
        "name",
        "to_location__name",
        "to_location__city",
        "to_location__country",
        "from_location__name",
        "from_location__city",
        "from_location__country",
    )

    inlines = (ShipmentItemInlineAdmin,)


@admin.register(ShipmentItem)
class ShipmentItemAdmin(ExportActionModelAdmin):
    list_display = (
        "amount",
        "admin_offered_item",
        # "admin_requested_item",
        "shipment",
        "is_delivered",
    )
    list_filter = (
        "shipment",
        "shipment__is_delivered",
        (
            "offered_item__offer__contact__organisation",
            admin.RelatedOnlyFieldListFilter,
        ),
        # (
        #     "requested_item__request__contact__organisation",
        #     admin.RelatedOnlyFieldListFilter,
        # ),
    )
    search_fields = (
        "offered_item__brand",
        "offered_item__model",
        # "requested_item__brand",
        # "requested_item__model",
        "offered_item__offer__contact__organisation__name",
        # "requested_item__request__contact__organisation__name",
    )
    ordering = ("shipment",)

    # TODO
    # resource_class = ShipmentItemExportResource

    def get_queryset(self, request: HttpRequest):
        qs = (
            super()
            .get_queryset(request)
            .select_related(
                "shipment",
                "offered_item__offer__contact__organisation",
            )
            .prefetch_related(
                "offered_item__requested_items__request__contact__organisation",
            )
        )
        return qs

    @admin.display(
        description=_("is delivered"),
        boolean=True,
    )
    def is_delivered(self, item: ShipmentItem):
        return item.shipment and item.shipment.is_delivered

    @admin.display(description=_("offered item"))
    def admin_offered_item(self, item: ShipmentItem):
        return format_html(
            "<b>{item}</b><br>{offer}",
            item=item.offered_item,
            offer=item.offered_item.offer,
        )

    # @admin.display(description=_("requested item"))
    # def admin_requested_item(self, claim: Claim):
    #     if claim.requested_item_id:
    #         return format_html(
    #             "<b>{item}</b><br>{request}",
    #             item=claim.requested_item,
    #             request=claim.requested_item.request,
    #         )
    #     else:
    #         return mark_safe("<b>Preemptive shipment</b><br>" "Just ship it to a distribution point")
