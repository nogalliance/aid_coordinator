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
from logistics.models import EquipmentData, Item, Location, Shipment, ShipmentItem, ShipmentStatus
from logistics.resources import (
    EquipmentDataResource,
    ItemExportResource,
    ShipmentItemExportResource,
)
from nonrelated_inlines.admin import NonrelatedTabularInline

static_import_icon = static("img/import.png")
static_export_icon = static("img/export.png")


@admin.register(EquipmentData)
class EquipmentDataAdmin(ImportExportActionModelAdmin):
    list_display = ("brand", "model", "admin_weight", "admin_size")
    ordering = ("brand", "model")
    search_fields = (
        "brand",
        "model",
    )
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
            )
        )
        return qs

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status == ShipmentStatus.PENDING:
            return tuple(field for field in self.readonly_fields if field not in ["amount"])
        return self.readonly_fields

    @admin.display(description=_("offered item"), ordering="offered_item")
    def admin_offered_item(self, item: ShipmentItem):
        return format_html(
            '<a href="{url}">{text}</a>',
            url=reverse("admin:supply_demand_offeritem_change", args=(item.offered_item_id,)),
            text=item.offered_item,
        )


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "shipment_date",
        "delivery_date",
        "from_location",
        "to_location",
        "status",
        "notes",
    )
    list_filter = (
        "status",
        "from_location",
        "to_location",
        "shipment_date",
        "delivery_date",
    )
    date_hierarchy = "shipment_date"
    ordering = ("-shipment_date",)
    search_fields = (
        "name",
        "to_location__name",
        "to_location__city",
        "to_location__country",
        "from_location__name",
        "from_location__city",
        "from_location__country",
    )
    autocomplete_fields = ("parent_shipment",)

    save_on_top = True

    inlines = (ShipmentItemInlineAdmin,)


@admin.register(ShipmentItem)
class ShipmentItemAdmin(ExportActionModelAdmin):
    list_display = (
        "admin_offered_item",
        "admin_amount",
        "admin_shipment",
        "last_location",
        "status",
    )
    list_filter = (
        "shipment__status",
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

    @admin.display(description=_("delivery status"))
    def status(self, item: ShipmentItem):
        return item.shipment and item.shipment.get_status_display()

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

    @admin.display(description=_("offered item"), ordering="offered_item")
    def admin_offered_item(self, item: ShipmentItem):
        return format_html(
            '<a href="{url}">{text}</a>',
            url=reverse("admin:supply_demand_offeritem_change", args=(item.offered_item_id,)),
            text=item.offered_item,
        )

    @admin.display(description=_("amount"))
    def admin_amount(self, item: ShipmentItem):
        return format_html(
            '<a href="{url}">{text}</a>',
            url=reverse("admin:logistics_shipmentitem_change", args=(item.id,)),
            text=item.available,
        )


class ShipmentItemHistoryInlineAdmin(NonrelatedTabularInline):
    model = ShipmentItem
    verbose_name = _("Shipment History of the Donated Item")
    verbose_name_plural = _("Shipment History of the Donated Items")

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

    def get_offeritem_id(self, obj):
        return obj.offered_item_id

    def get_form_queryset(self, obj):
        offered_item_id = self.get_offeritem_id(obj)
        return (
            ShipmentItem.objects.filter(offered_item_id=offered_item_id)
            .order_by("shipment__shipment_date", "created_at")
            .select_related(
                "offered_item",
                "last_location",
                "shipment__from_location",
                "shipment__to_location",
                "parent_shipment_item",
            )
        )

    @admin.display(description=_("shipment item"), ordering="offered_item")
    def admin_offered_item(self, item: ShipmentItem):
        return format_html(
            '<a href="{url}">{text}</a>',
            url=reverse("admin:logistics_shipmentitem_change", args=(item.id,)),
            text=item.offered_item,
        )

    @admin.display(description=_("shipment dates"))
    def shipment_dates(self, item: Item):
        return f"{item.shipment.shipment_date} -> {item.shipment.delivery_date} ({item.shipment.get_status_display()})"


@admin.register(Item)
class ItemAdmin(ShipmentItemAdmin):
    list_display = (
        "admin_offered_item",
        "admin_available",
        "admin_last_location",
        "admin_shipment",
        "status",
    )

    basic_fields = (
        "admin_shipment_item",
        "admin_available",
        "last_location",
        "shipment",
        "shipment_date",
        "delivery_date",
        "delivery_status",
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
                    "admin_offer_contact_through",
                ),
            },
        ),
    )

    readonly_fields = basic_fields

    ordering = ("-created_at",)
    actions = ("assign_to_shipment",)

    inlines = (ShipmentItemHistoryInlineAdmin,)

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
            created = False
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
                if not amount:
                    continue
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
            errors.append(_("Chosen items are in different locations."))
        if queryset.exclude(shipment__status=ShipmentStatus.DELIVERED).exists():
            errors.append(_("Some of items are not delivered yet or attached to another shipment."))
        if not errors:
            shipment_queryset = Shipment.objects.filter(
                from_location=queryset.first().last_location,
            )
            form = AssignToShipmentForm(initial=dict(shipment_queryset=shipment_queryset))

        return render(
            request,
            "admin/assign_to_shipment.html",
            context={"items": queryset, "errors": errors, "form": form},
        )

    @admin.display(description=_("shipment date"))
    def shipment_date(self, item: Item):
        return item.shipment.shipment_date

    @admin.display(description=_("delivery date"))
    def delivery_date(self, item: Item):
        return item.shipment.delivery_date

    @admin.display(description=_("delivery status"))
    def delivery_status(self, item: Item):
        return item.shipment.get_status_display()

    @admin.display(description=_("shipment item"), ordering="offered_item")
    def admin_shipment_item(self, item: Item):
        return format_html(
            '<strong><a href="{url}">{text}</a></strong>',
            url=reverse("admin:logistics_shipmentitem_change", args=(item.id,)),
            text=item,
        )

    @admin.display(description=_("amount"))
    def admin_available(self, item: Item):
        return format_html(
            '<a href="{url}">{text}</a>',
            url=reverse("admin:logistics_item_change", args=(item.id,)),
            text=item.available,
        )

    @admin.display(description=_("Initial Offer"))
    def admin_offer(self, item: Item):
        return format_html(
            '<a href="{url}">{text}</a>',
            url=reverse("admin:supply_demand_offeritem_change", args=(item.offered_item_id,)),
            text=f"{item.offered_item.offer}",
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

    @admin.display(description=_("contacted through"))
    def admin_offer_contact_through(self, item: Item):
        contact_through = item.offered_item.offer.contact.contact_through
        if not contact_through:
            return ""
        return format_html(
            '<a href="{url}">{text}</a>',
            url=reverse("admin:contacts_contact_change", args=(contact_through.id,)),
            text=contact_through,
        )
        return contact_through
