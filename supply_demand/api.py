from django_filters import CharFilter
from django_filters.rest_framework import FilterSet
from rest_framework.fields import CharField
from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet

from supply_demand.models import OfferItem


class OfferItemFilterSet(FilterSet):
    brand__not = CharFilter(field_name='brand', lookup_expr='icontains', exclude=True)

    class Meta:
        model = OfferItem
        fields = {
            'type': ['exact'],
            'brand': ['exact', 'icontains'],
            'model': ['exact', 'icontains'],
            'amount': ['exact', 'range'],
        }


# Serializers define the API representation.
class OfferItemSerializer(HyperlinkedModelSerializer):
    type = CharField(source='get_type_display')
    line = CharField(source='__str__')

    class Meta:
        model = OfferItem
        fields = ['type', 'brand', 'model', 'amount', 'notes', 'line']


# ViewSets define the view behavior.
class OfferItemViewSet(ReadOnlyModelViewSet):
    queryset = OfferItem.objects.all()
    serializer_class = OfferItemSerializer
    filterset_class = OfferItemFilterSet
    search_fields = ['brand', 'model', 'notes']
