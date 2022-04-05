from typing import Iterable

from admin_wizard.admin import UpdateAction
from django.contrib import admin
from django.http import HttpRequest
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from import_export.admin import ExportActionModelAdmin

from supply_demand.admin.base import CompactInline, ContactOnlyAdmin, ReadOnlyMixin
from supply_demand.admin.filters import ClaimedFilter
from supply_demand.admin.forms import MoveToOfferForm, MoveToRequestForm
from supply_demand.admin.resources import OfferItemResource, RequestItemResource
from supply_demand.models import Change, ChangeAction, ChangeType, Offer, OfferItem, Request, RequestItem


class RequestItemInline(CompactInline):
    model = RequestItem
    min_num = 1
    extra = 0

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)

        if db_field.name == 'alternative_for':
            parent_obj = request.parent_obj
            if parent_obj is not None:
                field.queryset = field.queryset.filter(request=parent_obj)
                field.limit_choices_to = {'request_id': parent_obj.id}
            else:
                field.queryset = field.queryset.none()

        return field


@admin.register(Request)
class RequestAdmin(ContactOnlyAdmin):
    list_display = ('contact', 'goal', 'admin_items')
    list_filter = ('contact__organisation',)
    autocomplete_fields = ('contact',)
    inlines = (RequestItemInline,)
    search_fields = ('goal', 'description',
                     'contact__first_name', 'contact__last_name', 'contact__organisation__name',
                     'items__brand', 'items__model', 'items__notes')

    @admin.display(description=_('items'))
    def admin_items(self, request: Request):
        def alts(alt_items: Iterable[RequestItem]) -> str:
            alt_out = ' or '.join([str(alt_item) + alts(alt_item.alternatives.all()) for alt_item in alt_items])
            if not alt_out:
                return ''
            return ' or ' + alt_out

        items = []
        for item in request.items.all():
            # Don't filter the query, it will ruin the prefetch_related we already did, this is much faster
            if item.alternative_for_id:
                continue

            out = str(item) + alts(item.alternatives.all())
            items.append((out,))

        return format_html_join(
            mark_safe('<br>'),
            '{}',
            items
        )

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if request.user.is_superuser:
            return fields

        # Non-superusers don't see notes
        return [field for field in fields if field != 'internal_notes']

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

    def delete_model(self, request, obj):
        before = obj.change_log_entry()
        after = ''
        Change(
            who=request.user,
            action=ChangeAction.DELETE,
            type=ChangeType.REQUEST,
            what=str(obj),
            before=before,
            after=after,
        ).save()
        super().delete_model(request, obj)


@admin.register(RequestItem)
class RequestItemAdmin(ExportActionModelAdmin):
    list_display = ('brand', 'model', 'amount', 'up_to', 'item_of')
    list_filter = ('brand',)
    autocomplete_fields = ('request',)
    ordering = ('brand', 'model')
    resource_class = RequestItemResource
    actions = (UpdateAction(form_class=MoveToRequestForm, title=_('Move to other request')),)

    @admin.display(description=_('item of'))
    def item_of(self, item: RequestItem):
        return format_html('<a href="{url}">{name}</a>',
                           url=reverse('admin:supply_demand_request_change', args=(item.request.id,)),
                           name=item.request)

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        if not obj:
            return request.user.is_superuser or request.user.is_donor

        return (
                request.user.is_superuser or
                request.user.is_donor or
                obj.request.contact == request.user or
                obj.request.contact.organisation_id == request.user.organisation_id
        )

    def has_change_permission(self, request, obj=None):
        if not obj:
            return request.user.is_superuser

        return (
                request.user.is_superuser or
                obj.request.contact == request.user or
                obj.request.contact.organisation_id == request.user.organisation_id
        )

    def has_delete_permission(self, request, obj=None):
        if not obj:
            return request.user.is_superuser

        return (
                request.user.is_superuser or
                obj.request.contact == request.user or
                obj.request.contact.organisation_id == request.user.organisation_id
        )

    def get_actions(self, request):
        if not request.user.is_superuser:
            return []

        return super().get_actions(request)

    def get_list_display(self, request):
        fields = super().get_list_display(request)

        if not request.user.is_superuser:
            fields = [field for field in fields if field not in ('request', 'item_of')]

        return fields

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if request.user.is_superuser:
            return fields

        # Non-superusers don't see notes
        return [field for field in fields if field not in ('request', 'notes', 'alternative_for')]


class OfferItemInline(CompactInline):
    model = OfferItem
    min_num = 1
    extra = 0

    autocomplete_fields = ('claimed_by',)

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if request.user.is_superuser:
            return fields

        # Non-superusers don't see notes
        return [field for field in fields if field != 'claimed_by']

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if not request.user.is_superuser:
            fields += ('received', 'claimed_by',)
        return fields


