from django.contrib import admin
from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import render
from django.templatetags.static import static
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from import_export.admin import ExportActionModelAdmin, ImportExportActionModelAdmin
from logistics.filters import UsedChoicesFieldListFilter
from logistics.forms import AssignToShipmentForm
from logistics.models import EquipmentData, Item, Location, Shipment, ShipmentItem
from logistics.resources import EquipmentDataResource
from nonrelated_inlines.admin import NonrelatedTabularInline

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
        "type",
        "managed_by",
    )
    list_filter = (
        ("country", UsedChoicesFieldListFilter),
        "type",
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


class ShipmentItemInlineAdmin(admin.TabularInline):
    model = ShipmentItem
    extra = 0
    max_num = 0
    readonly_fields = (
        "claim",
        "amount",
        "last_location",
    )
    exclude = ("parent_shipment_item",)

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("shipment")
        return qs


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("name", "shipment_date", "delivery_date", "from_location", "to_location", "is_delivered", "notes")
    list_filter = ("is_delivered", "from_location", "to_location", "shipment_date", "delivery_date")
    date_hierarchy = "delivery_date"
    ordering = ("delivery_date",)
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
        "claim",
        "amount",
        "shipment_link",
        "last_location",
        "is_delivered",
    )
    list_filter = (
        "last_location",
        "shipment__is_delivered",
        (
            "claim__offered_item__offer__contact__organisation",
            admin.RelatedOnlyFieldListFilter,
        ),
    )
    search_fields = (
        "shipment__name",
        "claim__offered_item__brand",
        "claim__offered_item__model",
        "claim__offered_item__offer__contact__organisation__name",
        "last_location__name",
    )
    autocomplete_fields = (
        "claim",
        "parent_shipment_item",
    )
    ordering = ("-created_at",)

    # TODO
    # resource_class = ShipmentItemExportResource

    def get_queryset(self, request: HttpRequest):
        qs = (
            super()
            .get_queryset(request)
            .select_related(
                "claim__offered_item",
                "last_location",
                "shipment__from_location",
                "shipment__to_location",
                "parent_shipment_item",
            )
        )
        return qs

    @admin.display(description=_("is delivered"), boolean=True)
    def is_delivered(self, item: ShipmentItem):
        return item.shipment and item.shipment.is_delivered

    @admin.display(description=_("last_location"))
    def last_location_link(self, item: ShipmentItem):
        if not item.last_location:
            return ""
        return format_html(
            '<a href="{url}">{text}</a>',
            url=reverse("admin:logistics_location_change", args=(item.last_location_id,)),
            text=f"{item.last_location}",
        )

    @admin.display(description=_("shipment"))
    def shipment_link(self, item: ShipmentItem):
        if not item.shipment:
            return ""
        return format_html(
            '<a href="{url}">{text}</a>',
            url=reverse("admin:logistics_shipment_change", args=(item.shipment_id,)),
            text=f"{item.shipment}",
        )


class ShipmentItemHistoryInlineAdmin(NonrelatedTabularInline):
    model = ShipmentItem
    verbose_name = _("Shipment History of the Item")
    verbose_name_plural = _("Shipment History of the Items")
    extra = 0
    max_num = 0
    can_delete = False
    fields = (
        "claim",
        "amount",
        "last_location",
        "shipment",
        "shipment_dates",
    )

    readonly_fields = fields

    def get_form_queryset(self, obj):
        query = """
            WITH RECURSIVE parents AS (
                SELECT logistics_shipmentitem.*, 0 AS relative_depth
                FROM logistics_shipmentitem
                WHERE id = %s

                UNION ALL

                SELECT logistics_shipmentitem.*, parents.relative_depth - 1
                FROM logistics_shipmentitem,parents
                WHERE logistics_shipmentitem.id = parents.parent_shipment_item_id
            )
            SELECT id, parent_shipment_item_id, relative_depth
            FROM parents
            ORDER BY relative_depth;
        """
        ids = [shipment_item.id for shipment_item in ShipmentItem.objects.raw(query, [obj.id])]

        return ShipmentItem.objects.filter(id__in=ids).select_related(
            "claim__offered_item",
            "last_location",
            "shipment__from_location",
            "shipment__to_location",
            "parent_shipment_item",
        )

    @admin.display(description=_("shipment_dates"))
    def shipment_dates(self, item: Item):
        text = f"{item.shipment.shipment_date} -> {item.shipment.delivery_date}"
        if not item.shipment.is_delivered:
            text = _("{text} (on the way)").format(text=text)
        return text


class ClaimedItemShipmentHistoryInlineAdmin(ShipmentItemHistoryInlineAdmin):
    verbose_name = _("Shipment History of the Claimed Item")
    verbose_name_plural = _("Shipment History of the Claimed Items")

    def get_form_queryset(self, obj):
        return (
            ShipmentItem.objects.filter(claim=obj.claim)
            .order_by("when", "created_at")
            .select_related(
                "claim__offered_item",
                "last_location",
                "shipment__from_location",
                "shipment__to_location",
                "parent_shipment_item",
            )
        )


@admin.register(Item)
class ItemAdmin(ShipmentItemAdmin):
    list_display = (
        "claim",
        "available",
        "amount",
        "last_location_link",
        "shipment_link",
        "is_delivered",
        "parent_shipment_item",
    )
    ordering = ("-created_at",)
    actions = ("assign_to_shipment",)

    inlines = (
        ShipmentItemHistoryInlineAdmin,
        ClaimedItemShipmentHistoryInlineAdmin,
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = (
            qs.annotate(sent=Coalesce(Sum("sent_items__amount"), 0))
            .prefetch_related("sent_items")
            .annotate(available=F("amount") - F("sent"))
            .filter(available__gt=0)
        )
        return qs

    @admin.action(description=_("Assign to shipment"))
    def assign_to_shipment(self, request, queryset):

        if "apply" in request.POST:
            shipment = Shipment.objects.get(id=request.POST["shipment"])
            amount_list = request.POST.getlist("amount")
            for index, item in enumerate(queryset):
                amount = amount_list[index]
                ShipmentItem.objects.create(
                    shipment=shipment,
                    claim=item.claim,
                    amount=amount,
                    last_location=shipment.from_location,
                    parent_shipment_item_id=item.id,
                )

            return HttpResponseRedirect(request.get_full_path())

        errors = []
        form = None
        if len(set(queryset.values_list("last_location", flat=True))) > 1:
            errors.append(_("Choosen items are in different locations."))
        if queryset.filter(shipment__is_delivered=False).exists():
            errors.append(_("Some of items are not delivered yet or attached to another shipment."))
        if not errors:
            shipment_queryset = Shipment.objects.filter(
                from_location=queryset.first().last_location,
            )
            form = AssignToShipmentForm(initial=dict(shipment_queryset=shipment_queryset))
        return render(
            request,
            "admin/assign_to_shipment.html",
            context={"items": queryset, "errors": errors, "form": form, "adjustable_amount": True},
        )

    @admin.display(description=_("available"))
    def available(self, item: Item):
        return item.available
