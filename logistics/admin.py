from django.contrib import admin
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import render
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from import_export.admin import ExportActionModelAdmin, ImportExportActionModelAdmin
from logistics.filters import UsedChoicesFieldListFilter
from logistics.forms import AssignToShipmentForm
from logistics.models import EquipmentData, Item, Location, Shipment, ShipmentItem
from logistics.resources import EquipmentDataResource, ItemExportResource, ShipmentItemExportResource
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
    fields = (
        "admin_offered_item",
        "amount",
        "last_location",
    )

    readonly_fields = fields

    def get_queryset(self, request):
        qs = (
            super()
            .get_queryset(request)
            .select_related(
                "shipment",
                "offered_item",
                "last_location",
                # "claim__requested_item",
            )
        )
        return qs

    @admin.display(description=_("shipment item"), ordering="offered_item")
    def admin_offered_item(self, item: ShipmentItem):
        return format_html(
            '<a href="{item_url}">{offered_item}</a>',
            item_url=reverse("admin:logistics_shipmentitem_change", args=(item.id,)),
            offered_item=item.offered_item,
        )


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

    save_on_top = True

    inlines = (ShipmentItemInlineAdmin,)


@admin.register(ShipmentItem)
class ShipmentItemAdmin(ExportActionModelAdmin):
    list_display = (
        "offered_item",
        "amount",
        "admin_shipment",
        "last_location",
        "is_delivered",
    )
    list_filter = (
        "shipment__is_delivered",
        "last_location",
        "shipment__to_location",
        "shipment__from_location",
        (
            "offered_item__offer__contact__organisation",
            admin.RelatedOnlyFieldListFilter,
        ),
    )
    search_fields = (
        "shipment__name",
        "offered_item__brand",
        "offered_item__model",
        "offered_item__offer__contact__organisation__name",
        "last_location__name",
    )
    autocomplete_fields = (
        "offered_item",
        "parent_shipment_item",
    )
    ordering = ("-created_at",)

    resource_class = ShipmentItemExportResource

    def get_queryset(self, request: HttpRequest):
        qs = (
            super()
            .get_queryset(request)
            .select_related(
                "offered_item__offer__contact__organisation",
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
    def admin_last_location(self, item: ShipmentItem):
        if not item.last_location:
            return ""
        return format_html(
            '<a href="{url}">{text}</a>',
            url=reverse("admin:logistics_location_change", args=(item.last_location_id,)),
            text=f"{item.last_location}",
        )

    @admin.display(description=_("shipment"))
    def admin_shipment(self, item: ShipmentItem):
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
        "admin_offered_item",
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
            "offered_item",
            "last_location",
            "shipment__from_location",
            "shipment__to_location",
            "parent_shipment_item",
        )

    @admin.display(description=_("shipment item"), ordering="offered_item")
    def admin_offered_item(self, item: ShipmentItem):
        return format_html(
            '<a href="{item_url}">{offered_item}</a>',
            item_url=reverse("admin:logistics_shipmentitem_change", args=(item.id,)),
            offered_item=item.offered_item,
        )

    @admin.display(description=_("shipment dates"))
    def shipment_dates(self, item: Item):
        text = f"{item.shipment.shipment_date} -> {item.shipment.delivery_date}"
        if not item.shipment.is_delivered:
            text = _("{text} (on the way)").format(text=text)
        return text


class OfferedItemShipmentHistoryInlineAdmin(ShipmentItemHistoryInlineAdmin):
    verbose_name = _("Shipment History of the Donated Item")
    verbose_name_plural = _("Shipment History of the Donated Items")

    def get_form_queryset(self, obj):
        return (
            ShipmentItem.objects.filter(offered_item=obj.offered_item)
            .order_by("when", "created_at")
            .select_related(
                "offered_item",
                "last_location",
                "shipment__from_location",
                "shipment__to_location",
                "parent_shipment_item",
            )
        )


@admin.register(Item)
class ItemAdmin(ShipmentItemAdmin):
    list_display = (
        "offered_item",
        "available",
        "admin_last_location",
        "admin_shipment",
        "is_delivered",
    )

    basic_fields = (
        "admin_offered_item",
        "available",
        "last_location",
        "shipment",
        "shipment_date",
        "delivery_date",
    )

    fieldsets = (
        (None, {"fields": basic_fields}),
        (
            _("Offer"),
            {
                "classes": ("collapse",),
                "fields": (
                    "admin_offer",
                    "admin_offer_by",
                    "admin_offer_email",
                    "admin_offer_phone",
                ),
            },
        ),
    )

    readonly_fields = basic_fields

    ordering = ("-created_at",)
    actions = ("assign_to_shipment",)

    inlines = (
        ShipmentItemHistoryInlineAdmin,
        # OfferedItemShipmentHistoryInlineAdmin,
    )

    resource_class = ItemExportResource

    def get_queryset(self, request: HttpRequest):
        qs = super().get_queryset(request).filter(available__gt=0)
        return qs

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.action(description=_("Assign to shipment"))
    def assign_to_shipment(self, request, queryset):

        if "apply" in request.POST:
            if request.POST["shipment"] == "new":
                today = timezone.now()
                shipment, created = Shipment.objects.get_or_create(
                    name=f"Shipment {request.user} - {today:%Y-%m-%d}",
                    defaults={
                        "shipment_date": today.date(),
                        "from_location": queryset.first().last_location,
                    },
                )
            else:
                shipment = Shipment.objects.get(id=request.POST["shipment"])
            amount_list = request.POST.getlist("amount")
            for index, item in enumerate(queryset):
                amount = amount_list[index]
                ShipmentItem.objects.create(
                    shipment=shipment,
                    offered_item_id=item.offered_item_id,
                    amount=amount,
                    last_location=shipment.from_location,
                    parent_shipment_item_id=item.id,
                )

            if created:
                return HttpResponseRedirect(reverse("admin:logistics_shipment_change", args=[shipment.id]))
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

    @admin.display(description=_("shipment date"))
    def shipment_date(self, item: Item):
        if item.shipment.shipment_date:
            return item.shipment.shipment_date
        return _("Not shipped yet")

    @admin.display(description=_("delivery date"))
    def delivery_date(self, item: Item):
        if item.shipment.shipment_date:
            if item.shipment.delivery_date:
                if item.shipment.is_delivered:
                    text = item.shipment.delivery_date
                else:
                    text = _("On the way (estimated date is {date})").format(date=item.shipment.delivery_date)
            else:
                text = _("On the way")
        else:
            text = _("Unknown")
        return text

    @admin.display(description=_("shipment item"), ordering="offered_item")
    def admin_offered_item(self, item: ShipmentItem):
        return format_html(
            '<a href="{item_url}">{offered_item}</a>',
            item_url=reverse("admin:logistics_shipmentitem_change", args=(item.id,)),
            offered_item=item.offered_item,
        )

    @admin.display(description=_("amount"))
    def available(self, item: Item):
        return item.available

    @admin.display(description=_("Initial Offer"))
    def admin_offer(self, item: Item):
        return format_html(
            '<a href="{offer_url}">{offer_text}</a>',
            offer_url=reverse("admin:supply_demand_offeritem_change", args=(item.offered_item_id,)),
            offer_text=f"{item.offered_item.offer}",
        )

    @admin.display(description=_("offered by"))
    def admin_offer_by(self, item: Item):
        return item.offered_item.offer.contact

    @admin.display(description=_("email"))
    def admin_offer_email(self, item: Item):
        return item.offered_item.offer.contact.email

    @admin.display(description=_("phone"))
    def admin_offer_phone(self, item: Item):
        return item.offered_item.offer.contact.phone
