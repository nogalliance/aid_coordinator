from typing import Iterable

from django.utils.html import format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.contrib import admin
from django.forms import TextInput, NumberInput

from supply_demand.models import Request, RequestItem


class RequestItemInline(admin.TabularInline):
    model = RequestItem
    min_num = 1
    extra = 0

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
    list_display = ('organisation', 'goal', 'admin_items')
    autocomplete_fields = ('organisation', 'contact')
    inlines = (RequestItemInline,)

    @admin.display(description=_('items'))
    def admin_items(self, request: Request):
        def alts(alt_items: Iterable[RequestItem]) -> str:
            alt_out = ' or '.join([str(alt_item) + alts(alt_item.requestitem_set.all()) for alt_item in alt_items])
            if not alt_out:
                return ''
            return ' or ' + alt_out

        items = []
        for item in request.requestitem_set.filter(alternative_for=None):
            out = str(item) + alts(item.requestitem_set.all())
            items.append((out,))

        return format_html_join(
            mark_safe('<br>'),
            '{}',
            items
        )

    def get_form(self, request, obj=None, **kwargs):
        request.parent_obj = obj
        return super().get_form(request, obj, **kwargs)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset

        if request.user.organisation_id:
            return queryset.filter(organisation_id=request.user.organisation_id)

        return queryset.none()

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.organisation_id

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.organisation_id

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.organisation_id
