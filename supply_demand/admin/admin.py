from typing import Iterable

from admin_wizard.admin import UpdateAction
from django.contrib import admin, messages
from django.db.models import Case, F, OuterRef, Subquery, Sum, When
from django.db.models.functions import Coalesce
from django.forms import forms
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import render
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html, format_html_join
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from import_export.admin import ExportActionModelAdmin, ImportExportActionModelAdmin
from logistics.forms import AssignToShipmentForm
from logistics.models import Location, LocationType, Shipment, ShipmentItem, ShipmentStatus
from supply_demand.admin.base import CompactInline, ContactOnlyAdmin, ReadOnlyMixin
from supply_demand.admin.filters import (
    LocationFilter,
    OverclaimedListFilter,
    ProcessedClaimListFilter,
    ProcessedOfferedItemListFilter,
    ReceivedClaimListFilter,
)
from supply_demand.admin.forms import (
    MoveToOfferForm,
    MoveToRequestForm,
    RequestItemInlineFormSet,
    change_type_form_factory,
)
from supply_demand.admin.resources import (
    CustomConfirmImportForm,
    CustomImportForm,
    OfferItemExportResource,
    OfferItemImportResource,
    RequestItemResource,
)
from supply_demand.models import (
    Change,
    ChangeAction,
    ChangeType,
    Claim,
    ItemType,
    Offer,
    OfferItem,
    Request,
    RequestItem,
)
from supply_demand.resources import ClaimExportResource


@admin.register(ItemType)
class ItemTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "order")


class RequestItemInline(CompactInline):
    model = RequestItem
    formset = RequestItemInlineFormSet
    extra = 1

    fields = (
        "type",
        "brand",
        "model",
        "amount",
        "up_to",
        "notes",
        "alternative_for",
        "assigned",
    )
    readonly_fields = ("assigned",)

    @admin.display(description=_("assigned"))
    def assigned(self, item: RequestItem):
        if not item.pk:
            return ""

        assignments = []
        for claim in item.claim_set.all():
            assignments.append((f"{claim.amount}x {claim.offered_item.brand} {claim.offered_item.model}",))

        if assignments:
            return format_html_join(mark_safe("<br>"), "{}", assignments)
        else:
            return "-"

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)

        if db_field.name == "alternative_for":
            parent_obj = request.parent_obj
            if parent_obj is not None:
                field.queryset = field.queryset.filter(request=parent_obj)
                field.limit_choices_to = {"request_id": parent_obj.id}
            else:
                field.queryset = field.queryset.none()

        return field


