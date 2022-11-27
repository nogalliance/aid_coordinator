import sys

from django import forms
from django.http import HttpRequest
from import_export import fields, resources
from import_export.forms import ConfirmImportForm, ImportForm

from supply_demand.models import Offer, OfferItem, RequestItem


class MyModelResource(resources.ModelResource):
    def __init__(self, request: HttpRequest = None):
        super().__init__()
        self.request = request


class RequestItemResource(MyModelResource):
    class Meta:
        model = RequestItem
        fields = [
            "type__name",
            "brand",
            "model",
            "amount",
            "up_to",
            "notes",
            "request__goal",
            "request__contact__first_name",
            "request__contact__last_name",
            "request__contact__email",
            "request__contact__organisation__name",
        ]

    def get_fields(self):
        my_fields = super().get_fields()
        if not self.request.user.is_superuser:
            my_fields = [field for field in my_fields if field.column_name not in ("request__contact__email",)]

        return my_fields


class CustomImportForm(ImportForm):
    offer = forms.ModelChoiceField(
        queryset=Offer.objects.order_by("contact__organisation__name", "contact__last_name", "description"),
        required=True,
    )


class CustomConfirmImportForm(ConfirmImportForm):
    offer = forms.ModelChoiceField(
        queryset=Offer.objects.order_by("contact__organisation__name", "contact__last_name", "description"),
        required=True,
    )


class OfferItemImportResource(MyModelResource):
    class Meta:
        model = OfferItem
        fields = ("brand", "model", "amount", "notes")
        force_init_instance = True

    def after_import_instance(self, instance, new, row_number=None, **kwargs):
        if "form" in kwargs and "offer" in kwargs["form"].cleaned_data:
            instance.offer_id = kwargs["form"].cleaned_data["offer"].id


class OfferItemExportResource(MyModelResource):
    class Meta:
        model = OfferItem
        fields = [
            "type__name",
            "brand",
            "model",
            "amount",
            "received",
            "notes",
            "offer__contact__first_name",
            "offer__contact__last_name",
            "offer__contact__email",
            "offer__contact__organisation__name",
        ]

    def get_fields(self):
        my_fields = super().get_fields()
        if not self.request.user.is_superuser:
            my_fields = [field for field in my_fields if field.column_name not in ("received", "offer__contact__email")]

        return my_fields
