from typing import Iterable

from django.contrib import admin
from django.db.models import Q
from django.forms import TextInput, NumberInput
from django.utils.html import format_html_join, format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from supply_demand.models import Request, RequestItem, OfferItem, Offer


class CompactInline(admin.TabularInline):
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)

        if db_field.name == 'brand':
            field.widget = TextInput(attrs={'style': 'width: 5em', 'maxlength': 50})
        elif db_field.name == 'model':
            field.widget = TextInput(attrs={'style': 'width: 8em', 'maxlength': 50})
        elif db_field.name == 'notes':
            field.widget = TextInput(attrs={'style': 'width: 16em', 'maxlength': 250})
        elif db_field.name in ['amount', 'up_to']:
            field.widget = NumberInput(attrs={'style': 'width: 3em', 'min': 0, 'max': 999})

        return field


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
class RequestAdmin(admin.ModelAdmin):
    list_display = ('admin_organisation', 'goal', 'admin_items')
    autocomplete_fields = ('contact',)
    inlines = (RequestItemInline,)

    @admin.display(description=_('organisation'), ordering='contact__organisation__name')
    def admin_organisation(self, offer: Offer):
        if offer.contact.organisation_id:
            return offer.contact.organisation

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

    def get_form(self, request, obj=None, **kwargs):
        request.parent_obj = obj
        return super().get_form(request, obj, **kwargs)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.prefetch_related('items__alternatives__alternatives', 'contact__organisation')

        if request.user.is_superuser:
            return queryset

        if request.user.organisation_id:
            return queryset.filter(
                Q(contact__organisation_id=request.user.organisation_id) |
                Q(contact=request.user)
            )

        return queryset.filter(contact=request.user)


class OfferItemInline(CompactInline):
    model = OfferItem
    min_num = 1
    extra = 0

    autocomplete_fields = ('claimed_by',)

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if not request.user.is_superuser:
            fields += ('received', 'claimed_by',)
        return fields


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('description', 'admin_organisation', 'admin_contact', 'admin_items')
    list_filter = ('contact__organisation',)
    autocomplete_fields = ('contact',)
    inlines = (OfferItemInline,)

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

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if request.user.is_superuser:
            return fields

        # Non-superusers don't see notes
        return [field for field in fields if field != 'internal_notes']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.prefetch_related('items', 'contact__organisation')

        if request.user.is_superuser:
            return queryset

        if request.user.organisation_id:
            return queryset.filter(
                Q(contact__organisation_id=request.user.organisation_id) |
                Q(contact=request.user)
            )

        return queryset.filter(contact=request.user)