@admin.register(Request)
class RequestAdmin(ContactOnlyAdmin):
    list_display = ("contact", "goal", "admin_items")
    list_filter = ("contact__organisation",)
    autocomplete_fields = ("contact",)
    inlines = (RequestItemInline,)
    search_fields = (
        "goal",
        "description",
        "contact__first_name",
        "contact__last_name",
        "contact__organisation__name",
        "items__brand",
        "items__model",
        "items__notes",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.prefetch_related("items__claim_set")
        return qs

    @admin.display(description=_("items"))
    def admin_items(self, request: Request):
        def prefix(my_item: RequestItem) -> str:
            # TODO - reduce number of queries
            if my_item.assigned:
                return "✅ "
            else:
                return ""

        def alts(alt_items: Iterable[RequestItem]) -> str:
            alt_out = " or ".join(
                [prefix(alt_item) + alt_item.counted_name + alts(alt_item.alternatives.all()) for alt_item in alt_items]
            )
            if not alt_out:
                return ""
            return " or " + alt_out

        items = []
        for item in request.items.all():
            # Don't filter the query, it will ruin the prefetch_related we already did, this is much faster
            if item.alternative_for_id:
                continue

            out = prefix(item) + item.counted_name + alts(item.alternatives.all())
            items.append((out,))

        return format_html_join(mark_safe("<br>"), "{}", items)

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if request.user.is_superuser:
            return fields

        # Non-superusers don't see notes
        return [field for field in fields if field != "internal_notes"]

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if request.user.is_superuser or request.user.is_viewer:
            fields = list(fields) + ["created_at", "updated_at"]
        return fields

    def get_list_filter(self, request: HttpRequest):
        if not request.user.is_superuser:
            return []

        return super().get_list_filter(request)

    def get_form(self, request, obj=None, **kwargs):
        request.parent_obj = obj
        return super().get_form(request, obj, **kwargs)

    # noinspection DuplicatedCode
    def save_related(self, request, form, *args, **kwargs):
        super().save_related(request, form, *args, **kwargs)

        # Now everything is saved, so we can add the change entry
        before = form.instance.change_before
        after = form.instance.change_log_entry()
        if before != after:
            Change(
                who=request.user,
                action=ChangeAction.CHANGE if form.instance.change_id else ChangeAction.ADD,
                type=ChangeType.REQUEST,
                what=str(form.instance),
                before=before,
                after=after,
            ).save()

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            self.delete_model(request, obj)

    def delete_model(self, request, obj):
        before = obj.change_log_entry()
        after = ""
        Change(
            who=request.user,
            action=ChangeAction.DELETE,
            type=ChangeType.REQUEST,
            what=str(obj),
            before=before,
            after=after,
        ).save()
        super().delete_model(request, obj)


class ClaimInlineAdmin(CompactInline):
    model = Claim
    extra = 0
    fields = (
        "offered_item",
        "admin_requested_item",
        "amount",
        "shipment",
        "requester",
        "donor",
    )

    readonly_fields = fields

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related()
        return qs

    @admin.display(description=_("requested item"))
    def admin_requested_item(self, item: Claim):
        if not item.requested_item_id:
            return mark_safe("<b>Preemptive shipment</b><br>" "Just ship it to a distribution point")
        return item.requested_item

    @admin.display(description=_("shipment"))
    def shipment(self, item: Claim):
        if item.shipment_item:
            return format_html(
                '<a href="{url}">{shipment_item}</a>',
                url=reverse("admin:logistics_item_change", args=(item.shipment_item_id,)),
                shipment_item=f"{item.shipment_item.shipment.name}",
            )
        return _("not shipped yet")

    @admin.display(description=_("requester"))
    def requester(self, item: Claim):
        if item.requested_item.request.contact.organisation_id:
            organisation = item.requested_item.request.contact.organisation
        else:
            organisation = _("no organisation")
        requester = item.requested_item.request.contact
        requester_name = requester.display_name()
        return format_html(
            '<a href="{url}">{requester}</a>',
            url=reverse("admin:contacts_contact_change", args=(requester.id,)),
            requester=f"{requester_name}({organisation})",
        )

    @admin.display(description=_("donor"))
    def donor(self, item: Claim):
        if item.offered_item.offer.contact.organisation_id:
            organisation = item.offered_item.offer.contact.organisation
        else:
            organisation = _("no organisation")
        donor = item.offered_item.offer.contact
        donor_name = donor.display_name()
        return format_html(
            '<a href="{url}">{donor}</a>',
            url=reverse("admin:contacts_contact_change", args=(donor.id,)),
            donor=f"{donor_name}({organisation})",
        )


@admin.register(RequestItem)
class RequestItemAdmin(ExportActionModelAdmin):
    list_display = (
        "type",
        "model",
        "brand",
        "amount",
        "up_to",
        "assigned",
        "needed",
        "created_at",
        "item_of",
    )
    list_filter = ("type", "brand", "request__contact__organisation")
    autocomplete_fields = ("request",)
    ordering = ("brand", "model")
    resource_class = RequestItemResource
    search_fields = (
        "brand",
        "model",
        "notes",
        "request__description",
        "request__contact__organisation__name",
        "request__contact__last_name",
    )
    actions = (
        UpdateAction(form_class=MoveToRequestForm, title=_("Move to other request")),
        "set_type_hardware",
        "set_type_software",
        "set_type_service",
        "set_type_other",
        "new_type_admin_action",
    )
    inlines = (ClaimInlineAdmin,)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.action_form = change_type_form_factory(self.action_form)

    @property
    def media(self):
        super_media = super().media
        # noinspection PyProtectedMember
        return forms.Media(js=super_media._js + ["supply_demand/action_itemtype.js"], css=super_media._css)

    @admin.action(
        permissions=["change"],
        description="Change item type",
    )
    def new_type_admin_action(self, request, queryset):
        new_type_id = request.POST["new_type"]
        if not new_type_id:
            messages.error(request, "No new item type selected")
            return

        new_type = ItemType.objects.get(pk=new_type_id)
        count = queryset.update(type=new_type)
        messages.info(request, f"{count} item(s) updated")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related("request__contact__organisation")
        qs = qs.annotate(assigned=Coalesce(Sum("claim__amount"), 0))
        qs = qs.annotate(
            needed=Case(
                When(up_to__isnull=False, then=F("up_to") - F("assigned")),
                default=F("amount") - F("assigned"),
            )
        )
        if request.user.is_donor:
            qs = qs.exclude(needed=0)
        return qs

    def get_resource_kwargs(self, request, *args, **kwargs):
        new_kwargs = super().get_resource_kwargs(request, *args, **kwargs)
        new_kwargs["request"] = request
        return new_kwargs

    @admin.display(description=_("assigned"))
    def assigned(self, item: RequestItem):
        if item.assigned == item.amount:
            icon_url = static("admin/img/icon-yes.svg")
            return format_html('<img src="{}" alt="True">', icon_url)
        elif item.assigned == 0:
            icon_url = static("admin/img/icon-no.svg")
            return format_html('<img src="{}" alt="False">', icon_url)
        return f"{item.assigned}/{item.amount}"

    @admin.display(description=_("needed"))
    def needed(self, item: RequestItem):
        if item.needed <= 0:
            return "0"

        url = reverse("offer", kwargs={"item_id": item.id})

        return format_html(
            """
            <div style="display: inline-flex; justify-content: space-between; align-items: center; width: 14ch">
                <span>{needed}</span>
                <a class="button" style="margin: -4px; margin-right: 0" href="{url}">{offer}</a>
            </div>
            """,
            url=url,
            needed=item.needed,
            offer=_("Donate"),
        )

    @admin.display(description=_("item of"))
    def item_of(self, item: RequestItem):
        return format_html(
            '<a href="{url}">{name}</a>',
            url=reverse("admin:supply_demand_request_change", args=(item.request.id,)),
            name=item.request,
        )

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        user = request.user
        if not obj:
            return user.is_superuser or user.is_donor or user.is_viewer

        return (
            user.is_superuser
            or user.is_donor
            or user.is_viewer
            or obj.request.contact == user
            or (
                obj.request.contact.organisation_id is not None
                and obj.request.contact.organisation_id == user.organisation_id
            )
        )

    def has_change_permission(self, request, obj=None):
        if not obj:
            return request.user.is_superuser

        return (
            request.user.is_superuser
            or obj.request.contact == request.user
            or (
                obj.request.contact.organisation_id is not None
                and obj.request.contact.organisation_id == request.user.organisation_id
            )
        )

    def has_delete_permission(self, request, obj=None):
        if not obj:
            return request.user.is_superuser

        return (
            request.user.is_superuser
            or obj.request.contact == request.user
            or (
                obj.request.contact.organisation_id is not None
                and obj.request.contact.organisation_id == request.user.organisation_id
            )
        )

    def get_actions(self, request):
        super_actions = super().get_actions(request)
        if request.user.is_viewer:
            return {key: value for key, value in super_actions.items() if key == "export_admin_action"}

        if not request.user.is_superuser:
            return {}

        return super_actions

    def get_inlines(self, request, obj):
        if not request.user.is_superuser:
            return []

        return super().get_inlines(request, obj)

    def get_list_display(self, request):
        fields = super().get_list_display(request)

        user = request.user
        if user.is_superuser:
            fields = [field for field in fields if field not in ("needed",)]
        elif user.is_viewer:
            fields = [field for field in fields if field not in ("needed",)]
        else:
            fields = [
                field for field in fields if field not in ("request", "created_at", "assigned", "delivered", "item_of")
            ]

        return fields

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if request.user.is_superuser or request.user.is_viewer:
            fields = list(fields) + ["created_at", "updated_at"]
        return fields

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if request.user.is_superuser:
            return fields

        if request.user.is_viewer:
            return [field for field in fields if field not in ("notes",)]

        return [field for field in fields if field not in ("request", "notes", "alternative_for")]


class OfferItemInline(CompactInline):
    model = OfferItem
    extra = 1

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if request.user.is_superuser:
            fields = [field for field in fields if field not in ("hold",)]
        else:
            fields = [field for field in fields if field not in ("rejected",)]
        return fields

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if request.user.is_superuser:
            fields += ("admin_claims",)
        else:
            fields += (
                "hold",
                "rejected",
                "received",
            )

        return fields

    @admin.display(description=_("Claims"))
    def admin_claims(self, item: OfferItem):
        lines = []
        for item in item.claim_set.all():
            url = reverse("admin:supply_demand_claim_change", args=(item.id,))
            lines.append(
                (url, f"{item.amount}x {item.requested_item.request}"),
            )
        if not lines:
            return "-"
        return format_html_join(mark_safe("<br>"), "<a href='{}'>{}</a>", lines)

    @admin.display(description=_("Please hold"))
    def hold(self, item: OfferItem):
        if item.rejected:
            return format_html(
                '<span style="display: inline-block; width: 20ch; margin-top: -0.7em">{}</span>',
                _("Likely not useful for Ukraine, please don't ship"),
            )
        else:
            return "-"


@admin.register(Offer)
class OfferAdmin(ContactOnlyAdmin):
    list_display = ("description", "admin_organisation", "admin_contact", "admin_items")
    list_filter = (LocationFilter, "contact__organisation")
    autocomplete_fields = ("contact",)
    inlines = (OfferItemInline,)
    search_fields = (
        "description",
        "contact__first_name",
        "contact__last_name",
        "contact__organisation__name",
        "items__brand",
        "items__model",
        "items__notes",
    )

    @admin.display(description=_("organisation"), ordering="contact__organisation__name")
    def admin_organisation(self, offer: Offer):
        if offer.contact.organisation_id:
            return offer.contact.organisation

    @admin.display(description=_("contact"), ordering="contact__first_name")
    def admin_contact(self, offer: Offer):
        return offer.contact.display_name()

    @admin.display(description=_("items"))
    def admin_items(self, offer: Offer):
        lines = []
        for item in offer.items.all():
            if item.rejected:
                prefix = "⛔️ "
            else:
                prefix = ""

            lines.append(
                (
                    prefix,
                    item.counted_name,
                )
            )

        return format_html_join(mark_safe("<br>"), "{}{}", lines)

    def get_list_filter(self, request: HttpRequest):
        if not request.user.is_superuser:
            return []

        return super().get_list_filter(request)

    def get_list_display(self, request):
        fields = super().get_list_display(request)

        # Non-donors don't see donor info
        if request.user.is_superuser or request.user.is_viewer:
            pass
        elif not request.user.is_donor:
            fields = [field for field in fields if field not in ("admin_organisation", "admin_contact")]

        return fields

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if request.user.is_superuser or request.user.is_viewer:
            fields = list(fields) + ["created_at", "updated_at"]
        return fields

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if request.user.is_superuser:
            return fields

        # Non-superusers don't see internal notes
        fields = [field for field in fields if field not in ("internal_notes",)]

        # Non-donors don't see donor info
        if request.user.is_viewer:
            fields = [field for field in fields if field not in ("location", "delivery_method")]
        elif not request.user.is_donor:
            fields = [
                field for field in fields if field not in ("organisation", "contact", "location", "delivery_method")
            ]

        return fields

    # noinspection DuplicatedCode
    def save_related(self, request, form, *args, **kwargs):
        super().save_related(request, form, *args, **kwargs)

        # Now everything is saved, so we can add the change entry
        before = form.instance.change_before
        after = form.instance.change_log_entry()
        if before != after:
            Change(
                who=request.user,
                action=ChangeAction.CHANGE if form.instance.change_id else ChangeAction.ADD,
                type=ChangeType.OFFER,
                what=str(form.instance),
                before=before,
                after=after,
            ).save()

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            self.delete_model(request, obj)

    def delete_model(self, request, obj):
        before = obj.change_log_entry()
        after = ""
        Change(
            who=request.user,
            action=ChangeAction.DELETE,
            type=ChangeType.OFFER,
            what=str(obj),
            before=before,
            after=after,
        ).save()
        super().delete_model(request, obj)


@admin.register(OfferItem)
class OfferItemAdmin(ImportExportActionModelAdmin):
    list_display = (
        "type",
        "model",
        "brand",
        "notes",
        "amount",
        "claimed",
        "available",
        "processed",
        "delivered",
        "rejected",
        "item_of",
    )
    list_filter = (
        ProcessedOfferedItemListFilter,
        "type",
        "rejected",
        "received",
        OverclaimedListFilter,
        "brand",
        ("offer__contact__organisation", admin.RelatedOnlyFieldListFilter),
        "offer",
    )
    autocomplete_fields = ("offer",)
    ordering = ("brand", "model")
    search_fields = (
        "brand",
        "model",
        "notes",
        "offer__description",
        "offer__contact__organisation__name",
        "offer__contact__last_name",
    )
    actions = [
        UpdateAction(form_class=MoveToOfferForm, title=_("Move to other offer")),
        "set_type_hardware",
        "set_type_software",
        "set_type_service",
        "set_type_other",
        "set_rejected",
        "set_not_rejected",
        "set_received",
        "set_not_received",
        "assign_to_shipment",
        "new_type_admin_action",
    ]
    inlines = (ClaimInlineAdmin,)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.action_form = change_type_form_factory(self.action_form)

    @property
    def media(self):
        super_media = super().media
        # noinspection PyProtectedMember
        return forms.Media(js=super_media._js + ["supply_demand/action_itemtype.js"], css=super_media._css)

    @admin.action(
        permissions=["change"],
        description="Change item type",
    )
    def new_type_admin_action(self, request, queryset):
        new_type_id = request.POST["new_type"]
        if not new_type_id:
            messages.error(request, "No new item type selected")
            return

        new_type = ItemType.objects.get(pk=new_type_id)
        count = queryset.update(type=new_type)
        messages.info(request, f"{count} item(s) updated")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related("offer__contact__organisation", "type")
        qs = qs.prefetch_related("shipmentitem_set")
        qs = qs.annotate(claimed=Coalesce(Sum("claim__amount"), 0))
        subquery = (
            ShipmentItem.objects.filter(
                offered_item_id=OuterRef("id"),
                shipment__status=ShipmentStatus.DELIVERED,
                last_location__type=LocationType.REQUESTER,
            )
            .values("offered_item_id")
            .annotate(total=Sum("amount"))
            .values("total")
        )
        qs = qs.annotate(delivered=Coalesce(Subquery(subquery), 0))
        subquery = (
            ShipmentItem.objects.filter(
                offered_item_id=OuterRef("id"),
                parent_shipment_item_id__isnull=True,
            )
            .values("offered_item_id")
            .annotate(total=Sum("amount"))
            .values("total")
        )
        qs = qs.annotate(processed=Coalesce(Subquery(subquery), 0))
        qs = qs.annotate(available=Coalesce(F("amount") - F("claimed"), 0))
        qs = qs.annotate(deliverable=Coalesce(F("amount") - F("processed"), 0))
        if request.user.is_requester:
            qs = qs.exclude(available=0)
        return qs

    @admin.action(description=_("Set to rejected"))
    def set_rejected(self, _request: HttpRequest, queryset: RequestItem.objects):
        queryset.update(rejected=True)

    @admin.action(description=_("Set to NOT rejected"))
    def set_not_rejected(self, _request: HttpRequest, queryset: RequestItem.objects):
        queryset.update(rejected=False)

    @admin.action(description=_("Set to received"))
    def set_received(self, _request: HttpRequest, queryset: RequestItem.objects):
        queryset.update(received=True)

    @admin.action(description=_("Set to NOT received"))
    def set_not_received(self, _request: HttpRequest, queryset: RequestItem.objects):
        queryset.update(received=False)

    @admin.action(description=_("Assign to shipment"))
    def assign_to_shipment(self, request, queryset):
        if "apply" in request.POST:
            created = False
            if request.POST["shipment"] == "new":
                contact = queryset.first().offer.contact
                today = timezone.now()
                shipment, created = Shipment.objects.get_or_create(
                    name=f"Offer from donor {contact} - {today:%Y-%m-%d}",
                    defaults={
                        "shipment_date": today.date(),
                        "from_location": Location.objects.filter(type=LocationType.DONOR).first(),
                    },
                )
            else:
                shipment = Shipment.objects.get(id=request.POST["shipment"])

            amount_list = request.POST.getlist("amount")
            for index, item in enumerate(queryset):
                amount = amount_list[index]
                if not amount:
                    continue
                shipment_item = ShipmentItem.objects.create(
                    shipment=shipment,
                    offered_item=item,
                    amount=amount,
                    last_location=shipment.from_location,
                )
                item.shipment_item = shipment_item
                item.save()

            if created:
                return HttpResponseRedirect(reverse("admin:logistics_shipment_change", args=[shipment.id]))
            return HttpResponseRedirect(request.get_full_path())

        errors = []
        form = None
        # Validation
        if len(set(queryset.values_list("offer__contact", flat=True))) > 1:
            errors.append(_("Chosen items are offered by different donors. Ship them separately please."))
        if not errors:
            shipment_queryset = Shipment.objects.filter(from_location__type=LocationType.DONOR)
            form = AssignToShipmentForm(initial=dict(shipment_queryset=shipment_queryset))

        return render(
            request,
            "admin/assign_to_shipment.html",
            context={"items": queryset, "errors": errors, "form": form, "is_deliverable": True},
        )

    def get_import_resource_class(self):
        """
        Returns ResourceClass to use for import.
        """
        return OfferItemImportResource

    def get_export_resource_class(self):
        """
        Returns ResourceClass to use for import.
        """
        return OfferItemExportResource

    def get_resource_kwargs(self, request, *args, **kwargs):
        new_kwargs = super().get_resource_kwargs(request, *args, **kwargs)
        new_kwargs["request"] = request
        return new_kwargs

    def get_import_form(self):
        return CustomImportForm

    def get_confirm_import_form(self):
        return CustomConfirmImportForm

    def get_form_kwargs(self, form, *args, **kwargs):
        initial = super().get_form_kwargs(form, *args, **kwargs)
        if hasattr(form, "cleaned_data") and "offer" in form.cleaned_data:
            initial["offer"] = form.cleaned_data["offer"].id
        return initial

    def get_import_data_kwargs(self, request, *args, **kwargs):
        """
        Prepare kwargs for import_data.
        """
        return kwargs

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        user = request.user
        if not obj:
            return user.is_superuser or user.is_requester or user.is_viewer

        return (
            user.is_superuser
            or user.is_requester
            or user.is_viewer
            or obj.offer.contact == user
            or (
                obj.offer.contact.organisation_id is not None
                and obj.offer.contact.organisation_id == user.organisation_id
            )
        )

    def has_change_permission(self, request, obj=None):
        if not obj:
            return request.user.is_superuser

        return (
            request.user.is_superuser
            or obj.offer.contact == request.user
            or (
                obj.offer.contact.organisation_id is not None
                and obj.offer.contact.organisation_id == request.user.organisation_id
            )
        )

    def has_delete_permission(self, request, obj=None):
        if not obj:
            return request.user.is_superuser

        return (
            request.user.is_superuser
            or obj.offer.contact == request.user
            or (
                obj.offer.contact.organisation_id is not None
                and obj.offer.contact.organisation_id == request.user.organisation_id
            )
        )

    def get_inlines(self, request, obj):
        if not request.user.is_superuser:
            return []

        return super().get_inlines(request, obj)

    def get_actions(self, request):
        super_actions = super().get_actions(request)
        if request.user.is_viewer:
            return {key: value for key, value in super_actions.items() if key == "export_admin_action"}

        if not request.user.is_superuser:
            return {}

        return super_actions

    def get_search_fields(self, request):
        if not request.user.is_superuser:
            return ["brand", "model", "notes"]

        return super().get_search_fields(request)

    def get_list_display(self, request):
        fields = super().get_list_display(request)

        if request.user.is_superuser:
            fields = [field for field in fields if field not in ("available",)]
        elif request.user.is_viewer:
            fields = [field for field in fields if field not in ("rejected", "received", "available")]
        else:
            fields = [
                field
                for field in fields
                if field not in ("rejected", "received", "amount", "processed", "claimed", "delivered", "item_of")
            ]

        return fields

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if request.user.is_superuser or request.user.is_viewer:
            fields = list(fields) + ["created_at", "updated_at"]
        return fields

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if request.user.is_superuser:
            return fields

        if request.user.is_viewer:
            fields = [field for field in fields if field not in ("rejected", "received", "available")]

        # Non-superusers don't see notes
        return [field for field in fields if field not in ("request", "notes", "alternative_for")]

    def get_list_filter(self, request):
        if not request.user.is_superuser:
            return ["type", "brand"]

        return super().get_list_filter(request)

    @admin.display(description=_("item of"))
    def item_of(self, item: OfferItem):
        offeritemlist_url = reverse("admin:supply_demand_offeritem_changelist")
        return format_html(
            '<a href="{url}">{name}</a><div><strong><a href="{filter_url}">{filter_text}</a></strong></div>',
            url=reverse("admin:supply_demand_offer_change", args=(item.offer.id,)),
            name=item.offer,
            filter_url=f"{offeritemlist_url}?{urlencode(dict(offer__id__exact=item.offer_id))}",
            filter_text=_("Filter by offer"),
        )

    @admin.display(description=_("claimed"))
    def claimed(self, item: OfferItem):
        if not item.amount:
            return None

        if item.amount >= item.claimed:
            return item.claimed
        else:
            return format_html('<span style="color:red">{amount}</span>', amount=item.claimed)

    @admin.display(description=_("delivered"))
    def delivered(self, item: OfferItem):
        return item.delivered

    @admin.display(description=_("processed"))
    def processed(self, item: OfferItem):
        return item.processed

    @admin.display(description=_("available"))
    def available(self, item: OfferItem):
        if item.available <= 0:
            return "0"

        url = reverse("request", kwargs={"item_id": item.id})

        return format_html(
            """
        <div style="display: inline-flex; justify-content: space-between; align-items: center; width: 14ch">
            <span>{available}</span>
            <a class="button" style="margin: -4px; margin-right: 0" href="{url}">{request}</a>
        </div>
        """,
            url=url,
            available=item.available,
            request=_("Request"),
        )


@admin.register(Change)
class ChangeAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ("when", "who", "action", "type", "what")
    list_filter = (
        "action",
        "type",
        ("who", admin.RelatedOnlyFieldListFilter),
    )
    date_hierarchy = "when"
    ordering = ("-when", "who")
    search_fields = (
        "who__last_name",
        "who__first_name",
        "who__organisation__name",
        "what",
        "before",
        "after",
    )


@admin.register(Claim)
class ClaimAdmin(ExportActionModelAdmin):
    list_display = (
        "amount",
        "admin_offered_item",
        "admin_requested_item",
        "when",
        "is_processed",
        "is_received",
        "shipment",
    )
    list_filter = (
        ProcessedClaimListFilter,
        ReceivedClaimListFilter,
        (
            "offered_item__offer__contact__organisation",
            admin.RelatedOnlyFieldListFilter,
        ),
        (
            "requested_item__request__contact__organisation",
            admin.RelatedOnlyFieldListFilter,
        ),
    )
    readonly_fields = ("when", "updated_at")
    search_fields = (
        "offered_item__brand",
        "offered_item__model",
        "requested_item__brand",
        "requested_item__model",
        "offered_item__offer__contact__organisation__name",
        "requested_item__request__contact__organisation__name",
    )
    autocomplete_fields = (
        "offered_item",
        "requested_item",
    )

    ordering = ("-when",)
    resource_class = ClaimExportResource

    def get_queryset(self, request: HttpRequest):
        qs = super().get_queryset(request)
        qs = qs.select_related(
            "offered_item__offer__contact__organisation",
            "requested_item__request__contact__organisation",
            "shipment_item__shipment",
        )
        qs = qs.prefetch_related(
            "offered_item__shipmentitem_set",
        )
        return qs

    @admin.display(description=_("offered item"))
    def admin_offered_item(self, claim: Claim):
        offeritemlist_url = reverse("admin:supply_demand_offeritem_changelist")
        return format_html(
            '<a href="{item_url}">{item_text}</a><div><strong><a href="{offer_url}">{offer_text}</a></strong></div>',
            item_url=reverse("admin:supply_demand_offeritem_change", args=(claim.offered_item_id,)),
            item_text=f"{claim.offered_item}",
            offer_url=f"{offeritemlist_url}?{urlencode(dict(offer__id__exact=claim.offered_item.offer_id))}",
            offer_text=f"{claim.offered_item.offer}",
        )

    @admin.display(description=_("requested item"))
    def admin_requested_item(self, claim: Claim):
        requestitemlist_url = reverse("admin:supply_demand_requestitem_changelist")
        if claim.requested_item_id:
            return format_html(
                '<a href="{item_url}">{item_text}</a><div><strong><a href="{request_url}">{request_text}</a></strong></div>',
                item_url=reverse("admin:supply_demand_requestitem_change", args=(claim.requested_item_id,)),
                item_text=f"{claim.requested_item}",
                request_url=f"{requestitemlist_url}?{urlencode(dict(request__id__exact=claim.requested_item.request_id))}",
                request_text=f"{claim.requested_item.request}",
            )
        else:
            return mark_safe("<b>Preemptive shipment</b><br>" "Just ship it to a distribution point")

    @admin.display(description=_("processed?"))
    def is_processed(self, claim: Claim):
        if claim.shipment_item:
            icon_url = static("admin/img/icon-yes.svg")
            return format_html('<img src="{}" alt="True">', icon_url)
        else:
            icon_url = static("admin/img/icon-no.svg")
            return format_html('<img src="{}" alt="False">', icon_url)

    @admin.display(description=_("received?"))
    def is_received(self, claim: Claim):
        if claim.shipment_item_id and claim.shipment_item.shipment.status == ShipmentStatus.DELIVERED:
            icon_url = static("admin/img/icon-yes.svg")
            return format_html('<img src="{}" alt="True">', icon_url)
        else:
            icon_url = static("admin/img/icon-no.svg")
            return format_html('<img src="{}" alt="False">', icon_url)

    @admin.display(description=_("shipment"))
    def shipment(self, item: Claim):
        shipment_item = item.shipment_item
        if not shipment_item:
            return
        shipment_name = shipment_item.shipment.name if shipment_item.shipment else _("No shipment")

        return format_html(
            '<a href="{url}">{shipment}</a>',
            url=reverse("admin:logistics_shipment_change", args=(shipment_item.shipment.id,)),
            shipment=shipment_name,
        )
