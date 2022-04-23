from django.contrib import admin
from django.db.models import Q, QuerySet
from django.forms import NumberInput, TextInput


class ContactOnlyAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        if request.user.is_superuser:
            return queryset

        if request.user.organisation_id:
            return queryset.filter(
                Q(contact__organisation_id=request.user.organisation_id) |
                Q(contact=request.user)
            )

        return queryset.filter(contact=request.user)


# noinspection PyMethodMayBeStatic,PyUnusedLocal
class ReadOnlyMixin:
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class CompactInline(admin.TabularInline):
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)

        if db_field.name == 'brand':
            field.widget = TextInput(attrs={'style': 'width: 5em', 'maxlength': 50})
        elif db_field.name == 'model':
            field.widget = TextInput(attrs={'style': 'width: 16em', 'maxlength': 50})
        elif db_field.name == 'notes':
            field.widget = TextInput(attrs={'style': 'width: 16em', 'maxlength': 250})
        elif db_field.name in ['amount', 'up_to']:
            field.widget = NumberInput(attrs={'style': 'width: 3em', 'min': 0, 'max': 999})

        return field
