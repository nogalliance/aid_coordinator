from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.db.models import F, QuerySet, Q
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from aid_coordinator.filters import InputFilter
from logistics.models import ShipmentStatus


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


class ReceivedClaimListFilter(admin.SimpleListFilter):
    title = _("received")
    parameter_name = "received"

    def lookups(self, request: HttpRequest, model_admin: ModelAdmin):
        return (
            ("yes", _("Yes")),
            ("no", _("No")),
        )

    def queryset(self, request: HttpRequest, queryset: QuerySet):
        if self.value() == "yes":
            return queryset.filter(shipment_item__shipment__status=ShipmentStatus.DELIVERED).distinct()
        if self.value() == "no":
            return queryset.exclude(shipment_item__shipment__status=ShipmentStatus.DELIVERED).distinct()
        return queryset


class ProcessedClaimListFilter(admin.SimpleListFilter):
    title = _("processed")
    parameter_name = "processed"

    def lookups(self, request: HttpRequest, model_admin: ModelAdmin):
        return (
            ("yes", _("Yes")),
            ("no", _("No")),
        )

    def queryset(self, request: HttpRequest, queryset: QuerySet):
        if self.value() == "yes":
            return queryset.filter(shipment_item__isnull=False).distinct()
        if self.value() == "no":
            return queryset.filter(shipment_item__isnull=True).distinct()
        return queryset


class ProcessedOfferedItemListFilter(admin.SimpleListFilter):
    title = _("processed")
    parameter_name = "processed"

    def lookups(self, request: HttpRequest, model_admin: ModelAdmin):
        return (
            ("yes", _("Yes")),
            ("partially", _("Partially")),
            ("no", _("No")),
        )

    def queryset(self, request: HttpRequest, queryset: QuerySet):
        if self.value() == "yes":
            return queryset.filter(Q(processed=F("amount"))|Q(rejected=True)).distinct()
        if self.value() == "partially":
            return queryset.filter(processed__gt=0, processed__lt=F("amount")).distinct()
        if self.value() == "no":
            return queryset.filter(processed=0, rejected=False).distinct()
        return queryset


class LocationFilter(InputFilter):
    parameter_name = "location"
    title = _("location")

    def queryset(self, request: HttpRequest, queryset: QuerySet):
        if self.value() is not None:
            location = self.value()

            queryset = queryset.filter(location__icontains=location)

        return queryset
