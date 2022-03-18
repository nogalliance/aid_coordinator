from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from contacts.models import Organisation, Contact


@admin.register(Contact)
class ContactAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'organisation', 'role', 'admin_email')
    search_fields = ('username', 'first_name', 'last_name', 'organisation__name')

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)

        if len(fieldsets) < 2:
            return fieldsets

        return (
            fieldsets[0],
            (fieldsets[1][0], {
                **fieldsets[1][1],
                'fields': fieldsets[1][1]['fields'] + ('phone', 'organisation', 'role'),
            }),
            *fieldsets[2:]
        )

    @admin.display(description=_('email'))
    def admin_email(self, contact: Contact):
        return format_html('<a href="mailto:{name} %3c{email}%3e">{email}</a>', name=contact.get_full_name(),
                           email=contact.email)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset

        if request.user.organisation_id:
            return queryset.filter(organisation_id=request.user.organisation_id)

        return queryset.none()


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'admin_website')
    search_fields = ('name',)
    ordering = ('name',)

    @admin.display(description=_('website'))
    def admin_website(self, organisation: Organisation):
        return format_html('<a href="{url}" target="_blank">{url}</a>', url=organisation.website)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset

        if request.user.organisation_id:
            return queryset.filter(id=request.user.organisation_id)

        return queryset.none()
