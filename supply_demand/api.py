from django.db.models import Sum
from django.db.models.functions import Coalesce
from django_filters import CharFilter, NumberFilter
from django_filters.rest_framework import FilterSet
from rest_framework.fields import CharField, IntegerField, ReadOnlyField
from rest_framework.relations import StringRelatedField
from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet

from supply_demand.models import OfferItem, RequestItem


class OfferItemFilterSet(FilterSet):
    brand__not = CharFilter(field_name="brand", lookup_expr="icontains", exclude=True)

    class Meta:
        model = OfferItem
        fields = {
            "type": ["exact"],
            "brand": ["exact", "icontains"],
            "model": ["exact", "icontains"],
            "amount": ["exact", "range"],
        }


class RequestItemFilterSet(FilterSet):
    type__not = NumberFilter(field_name="type", lookup_expr="exact", exclude=True)
    brand__not = CharFilter(field_name="brand", lookup_expr="icontains", exclude=True)

    class Meta:
        model = RequestItem
        fields = {
            "type": ["exact"],
            "brand": ["exact", "icontains"],
            "model": ["exact", "icontains"],
            "amount": ["exact", "range"],
        }


# Serializers define the API representation.
class OfferItemSerializer(HyperlinkedModelSerializer):
    type = StringRelatedField()
    line = CharField(source="counted_name")

    class Meta:
        model = OfferItem
        fields = ["type", "brand", "model", "amount", "notes", "line"]


class RequestItemSerializer(HyperlinkedModelSerializer):
    type = StringRelatedField()
    amount = IntegerField(source='max_amount')

    class Meta:
        model = RequestItem
        fields = ["type", "brand", "model", "notes", "amount"]


# ViewSets define the view behavior
class OfferItemViewSet(ReadOnlyModelViewSet):
    queryset = OfferItem.objects.filter(claim=None).prefetch_related('type')
    serializer_class = OfferItemSerializer
    filterset_class = OfferItemFilterSet
    search_fields = ["brand", "model", "notes"]


class RequestItemViewSet(ReadOnlyModelViewSet):
    queryset = (
        RequestItem.objects.filter(claim=None)
        .prefetch_related('type')
        .annotate(max_amount=Sum(Coalesce("up_to", "amount")))
    )
    serializer_class = RequestItemSerializer
    filterset_class = RequestItemFilterSet
    search_fields = ["brand", "model"]
