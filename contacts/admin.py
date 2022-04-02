from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.tokens import default_token_generator
from django.db import models
from django.db.models import Q
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.html import format_html, format_html_join
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _

from contacts.forms import ContactForm, AddContactForm
from contacts.models import Organisation, Contact


@admin.register(Contact)
class ContactAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'organisation', 'admin_groups', 'admin_email')
    list_filter = ("is_superuser", "is_active", "groups")
    search_fields = ('username', 'first_name', 'last_name', 'organisation__name')
    readonly_fields = ("last_login", "date_joined")
    actions = ('send_welcome_email',)
    form = ContactForm
    superuser_fieldsets = (
        (None, {
            "fields": ("username", "password", "send_welcome_email"),
        }),
        (_("Personal info"), {
            "fields": ("first_name", "last_name", "listed"),
        }),
        (_("Contact"), {
            "fields": ("email", "phone"),
        }),
        (_("Organisation"), {
            "fields": ("organisation", "role"),
        }),
        (_("Permissions"), {
            "fields": ("is_active", "is_superuser", "groups"),
        }),
        (_("Important dates"), {
            "fields": ("last_login", "date_joined"),
        }),
    )
    fieldsets = (
        (None, {
            "fields": ("username",),
        }),
        (_("Personal info"), {
            "fields": ("first_name", "last_name", "listed"),
        }),
        (_("Contact"), {
            "fields": ("email", "phone"),
        }),
        (_("Organisation"), {
            "fields": ("organisation", "role"),
        }),
        (_("Important dates"), {
            "fields": ("last_login", "date_joined"),
        }),
    )
    add_form_template = None
    add_form = AddContactForm
    add_fieldsets = (
        (None, {
            "fields": ("username", "send_welcome_email"),
        }),
        (_("Personal info"), {
            "fields": ("first_name", "last_name"),
        }),
        (_("Contact"), {
            "fields": ("email", "phone"),
        }),
        (_("Organisation"), {
            "fields": ("organisation", "role"),
        }),
        (_("Permissions"), {
            "fields": ("is_superuser", "groups"),
        }),
    )
    formfield_overrides = {
        models.ManyToManyField: {'widget': forms.CheckboxSelectMultiple},
    }

    @admin.display(description=_('Send welcome email'))
    def send_welcome_email(self, request: HttpRequest, queryset: Contact.objects):
        queryset = queryset.prefetch_related('groups')
        queryset = queryset.select_related('organisation')
        for contact in queryset:
            if contact.is_superuser:
                self.message_user(request, f"Not sending a message to superuser {contact}", level=messages.WARNING)
                continue

            groups = [str(group).lower() for group in contact.groups.all()]
            if 'donors' not in groups and 'requesters' not in groups:
                self.message_user(request, f"{contact} is neither a donor nor a requester, not sending welcome message",
                                  level=messages.ERROR)
                continue

            password_reset_url = 'https://' + request.get_host() + reverse('password_reset_confirm', kwargs={
                'uidb64': urlsafe_base64_encode(force_bytes(contact.pk)),
                'token': default_token_generator.make_token(contact)
            })
            message = render_to_string("email/welcome.txt.j2", {
                'request': request,
                'contact': contact,
                'groups': groups,
                'password_reset_url': password_reset_url,
            }, request)
            contact.email_user("Your keepukraineconnected.org account", message)

            self.message_user(request, f"Sent welcome message to {contact}")

    @admin.display(description=_('groups'))
    def admin_groups(self, contact: Contact):
        if contact.is_superuser:
            return "Superuser"

        return format_html_join(
            ', ',
            '{}',
            [(str(group),) for group in contact.groups.all()]
        )

    @admin.display(description=_('email'))
    def admin_email(self, contact: Contact):
        return format_html('<a href="mailto:{name} %3c{email}%3e">{email}</a>', name=contact.get_full_name(),
                           email=contact.email)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.prefetch_related('organisation', 'groups')

        if request.user.is_superuser:
            return queryset

        if request.user.organisation_id:
            return queryset.filter(
                Q(organisation_id=request.user.organisation_id) |
                Q(pk=request.user.pk)
            )

        return queryset.filter(pk=request.user.pk)

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        elif request.user.is_superuser:
            return self.superuser_fieldsets
        else:
            return self.fieldsets

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if not request.user.is_superuser:
            fields += ('password', 'organisation', 'is_active', 'is_superuser', 'groups')
        return fields

    def response_add(self, request, obj, post_url_continue=None):
        # Redirect to the list after creation
        if not post_url_continue:
            post_url_continue = reverse("admin:contacts_contact_changelist")

        response = super().response_add(request, obj, post_url_continue)
        if request.POST.get('send_welcome_email') == 'on':
            # Insert a hook to send the welcome email
            queryset = Contact.objects.filter(pk=obj.pk)
            self.send_welcome_email(request, queryset)
        return response

    def response_change(self, request, obj):
        response = super().response_change(request, obj)
        if request.user.is_superuser and request.POST.get('send_welcome_email') == 'on':
            # Insert a hook to send the welcome email
            queryset = Contact.objects.filter(pk=obj.pk)
            self.send_welcome_email(request, queryset)
        return response


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
