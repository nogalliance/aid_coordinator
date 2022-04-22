import sys

from django import forms
from import_export import fields, resources
from import_export.forms import ConfirmImportForm, ImportForm

from supply_demand.models import Offer, OfferItem, RequestItem


class RequestItemResource(resources.ModelResource):
    type = fields.Field(attribute='get_type_display', column_name='type')

    class Meta:
        model = RequestItem
        fields = ('type', 'brand', 'model', 'amount', 'up_to', 'notes',
                  'request__goal',
                  'request__contact__first_name', 'request__contact__last_name', 'request__contact__email',
                  'request__contact__organisation__name')


class CustomImportForm(ImportForm):
    offer = forms.ModelChoiceField(
        queryset=Offer.objects.order_by('contact__organisation__name', 'contact__last_name', 'description'),
        required=True,
    )


class CustomConfirmImportForm(ConfirmImportForm):
    offer = forms.ModelChoiceField(
        queryset=Offer.objects.order_by('contact__organisation__name', 'contact__last_name', 'description'),
        required=True,
    )


class OfferItemImportResource(resources.ModelResource):
    class Meta:
        model = OfferItem
        fields = ('brand', 'model', 'amount', 'notes')
        force_init_instance = True

    def after_import_instance(self, instance, new, row_number=None, **kwargs):
        if 'form' in kwargs and 'offer' in kwargs['form'].cleaned_data:
            instance.offer_id = kwargs['form'].cleaned_data['offer'].id


class OfferItemExportResource(resources.ModelResource):
    type = fields.Field(attribute='get_type_display', column_name='type')

    class Meta:
        model = OfferItem
        fields = ('type', 'brand', 'model', 'amount', 'received', 'notes',
                  'offer__contact__first_name', 'offer__contact__last_name', 'offer__contact__email',
                  'offer__contact__organisation__name')
