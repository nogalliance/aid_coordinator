from django.db.models import Case, F, Sum, When
from django.db.models.functions import Coalesce
from django_filters import CharFilter, NumberFilter
from django_filters.rest_framework import FilterSet
from rest_framework.fields import CharField, IntegerField
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
    amount = CharField(source="available")
    line = CharField(source="counted_name")

    class Meta:
        model = OfferItem
        fields = ["type", "brand", "model", "amount", "notes", "line"]


class RequestItemSerializer(HyperlinkedModelSerializer):
    type = StringRelatedField()
    amount = IntegerField(source="needed")

    class Meta:
        model = RequestItem
        fields = ["type", "brand", "model", "notes", "amount"]


# ViewSets define the view behavior
class OfferItemViewSet(ReadOnlyModelViewSet):
    queryset = (
        OfferItem.objects.select_related("type")
        .annotate(claimed=Coalesce(Sum("claim__amount"), 0))
        .annotate(available=Coalesce(F("amount") - F("claimed"), 0))
        .exclude(available__lte=0)
    )
    serializer_class = OfferItemSerializer
    filterset_class = OfferItemFilterSet
    search_fields = ["brand", "model", "notes"]


class RequestItemViewSet(ReadOnlyModelViewSet):
    queryset = (
        RequestItem.objects.select_related("type")
        .annotate(assigned=Coalesce(Sum("claim__amount"), 0))
        .annotate(
            needed=Case(
                When(up_to__isnull=False, then=F("up_to") - F("assigned")),
                default=F("amount") - F("assigned"),
            )
        )
        .exclude(needed__lte=0)
    )
    serializer_class = RequestItemSerializer
    filterset_class = RequestItemFilterSet
    search_fields = ["brand", "model"]
