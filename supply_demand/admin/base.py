from django.contrib import admin
from django.db.models import Q


class ContactOnlyAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        if request.user.is_superuser or request.user.is_viewer:
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