@admin.register(Offer)
class OfferAdmin(ContactOnlyAdmin):
    list_display = ('description', 'admin_organisation', 'admin_contact', 'admin_items')
    list_filter = ('contact__organisation',)
    autocomplete_fields = ('contact',)
    inlines = (OfferItemInline,)
    search_fields = ('description',
                     'contact__first_name', 'contact__last_name', 'contact__organisation__name',
                     'items__brand', 'items__model', 'items__notes')

    @admin.display(description=_('organisation'), ordering='contact__organisation__name')
    def admin_organisation(self, offer: Offer):
        if offer.contact.organisation_id:
            return offer.contact.organisation

    @admin.display(description=_('contact'), ordering='contact__first_name')
    def admin_contact(self, offer: Offer):
        return offer.contact.display_name()

    @admin.display(description=_('items'))
    def admin_items(self, offer: Offer):
        lines = []
        for item in offer.items.all():
            marker = mark_safe('<span style="color:green">✔︎</span>&nbsp') if item.received else ''
            if item.claimed_by_id:
                description = format_html('<s>{}</s>', str(item))
            else:
                description = str(item)

            lines.append((marker, description))

        return format_html_join(mark_safe('<br>'), '{} {}', lines)

    def get_list_filter(self, request: HttpRequest):
        if not request.user.is_superuser:
            return []

        return super().get_list_filter(request)

    def get_list_display(self, request):
        fields = super().get_list_display(request)

        # Non-donors don't see donor info
        if not request.user.is_donor:
            fields = [field for field in fields if field not in ('admin_organisation', 'admin_contact')]

        return fields

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if request.user.is_superuser:
            return fields

        # Non-superusers don't see internal notes
        fields = [field for field in fields if field not in ('internal_notes',)]

        # Non-donors don't see donor info
        if not request.user.is_donor:
            fields = [field for field in fields if field not in ('organisation', 'contact',
                                                                 'location', 'delivery_method')]

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

    def delete_model(self, request, obj):
        before = obj.change_log_entry()
        after = ''
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
class OfferItemAdmin(ExportActionModelAdmin):
    list_display = ('brand', 'model', 'amount', 'received', 'claimed', 'item_of')
    list_filter = ('received', ClaimedFilter, 'brand')
    autocomplete_fields = ('offer', 'claimed_by')
    ordering = ('brand', 'model')
    resource_class = OfferItemResource
    actions = (UpdateAction(form_class=MoveToOfferForm, title=_('Move to other offer')),)

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        if not obj:
            return request.user.is_superuser or request.user.is_requester

        return (
                request.user.is_superuser or
                request.user.is_requester or
                obj.offer.contact == request.user or
                obj.offer.contact.organisation_id == request.user.organisation_id
        )

    def has_change_permission(self, request, obj=None):
        if not obj:
            return request.user.is_superuser

        return (
                request.user.is_superuser or
                obj.offer.contact == request.user or
                obj.offer.contact.organisation_id == request.user.organisation_id
        )

    def has_delete_permission(self, request, obj=None):
        if not obj:
            return request.user.is_superuser

        return (
                request.user.is_superuser or
                obj.offer.contact == request.user or
                obj.offer.contact.organisation_id == request.user.organisation_id
        )

    def get_actions(self, request):
        if not request.user.is_superuser:
            return []

        return super().get_actions(request)

    def get_list_display(self, request):
        fields = super().get_list_display(request)

        if not request.user.is_superuser:
            fields = [field for field in fields if field not in ('received', 'claimed', 'item_of')]

        return fields

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if request.user.is_superuser:
            return fields

        # Non-superusers don't see notes
        return [field for field in fields if field not in ('request', 'notes', 'alternative_for')]

    def get_list_filter(self, request):
        if not request.user.is_superuser:
            return ['brand']

        return super().get_list_filter(request)

    @admin.display(description=_('item of'))
    def item_of(self, item: OfferItem):
        return format_html('<a href="{url}">{name}</a>',
                           url=reverse('admin:supply_demand_offer_change', args=(item.offer.id,)),
                           name=item.offer)

    @admin.display(description=_('claimed'), boolean=True)
    def claimed(self, item: OfferItem):
        return item.claimed_by_id is not None


@admin.register(Change)
class ChangeAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ('when', 'who', 'action', 'type', 'what')
    list_filter = (
        'action',
        'type',
        ('who', admin.RelatedOnlyFieldListFilter),
    )
    date_hierarchy = 'when'
    ordering = ('-when', 'who')
