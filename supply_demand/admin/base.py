from django.contrib import admin
from django.forms import NumberInput, TextInput


# noinspection PyMethodMayBeStatic
class SuperUserOnlyMixin:
    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# noinspection PyMethodMayBeStatic
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
            field.widget = TextInput(attrs={'style': 'width: 8em', 'maxlength': 50})
        elif db_field.name == 'notes':
            field.widget = TextInput(attrs={'style': 'width: 16em', 'maxlength': 250})
        elif db_field.name in ['amount', 'up_to']:
            field.widget = NumberInput(attrs={'style': 'width: 3em', 'min': 0, 'max': 999})

        return field
