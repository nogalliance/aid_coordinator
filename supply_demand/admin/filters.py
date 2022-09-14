from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.db.models import F, QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from aid_coordinator.filters import InputFilter


class OverclaimedListFilter(admin.SimpleListFilter):
    title = _("overclaimed")
    parameter_name = "overclaimed"

    def lookups(self, request: HttpRequest, model_admin: ModelAdmin):
        return (
            ("yes", _("Yes")),
            ("no", _("No")),
        )

    def queryset(self, request: HttpRequest, queryset: QuerySet):
        if self.value() == "yes":
            return queryset.filter(claimed__gt=F("amount"))
        if self.value() == "yes":
            return queryset.filter(claimed__lte=F("amount"))
        else:
            return queryset


class LocationFilter(InputFilter):
    parameter_name = "location"
    title = _("location")

    def queryset(self, request: HttpRequest, queryset: QuerySet):
        if self.value() is not None:
            location = self.value()

            queryset = queryset.filter(location__icontains=location)

        return queryset
