from django.db.models import Sum
from django.db.models.functions import Coalesce
from django_filters import CharFilter, NumberFilter
from django_filters.rest_framework import FilterSet
from rest_framework.fields import CharField, Field
from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet

from supply_demand.models import ItemType, OfferItem, RequestItem


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


class RequestItemFilterSet(FilterSet):
    type__not = NumberFilter(field_name='type', lookup_expr='exact', exclude=True)
    brand__not = CharFilter(field_name='brand', lookup_expr='icontains', exclude=True)

    class Meta:
        model = RequestItem
        fields = {
            'type': ['exact'],
            'brand': ['exact', 'icontains'],
            'model': ['exact', 'icontains'],
            'amount': ['exact', 'range'],
        }


# Serializers define the API representation.
class OfferItemSerializer(HyperlinkedModelSerializer):
    type = CharField(source='get_type_display')
    line = CharField(source='counted_name')

    class Meta:
        model = OfferItem
        fields = ['type', 'brand', 'model', 'amount', 'notes', 'line']


class TypeField(Field):
    def to_internal_value(self, data):
        raise NotImplemented

    def to_representation(self, value):
        return ItemType(value).label


class RequestItemSerializer(HyperlinkedModelSerializer):
    type = TypeField()

    class Meta:
        model = RequestItem
        fields = ['type', 'brand', 'model', 'notes', 'amount']


# ViewSets define the view behavior.
class OfferItemViewSet(ReadOnlyModelViewSet):
    queryset = OfferItem.objects.filter(claim=None)
    serializer_class = OfferItemSerializer
    filterset_class = OfferItemFilterSet
    search_fields = ['brand', 'model', 'notes']


class RequestItemViewSet(ReadOnlyModelViewSet):
    queryset = RequestItem.objects.filter(claim=None).values('type', 'brand', 'model', 'notes').annotate(
        amount=Sum(Coalesce('up_to', 'amount'))
    )
    serializer_class = RequestItemSerializer
    filterset_class = RequestItemFilterSet
    search_fields = ['brand', 'model']
