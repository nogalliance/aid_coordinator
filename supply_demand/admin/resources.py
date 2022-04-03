from import_export import resources

from supply_demand.models import OfferItem


class OfferItemResource(resources.ModelResource):
    class Meta:
        model = OfferItem
        fields = ('brand', 'model', 'received',
                  'offer__contact__first_name', 'offer__contact__last_name', 'offer__contact__email',
                  'offer__contact__organisation__name',
                  'claimed_by__first_name', 'claimed_by__last_name', 'claimed_by__email',
                  "claimed_by__organisation__name")
