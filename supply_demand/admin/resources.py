from import_export import fields, resources

from supply_demand.models import OfferItem, RequestItem


class RequestItemResource(resources.ModelResource):
    type = fields.Field(attribute='get_type_display', column_name='type')

    class Meta:
        model = RequestItem
        fields = ('type', 'brand', 'model', 'amount', 'up_to', 'notes',
                  'request__goal',
                  'request__contact__first_name', 'request__contact__last_name', 'request__contact__email',
                  'request__contact__organisation__name')


class OfferItemResource(resources.ModelResource):
    class Meta:
        model = OfferItem
        fields = ('type', 'brand', 'model', 'received', 'notes',
                  'offer__contact__first_name', 'offer__contact__last_name', 'offer__contact__email',
                  'offer__contact__organisation__name',
                  'claimed_by__first_name', 'claimed_by__last_name', 'claimed_by__email',
                  "claimed_by__organisation__name")
